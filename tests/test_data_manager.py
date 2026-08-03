"""Pruebas de validación de entrada y exportación."""

from io import StringIO

import pandas as pd
import pytest

from src.data_manager import DataValidationError, read_locations_csv, validate_locations_dataframe
from src.exporters import build_route_dataframe


def test_sample_csv_is_valid() -> None:
    locations = read_locations_csv("data/sample_locations.csv")
    assert locations[0].id == 0
    assert len(locations) == 11


def test_csv_rejects_missing_required_columns() -> None:
    frame = pd.DataFrame({"id": [0], "name": ["Centro"], "x": [50]})
    with pytest.raises(DataValidationError, match="Faltan columnas"):
        validate_locations_dataframe(frame)


def test_csv_rejects_duplicate_ids() -> None:
    csv = "id,name,x,y\n0,Centro,0,0\n1,A,1,1\n1,B,2,2\n"
    with pytest.raises(DataValidationError, match="identificadores deben ser únicos"):
        read_locations_csv(StringIO(csv))


def test_route_export_includes_return_to_depot(square_locations) -> None:
    frame = build_route_dataframe(square_locations, [1, 2, 3])
    assert list(frame.columns) == [
        "order", "id", "name", "x", "y", "distance_from_previous", "cumulative_distance"
    ]
    assert frame["id"].tolist() == [0, 1, 2, 3, 0]
    assert frame.iloc[-1]["cumulative_distance"] == pytest.approx(14.0)
