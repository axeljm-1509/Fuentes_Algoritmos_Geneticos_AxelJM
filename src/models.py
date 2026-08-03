"""Modelos de datos compartidos por la aplicación."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass(frozen=True, slots=True)
class Location:
    """Ubicación del centro de distribución o de una entrega."""

    id: int
    name: str
    x: float
    y: float


@dataclass(frozen=True, slots=True)
class GAConfig:
    """Parámetros seguros y reproducibles del algoritmo genético."""

    population_size: int = 100
    max_generations: int = 300
    crossover_probability: float = 0.90
    mutation_probability: float = 0.10
    tournament_size: int = 3
    elite_size: int = 2
    stagnation_limit: int = 50
    seed: int = 42
    snapshot_interval: int = 5

    def validate(self) -> None:
        """Lanza ``ValueError`` si un parámetro está fuera de su rango."""

        if not 10 <= self.population_size <= 1000:
            raise ValueError("La población debe estar entre 10 y 1000.")
        if not 1 <= self.max_generations <= 5000:
            raise ValueError("Las generaciones deben estar entre 1 y 5000.")
        if not 0.0 <= self.crossover_probability <= 1.0:
            raise ValueError("La probabilidad de cruce debe estar entre 0 y 1.")
        if not 0.0 <= self.mutation_probability <= 1.0:
            raise ValueError("La probabilidad de mutación debe estar entre 0 y 1.")
        if not 2 <= self.tournament_size <= self.population_size:
            raise ValueError("El torneo debe tener entre 2 y el tamaño de la población.")
        if not 0 <= self.elite_size < self.population_size:
            raise ValueError("El elitismo debe ser menor que la población.")
        if not 1 <= self.stagnation_limit <= self.max_generations:
            raise ValueError("El límite de estancamiento debe estar entre 1 y las generaciones.")
        if self.snapshot_interval < 1:
            raise ValueError("El intervalo de capturas debe ser positivo.")

    def to_dict(self) -> dict[str, Any]:
        """Convierte la configuración en un diccionario serializable."""

        return asdict(self)


@dataclass(frozen=True, slots=True)
class GenerationRecord:
    """Resumen estadístico de una generación."""

    generation: int
    best_distance: float
    average_distance: float
    best_fitness: float
    best_route: tuple[int, ...]
    elapsed_seconds: float

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["best_route"] = " → ".join(map(str, self.best_route))
        return data


@dataclass(slots=True)
class GAResult:
    """Resultado completo de una ejecución del algoritmo."""

    best_route: list[int]
    best_distance: float
    initial_route: list[int]
    initial_distance: float
    initial_best_distance: float
    improvement_percentage: float
    best_generation: int
    generations_executed: int
    termination_reason: str
    elapsed_seconds: float
    history: list[GenerationRecord] = field(default_factory=list)
    snapshots: dict[int, list[int]] = field(default_factory=dict)
    snapshot_distances: dict[int, float] = field(default_factory=dict)
    config: GAConfig | None = None
    run_number: int = 1

    @property
    def best_fitness(self) -> float:
        return 0.0 if self.best_distance <= 0 else 1.0 / self.best_distance
