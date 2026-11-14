import json
import os
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

DB_URL = os.getenv('DATABASE_URL', 'postgresql+psycopg2://nova:nova@db:5432/nova')
engine = create_engine(DB_URL, pool_pre_ping=True)
Session = sessionmaker(bind=engine)

DDL = [
 '''CREATE TABLE IF NOT EXISTS solicitudes (id BIGSERIAL PRIMARY KEY, tienda_id INT NOT NULL, fecha DATE NOT NULL, payload JSONB NOT NULL, calidad JSONB NOT NULL, creado TIMESTAMPTZ NOT NULL DEFAULT NOW())''',
 '''CREATE TABLE IF NOT EXISTS predicciones (id BIGSERIAL PRIMARY KEY, solicitud_id BIGINT REFERENCES solicitudes(id), tienda_id INT NOT NULL, fecha DATE NOT NULL, familia_id TEXT NOT NULL, en_promocion INT NOT NULL, venta_esperada DOUBLE PRECISION NOT NULL, cantidad_sugerida INT NOT NULL, version_modelo TEXT NOT NULL, creado TIMESTAMPTZ NOT NULL DEFAULT NOW())''',
 '''CREATE TABLE IF NOT EXISTS observaciones (tienda_id INT NOT NULL, fecha DATE NOT NULL, familia_id TEXT NOT NULL, ventas INT NOT NULL, actualizado TIMESTAMPTZ DEFAULT NOW(), PRIMARY KEY(tienda_id, fecha, familia_id))''',
 '''CREATE TABLE IF NOT EXISTS informes_observaciones (id BIGSERIAL PRIMARY KEY, tienda_id INT NOT NULL, fecha DATE NOT NULL, payload JSONB NOT NULL, calidad JSONB NOT NULL, cread TIMESTAMPTZ NOT NULL DEFAULT NOW())'''
]

def init_db():
    with engine.begin() as con:
        for ddl in DDL:
            con.execute(text(ddl))


def save_predictions(req, quality, version, items):
    with engine.begin() as con:
        res = con.execute(text('INSERT INTO solicitudes(tienda_id,fecha,payload,calidad) VALUES (:s,:d,CAST(:p AS jsonb),CAST(:q AS jsonb)) RETURNING id'),
                          {'s': req.tienda_id, 'd': req.fecha, 'p': req.model_dump_json(), 'q': quality.model_dump_json()})
        sid = res.scalar_one()
        promos = {x.familia_id: x.en_promocion for x in req.familias}
        for x in items:
            con.execute(text('INSERT INTO predicciones(solicitud_id,tienda_id,fecha,familia_id,en_promocion,venta_esperada,cantidad_sugerida,version_modelo) VALUES (:i,:s,:d,:f,:p,:v,:c,:m)'),
                        {'i': sid, 's': req.tienda_id, 'd': req.fecha, 'f': x.familia_id, 'p': promos[x.familia_id], 'v': x.venta_esperada, 'c': x.cantidad_sugerida, 'm': version})


def save_observations(req, quality):
    count = 0
    with engine.begin() as con:
        con.execute(text('INSERT INTO informes_observaciones(tienda_id,fecha,payload,calidad) VALUES (:s,:d,CAST(:p AS jsonb),CAST(:q AS jsonb))'),
                    {'s': req.tienda_id, 'd': req.fecha, 'p': req.model_dump_json(), 'q': quality.model_dump_json()})
        for x in req.ventas:
            result = con.execute(text('''INSERT INTO observaciones(tienda_id,fecha,familia_id,ventas) VALUES (:s,:d,:f,:v)
            ON CONFLICT (tienda_id,fecha,familia_id) DO UPDATE SET ventas=EXCLUDED.ventas, actualizado=NOW()
            WHERE observaciones.ventas IS DISTINCT FROM EXCLUDED.ventas RETURNING ventas'''),
            {'s': req.tienda_id, 'd': req.fecha, 'f': x.familia_id, 'v': x.ventas})
            count += int(result.scalar_one_or_none() is not None)
    return count
