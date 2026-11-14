"""General and auditable repairs. Pure logic, testable without infrastructure."""
from datetime import date, datetime
import math
import re
import unicodedata
from fastapi import HTTPException
from .contracts import PredictionRequest, ObservationRequest, Quality, QualityNote


def reject(message):
    raise HTTPException(status_code=422, detail=message)


def slug(text):
    s = unicodedata.normalize('NFKD', str(text).strip().lower())
    s = ''.join(c for c in s if not unicodedata.combining(c))
    return re.sub(r'[^a-z0-9]', '', s)


def note(notes, field, action, detail):
    notes.append(QualityNote(campo=field, accion=action, detalle=detail))


def quality(notes):
    status = 'advertencia' if any(x.accion == 'advertir' for x in notes) else ('corregido' if notes else 'ok')
    return Quality(estado=status, observaciones=notes)


def parse_store(value, stores, notes):
    if isinstance(value, bool):
        reject('tienda_id no puede ser booleano')
    if isinstance(value, int):
        num = value
    elif isinstance(value, str) and re.fullmatch(r'\s*(?:T\s*[-_]?\s*)?\d+\s*', value, re.I):
        num = int(re.sub(r'[^0-9]', '', value))
        note(notes, 'tienda_id', 'reparar', f'{value!r} se interpretó como {num}')
    else:
        reject('tienda_id no es un identificador válido')
    if num not in stores:
        reject(f'tienda_id {num} no existe')
    return num


def parse_date(value, notes):
    if not isinstance(value, str):
        reject('fecha debe ser texto')
    try:
        d = date.fromisoformat(value)
        if value != d.isoformat():
            note(notes, 'fecha', 'reparar', f'{value!r} normalizada a {d.isoformat()}')
        return d
    except ValueError:
        pass
    for fmt in ('%d/%m/%Y', '%Y-%m-%dT%H:%M:%S'):
        try:
            d = datetime.strptime(value, fmt).date()
            note(notes, 'fecha', 'reparar', f'{value!r} normalizada a {d.isoformat()}')
            return d
        except ValueError:
            continue
    reject('fecha inválida; use AAAA-MM-DD o formato reconocido no ambiguo')


def parse_family(value, families, notes, field):
    if not isinstance(value, str):
        reject(f'{field} debe ser texto')
    aliases = {slug(k): k for k in families}
    aliases.update({slug(v): k for k, v in families.items()})
    key = aliases.get(slug(value))
    if not key:
        reject(f'{field}: familia {value!r} desconocida')
    if value != key:
        note(notes, field, 'reparar', f'{value!r} se interpretó como {key!r}')
    return key


def parse_count(value, field, notes):
    if isinstance(value, bool):
        reject(f'{field} no puede ser booleano')
    if isinstance(value, int):
        v = value
    elif isinstance(value, float) and math.isfinite(value) and value.is_integer():
        v = int(value)
        note(notes, field, 'reparar', f'{value!r} convertido a entero')
    elif isinstance(value, str):
        original = value
        value = value.strip().replace(' ', '')
        # A single comma with three trailing digits = grouping; otherwise decimal comma.
        if re.fullmatch(r'\d{1,3}(,\d{3})+', value):
            value = value.replace(',', '')
        elif re.fullmatch(r'\d+,\d+', value):
            value = value.replace(',', '.')
        try:
            x = float(value)
            if not math.isfinite(x) or not x.is_integer():
                reject(f'{field}: se requiere un entero exacto')
            v = int(x)
        except ValueError:
            reject(f'{field}: cantidad numérica inválida')
        note(notes, field, 'reparar', f'{original!r} convertido a {v}')
    else:
        reject(f'{field}: tipo de dato inválido')
    if v < 0:
        reject(f'{field}: valor negativo no permitido (no se inventan ventas)')
    return v


def normalize_payload(raw, kind, stores, families):
    if not isinstance(raw, dict):
        reject('La solicitud debe ser un objeto JSON')
    raw = dict(raw)
    notes = []
    if 'tienda_id' not in raw and 'tienda' in raw:
        raw['tienda_id'] = raw['tienda']
        note(notes, 'tienda_id', 'reparar', "campo 'tienda' renombrado a 'tienda_id'")
    if 'tienda_id' not in raw or 'fecha' not in raw:
        reject('Falta tienda_id o fecha')
    store = parse_store(raw['tienda_id'], stores, notes)
    when = parse_date(raw['fecha'], notes)
    field = 'familias' if kind == 'prediccion' else 'ventas'
    lines = raw.get(field)
    if not isinstance(lines, list) or not lines:
        reject(f'{field} debe ser una lista no vacía')
    cleaned = []
    used = set()
    for i, x in enumerate(lines):
        if not isinstance(x, dict):
            reject(f'{field}[{i}] debe ser un objeto')
        family = parse_family(x.get('familia_id'), families, notes, f'{field}[{i}].familia_id')
        if family in used:
            reject(f'Familia repetida {family}: no se puede decidir qué valor utilizar')
        used.add(family)
        num_key = 'en_promocion' if kind == 'prediccion' else 'ventas'
        if num_key not in x:
            reject(f'Falta {field}[{i}].{num_key}')
        count = parse_count(x[num_key], f'{field}[{i}].{num_key}', notes)
        cleaned.append({'familia_id': family, num_key: count})
    if kind == 'prediccion':
        for family in families:
            if family not in used:
                cleaned.append({'familia_id': family, 'en_promocion': 0})
                note(notes, f'familias.{family}', 'advertir', 'Familia omitida: se supone en_promocion=0')
        model = PredictionRequest.model_validate({'tienda_id': store, 'fecha': when, 'familias': cleaned})
    else:
        model = ObservationRequest.model_validate({'tienda_id': store, 'fecha': when, 'ventas': cleaned})
    return model, quality(notes)
