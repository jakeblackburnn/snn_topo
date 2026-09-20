"""CLI argparse wiring: TopoConfig fields round-trip through --n-pca and friends."""
import argparse

from snntopo.cli import add_topo_args, topo_from_args
from snntopo.contracts import TopoConfig


def test_topo_from_args_round_trips_defaults():
    p = argparse.ArgumentParser()
    add_topo_args(p)
    args = p.parse_args([])
    assert topo_from_args(args) == TopoConfig()


def test_topo_from_args_honors_overrides():
    p = argparse.ArgumentParser()
    add_topo_args(p)
    args = p.parse_args(["--n-pca", "20"])
    assert topo_from_args(args) == TopoConfig(n_pca=20)
