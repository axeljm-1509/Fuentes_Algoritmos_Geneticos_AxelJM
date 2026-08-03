"""Pruebas de distancia, matriz y aptitud."""

import math

import numpy as np

from src.distance import build_distance_matrix, euclidean_distance, route_fitness, route_total_distance


def test_euclidean_distance_uses_pythagoras(square_locations) -> None:
    assert euclidean_distance(square_locations[0], square_locations[2]) == 5.0


def test_distance_matrix_is_symmetric(square_locations) -> None:
    matrix = build_distance_matrix(square_locations)
    assert matrix.shape == (4, 4)
    assert np.allclose(matrix, matrix.T)
    assert np.allclose(np.diag(matrix), 0.0)


def test_total_distance_closes_route_at_depot(square_locations) -> None:
    matrix = build_distance_matrix(square_locations)
    assert route_total_distance([1, 2, 3], matrix) == 14.0


def test_fitness_handles_zero_without_error() -> None:
    assert math.isinf(route_fitness(0.0))
    assert route_fitness(4.0) == 0.25
