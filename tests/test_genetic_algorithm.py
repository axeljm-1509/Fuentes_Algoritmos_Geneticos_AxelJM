"""Pruebas de integración del ciclo genético."""

import pytest

from src.genetic_algorithm import run_genetic_algorithm
from src.models import GAConfig


def make_config(**changes) -> GAConfig:
    values = {
        "population_size": 40,
        "max_generations": 30,
        "crossover_probability": 0.9,
        "mutation_probability": 0.15,
        "tournament_size": 3,
        "elite_size": 2,
        "stagnation_limit": 30,
        "seed": 123,
        "snapshot_interval": 5,
    }
    values.update(changes)
    return GAConfig(**values)


def test_algorithm_respects_maximum_generations(study_locations) -> None:
    result = run_genetic_algorithm(study_locations, make_config(max_generations=8, stagnation_limit=8))
    assert result.generations_executed <= 8
    assert result.history[-1].generation == result.generations_executed


def test_algorithm_stops_after_stagnation(study_locations) -> None:
    config = make_config(
        max_generations=50,
        stagnation_limit=3,
        crossover_probability=0.0,
        mutation_probability=0.0,
    )
    result = run_genetic_algorithm(study_locations, config)
    assert result.generations_executed == 3
    assert "Estancamiento" in result.termination_reason


def test_same_seed_produces_same_solution(study_locations) -> None:
    first = run_genetic_algorithm(study_locations, make_config())
    second = run_genetic_algorithm(study_locations, make_config())
    assert first.best_route == second.best_route
    assert first.best_distance == pytest.approx(second.best_distance)
    assert [row.best_distance for row in first.history] == pytest.approx(
        [row.best_distance for row in second.history]
    )


def test_elitism_never_loses_initial_best_solution(study_locations) -> None:
    result = run_genetic_algorithm(study_locations, make_config())
    assert result.best_distance <= result.initial_best_distance + 1e-12
    assert 0 not in result.best_route
    assert set(result.best_route) == set(range(1, 11))
