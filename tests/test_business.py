import numpy as np
import pytest
from app.business import metrics, should_promote, suggestions


def test_costos_reales():
    result = metrics([10, 10], [8, 12], ['a', 'a'], {'a': (1, 1)}, 0)
    assert result == {'mae': 2, 'costo_medio': 2, 'costo_total': 4}


def test_faltantes_caros_aumentan_reserva():
    assert suggestions([100], ['a'], {'a': (9, 1)}, 10)[0] > 100
    assert suggestions([100], ['a'], {'a': (1, 9)}, 10)[0] < 100


@pytest.mark.parametrize('candidate,baseline,old,expected', [
    (99.5, 110, 100, True), (99.6, 110, 100, False),
    (100, 100, None, False), (90, 100, None, True),
    (0, 10, 0, False), (np.nan, 10, 20, False), (1, 0, 10, False)])
def test_criterio(candidate, baseline, old, expected):
    assert bool(should_promote(candidate, baseline, old)) == expected


def test_costos_invalidos():
    with pytest.raises(ValueError):
        suggestions([100], ['a'], {'a': (0, 0)}, 10)
