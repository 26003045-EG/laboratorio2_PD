"""Una sola política de inventario para evaluación y servicio."""
from statistics import NormalDist
import numpy as np


def suggestions(preds, families, costs, uncertainty):
    values = []
    for y, family in zip(preds, families):
        cf, cs = costs[family]
        if not np.isfinite([cf, cs, y, uncertainty]).all() or cf <= 0 or cs <= 0:
            raise ValueError('Costos, predicción o incertidumbre inválidos')
        y = max(float(y), 0)
        z = NormalDist().inv_cdf(cf / (cf + cs))
        values.append(max(0, int(np.ceil(y + z * max(uncertainty, .1 * y, 1)))))
    return np.array(values)


def metrics(actual, predicted, families, costs, uncertainty):
    actual, predicted = np.asarray(actual), np.maximum(predicted, 0)
    suggested = suggestions(predicted, families, costs, uncertainty)
    cf = np.array([costs[f][0] for f in families])
    cs = np.array([costs[f][1] for f in families])
    cost = cf * np.maximum(actual - suggested, 0) + cs * np.maximum(suggested - actual, 0)
    if not len(actual) or not np.isfinite(cost).all():
        raise ValueError('Evaluación vacía o inválida')
    return {'mae': float(np.mean(abs(actual - predicted))),
            'costo_medio': float(np.mean(cost)), 'costo_total': float(np.sum(cost))}


def should_promote(candidate, baseline, incumbent=None):
    values = [candidate, baseline] + ([] if incumbent is None else [incumbent])
    if not np.isfinite(values).all() or min(values) < 0:
        return False
    return candidate < baseline and (incumbent is None or candidate <= incumbent * .995 and candidate < incumbent)
