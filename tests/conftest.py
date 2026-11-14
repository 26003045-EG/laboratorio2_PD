"""Archivos temporales dentro del proyecto, también en entornos restringidos."""
from pathlib import Path
from uuid import uuid4
import pytest


@pytest.fixture
def work_path():
    path = Path(__file__).resolve().parents[1] / 'shared' / 'tests' / uuid4().hex
    path.mkdir(parents=True)
    return path
