"""`snntopo run` and `snntopo status`: a spec file expanded into recipes and pairs, produced
and measured into one run directory (design.md "Runner", "Spec interface").

A spec is a Python file exporting TOPO (TopoConfig), CMP (dict(metrics, n_resamples)),
optionally PERSIST (dict(spikes="none"|"paired"|"all", weights=bool); default
producers.PERSIST_DEFAULT) and expand(mini) -> (recipes, pairs), where a pair is
{"a": recipe, "b": recipe, "condition": str, "h": int, "seeds": [int], "label": str}.

Resume is an anti-join: every invocation expands the spec, reads the rows already in the
run dir (every shard's files) and does only what is missing. There is no state file.

Phase 1, one activity at a time, sharded by stable_hash(training key or activity_id) % N so
one SNN training is never split across shards: produce -> spikes blob (if PERSIST) ->
signature rows -> self-null rows (each usable condition, h = n//2, seed 0) -> the activity
row, written last. The activity row is the commit marker: if an ok/degenerate one exists,
all of that activity's signature and self-null rows exist too. So resume never has to
guess an activity's conditions, and a concurrent shard's phase 2 never sees an activity
whose signature rows are still being written. A kill before the marker means the
activity is produced again; rows already on disk are skipped by key.

Phase 2, one pair at a time, sharded by stable_hash(pair_key) % N: pairs whose two sides
have ok/degenerate activity rows in this run dir -> per seed, compare at the pair's h plus
null rows for both sides at that h and seed (their halves are the ones compare just
cached). A side comes from the in-process cache, else store/spikes if persisted, else is
produced again from its recipe and must reproduce its recorded content_hash. Pairs with a
side not yet produced wait for a later run; pairs that can never run (a failed side, an
unusable condition, h too large) are reported as blocked.

A run dir holds one spec at one (topo_id, cmp_id) and one --mini setting; resuming with
a different one is refused. Each shard writes its own jsonl files and its own
run[.sIofN].json (a list of invocations), and holds an flock on .lock[.sIofN] while it
runs, so no two processes ever write one file.
"""
from __future__ import annotations

import fcntl
import hashlib
import importlib.util
import json
import numbers
import os
import socket
import subprocess
import sys
import time
import warnings
from collections import OrderedDict
from pathlib import Path

from . import config, dataset, measure, producers
from .contracts import Activity
from .logging_utils import setup_logging
from .topology import stats

SIDE_CACHE_SIZE = 16  # activities kept in memory for phase 2 (bio ~2.4 MB, SNN up to tens of MB)

# Cost model, orchestration.md "Cost model": seconds on this box with a full 16-core pool.
COST_PRODUCE = {"synthetic": 1.0, "bio": 5.0, "snn": 1.0}  # snn: evaluation of one checkpoint
COST_TRAIN_BASE, COST_TRAIN_PER_UPDATE = 5.0, 0.05  # ~15 s at 200 updates, ~155 s at 3000
COST_MEASURE = 12.0  # signature + self-nulls of one activity (~3 conditions) at n_resamples=50
COST_COMPARE = 3.0  # one compare call (one pair, one seed) at n_resamples=50 (E12: 3.2 s/pair)


# --- spec ----------------------------------------------------------------------------

