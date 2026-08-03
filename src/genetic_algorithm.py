"""Algoritmo genético implementado desde cero para una variante del TSP."""

from __future__ import annotations

from collections.abc import Callable, Sequence
from time import perf_counter

import numpy as np

from .distance import build_distance_matrix, build_id_index, route_fitness, route_total_distance
from .models import GAConfig, GAResult, GenerationRecord, Location

ProgressCallback = Callable[[int, int, float, str], None]


def create_initial_population(
    delivery_ids: Sequence[int], population_size: int, rng: np.random.Generator
) -> list[list[int]]:
    """Crea rutas aleatorias válidas sin incluir el depósito (id 0)."""

    genes = list(delivery_ids)
    if not genes or 0 in genes or len(set(genes)) != len(genes):
        raise ValueError("Las entregas deben ser identificadores únicos distintos de 0.")
    return [rng.permutation(genes).astype(int).tolist() for _ in range(population_size)]


def is_valid_individual(individual: Sequence[int], delivery_ids: Sequence[int]) -> bool:
    """Comprueba que un cromosoma es una permutación exacta de las entregas."""

    return 0 not in individual and len(individual) == len(delivery_ids) and set(individual) == set(delivery_ids)


def tournament_selection(
    population: Sequence[list[int]],
    distances: Sequence[float],
    tournament_size: int,
    rng: np.random.Generator,
) -> list[int]:
    """Selecciona por torneo el candidato de menor distancia (mayor aptitud)."""

    if len(population) != len(distances):
        raise ValueError("Cada individuo debe tener una distancia asociada.")
    if not 1 <= tournament_size <= len(population):
        raise ValueError("El tamaño del torneo no es válido.")
    candidate_indexes = rng.choice(len(population), size=tournament_size, replace=False)
    winner_index = min(candidate_indexes, key=lambda index: distances[int(index)])
    return list(population[int(winner_index)])


def ordered_crossover(
    first_parent: Sequence[int], second_parent: Sequence[int], rng: np.random.Generator
) -> tuple[list[int], list[int]]:
    """Aplica Ordered Crossover (OX) y genera dos permutaciones válidas."""

    if len(first_parent) != len(second_parent) or set(first_parent) != set(second_parent):
        raise ValueError("Los padres deben representar la misma permutación.")
    size = len(first_parent)
    if size < 2:
        return list(first_parent), list(second_parent)
    start, end = sorted(rng.choice(size, size=2, replace=False).tolist())

    def make_child(segment_parent: Sequence[int], order_parent: Sequence[int]) -> list[int]:
        child: list[int | None] = [None] * size
        child[start : end + 1] = segment_parent[start : end + 1]
        used = set(segment_parent[start : end + 1])

        # OX recorre el segundo padre desde el final del segmento y también
        # rellena circularmente desde esa misma posición.
        ordered_genes = [order_parent[(end + 1 + offset) % size] for offset in range(size)]
        available = [gene for gene in ordered_genes if gene not in used]
        fill_positions = [(end + 1 + offset) % size for offset in range(size) if child[(end + 1 + offset) % size] is None]
        for position, gene in zip(fill_positions, available, strict=True):
            child[position] = gene
        return [int(gene) for gene in child if gene is not None]

    return make_child(first_parent, second_parent), make_child(second_parent, first_parent)


def swap_mutation(individual: Sequence[int], rng: np.random.Generator) -> list[int]:
    """Intercambia dos genes y conserva la validez de la permutación."""

    mutant = list(individual)
    if len(mutant) >= 2:
        first, second = rng.choice(len(mutant), size=2, replace=False)
        mutant[int(first)], mutant[int(second)] = mutant[int(second)], mutant[int(first)]
    return mutant


def preserve_elite(
    population: Sequence[list[int]], distances: Sequence[float], elite_size: int
) -> list[list[int]]:
    """Devuelve copias de los mejores individuos de una generación."""

    if not 0 <= elite_size < len(population):
        raise ValueError("El elitismo debe ser menor que la población.")
    elite_indexes = np.argsort(np.asarray(distances, dtype=float))[:elite_size]
    return [list(population[int(index)]) for index in elite_indexes]


def _evaluate_population(
    population: Sequence[list[int]], distance_matrix: np.ndarray, id_to_index: dict[int, int]
) -> np.ndarray:
    return np.asarray(
        [route_total_distance(individual, distance_matrix, id_to_index) for individual in population],
        dtype=float,
    )


def _history_record(
    generation: int,
    population: Sequence[list[int]],
    distances: np.ndarray,
    elapsed_seconds: float,
) -> GenerationRecord:
    best_index = int(np.argmin(distances))
    best_distance = float(distances[best_index])
    return GenerationRecord(
        generation=generation,
        best_distance=best_distance,
        average_distance=float(np.mean(distances)),
        best_fitness=route_fitness(best_distance),
        best_route=tuple(population[best_index]),
        elapsed_seconds=elapsed_seconds,
    )


