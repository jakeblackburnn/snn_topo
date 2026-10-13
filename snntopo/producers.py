"""Recipe producers for the v3 activity dataset.

Recipes are deliberately plain dictionaries: their canonical representation is the
activity id, while this module turns them into an ``Activity`` and a row ready for a
``RunWriter``.  A malformed recipe is data, not a runner failure, so ``produce``
returns a failed row instead of propagating its exception.
"""
from __future__ import annotations

import copy
import hashlib
import io
import os
import time
import traceback
from collections import defaultdict
from dataclasses import asdict
from typing import Iterator

import numpy as np
import torch

from . import dataset, generators
from .contracts import Activity, ModelConfig, TopoConfig, TrainConfig
from .data import load_session
from .data import steinmetz
from .evaluate import evaluate, policy_logits
from .models import build_model, build_rate_model
from .tasks import TASKS
from .training import train
from .topology.pipeline import compute_signature


# CUDA re-runs are bit-identical (recurrent LIF, 256 units, 200 updates), so SNN activities can be
# regenerated on the same device unless a spec asks to keep them. Trained CUDA and CPU spikes differ
# (checkpoint 0 agrees), which the runner's content_hash check on regeneration catches.
PERSIST_DEFAULT = dict(spikes="none", weights=False)

# SNNTOPO_DEVICE=cpu forces CPU (tests, a busy GPU). The device goes in meta, not the recipe, so one
# recipe names one model; a run's content_hash records which spikes it actually measured
DEVICE = os.environ.get("SNNTOPO_DEVICE") or ("cuda" if torch.cuda.is_available() else "cpu")


def training_key(recipe: dict) -> str | None:
    """The one unit that may share a training run across recipes."""
    base = recipe.get("of", recipe) if recipe.get("kind") == "control" else recipe
    if base.get("kind") != "snn" or base.get("family") not in ("snn", "rate"):
        return None
    return dataset.short_hash({k: base[k] for k in ("family", "task", "model", "train")})


def _activity_arrays(activity: Activity) -> dict[str, np.ndarray]:
    arrays = {
        "spikes": np.ascontiguousarray(activity.spikes),
        "window": np.array([activity.window.start, activity.window.stop,
                            1 if activity.window.step is None else activity.window.step], dtype=np.int64),
        "bin_size_s": np.array(activity.bin_size_s, dtype=np.float64),
    }
    arrays.update({f"mask:{name}": np.ascontiguousarray(activity.conditions[name], dtype=np.bool_)
                   for name in sorted(activity.conditions)})
    return arrays


def content_hash(activity: Activity) -> str:
    """Fingerprint exactly the numerical activity and its trial semantics."""
    return dataset.array_hash(_activity_arrays(activity))


def save_activity(activity: Activity, key: str, root=None) -> None:
    arrays = _activity_arrays(activity)
    spikes = arrays.pop("spikes")
    # Most SNN activity is 0/1. Packing it saves material disk without changing the
    # in-memory Activity contract; synthetic and bio counts retain their exact dtype.
    if np.all((spikes == 0) | (spikes == 1)):
        arrays["packed_spikes"] = np.packbits(spikes.astype(np.uint8).ravel())
        arrays["spikes_shape"] = np.asarray(spikes.shape, dtype=np.int64)
        arrays["spikes_dtype"] = np.asarray(spikes.dtype.str)
    else:
        arrays["spikes"] = spikes
    dataset.store_put_npz("spikes", arrays, key=key, root=root)


def load_activity(key: str, root=None) -> Activity:
    arrays = dataset.store_get_npz("spikes", key, root=root)
    if "packed_spikes" in arrays:
        shape = tuple(int(x) for x in arrays["spikes_shape"])
        n = int(np.prod(shape))
        dtype = np.dtype(str(arrays["spikes_dtype"].item()))
        spikes = np.unpackbits(arrays["packed_spikes"], count=n).reshape(shape).astype(dtype)
    else:
        spikes = arrays["spikes"]
    conditions = {name.removeprefix("mask:"): arrays[name].astype(bool)
                  for name in arrays if name.startswith("mask:")}
    start, stop, step = (int(x) for x in arrays["window"])
    return Activity(spikes, conditions, slice(start, stop, step), float(arrays["bin_size_s"]))


