"""Datos compartidos por las pruebas."""

import pytest

from src.models import Location


@pytest.fixture
def square_locations() -> list[Location]:
    return [
        Location(0, "Centro", 0.0, 0.0),
        Location(1, "A", 3.0, 0.0),
        Location(2, "B", 3.0, 4.0),
        Location(3, "C", 0.0, 4.0),
    ]


@pytest.fixture
def study_locations() -> list[Location]:
    coordinates = [
        (50, 50), (12, 78), (25, 12), (82, 74), (71, 18), (42, 88),
        (91, 42), (14, 39), (61, 62), (36, 27), (77, 91),
    ]
    return [Location(index, "Centro" if index == 0 else f"Entrega {index:02d}", x, y)
            for index, (x, y) in enumerate(coordinates)]
