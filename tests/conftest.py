import os

# SNN tests run on CPU (requirements.md: same recipe -> same content_hash on CPU); set before
# snntopo.producers reads it, and inherited by the runner tests' subprocesses
os.environ.setdefault("SNNTOPO_DEVICE", "cpu")