def run_genetic_algorithm(
    locations: list[Location],
    config: GAConfig,
    progress_callback: ProgressCallback | None = None,
    *,
    distance_matrix: np.ndarray | None = None,
    id_to_index: dict[int, int] | None = None,
) -> GAResult:
    """Ejecuta el ciclo evolutivo y retorna historial, capturas y métricas."""

    config.validate()
    if len(locations) < 2 or not any(location.id == 0 for location in locations):
        raise ValueError("El escenario debe incluir el centro y al menos una entrega.")
    delivery_ids = [location.id for location in locations if location.id != 0]
    if len(set(location.id for location in locations)) != len(locations):
        raise ValueError("Los identificadores de ubicación deben ser únicos.")

    rng = np.random.default_rng(config.seed)
    # Los parámetros opcionales permiten reutilizar la misma matriz cuando la
    # interfaz solicita varias ejecuciones sobre un único escenario.
    matrix = distance_matrix if distance_matrix is not None else build_distance_matrix(locations)
    index_mapping = id_to_index if id_to_index is not None else build_id_index(locations)
    if matrix.shape != (len(locations), len(locations)):
        raise ValueError("La matriz de distancias no coincide con las ubicaciones.")
    started_at = perf_counter()
    if progress_callback:
        progress_callback(0, config.max_generations, 0.0, "Inicializando población")

    population = create_initial_population(delivery_ids, config.population_size, rng)
    distances = _evaluate_population(population, matrix, index_mapping)
    initial_route = list(population[0])
    initial_distance = float(distances[0])
    initial_best_distance = float(np.min(distances))
    best_index = int(np.argmin(distances))
    global_best_route = list(population[best_index])
    global_best_distance = float(distances[best_index])
    best_generation = 0
    stagnation_count = 0

    first_record = _history_record(0, population, distances, perf_counter() - started_at)
    history = [first_record]
    snapshots = {0: list(global_best_route)}
    snapshot_distances = {0: global_best_distance}
    termination_reason = "Máximo de generaciones alcanzado"
    generations_executed = 0

    for generation in range(1, config.max_generations + 1):
        next_population = preserve_elite(population, distances, config.elite_size)

        while len(next_population) < config.population_size:
            first_parent = tournament_selection(population, distances, config.tournament_size, rng)
            second_parent = tournament_selection(population, distances, config.tournament_size, rng)
            if rng.random() < config.crossover_probability:
                first_child, second_child = ordered_crossover(first_parent, second_parent, rng)
            else:
                first_child, second_child = list(first_parent), list(second_parent)
            if rng.random() < config.mutation_probability:
                first_child = swap_mutation(first_child, rng)
            if rng.random() < config.mutation_probability:
                second_child = swap_mutation(second_child, rng)
            next_population.extend((first_child, second_child))

        population = next_population[: config.population_size]
        distances = _evaluate_population(population, matrix, index_mapping)
        current_best_index = int(np.argmin(distances))
        current_best_distance = float(distances[current_best_index])

        if current_best_distance < global_best_distance - 1e-12:
            global_best_distance = current_best_distance
            global_best_route = list(population[current_best_index])
            best_generation = generation
            stagnation_count = 0
        else:
            stagnation_count += 1

        record = _history_record(generation, population, distances, perf_counter() - started_at)
        history.append(record)
        generations_executed = generation

        should_capture = generation % config.snapshot_interval == 0
        if should_capture:
            snapshots[generation] = list(global_best_route)
            snapshot_distances[generation] = global_best_distance

        if progress_callback and (generation == 1 or generation % config.snapshot_interval == 0):
            message = "Buscando convergencia" if generation > 1 else "Evaluando rutas"
            progress_callback(generation, config.max_generations, global_best_distance, message)

        if stagnation_count >= config.stagnation_limit:
            termination_reason = f"Estancamiento durante {config.stagnation_limit} generaciones"
            break

    if generations_executed not in snapshots:
        snapshots[generations_executed] = list(global_best_route)
        snapshot_distances[generations_executed] = global_best_distance

    elapsed_seconds = perf_counter() - started_at
    improvement = 0.0
    if initial_distance > 0:
        improvement = ((initial_distance - global_best_distance) / initial_distance) * 100.0
    if progress_callback:
        progress_callback(generations_executed, config.max_generations, global_best_distance, "Misión completada")

    return GAResult(
        best_route=global_best_route,
        best_distance=global_best_distance,
        initial_route=initial_route,
        initial_distance=initial_distance,
        initial_best_distance=initial_best_distance,
        improvement_percentage=improvement,
        best_generation=best_generation,
        generations_executed=generations_executed,
        termination_reason=termination_reason,
        elapsed_seconds=elapsed_seconds,
        history=history,
        snapshots=dict(sorted(snapshots.items())),
        snapshot_distances=dict(sorted(snapshot_distances.items())),
        config=config,
    )
