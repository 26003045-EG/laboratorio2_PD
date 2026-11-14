"""Entrenamiento, calibración y evaluación temporal sin servicios externos."""
import hashlib
import json
import numpy as np
import pandas as pd
from sklearn.base import BaseEstimator, RegressorMixin
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import HistGradientBoostingRegressor
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OrdinalEncoder
from app.data import feature_table
from app.business import metrics


class MedianBaseline(RegressorMixin, BaseEstimator):
    def fit(self, x, y):
        self.medians_ = pd.DataFrame({'family': x.familia_id, 'y': np.asarray(y)}).groupby('family').y.median().to_dict()
        self.global_ = float(np.median(y))
        return self

    def predict(self, x):
        return x.familia_id.map(self.medians_).fillna(self.global_).to_numpy()


def split_data(df, evaluation_start=None, evaluation_end=None):
    df = df.copy()
    df['fecha'] = pd.to_datetime(df.fecha)
    end = pd.Timestamp(evaluation_end) if evaluation_end is not None else df.fecha.max()
    start = pd.Timestamp(evaluation_start) if evaluation_start is not None else end - pd.Timedelta(days=27)
    calibration = start - pd.Timedelta(days=28)
    train = df[df.fecha < calibration]
    cal = df[(df.fecha >= calibration) & (df.fecha < start)]
    val = df[(df.fecha >= start) & (df.fecha <= end)]
    if len(train) < 1000 or len(cal) < 100 or len(val) < 1:
        raise ValueError('Datos insuficientes para entrenamiento, calibración o evaluación')
    return train, cal, val


def evaluate(df, costs, evaluation_start=None, evaluation_end=None):
    train, cal, val = split_data(df, evaluation_start, evaluation_end)
    xt, xc, xv = map(feature_table, (train, cal, val))
    baseline = MedianBaseline().fit(xt, train.ventas)
    model = Pipeline([
        ('prep', ColumnTransformer([('family', OrdinalEncoder(handle_unknown='use_encoded_value', unknown_value=-1), ['familia_id'])], remainder='passthrough')),
        ('model', HistGradientBoostingRegressor(max_iter=70, max_leaf_nodes=25, learning_rate=.09, random_state=42))])
    model.fit(xt, train.ventas)
    for fitted in (baseline, model):
        fitted.residual_sigma_ = float(np.std(cal.ventas.to_numpy() - np.maximum(fitted.predict(xc), 0)))
    result = {}
    for label, fitted in [('baseline', baseline), ('candidato', model)]:
        result[label] = metrics(val.ventas.to_numpy(), fitted.predict(xv), val.familia_id, costs, fitted.residual_sigma_)
    used = pd.concat([train, cal, val]).sort_values(['fecha', 'tienda_id', 'familia_id'])
    fingerprint = used.to_csv(index=False) + feature_table(used).to_csv(index=False) + json.dumps(costs, sort_keys=True)
    result['datos_sha256'] = hashlib.sha256(fingerprint.encode()).hexdigest()
    result['ventanas'] = {name: {'inicio': str(frame.fecha.min().date()), 'fin': str(frame.fecha.max().date()), 'filas': len(frame)}
                          for name, frame in [('entrenamiento', train), ('calibracion', cal), ('evaluacion', val)]}
    base_cost = result['baseline']['costo_medio']
    result['mejora_costo_pct'] = (1 - result['candidato']['costo_medio'] / base_cost) * 100 if base_cost else 0
    return model, baseline, val, result