def _subset(activity: Activity, mask: np.ndarray, unit_indices: np.ndarray | None = None) -> Activity:
    if mask.dtype != bool or mask.shape != (activity.spikes.shape[1],):
        raise ValueError("trial selector did not produce a full boolean trial mask")
    spikes = activity.spikes if unit_indices is None else activity.spikes[unit_indices]
    conditions = {name: (mask if name == "all" else (base & mask))
                  for name, base in activity.conditions.items()}
    conditions["all"] = mask
    return Activity(spikes, conditions, activity.window, activity.bin_size_s)


def subsample(activity: Activity, spec: dict) -> Activity:
    """`units` neurons and `trials` of the `all` trials, one seeded draw: puts bio and SNN
    activities at the same (units x trials) scale, since the split-half null depends on both."""
    rng = np.random.default_rng(spec["seed"])
    n_units, n_trials = int(spec["units"]), int(spec["trials"])
    pool = np.flatnonzero(activity.conditions["all"])
    if n_units > activity.spikes.shape[0] or n_trials > len(pool):
        raise ValueError(f"cannot subsample {n_units} units x {n_trials} trials "
                         f"from {activity.spikes.shape[0]} x {len(pool)}")
    units = np.sort(rng.choice(activity.spikes.shape[0], n_units, replace=False))
    mask = np.zeros(activity.spikes.shape[1], dtype=bool)
    mask[rng.choice(pool, n_trials, replace=False)] = True
    return _subset(activity, mask, units)


