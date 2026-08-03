"""Construcción de exportables en memoria para Streamlit."""

from __future__ import annotations

import json
from dataclasses import asdict
from typing import Any

import pandas as pd

from .distance import euclidean_distance
from .models import GAResult, Location


def build_route_dataframe(locations: list[Location], route: list[int]) -> pd.DataFrame:
    """Crea el orden completo con distancias parciales y acumuladas."""

    by_id = {location.id: location for location in locations}
    complete_route = [0, *route, 0]
    rows: list[dict[str, Any]] = []
    cumulative = 0.0
    for order, location_id in enumerate(complete_route):
        location = by_id[location_id]
        leg_distance = 0.0 if order == 0 else euclidean_distance(by_id[complete_route[order - 1]], location)
        cumulative += leg_distance
        rows.append(
            {
                "order": order,
                "id": location.id,
                "name": location.name,
                "x": location.x,
                "y": location.y,
                "distance_from_previous": leg_distance,
                "cumulative_distance": cumulative,
            }
        )
    return pd.DataFrame(rows)


def route_csv_bytes(locations: list[Location], route: list[int]) -> bytes:
    return build_route_dataframe(locations, route).to_csv(index=False).encode("utf-8-sig")


def history_csv_bytes(result: GAResult) -> bytes:
    rows = [record.to_dict() for record in result.history]
    return pd.DataFrame(rows).to_csv(index=False).encode("utf-8-sig")


def result_summary_bytes(result: GAResult, extra_metrics: dict[str, Any] | None = None) -> bytes:
    """Serializa configuración y métricas reales de la ejecución elegida."""

    payload: dict[str, Any] = {
        "configuration": result.config.to_dict() if result.config else {},
        "metrics": {
            "initial_distance": result.initial_distance,
            "initial_best_distance": result.initial_best_distance,
            "best_distance": result.best_distance,
            "improvement_percentage": result.improvement_percentage,
            "elapsed_seconds": result.elapsed_seconds,
            "best_generation": result.best_generation,
            "generations_executed": result.generations_executed,
            "termination_reason": result.termination_reason,
            "best_run_number": result.run_number,
        },
        "best_route": [0, *result.best_route, 0],
    }
    if extra_metrics:
        payload["multiple_runs"] = extra_metrics
    return json.dumps(payload, ensure_ascii=False, indent=2).encode("utf-8")
