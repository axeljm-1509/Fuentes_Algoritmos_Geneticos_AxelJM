"""Pruebas de operadores evolutivos."""

import numpy as np

from src.genetic_algorithm import (
    create_initial_population,
    is_valid_individual,
    ordered_crossover,
    preserve_elite,
    swap_mutation,
    tournament_selection,
)


def test_initial_population_contains_valid_permutations_without_depot() -> None:
    rng = np.random.default_rng(7)
    population = create_initial_population(range(1, 11), 40, rng)
    assert len(population) == 40
    assert all(is_valid_individual(individual, range(1, 11)) for individual in population)
    assert all(0 not in individual for individual in population)


def test_ordered_crossover_preserves_each_gene_once() -> None:
    first = list(range(1, 11))
    second = list(reversed(first))
    child_a, child_b = ordered_crossover(first, second, np.random.default_rng(21))
    assert is_valid_individual(child_a, first)
    assert is_valid_individual(child_b, first)


def test_swap_mutation_preserves_valid_permutation() -> None:
    original = list(range(1, 11))
    mutant = swap_mutation(original, np.random.default_rng(3))
    assert is_valid_individual(mutant, original)
    assert mutant != original
    assert original == list(range(1, 11))


def test_tournament_selection_returns_population_member() -> None:
    population = [[1, 2, 3], [2, 1, 3], [3, 2, 1]]
    selected = tournament_selection(population, [10.0, 9.0, 8.0], 3, np.random.default_rng(2))
    assert selected == [3, 2, 1]
    assert selected is not population[2]


def test_elitism_preserves_best_individuals() -> None:
    population = [[1, 2, 3], [2, 1, 3], [3, 2, 1], [3, 1, 2]]
    elite = preserve_elite(population, [12.0, 7.0, 10.0, 8.0], 2)
    assert elite == [[2, 1, 3], [3, 1, 2]]
