"""Visualizaciones Matplotlib coherentes con el HUD de la aplicación."""

from __future__ import annotations

from io import BytesIO

import matplotlib.pyplot as plt
from matplotlib.figure import Figure

from .models import GenerationRecord, Location

BACKGROUND = "#080B14"
PANEL = "#111827"
CYAN = "#22D3EE"
VIOLET = "#8B5CF6"
GREEN = "#34D399"
TEXT = "#E5E7EB"
MUTED = "#94A3B8"
GRID = "#263247"


def _style_axes(figure: Figure, axes) -> None:
    figure.patch.set_facecolor(PANEL)
    axes.set_facecolor(BACKGROUND)
    axes.tick_params(colors=MUTED)
    axes.xaxis.label.set_color(MUTED)
    axes.yaxis.label.set_color(MUTED)
    axes.title.set_color(TEXT)
    for spine in axes.spines.values():
        spine.set_color(GRID)
    axes.grid(color=GRID, alpha=0.32, linewidth=0.7)


def create_route_figure(
    locations: list[Location], route: list[int] | None = None, title: str = "Mapa de la misión"
) -> Figure:
    """Dibuja las ubicaciones y, opcionalmente, una ruta cerrada."""

    by_id = {location.id: location for location in locations}
    depot = by_id[0]
    deliveries = [location for location in locations if location.id != 0]
    figure, axes = plt.subplots(figsize=(8.4, 6.2), constrained_layout=True)
    _style_axes(figure, axes)

    if route:
        complete = [0, *route, 0]
        route_x = [by_id[item].x for item in complete]
        route_y = [by_id[item].y for item in complete]
        axes.plot(route_x, route_y, color=VIOLET, linewidth=2.1, alpha=0.86, zorder=2)
        axes.scatter(route_x[1:-1], route_y[1:-1], s=150, color=CYAN, edgecolor="#CFFAFE", linewidth=1.0, zorder=3)
    else:
        axes.scatter(
            [item.x for item in deliveries],
            [item.y for item in deliveries],
            s=145,
            color=CYAN,
            edgecolor="#CFFAFE",
            linewidth=1.0,
            zorder=3,
        )

    axes.scatter([depot.x], [depot.y], marker="*", s=420, color=GREEN, edgecolor="#D1FAE5", linewidth=1.2, zorder=4)
    axes.annotate("BASE", (depot.x, depot.y), xytext=(7, 8), textcoords="offset points", color=GREEN, weight="bold")
    for location in deliveries:
        axes.annotate(
            f"E{location.id:02d}",
            (location.x, location.y),
            xytext=(6, 6),
            textcoords="offset points",
            color=TEXT,
            fontsize=8,
        )
    axes.set_title(title, loc="left", fontsize=14, pad=12, weight="bold")
    axes.set_xlabel("Coordenada X")
    axes.set_ylabel("Coordenada Y")
    axes.set_aspect("equal", adjustable="datalim")
    axes.margins(0.12)
    return figure


def create_evolution_figure(history: list[GenerationRecord]) -> Figure:
    """Compara la mejor distancia y el promedio de cada generación."""

    figure, axes = plt.subplots(figsize=(8.4, 4.3), constrained_layout=True)
    _style_axes(figure, axes)
    generations = [item.generation for item in history]
    axes.plot(generations, [item.best_distance for item in history], color=GREEN, linewidth=2.2, label="Mejor distancia")
    axes.plot(
        generations,
        [item.average_distance for item in history],
        color=CYAN,
        linewidth=1.7,
        alpha=0.82,
        label="Distancia promedio",
    )
    axes.fill_between(generations, [item.best_distance for item in history], color=GREEN, alpha=0.07)
    axes.set_title("Registro evolutivo", loc="left", fontsize=14, pad=12, weight="bold")
    axes.set_xlabel("Generación")
    axes.set_ylabel("Distancia total")
    legend = axes.legend(facecolor=PANEL, edgecolor=GRID, labelcolor=TEXT)
    legend.get_frame().set_alpha(0.95)
    return figure


def route_figure_to_png(locations: list[Location], route: list[int]) -> bytes:
    """Genera en memoria el PNG descargable de la mejor ruta."""

    figure = create_route_figure(locations, route, "Mejor ruta de la misión")
    buffer = BytesIO()
    figure.savefig(buffer, format="png", dpi=180, facecolor=figure.get_facecolor(), bbox_inches="tight")
    plt.close(figure)
    return buffer.getvalue()
