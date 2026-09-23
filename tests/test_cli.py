"""CLI argparse wiring: TopoConfig fields round-trip through --n-pca and friends."""
import argparse
from dataclasses import fields

from snntopo.cli import add_topo_args, topo_from_args
from snntopo.contracts import TopoConfig


def test_topo_from_args_round_trips_defaults():
    p = argparse.ArgumentParser()
    add_topo_args(p)
    args = p.parse_args([])
    assert set(vars(args)) >= {f.name for f in fields(TopoConfig)}
    assert topo_from_args(args) == TopoConfig()


def test_topo_from_args_honors_overrides():
    p = argparse.ArgumentParser()
    add_topo_args(p)
    args = p.parse_args(["--n-pca", "20", "--residualize-raw-diameter"])
    assert topo_from_args(args) == TopoConfig(n_pca=20, residualize_raw_diameter=True)
