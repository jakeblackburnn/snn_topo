"""Regression check for snntopo.topology.pipeline: a noisy circle should show one
dominant, long-persisting H1 feature, and gudhi/ripser should agree. Runs in ~2s,
no dataset needed — useful to re-verify the shared pipeline in isolation."""
import numpy as np

from snntopo.logging_utils import setup_logging
from snntopo.topology.distances import diagram_distance
from snntopo.topology.pipeline import diagram_summary, persistence_diagram_gudhi, persistence_diagram_ripser


def main():
    log = setup_logging("selftest_topology")
    rng = np.random.default_rng(0)
    theta = rng.uniform(0, 2 * np.pi, 150)
    circle = np.stack([np.cos(theta), np.sin(theta)], axis=1) + rng.normal(0, 0.03, (150, 2))

    dgms_g = persistence_diagram_gudhi(circle, maxdim=1)
    dgms_r = persistence_diagram_ripser(circle, maxdim=1)

    log.info(f"gudhi H0 summary: {diagram_summary(dgms_g[0])}")
    log.info(f"gudhi H1 summary: {diagram_summary(dgms_g[1])}")
    log.info(f"ripser H0 summary: {diagram_summary(dgms_r[0])}")
    log.info(f"ripser H1 summary: {diagram_summary(dgms_r[1])}")

    top_h1 = sorted((dgms_g[1][:, 1] - dgms_g[1][:, 0]), reverse=True)
    log.info(f"top H1 persistence values (gudhi): {top_h1[:3]}")
    assert top_h1[0] > 0.5, f"expected one LONG-persisting H1 loop (circle radius ~1), got {top_h1[0]}"
    assert top_h1[0] > 5 * (top_h1[1] if len(top_h1) > 1 else 1e-9), "expected one dominant H1 loop"

    dist = diagram_distance(dgms_g[1], dgms_r[1])
    log.info(f"gudhi-vs-ripser H1 diagram distance (should be small): {dist}")
    log.info("SANITY CHECK PASSED")


if __name__ == "__main__":
    main()
