import numpy as np
import pandas as pd
import pytest
from training.evaluation import split_data, evaluate


def frame():
    dates = pd.date_range('2024-01-01', periods=130)
    return pd.DataFrame([{'fecha': d, 'tienda_id': 1, 'familia_id': 'a',
                          'ventas': 10 + d.dayofweek, 'en_promocion': 0}
                         for d in dates for _ in range(20)])


def test_ventanas_disjuntas():
    train, cal, val = split_data(frame())
    assert train.fecha.max() < cal.fecha.min() < val.fecha.min()
    assert cal.fecha.max() < val.fecha.min()
    assert (val.fecha.max() - val.fecha.min()).days == 27


def test_insuficientes():
    with pytest.raises(ValueError):
        split_data(frame().head(10))


def test_ventas_evaluacion_no_calibran(monkeypatch):
    import training.evaluation as module
    monkeypatch.setattr(module, 'feature_table', lambda df: df[['tienda_id', 'familia_id', 'en_promocion']])
    df = frame()
    first, _, _, _ = evaluate(df, {'a': (2, 1)})
    df.loc[df.fecha >= df.fecha.max() - pd.Timedelta(days=27), 'ventas'] = 100000
    second, _, _, _ = evaluate(df, {'a': (2, 1)})
    assert first.residual_sigma_ == second.residual_sigma_
    assert np.array_equal(first.predict(module.feature_table(df)), second.predict(module.feature_table(df)))
