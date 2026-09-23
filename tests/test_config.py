import importlib

import snntopo.config as config


def test_data_and_results_dirs_default_to_the_checkout(monkeypatch):
    monkeypatch.delenv("SNNTOPO_DATA_DIR", raising=False)
    monkeypatch.delenv("SNNTOPO_RESULTS_DIR", raising=False)
    module = importlib.reload(config)
    assert module.DATA_DIR == module.ROOT / "data" / "raw"
    assert module.RESULTS_DIR == module.ROOT / "results"


def test_data_and_results_dirs_honor_environment_overrides(monkeypatch, tmp_path):
    data_dir = tmp_path / "shared-data"
    results_dir = tmp_path / "shared-results"
    monkeypatch.setenv("SNNTOPO_DATA_DIR", str(data_dir))
    monkeypatch.setenv("SNNTOPO_RESULTS_DIR", str(results_dir))
    module = importlib.reload(config)
    assert module.DATA_DIR == data_dir
    assert module.RESULTS_DIR == results_dir
    monkeypatch.delenv("SNNTOPO_DATA_DIR")
    monkeypatch.delenv("SNNTOPO_RESULTS_DIR")
    importlib.reload(config)
