from unittest.mock import patch
from argparse import Namespace
from app.run import resolve_env


def test_resolve_env_dev():
    with patch(
        "argparse.ArgumentParser.parse_args",
        return_value=Namespace(dev=True, port=8000),
    ):
        assert resolve_env(True) == "development"


def test_resolve_env_production():
    with patch(
        "argparse.ArgumentParser.parse_args",
        return_value=Namespace(dev=False, port=8000),
    ):
        assert resolve_env(False) == "production"
