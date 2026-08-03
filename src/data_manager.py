"""Generación, lectura y validación de ubicaciones."""

from __future__ import annotations

from io import BytesIO, StringIO
from pathlib import Path
from typing import BinaryIO, TextIO

import numpy as np
import pandas as pd

from .models import Location

REQUIRED_COLUMNS = ["id", "name", "x", "y"]


class DataValidationError(ValueError):
    """Error esperado al validar un escenario de entrada."""


def generate_locations(delivery_count: int, seed: int) -> list[Location]:
    """Genera un centro fijo y entre 10 y 15 entregas reproducibles."""

    if not 10 <= delivery_count <= 15:
        raise ValueError("La cantidad de entregas debe estar entre 10 y 15.")
    rng = np.random.default_rng(seed)
    locations = [Location(0, "Centro de Distribución", 50.0, 50.0)]
    coordinates = rng.uniform(5.0, 95.0, size=(delivery_count, 2))
    for index, (x, y) in enumerate(coordinates, start=1):
        locations.append(Location(index, f"Entrega {index:02d}", float(x), float(y)))
    return locations


def validate_locations_dataframe(dataframe: pd.DataFrame) -> pd.DataFrame:
    """Valida el formato académico del CSV y devuelve datos normalizados."""

    missing = [column for column in REQUIRED_COLUMNS if column not in dataframe.columns]
    if missing:
        raise DataValidationError(f"Faltan columnas obligatorias: {', '.join(missing)}.")

    frame = dataframe[REQUIRED_COLUMNS].copy()
    if frame.empty:
        raise DataValidationError("El archivo CSV está vacío.")
    if frame.isna().any().any() or frame["name"].astype(str).str.strip().eq("").any():
        raise DataValidationError("No se permiten valores vacíos en id, name, x o y.")
    if frame.duplicated().any():
        raise DataValidationError("El archivo contiene filas completamente duplicadas.")

    try:
        numeric_ids = pd.to_numeric(frame["id"], errors="raise")
        numeric_x = pd.to_numeric(frame["x"], errors="raise")
        numeric_y = pd.to_numeric(frame["y"], errors="raise")
    except (TypeError, ValueError) as error:
        raise DataValidationError("Los identificadores y las coordenadas deben ser numéricos.") from error

    if not np.isfinite(numeric_x).all() or not np.isfinite(numeric_y).all():
        raise DataValidationError("Las coordenadas deben ser números finitos.")
    if not np.equal(numeric_ids, np.floor(numeric_ids)).all():
        raise DataValidationError("Los identificadores deben ser números enteros.")

    frame["id"] = numeric_ids.astype(int)
    frame["x"] = numeric_x.astype(float)
    frame["y"] = numeric_y.astype(float)
    frame["name"] = frame["name"].astype(str).str.strip()

    if frame["id"].duplicated().any():
        raise DataValidationError("Los identificadores deben ser únicos.")
    if 0 not in frame["id"].values:
        raise DataValidationError("Debe existir el centro de distribución con identificador 0.")
    if (frame["id"] < 0).any():
        raise DataValidationError("Los identificadores no pueden ser negativos.")
    delivery_count = len(frame) - 1
    if not 10 <= delivery_count <= 15:
        raise DataValidationError("Debe haber entre 10 y 15 entregas, sin contar el centro.")
    return frame.sort_values("id", kind="stable").reset_index(drop=True)


def dataframe_to_locations(dataframe: pd.DataFrame) -> list[Location]:
    """Convierte un DataFrame ya validado en objetos ``Location``."""

    validated = validate_locations_dataframe(dataframe)
    return [
        Location(int(row.id), str(row.name), float(row.x), float(row.y))
        for row in validated.itertuples(index=False)
    ]


def read_locations_csv(source: str | Path | BinaryIO | TextIO | BytesIO | StringIO) -> list[Location]:
    """Lee y valida un archivo CSV desde ruta o archivo cargado por Streamlit."""

    try:
        dataframe = pd.read_csv(source)
    except Exception as error:
        raise DataValidationError(f"No fue posible leer el CSV: {error}.") from error
    return dataframe_to_locations(dataframe)


def locations_to_dataframe(locations: list[Location]) -> pd.DataFrame:
    """Convierte ubicaciones a un DataFrame con el orden de columnas esperado."""

    return pd.DataFrame(
        [{"id": item.id, "name": item.name, "x": item.x, "y": item.y} for item in locations],
        columns=REQUIRED_COLUMNS,
    )