def load_spec(path):
    """Import a spec file by path. Registered in sys.modules so dataclasses in it work."""
    path = Path(path).resolve()
    name = "snntopo_spec_" + hashlib.sha256(str(path).encode()).hexdigest()[:12]
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None:
        raise ValueError(f"cannot import spec {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    for attr in ("TOPO", "CMP", "expand"):
        if not hasattr(module, attr):
            raise ValueError(f"spec {path} does not define {attr}")
    return module


def expand(module, mini: bool) -> tuple[dict[str, dict], list[dict]]:
    """-> ({activity_id: recipe}, pairs). Activities are the spec's recipes followed by any
    pair side not among them; each pair gains a_id, b_id and pair_key."""
    recipes, pairs = module.expand(mini)
    activities = {}
    for recipe in recipes:
        activities.setdefault(dataset.recipe_id(recipe), recipe)
    out = []
    for pair in pairs:
        h, seeds = pair["h"], pair["seeds"]
        if (not isinstance(h, numbers.Integral) or h < 1 or not seeds
                or not all(isinstance(s, numbers.Integral) for s in seeds)):
            raise ValueError(f"pair {pair.get('label')!r}: h must be an int >= 1 and seeds a non-empty int list")
        a, b = dataset.recipe_id(pair["a"]), dataset.recipe_id(pair["b"])
        activities.setdefault(a, pair["a"])
        activities.setdefault(b, pair["b"])
        out.append({**pair, "h": int(h), "seeds": [int(s) for s in seeds], "a_id": a, "b_id": b,
                    "pair_key": dataset.pair_key(a, b)})
    return activities, out


def stable_hash(key: str) -> int:
    return int(hashlib.sha256(key.encode()).hexdigest()[:15], 16)


def group_key(recipe: dict) -> str:
    """Recipes sharing a training run share a group; everything else is its own group."""
    return producers.training_key(recipe) or dataset.recipe_id(recipe)


def in_shard(key: str, shard: tuple[int, int] | None) -> bool:
    return shard is None or stable_hash(key) % shard[1] == shard[0]


def _base(recipe: dict) -> dict:
    return recipe["of"] if recipe.get("kind") == "control" else recipe


def _persisted_ids(activities: dict[str, dict], pairs: list[dict], spikes: str) -> set[str]:
    """SNN activities (incl. controls of one) whose spikes PERSIST says to save."""
    if spikes not in ("none", "paired", "all"):
        raise ValueError(f"PERSIST spikes must be none|paired|all, not {spikes!r}")
    if spikes == "none":
        return set()
    named = activities if spikes == "all" else {p[s] for p in pairs for s in ("a_id", "b_id")}
    return {aid for aid in named if _base(activities[aid]).get("kind") == "snn"}


# --- rows already in the run dir -----------------------------------------------------

def read_rows(run_dir) -> tuple[dict[str, list[dict]], dict[str, int], list[str]]:
    """-> (rows per record type over every shard's file, row count per file, torn-line
    warnings)."""
    run_dir = Path(run_dir)
    rows = {t: [] for t in dataset.RECORD_TYPES}
    per_file, torn = {}, []
    for t in dataset.RECORD_TYPES:
        for path in sorted(run_dir.glob(f"{t}.jsonl")) + sorted(run_dir.glob(f"{t}.s*of*.jsonl")):
            with warnings.catch_warnings(record=True) as caught:
                warnings.simplefilter("always")
                got = dataset.read_jsonl(path)
            torn += [str(w.message) for w in caught]
            rows[t] += got
            per_file[path.name] = len(got)
    return rows, per_file, torn


def row_key(record_type: str, row: dict) -> tuple:
    return tuple(row[k] for k in dataset.KEYS[record_type])


class State:
    """What a run dir already holds, at one (topo_id, cmp_id)."""

    def __init__(self, rows: dict[str, list[dict]], topo_key: str, cmp_key: str, maxdim: int, metrics):
        self.topo_key, self.cmp_key = topo_key, cmp_key
        self.dims, self.metrics = range(maxdim + 1), sorted(metrics)
        self.status, self.content = {}, {}  # activity_id -> "done" | "failed"; -> content_hash
        for row in rows["activities"]:
            aid = row["activity_id"]
            if row["status"] in ("ok", "degenerate"):
                if self.status.get(aid) != "done":
                    self.content[aid] = row["content_hash"]
                self.status[aid] = "done"
            else:
                self.status.setdefault(aid, "failed")
        self.sigs = {}  # (activity_id, condition) -> (n_trials, skipped)
        for row in rows["signatures"]:
            if row["topo_id"] == topo_key:
                self.sigs[(row["activity_id"], row["condition"])] = (row["n_trials"], row["skipped"])
        self.keys = {t: {row_key(t, row) for row in rows[t]} for t in ("signatures", "nulls", "comparisons")}

    def self_null_keys(self, aid: str) -> set[tuple]:
        return {(aid, cond, self.topo_key, self.cmp_key, n // 2, 0, m, d)
                for (a, cond), (n, skipped) in self.sigs.items() if a == aid and skipped is None
                for m in self.metrics for d in self.dims}

    def comparison_keys(self, pair: dict, seed: int) -> set[tuple]:
        return {(pair["pair_key"], pair["condition"], self.topo_key, self.cmp_key, pair["h"], seed, m, d)
                for m in self.metrics for d in self.dims}

    def pair_null_keys(self, pair: dict, seed: int) -> set[tuple]:
        return {(side, pair["condition"], self.topo_key, self.cmp_key, pair["h"], seed, m, d)
                for side in (pair["a_id"], pair["b_id"]) for m in self.metrics for d in self.dims}

    def pair_state(self, pair: dict) -> tuple[str, str | None]:
        """-> ("done" | "ready" | "waiting" | "blocked", reason)."""
        cond, h = pair["condition"], pair["h"]
        for side in (pair["a_id"], pair["b_id"]):
            status = self.status.get(side)
            if status is None:
                return "waiting", f"activity {side} not produced yet"
            if status == "failed":
                return "blocked", f"activity {side} failed"
            sig = self.sigs.get((side, cond))
            if sig is None:
                return "blocked", f"activity {side} has no condition {cond!r}"
            if sig[1] is not None:
                return "blocked", f"activity {side} condition {cond!r} skipped: {sig[1]}"
            if 2 * h > sig[0]:
                return "blocked", f"h={h} needs {2 * h} trials; activity {side} {cond!r} has {sig[0]}"
        missing = any(not self.comparison_keys(pair, s) <= self.keys["comparisons"]
                      or not self.pair_null_keys(pair, s) <= self.keys["nulls"] for s in pair["seeds"])
        return ("ready" if missing else "done"), None


# --- git and run.json ----------------------------------------------------------------

def _git(args: list[str], cwd) -> str | None:
    """stdout of a git command, or None if it fails (not a repo, untracked file, ...)."""
    try:
        out = subprocess.run(["git", *args], cwd=cwd, capture_output=True, text=True)
    except FileNotFoundError:
        return None
    return out.stdout.strip() if out.returncode == 0 else None


def git_state(spec_path, code_root=None) -> dict:
    """code_rev of the code checkout; clean = the code checkout's and the spec's repo have
    no modified tracked files (untracked ones, like .nodeterm/, don't count) and the spec
    itself is tracked and unmodified."""
    spec_path = Path(spec_path).resolve()
    code_root = Path(code_root or config.ROOT)
    code_top = _git(["rev-parse", "--show-toplevel"], code_root)
    spec_top = _git(["rev-parse", "--show-toplevel"], spec_path.parent)
    tracked = spec_top is not None and _git(["ls-files", "--error-unmatch", str(spec_path)], spec_top) is not None
    unmodified = tracked and _git(["diff", "--quiet", "HEAD", "--", str(spec_path)], spec_top) is not None
    trees = [top for top in {code_top, spec_top} if top is not None]
    trees_clean = code_top is not None and all(
        _git(["status", "--porcelain", "--untracked-files=no"], top) == "" for top in trees)
    return {"code_rev": _git(["describe", "--always", "--dirty"], code_root),
            "spec_blob": _git(["hash-object", str(spec_path)], spec_path.parent),
            "spec_tracked": tracked, "clean": bool(trees_clean and unmodified)}


def is_experiment(spec_path) -> bool:
    """Preregistered specs live in experiments/ at a repo root (sweeps/ are exploratory)."""
    return Path(spec_path).resolve().parent.name == "experiments"


def run_json_path(run_dir, shard) -> Path:
    return Path(run_dir) / f"run{dataset.shard_suffix(shard)}.json"


def read_invocations(run_dir) -> list[dict]:
    out = []
    for path in sorted(Path(run_dir).glob("run*.json")):
        out += json.loads(path.read_text())["invocations"]
    return out


def _write_json(path: Path, obj) -> None:
    tmp = path.with_name(f".{path.name}.{os.getpid()}.tmp")
    tmp.write_text(json.dumps(obj, indent=1, default=dataset._json_default) + "\n")
    os.replace(tmp, path)


def _now() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%S%z")


def new_run_dir(spec_path) -> Path:
    """results/runs/<YYYYMMDD-HHMM>-<spec-stem>[-k], created atomically so two runs started
    in the same minute never share a dir."""
    base = Path(config.RESULTS_DIR) / "runs" / f"{time.strftime('%Y%m%d-%H%M')}-{Path(spec_path).stem}"
    base.parent.mkdir(parents=True, exist_ok=True)
    for k in range(1, 1000):
        path = base if k == 1 else base.with_name(f"{base.name}-{k}")
        try:
            path.mkdir()
            return path
        except FileExistsError:
            continue
    raise RuntimeError(f"no free run dir name for {base}")


# --- planning (dry-run, status, and the run itself) ----------------------------------

def plan(module, mini: bool, run_dir, shard, retry_failed: bool) -> dict:
    topo, cmp = module.TOPO, module.CMP
    topo_key, cmp_key = dataset.topo_id(topo), dataset.cmp_id(cmp["metrics"], cmp["n_resamples"])
    activities, pairs = expand(module, mini)
    rows, per_file, torn = read_rows(run_dir) if run_dir is not None and Path(run_dir).exists() else (
        {t: [] for t in dataset.RECORD_TYPES}, {}, [])
    state = State(rows, topo_key, cmp_key, topo.maxdim, cmp["metrics"])
    mine = [aid for aid in activities if in_shard(group_key(activities[aid]), shard)]
    todo = [aid for aid in mine if state.status.get(aid) is None
            or (retry_failed and state.status[aid] == "failed")]
    my_pairs = [p for p in pairs if in_shard(p["pair_key"], shard)]
    return {"topo": topo, "cmp": cmp, "topo_key": topo_key, "cmp_key": cmp_key, "activities": activities,
            "pairs": pairs, "mine": mine, "todo": todo, "my_pairs": my_pairs, "state": state,
            "rows": rows, "per_file": per_file, "torn": torn}


def _cost(p: dict, persisted: set[str]) -> tuple[float, str]:
    scale = p["cmp"]["n_resamples"] / 50
    def n_updates(base):
        return int(base.get("train", {}).get("n_updates", 3000))

    trainings, produce = {}, 0.0
    for aid in p["todo"]:
        base = _base(p["activities"][aid])
        produce += COST_PRODUCE.get(base.get("kind"), 1.0)
        if producers.training_key(base) is not None:
            trainings[producers.training_key(base)] = n_updates(base)
    state = p["state"]
    pending = [pr for pr in p["my_pairs"] if state.pair_state(pr)[0] in ("ready", "waiting")]
    compares = sum(len(pr["seeds"]) for pr in pending)
    # SNN sides not persisted may have to be trained again in phase 2 (an upper bound: a
    # side still in the in-process cache is not)
    regen = {}
    for pr in pending:
        for side in (pr["a_id"], pr["b_id"]):
            base = _base(p["activities"][side])
            if side not in persisted and producers.training_key(base) is not None:
                regen[producers.training_key(base)] = n_updates(base)
    train = sum(COST_TRAIN_BASE + COST_TRAIN_PER_UPDATE * n for n in trainings.values())
    regen_s = sum(COST_TRAIN_BASE + COST_TRAIN_PER_UPDATE * n for n in regen.values())
    measure_s = len(p["todo"]) * COST_MEASURE * scale
    compare_s = compares * COST_COMPARE * scale
    total = produce + train + measure_s + compare_s + regen_s
    detail = (f"produce {produce:.0f} s, train {len(trainings)}x {train:.0f} s, measure {len(p['todo'])}x "
              f"{measure_s:.0f} s, compare {compares}x {compare_s:.0f} s"
              + (f", phase-2 SNN retrain <= {len(regen)}x {regen_s:.0f} s" if regen else ""))
    return total, detail


def format_plan(p: dict, persisted: set[str], retry_failed: bool) -> list[str]:
    state = p["state"]
    mine = p["mine"]
    done = [a for a in mine if state.status.get(a) == "done"]
    failed = [a for a in mine if state.status.get(a) == "failed"]
    done_set = set(done)
    sig_rows = sum(1 for k in state.keys["signatures"] if k[0] in done_set and k[2] == p["topo_key"])
    null_expected = set()
    for aid in done:
        null_expected |= state.self_null_keys(aid)
    comp_expected, comp_blocked = set(), set()
    counts = {"done": 0, "ready": 0, "waiting": 0, "blocked": 0}
    for pr in p["my_pairs"]:
        st, _ = state.pair_state(pr)
        counts[st] += 1
        for s in pr["seeds"]:
            (comp_blocked if st == "blocked" else comp_expected).update(state.comparison_keys(pr, s))
            if st != "blocked":
                null_expected |= state.pair_null_keys(pr, s)
    null_done = len(null_expected & state.keys["nulls"])
    comp_done = len(comp_expected & state.keys["comparisons"])
    retry = "retried (--retry-failed)" if retry_failed else "not retried without --retry-failed"
    total, detail = _cost(p, persisted)
    return [
        f"activities   expanded {len(mine)} | done {len(done)} | failed {len(failed)} ({retry}) | to do {len(p['todo'])}",
        f"signatures   rows done {sig_rows} | to do: every row of the {len(p['todo'])} activities to produce "
        f"(conditions known after produce)",
        f"nulls        rows done {null_done} of {len(null_expected)} known (self + pair) | "
        f"+ self-nulls of the {len(p['todo'])} activities to produce",
        f"comparisons  rows done {comp_done} of {len(comp_expected)}"
        + (f" (+{len(comp_blocked)} blocked)" if comp_blocked else "")
        + f" | pairs: {counts['done']} done, {counts['ready']} ready, {counts['waiting']} waiting on activities, "
          f"{counts['blocked']} blocked",
        f"cost         ~{total / 60:.1f} min serial ({detail}); rough, from orchestration.md's cost model, "
        f"assumes a 16-core pool",
    ]


# --- run -----------------------------------------------------------------------------

def run(spec_path, out=None, shard: tuple[int, int] | None = None, mini: bool = False, dry_run: bool = False,
        retry_failed: bool = False, argv: list[str] | None = None) -> Path | None:
    spec_path = Path(spec_path).resolve()
    if shard is not None and out is None:
        raise SystemExit("--shard needs --out: all shards of one run share its dir")
    module = load_spec(spec_path)
    git = git_state(spec_path)
    exploratory = mini or not is_experiment(spec_path)
    refusal = None
    if is_experiment(spec_path) and not mini and not git["clean"]:
        refusal = (f"refusing {spec_path}: experiments run only from a clean tree with the spec committed "
                   f"(clean={git['clean']}, spec tracked={git['spec_tracked']}); use --mini for an exploratory run")
    persist = getattr(module, "PERSIST", None) or producers.PERSIST_DEFAULT

    if dry_run:
        p = plan(module, mini, out, shard, retry_failed)
        persisted = _persisted_ids(p["activities"], p["pairs"], persist.get("spikes", "none"))
        print(f"spec {spec_path}{' (mini)' if mini else ''} | shard {shard_label(shard)} | run dir "
              f"{out if out is not None and Path(out).exists() else '(new)'}")
        print(f"topo_id {p['topo_key']} | cmp_id {p['cmp_key']} | persist {persist}")
        for line in format_plan(p, persisted, retry_failed):
            print(line)
        if refusal:
            print(f"note: a real run would be refused: {refusal}")
        return None
    if refusal:
        raise SystemExit(refusal)

    run_dir = Path(out) if out is not None else new_run_dir(spec_path)
    topo_key = dataset.topo_id(module.TOPO)
    cmp_key = dataset.cmp_id(module.CMP["metrics"], module.CMP["n_resamples"])
    for inv in read_invocations(run_dir):  # run.json files are replaced atomically: safe to read
        theirs = (inv["spec"], inv["topo_id"], inv["cmp_id"], inv["mini"])
        if theirs != (str(spec_path), topo_key, cmp_key, mini):
            raise SystemExit(f"{run_dir} holds (spec, topo_id, cmp_id, mini) = {theirs}; this run is "
                             f"{(str(spec_path), topo_key, cmp_key, mini)}. Use a new --out.")
    run_dir.mkdir(parents=True, exist_ok=True)
    lock = open(run_dir / f".lock{dataset.shard_suffix(shard)}", "w")
    try:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except BlockingIOError:
        lock.close()
        raise SystemExit(f"another process is running shard {shard_label(shard)} of {run_dir}")

    log = setup_logging(f"run{dataset.shard_suffix(shard)}", run_dir / "logs")
    json_path = run_json_path(run_dir, shard)
    record = {"spec": str(spec_path), **git, "argv": argv if argv is not None else sys.argv,
              "host": socket.gethostname(), "shard": list(shard) if shard else None, "mini": mini,
              "exploratory": exploratory, "retry_failed": retry_failed, "topo_id": topo_key, "cmp_id": cmp_key,
              "persist": persist, "start": _now(), "end": None, "status": "running"}
    invocations = json.loads(json_path.read_text())["invocations"] if json_path.exists() else []
    invocations.append(record)
    _write_json(json_path, {"invocations": invocations})
    log.info(f"run {spec_path.name} -> {run_dir} shard {shard_label(shard)} code_rev {git['code_rev']} "
             f"clean {git['clean']}{' exploratory' if exploratory else ''}")

    disk_cache = stats.DISK_CACHE
    stats.DISK_CACHE = True
    writer = dataset.RunWriter(run_dir, shard=shard)
    try:
        summary = _run_phases(module, mini, run_dir, shard, retry_failed, persist, writer, log)
        record.update(end=_now(), status="done" if not summary["waiting"] else "incomplete", summary=summary)
    except BaseException as e:
        record.update(end=_now(), status="failed", error=f"{type(e).__name__}: {e}")
        raise
    finally:
        stats.DISK_CACHE = disk_cache
        writer.close()
        _write_json(json_path, {"invocations": invocations})
        lock.close()
    return run_dir


def shard_label(shard) -> str:
    return "all" if shard is None else f"{shard[0]}/{shard[1]}"


def _run_phases(module, mini, run_dir, shard, retry_failed, persist, writer, log) -> dict:
    topo, cmp = module.TOPO, module.CMP
    p = plan(module, mini, run_dir, shard, retry_failed)
    state, activities, pairs = p["state"], p["activities"], p["pairs"]
    persisted = _persisted_ids(activities, pairs, persist.get("spikes", "none"))
    pair_sides = {pr[s] for pr in pairs for s in ("a_id", "b_id")}
    keys = state.keys
    cache: OrderedDict[str, Activity] = OrderedDict()

    def write_new(record_type: str, row: dict) -> None:
        key = row_key(record_type, row)
        if key not in keys[record_type]:
            writer.write(record_type, row)
            keys[record_type].add(key)

    def remember(aid: str, activity: Activity) -> None:
        cache[aid] = activity
        cache.move_to_end(aid)
        while len(cache) > SIDE_CACHE_SIZE:
            cache.popitem(last=False)

    # phase 1: activities -> signatures -> self-nulls -> activity row (the commit marker)
    groups: OrderedDict[str, list[str]] = OrderedDict()
    for aid in p["todo"]:
        groups.setdefault(group_key(activities[aid]), []).append(aid)
    n_done = n_failed = 0
    log.info(f"phase 1: {len(p['todo'])} of {len(p['mine'])} activities in this shard to produce "
             f"({len(groups)} groups)")
    for aids in groups.values():
        t0 = time.time()
        for recipe, activity, row in producers.produce([activities[a] for a in aids],
                                                       persist_weights=bool(persist.get("weights", False))):
            aid = row["activity_id"]
            if activity is not None:
                if aid in persisted:
                    producers.save_activity(activity, row["content_hash"])  # blob before any row
                for r in measure.signature_rows(aid, activity, topo):
                    write_new("signatures", r)
                for r in measure.null_rows(aid, activity, topo, cmp, None, 0):
                    write_new("nulls", r)
                if aid in pair_sides:
                    remember(aid, activity)
            writer.write("activities", row)
            n_done += row["status"] != "failed"
            n_failed += row["status"] == "failed"
            log.info(f"activity {aid} {row['label']} {row['status']} ({time.time() - t0:.1f} s)"
                     + (f": {row['meta'].get('error')}" if row["status"] == "failed" else ""))

    # phase 2: pairs whose two sides exist in this run dir (any shard's rows)
    rows, _, _ = read_rows(run_dir)  # other shards may have produced sides meanwhile; own rows are flushed
    state = State(rows, p["topo_key"], p["cmp_key"], topo.maxdim, cmp["metrics"])
    keys = state.keys  # write_new's closure sees the rebinding
    waiting, blocked, n_pairs = [], [], 0
    for pair in p["my_pairs"]:
        st, why = state.pair_state(pair)
        if st == "waiting":
            waiting.append(f"{pair.get('label')}: {why}")
            continue
        if st == "blocked":
            blocked.append(f"{pair.get('label')}: {why}")
            continue
        if st == "done":
            continue
        sides, why = _sides(pair, activities, state, cache, remember)
        if sides is None:
            blocked.append(f"{pair.get('label')}: {why}")
            continue
        (a_id, a), (b_id, b) = sides
        cond, h = pair["condition"], pair["h"]
        t0 = time.time()
        for seed in pair["seeds"]:
            if not state.comparison_keys(pair, seed) <= keys["comparisons"]:
                for r in measure.comparison_rows(a_id, a, b_id, b, [cond], topo, cmp, h, seed,
                                                 pair.get("label", "")):
                    write_new("comparisons", r)
            if not state.pair_null_keys(pair, seed) <= keys["nulls"]:
                for side_id, act in ((a_id, a), (b_id, b)):
                    # only the pair's condition: an explicit h may be too large for the others
                    only = Activity(act.spikes, {cond: act.conditions[cond]}, act.window, act.bin_size_s)
                    for r in measure.null_rows(side_id, only, topo, cmp, h, seed):
                        write_new("nulls", r)
        n_pairs += 1
        log.info(f"pair {pair.get('label')} {cond} h={h} seeds={pair['seeds']} ({time.time() - t0:.1f} s)")

    for line in waiting:
        log.info(f"waiting: {line}")
    for line in blocked:
        log.warning(f"blocked: {line}")
    log.info(f"done: {n_done} activities produced, {n_failed} failed, {n_pairs} pairs compared, "
             f"{len(waiting)} waiting (rerun to pick them up), {len(blocked)} blocked")
    return {"produced": n_done, "failed": n_failed, "pairs": n_pairs, "waiting": len(waiting),
            "blocked": len(blocked)}


def _sides(pair, activities, state, cache, remember):
    """-> (((a_id, Activity), (b_id, Activity)), None) or (None, reason). Sides not in the
    cache come from store/spikes or are produced again (together, so SNN sides sharing a
    training are trained once) and must reproduce their recorded content_hash."""
    ids = [pair["a_id"], pair["b_id"]]
    missing = [aid for aid in dict.fromkeys(ids) if aid not in cache]
    regenerate = []
    for aid in missing:
        if dataset.store_has("spikes", state.content[aid], "npz"):
            remember(aid, producers.load_activity(state.content[aid]))
        else:
            regenerate.append(aid)
    if regenerate:
        for recipe, activity, row in producers.produce([activities[a] for a in regenerate]):
            aid = row["activity_id"]
            if activity is None:
                return None, f"activity {aid} failed when produced again: {row['meta'].get('error')}"
            remember(aid, activity)
    for aid in missing:
        got = producers.content_hash(cache[aid])
        if got != state.content[aid]:
            return None, (f"activity {aid} did not reproduce its content_hash ({got} != {state.content[aid]}); "
                          f"persist its spikes (PERSIST spikes='paired')")
    return tuple((aid, cache[aid]) for aid in ids), None


# --- status --------------------------------------------------------------------------

def status(run_dir) -> list[str]:
    run_dir = Path(run_dir)
    invocations = read_invocations(run_dir)
    if not invocations:
        raise SystemExit(f"{run_dir}: no run.json")
    out = [f"run {run_dir}"]
    last = {}
    for inv in invocations:
        last[shard_label(inv["shard"])] = inv
    for label, inv in last.items():
        n = sum(1 for i in invocations if shard_label(i["shard"]) == label)
        out.append(f"shard {label}: {inv['status']} (last of {n} invocations, {inv['start']} -> {inv['end']}, "
                   f"code_rev {inv['code_rev']}, clean {inv['clean']}"
                   + (", exploratory" if inv["exploratory"] else "") + ")")
    spec_path, mini = invocations[-1]["spec"], invocations[-1]["mini"]
    module = load_spec(spec_path)
    p = plan(module, mini, run_dir, None, retry_failed=False)
    out.append("rows per file:")
    out += [f"  {name:<32} {n}" for name, n in p["per_file"].items()]
    for warning in p["torn"]:
        out.append(f"warning: {warning}")
    failed = sorted(a for a, s in p["state"].status.items() if s == "failed")
    out.append(f"failed activities ({len(failed)}): {' '.join(failed) if failed else '-'}")
    for aid in p["mine"]:
        if p["state"].status.get(aid) == "done":
            gap = p["state"].self_null_keys(aid) - p["state"].keys["nulls"]
            if gap:
                out.append(f"warning: activity {aid} is marked done but lacks {len(gap)} self-null rows")
    out.append(f"vs expansion of {spec_path}{' (mini)' if mini else ''}:")
    persist = getattr(module, "PERSIST", None) or producers.PERSIST_DEFAULT
    out += ["  " + line for line in format_plan(p, _persisted_ids(p["activities"], p["pairs"],
                                                                   persist.get("spikes", "none")), False)]
    for pr in p["my_pairs"]:
        st, why = p["state"].pair_state(pr)
        if st in ("waiting", "blocked"):
            out.append(f"  {st}: {pr.get('label')}: {why}")
    return out
