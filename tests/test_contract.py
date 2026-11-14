import pytest
from fastapi import HTTPException
from app.cleaning import normalize_payload

STORES = {5: 'Quetzaltenango'}
FAMILIES = {'abarrotes': 'Abarrotes', 'lacteos': 'Lácteos', 'frutas_verduras': 'Frutas y verduras'}
BASE = {'tienda_id': 5, 'fecha': '2025-11-17', 'familias': [
    {'familia_id': 'abarrotes', 'en_promocion': 0},
    {'familia_id': 'lacteos', 'en_promocion': 2},
    {'familia_id': 'frutas_verduras', 'en_promocion': 0}]}

def test_valida():
    req, q = normalize_payload(BASE, 'prediccion', STORES, FAMILIES)
    assert q.estado == 'ok' and len(req.familias) == 3

def test_reparacion():
    data = {**BASE, 'tienda_id': 'T05', 'fecha': '17/11/2025', 'familias': [
        {'familia_id': 'LÁCTEOS', 'en_promocion': '2'},
        {'familia_id': 'abarrotes', 'en_promocion': 0}]}
    req, q = normalize_payload(data, 'prediccion', STORES, FAMILIES)
    assert q.estado == 'advertencia' and len(req.familias) == 3

def test_familia_duplicada_rechazada():
    data = {**BASE, 'familias': BASE['familias'] + [BASE['familias'][0]]}
    with pytest.raises(HTTPException) as error:
        normalize_payload(data, 'prediccion', STORES, FAMILIES)
    assert error.value.status_code == 422

def test_negativa_rechazada():
    data = {'tienda_id': 5, 'fecha': '2025-11-17', 'ventas': [{'familia_id': 'lacteos', 'ventas': -4}]}
    with pytest.raises(HTTPException):
        normalize_payload(data, 'observaciones', STORES, FAMILIES)

def test_numero_texto():
    data = {'tienda_id': 5, 'fecha': '2025-11-17', 'ventas': [{'familia_id': 'lacteos', 'ventas': '1,234'}]}
    req, q = normalize_payload(data, 'observaciones', STORES, FAMILIES)
    assert req.ventas[0].ventas == 1234 and q.estado == 'corregido'

def test_fecha_invalida():
    with pytest.raises(HTTPException):
        normalize_payload({**BASE, 'fecha': 'ayer'}, 'prediccion', STORES, FAMILIES)
