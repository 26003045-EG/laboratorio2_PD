"""Pydantic contract for NovaMercado. Cleaning is performed separately."""
from datetime import date
from typing import Literal
from pydantic import BaseModel, ConfigDict, Field

class QualityNote(BaseModel):
    campo: str
    accion: Literal['reparar', 'advertir']
    detalle: str

class Quality(BaseModel):
    estado: Literal['ok', 'corregido', 'advertencia']
    observaciones: list[QualityNote] = Field(default_factory=list)

class FamilyRequest(BaseModel):
    familia_id: str
    en_promocion: int = Field(ge=0)

class PredictionRequest(BaseModel):
    model_config = ConfigDict(extra='forbid')
    tienda_id: int
    fecha: date
    familias: list[FamilyRequest] = Field(min_length=1)

class SaleRequest(BaseModel):
    familia_id: str
    ventas: int = Field(ge=0)

class ObservationRequest(BaseModel):
    model_config = ConfigDict(extra='forbid')
    tienda_id: int
    fecha: date
    ventas: list[SaleRequest] = Field(min_length=1)

class PredictionItem(BaseModel):
    familia_id: str
    venta_esperada: float
    cantidad_sugerida: int = Field(ge=0)

class PredictionResponse(BaseModel):
    tienda_id: int
    fecha: date
    version_modelo: str
    predicciones: list[PredictionItem]
    calidad: Quality

class ObservationResponse(BaseModel):
    registros_guardados: int
    calidad: Quality
