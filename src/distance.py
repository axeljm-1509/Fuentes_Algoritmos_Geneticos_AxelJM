"""Cálculos de distancia y aptitud para rutas cerradas."""

from __future__ import annotations

import numpy as np

from .models import Location


def euclidean_distance(first: Location, second: Location) -> float:
    """Calcula la distancia euclidiana entre dos ubicaciones."""

    return float(np.hypot(second.x - first.x, second.y - first.y))


def build_distance_matrix(locations: list[Location]) -> np.ndarray:
    """Construye una matriz simétrica de distancias mediante NumPy."""

    if not locations:
        raise ValueError("Se necesita al menos una ubicación.")
    coordinates = np.asarray([(item.x, item.y) for item in locations], dtype=float)
    differences = coordinates[:, np.newaxis, :] - coordinates[np.newaxis, :, :]
    return np.sqrt(np.sum(differences**2, axis=2))


def build_id_index(locations: list[Location]) -> dict[int, int]:
    """Relaciona los identificadores del CSV con las filas de la matriz."""

    return {location.id: index for index, location in enumerate(locations)}


def route_total_distance(
    chromosome: list[int] | tuple[int, ...],
    distance_matrix: np.ndarray,
    id_to_index: dict[int, int] | None = None,
) -> float:
    """Calcula 0 → entregas → 0, sin insertar el centro en el cromosoma."""

    mapping = id_to_index or {index: index for index in range(distance_matrix.shape[0])}
    if 0 not in mapping:
        raise ValueError("No se encontró el centro de distribución con id 0.")
    complete_route = [0, *chromosome, 0]
    try:
        indexes = np.asarray([mapping[location_id] for location_id in complete_route], dtype=int)
    except KeyError as error:
        raise ValueError(f"La ruta contiene un identificador desconocido: {error.args[0]}.") from error
    return float(distance_matrix[indexes[:-1], indexes[1:]].sum())


def route_fitness(distance: float) -> float:
    """Convierte una distancia en aptitud; evita dividir entre cero."""

    if distance < 0:
        raise ValueError("La distancia no puede ser negativa.")
    return float("inf") if distance == 0 else 1.0 / distance
