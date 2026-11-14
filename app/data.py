from functools import lru_cache
from pathlib import Path
import os
import pandas as pd

ROOT = Path(os.environ.get('DATA_DIR', '/project/data/entrada'))

@lru_cache(maxsize=1)
def catalogs():
    tiendas = pd.read_csv(ROOT / 'tiendas.csv')
    familias = pd.read_csv(ROOT / 'familias.csv')
    costos = pd.read_csv(ROOT / 'costos.csv')
    feriados = pd.read_csv(ROOT / 'feriados.csv')
    feriados['fecha'] = pd.to_datetime(feriados.fecha)
    stores = {int(x.tienda_id): str(x.ciudad) for x in tiendas.itertuples()}
    names = dict(zip(familias.familia_id, familias.nombre))
    costs = {r.familia_id: (float(r.costo_faltante), float(r.costo_sobrante)) for r in costos.itertuples()}
    holidays = {(r.fecha.date().isoformat(), r.ambito) for r in feriados.itertuples()}
    return stores, names, costs, holidays


def feature_table(rows):
    """Features knowable at forecast time only: date, store, family, promotion, holidays."""
    stores, names, costs, holidays = catalogs()
    df = pd.DataFrame(rows).copy()
    df['fecha'] = pd.to_datetime(df['fecha'])
    df['tienda_id'] = df['tienda_id'].astype(int)
    df['familia_id'] = df['familia_id'].astype(str)
    df['en_promocion'] = df['en_promocion'].astype(int)
    df['dia_semana'] = df.fecha.dt.dayofweek
    df['mes'] = df.fecha.dt.month
    df['dia_anio'] = df.fecha.dt.dayofyear
    df['feriado'] = [int((d.date().isoformat(), 'nacional') in holidays or
                         (d.date().isoformat(), stores[int(s)]) in holidays)
                      for d, s in zip(df.fecha, df.tienda_id)]
    return df[['tienda_id', 'familia_id', 'en_promocion', 'dia_semana', 'mes', 'dia_anio', 'feriado']]