def bio_activity(recipe: dict) -> tuple[Activity, dict]:
    if recipe.get("dataset") != "steinmetz":
        raise NotImplementedError(f"bio dataset {recipe.get('dataset')!r} is not implemented")
    session = str(recipe["session"])
    block = recipe.get("block", "active")
    if block not in ("active", "passive"):
        raise ValueError("bio block must be 'active' or 'passive'")
    loaded = load_session("steinmetz", session + ("/passive" if block == "passive" else ""))
    trial = steinmetz.trial_arrays(session, block)
    n_trials = loaded.activity.spikes.shape[1]
    select = recipe.get("trials", {}).get("select", "all")
    if block == "active":
        response = trial["response"]
        selectors = {"responded": response != 0, "nogo": response == 0, "all": np.ones(n_trials, dtype=bool)}
        if select not in selectors:
            raise ValueError(f"unknown active trial selection {select!r}")
        mask = selectors[select].copy()
    elif select == "all":
        mask = np.ones(n_trials, dtype=bool)
    else:
        raise ValueError("passive trials only support select='all'")
    contrast = recipe.get("trials", {}).get("contrast")
    if contrast is not None:
        left, right = contrast
        mask &= np.isclose(trial["contrast_left"], left) & np.isclose(trial["contrast_right"], right)
    trial_range = recipe.get("trials", {}).get("range")
    if trial_range is not None:
        start, stop = trial_range
        selected = np.flatnonzero(mask)
        keep = np.zeros(n_trials, dtype=bool)
        keep[selected[start:stop]] = True
        mask &= keep

    units = recipe.get("units", {})
    regions = np.asarray(steinmetz._session_data(session)["brain_area"]).astype(str)
    unit_indices = np.arange(len(regions))
    if units.get("area") is not None:
        unit_indices = unit_indices[regions == units["area"]]
        if not len(unit_indices):
            raise KeyError(f"unknown/empty Steinmetz area {units['area']!r}")
    if units.get("subsample") is not None:
        spec = units["subsample"]
        n = int(spec["n"])
        if n > len(unit_indices):
            raise ValueError(f"cannot subsample {n} from {len(unit_indices)} units")
        unit_indices = np.sort(np.random.default_rng(spec["seed"]).choice(unit_indices, n, replace=False))
    if units.get("split") is not None:
        spec = units["split"]
        half = int(spec["half"])
        if half not in (0, 1):
            raise ValueError("unit split half must be 0 or 1")
        perm = np.random.default_rng(spec["seed"]).permutation(unit_indices)
        unit_indices = perm[:len(perm) // 2] if half == 0 else perm[len(perm) // 2:]
    activity = _subset(loaded.activity, mask, unit_indices)
    return activity, {**loaded.meta, "subject": loaded.meta.get("subject"), "n_units": int(len(unit_indices))}


def synthetic_activity(recipe: dict) -> tuple[Activity, dict]:
    name = recipe["generator"]
    if name not in generators.GENERATORS:
        raise KeyError(f"unknown synthetic generator {name!r}")
    fields = ("seed", "n_neurons", "n_trials", "n_bins", "noise_level", "mixing_seed")
    activity = generators.GENERATORS[name](**{k: recipe[k] for k in fields if k in recipe})
    return activity, {"n_units": int(activity.spikes.shape[0])}


def _evaluate_spontaneous(model, task, n_eval: int, device: str, seed: int) -> tuple[float | None, Activity]:
    model.eval()
    torch.manual_seed(seed)
    inputs = torch.zeros(task.num_steps, n_eval, task.n_in, device=device)
    with torch.no_grad():
        hidden, _ = model(inputs)
    model.train()
    spikes = hidden.permute(2, 1, 0).cpu().numpy().astype(np.float32)
    return None, Activity(spikes, {"all": np.ones(n_eval, dtype=bool)}, slice(0, task.num_steps), 1.0)


def _model_and_train(base: dict, checkpoints: set[int], device: str) -> tuple[dict, object, object]:
    task = TASKS[base["task"]]
    train_cfg = TrainConfig(**base["train"])
    torch.manual_seed(train_cfg.seed)  # before build_model: this is the v1 seeding bug fix.
    if base.get("family") == "snn":
        model = build_model(ModelConfig(**base["model"]), task.n_in, task.n_actions)
    elif base.get("family") == "rate":
        model = build_rate_model(base["model"], task.n_in, task.n_actions)
    else:
        raise ValueError(f"unknown SNN family {base.get('family')!r}")
    model = model.to(device)
    result = train(model, task, train_cfg, device, checkpoints=sorted(checkpoints))
    return result, model, task


def snn_activity(recipe: dict, trained: tuple[dict, object, object] | None = None,
                 device: str | None = None) -> tuple[Activity, dict, float | None]:
    """Evaluate a checkpointed spiking or rate family into count-valued Activity."""
    device = device or DEVICE
    family = recipe.get("family")
    if family not in ("snn", "rate"):
        raise NotImplementedError(f"SNN family {family!r} is not implemented")
    checkpoint = int(recipe.get("checkpoint", 0))
    if trained is None:
        trained = _model_and_train(recipe, {checkpoint}, device)
    result, model, task = trained
    if result["status"] == "failed":
        raise RuntimeError(result["error"] or "training failed")
    if checkpoint not in result["checkpoints"]:
        raise ValueError(f"checkpoint {checkpoint} was not captured")
    model.load_state_dict(result["checkpoints"][checkpoint])
    ev = recipe.get("eval", {})
    n_eval, seed, regime = int(ev.get("n_eval", 340)), int(ev.get("seed", 1)), ev.get("regime", "task")
    if regime == "task":
        accuracy, activity = evaluate(model, task, n_eval, device, seed=seed)
    elif regime == "spontaneous":
        accuracy, activity = _evaluate_spontaneous(model, task, n_eval, device, seed)
    else:
        raise ValueError(f"unknown SNN evaluation regime {regime!r}")
    if family == "rate":
        gain = recipe.get("gain")
        if gain is None or float(gain) <= 0:
            raise ValueError("rate recipes require a positive recorded gain")
        # This generator is deliberately separate from evaluation/model RNG: a resolved
        # recipe's eval seed fixes the Poisson draw as well as the task trials.
        generator = torch.Generator(device=device).manual_seed(seed)
        rates = torch.from_numpy(activity.spikes).to(device)
        counts = torch.poisson(rates * float(gain), generator=generator).cpu().numpy().astype(np.float32)
        activity = Activity(counts, activity.conditions, activity.window, activity.bin_size_s)
    return activity, {"train_elapsed_s": result["elapsed_s"], "n_updates_done": result["n_updates_done"],
                       "device": device, "max_memory_allocated": int(torch.cuda.max_memory_allocated(device))
                       if device.startswith("cuda") else 0}, accuracy


def _label(recipe: dict) -> str:
    if recipe.get("kind") == "bio":
        return f"{recipe.get('dataset')}:{recipe.get('session')}:{recipe.get('block', 'active')}"
    if recipe.get("kind") == "synthetic":
        return f"synthetic:{recipe.get('generator')}:{recipe.get('seed')}"
    if recipe.get("kind") == "snn":
        return f"snn:{recipe.get('task')}:{recipe.get('checkpoint', 0)}:{recipe.get('eval', {}).get('regime', 'task')}"
    return f"control:{recipe.get('surrogate')}"


def _row(recipe: dict, activity: Activity | None, status: str, meta: dict, accuracy=None) -> dict:
    kind = recipe.get("kind")
    base = recipe.get("of", {}) if kind == "control" else recipe
    model = base.get("model", {}) if base.get("kind") == "snn" else {}
    train_cfg = base.get("train", {}) if base.get("kind") == "snn" else {}
    return {
        "activity_id": dataset.recipe_id(recipe), "recipe": recipe, "label": _label(recipe),
        "kind": kind, "family": base.get("family"), "dataset": base.get("dataset"),
        "session": str(base["session"]) if base.get("session") is not None else None,
        "subject": base.get("subject", meta.get("subject")), "task": base.get("task"), "arch": model.get("arch"),
        "neuron": model.get("neuron"), "connectivity": model.get("connectivity"),
        "n_hidden": model.get("n_hidden"), "seed": train_cfg.get("seed", base.get("seed")),
        "checkpoint": base.get("checkpoint"), "regime": base.get("eval", {}).get("regime"),
        "n_units": None if activity is None else int(activity.spikes.shape[0]),
        "independence_group": (f"steinmetz:{base['session']}" if base.get("kind") == "bio"
                               else f"{kind}:{dataset.recipe_id(recipe)}"),
        "status": status, "accuracy": accuracy,
        "content_hash": None if activity is None else content_hash(activity), "meta": meta,
    }


def _produce_one(recipe: dict, trained=None) -> tuple[Activity, dict, float | None]:
    kind = recipe.get("kind")
    if kind == "bio":
        activity, meta = bio_activity(recipe)
        return activity, meta, None
    if kind == "synthetic":
        activity, meta = synthetic_activity(recipe)
        return activity, meta, None
    if kind == "snn":
        return snn_activity(recipe, trained)
    if kind == "control":
        original, meta, accuracy = _produce_one(recipe["of"], trained)
        surrogate = recipe["surrogate"]
        if surrogate == "shuffled":
            from .controls import shuffled
            return shuffled(original, int(recipe.get("seed", 0))), meta, accuracy
        if surrogate == "untrained":
            base = recipe["of"]
            if base.get("kind") != "snn":
                raise ValueError("untrained control requires an SNN recipe")
            untrained = {**base, "checkpoint": 0}
            return snn_activity(untrained, trained)
        raise ValueError(f"unknown control surrogate {surrogate!r}")
    raise ValueError(f"unknown recipe kind {kind!r}")


def _checkpoint_requests(recipe: dict, out: dict[str, set[int]]) -> None:
    if recipe.get("kind") == "snn" and training_key(recipe) is not None:
        out[training_key(recipe)].add(int(recipe.get("checkpoint", 0)))
    if recipe.get("kind") == "control" and isinstance(recipe.get("of"), dict):
        _checkpoint_requests(recipe["of"], out)
        if recipe.get("surrogate") == "untrained" and training_key(recipe["of"]) is not None:
            out[training_key(recipe["of"])].add(0)


def _train(base: dict, checkpoints: set[int], persist_weights: bool):
    """-> _model_and_train's result, or the exception, so every recipe of a failed training
    becomes a failed row instead of stopping the others."""
    try:
        trained = _model_and_train(base, checkpoints, DEVICE)
        if persist_weights:
            result = trained[0]
            for checkpoint, state in result["checkpoints"].items():
                buf = io.BytesIO()
                torch.save(state, buf)
                weight_key = hashlib.sha256(buf.getvalue()).hexdigest()[:16]
                dataset.store_put_bytes("weights", weight_key, "pt", buf.getvalue())
                result.setdefault("weight_keys", {})[checkpoint] = weight_key
        return trained
    except Exception as error:
        return error


def produce(recipes: list[dict], persist_weights: bool = False) -> Iterator[tuple[dict, Activity | None, dict]]:
    """Yield one completed producer result per input recipe; bad inputs become rows."""
    requests: dict[str, set[int]] = defaultdict(set)
    bases: dict[str, dict] = {}
    for recipe in recipes:
        try:
            _checkpoint_requests(recipe, requests)
            base = recipe.get("of", recipe) if recipe.get("kind") == "control" else recipe
            key = training_key(base)
            if key is not None:
                bases.setdefault(key, base)
        except Exception:
            pass
    remaining = defaultdict(int)  # recipes still to yield per training, so a model is freed after its last one
    for recipe in recipes:
        try:
            key = training_key(recipe)
        except Exception:
            key = None
        if key is not None:
            remaining[key] += 1
    trained = {}
    for recipe in recipes:
        try:
            key = training_key(recipe)
        except Exception:
            key = None
        try:
            source = recipe.get("of") if recipe.get("kind") == "control" else recipe
            if key is not None and key not in trained:
                # trained lazily, in recipe order: the runner puts a training's recipes next to each
                # other, so rows land as each training finishes and only one model is held at a time
                trained[key] = _train(bases[key], requests[key], persist_weights)
            state = trained.get(key) if key else None
            if isinstance(state, Exception):
                raise state
            activity, meta, accuracy = _produce_one(recipe, state)
            if recipe.get("subsample") is not None:
                activity = subsample(activity, recipe["subsample"])
            if state and persist_weights:
                checkpoint = 0 if recipe.get("kind") == "control" and recipe.get("surrogate") == "untrained" else int(source.get("checkpoint", 0))
                meta["weights"] = state[0].get("weight_keys", {}).get(checkpoint)
            if source.get("kind") == "snn":
                required = ("all",) if source.get("eval", {}).get("regime") == "spontaneous" else TASKS[source["task"]].action_names
                signature = compute_signature(activity, TopoConfig())
                status = "degenerate" if any(condition in signature.skipped for condition in required) else "ok"
            else:
                status = "ok"
            row = _row(recipe, activity, status, meta, accuracy)
        except Exception as error:
            activity, row = None, _row(recipe, None, "failed", {"error": f"{type(error).__name__}: {error}"})
        if key is not None:
            remaining[key] -= 1
            if remaining[key] == 0:
                trained.pop(key, None)
        yield recipe, activity, row


PRODUCERS = {"bio": bio_activity, "synthetic": synthetic_activity, "snn": snn_activity}
