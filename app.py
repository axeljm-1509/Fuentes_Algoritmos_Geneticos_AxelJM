"""Interfaz Streamlit de Genetic Route Commander."""

from __future__ import annotations

from dataclasses import replace
from html import escape

import matplotlib.pyplot as plt
import numpy as np
import streamlit as st

from src.data_manager import (
    DataValidationError,
    generate_locations,
    locations_to_dataframe,
    read_locations_csv,
)
from src.distance import build_distance_matrix, build_id_index
from src.exporters import history_csv_bytes, result_summary_bytes, route_csv_bytes
from src.genetic_algorithm import run_genetic_algorithm
from src.models import GAConfig, GAResult, Location
from src.ui_theme import apply_theme, metric_card, render_header, render_status, section_title
from src.visualization import create_evolution_figure, create_route_figure, route_figure_to_png

st.set_page_config(
    page_title="Genetic Route Commander",
    page_icon="🧬",
    layout="wide",
    initial_sidebar_state="expanded",
)
apply_theme()


def initialize_state() -> None:
    """Crea un escenario inicial sin ejecutar automáticamente el algoritmo."""

    defaults = {
        "locations": generate_locations(10, 42),
        "result": None,
        "run_results": [],
        "aggregate_metrics": {},
        "config": GAConfig(),
        "history": [],
        "snapshots": {},
        "best_run": None,
        "scenario_message": "Escenario inicial preparado con la semilla 42.",
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


def reset_mission() -> None:
    """Elimina el escenario y los resultados conservados en la sesión."""

    for key in list(st.session_state.keys()):
        del st.session_state[key]
    st.rerun()


def sidebar_controls() -> tuple[GAConfig, int, str, int, int, object | None]:
    """Renderiza controles y devuelve una configuración aún no ejecutada."""

    with st.sidebar:
        st.markdown("### ⚙️ CONSOLA DE MISIÓN")
        st.caption("Los cambios no ejecutan el algoritmo hasta pulsar INICIAR EVOLUCIÓN.")
        data_source = st.radio("Fuente de datos", ["Generación automática", "Carga mediante CSV"])
        delivery_count = st.slider(
            "Cantidad de entregas", 10, 15, 10,
            help="Número de puntos que visitará el vehículo, sin contar el centro.",
            disabled=data_source != "Generación automática",
        )
        seed = int(st.number_input(
            "Semilla aleatoria", min_value=0, max_value=2_147_483_647, value=42, step=1,
            help="Permite repetir exactamente el mismo escenario y evolución.",
        ))
        uploaded_file = None
        if data_source == "Carga mediante CSV":
            uploaded_file = st.file_uploader("Archivo CSV", type=["csv"], help="Columnas: id, name, x, y")

        generate_clicked = st.button("GENERAR ESCENARIO", width="stretch")
        st.divider()
        st.markdown("#### PARÁMETROS EVOLUTIVOS")
        population_size = st.slider(
            "Tamaño de población", 20, 500, 100, 10,
            help="Cantidad de rutas candidatas evaluadas en cada generación.",
        )
        max_generations = st.slider(
            "Generaciones máximas", 10, 1000, 300, 10,
            help="Tope de ciclos evolutivos antes de detener la búsqueda.",
        )
        crossover_probability = st.slider(
            "Probabilidad de cruce", 0.0, 1.0, 0.90, 0.05,
            help="Frecuencia con la que OX combina dos rutas seleccionadas.",
        )
        mutation_probability = st.slider(
            "Probabilidad de mutación", 0.0, 1.0, 0.10, 0.01,
            help="Probabilidad de intercambiar dos entregas en cada hijo.",
        )
        tournament_size = st.slider(
            "Tamaño del torneo", 2, min(10, population_size), 3,
            help="Cantidad de candidatos que compiten para convertirse en padre.",
        )
        elite_size = st.slider(
            "Individuos élite", 0, min(20, population_size - 1), 2,
            help="Mejores rutas copiadas directamente a la siguiente generación.",
        )
        stagnation_limit = st.slider(
            "Límite de estancamiento", 5, max_generations, min(50, max_generations), 5,
            help="Detiene la búsqueda tras este número de generaciones sin mejora.",
        )
        run_count = st.slider(
            "Cantidad de ejecuciones", 1, 5, 1,
            help="Repite el algoritmo con semillas derivadas y conserva la mejor ruta global.",
        )
        start_clicked = st.button("INICIAR EVOLUCIÓN", type="primary", width="stretch")
        st.button("REINICIAR MISIÓN", width="stretch", on_click=reset_mission)

    config = GAConfig(
        population_size=population_size,
        max_generations=max_generations,
        crossover_probability=crossover_probability,
        mutation_probability=mutation_probability,
        tournament_size=tournament_size,
        elite_size=elite_size,
        stagnation_limit=stagnation_limit,
        seed=seed,
        snapshot_interval=5,
    )
    return config, run_count, data_source, delivery_count, seed, (uploaded_file, generate_clicked, start_clicked)


def prepare_scenario(data_source: str, delivery_count: int, seed: int, uploaded_file: object | None) -> None:
    """Genera o carga ubicaciones y deja cualquier error visible en español."""

    try:
        if data_source == "Generación automática":
            locations = generate_locations(delivery_count, seed)
            message = f"Escenario generado: {delivery_count} entregas · semilla {seed}."
        else:
            if uploaded_file is None:
                raise DataValidationError("Selecciona un archivo CSV antes de generar el escenario.")
            uploaded_file.seek(0)
            locations = read_locations_csv(uploaded_file)
            message = f"CSV validado: {len(locations) - 1} entregas listas para la misión."
        st.session_state.locations = locations
        st.session_state.result = None
        st.session_state.run_results = []
        st.session_state.aggregate_metrics = {}
        st.session_state.history = []
        st.session_state.snapshots = {}
        st.session_state.best_run = None
        st.session_state.scenario_message = message
        st.success(message)
    except (DataValidationError, ValueError) as error:
        st.error(str(error))


def execute_runs(locations: list[Location], config: GAConfig, run_count: int) -> None:
    """Ejecuta de una a cinco búsquedas y conserva la mejor global."""

    progress = st.progress(0.0, text="Inicializando población")
    live_metrics = st.empty()
    results: list[GAResult] = []
    distance_matrix = build_distance_matrix(locations)
    id_to_index = build_id_index(locations)

    for run_index in range(1, run_count + 1):
        run_config = replace(config, seed=config.seed + (run_index - 1) * 1009)

        def update_progress(generation: int, maximum: int, best_distance: float, message: str) -> None:
            fraction = ((run_index - 1) + min(generation / maximum, 1.0)) / run_count
            progress.progress(
                min(fraction, 1.0),
                text=f"Ejecución {run_index}/{run_count} · {message}",
            )
            best_text = "—" if best_distance <= 0 else f"{best_distance:.2f}"
            live_metrics.caption(f"Generación {generation}/{maximum} · Mejor distancia actual: {best_text}")

        result = run_genetic_algorithm(
            locations,
            run_config,
            update_progress,
            distance_matrix=distance_matrix,
            id_to_index=id_to_index,
        )
        result.run_number = run_index
        results.append(result)
        progress.progress(run_index / run_count, text=f"Ejecución {run_index}/{run_count} completada")

    best_result = min(results, key=lambda item: item.best_distance)
    distances = np.asarray([item.best_distance for item in results], dtype=float)
    aggregate_metrics = {
        "run_count": run_count,
        "global_best_distance": float(np.min(distances)),
        "average_distance_between_runs": float(np.mean(distances)),
        "standard_deviation": float(np.std(distances)),
        "best_run_number": best_result.run_number,
        "derived_seeds": [item.config.seed for item in results if item.config],
    }
    st.session_state.result = best_result
    st.session_state.run_results = results
    st.session_state.aggregate_metrics = aggregate_metrics
    st.session_state.config = config
    st.session_state.history = best_result.history
    st.session_state.snapshots = best_result.snapshots
    st.session_state.best_run = best_result.run_number
    progress.progress(1.0, text="Misión completada")
    live_metrics.success(
        f"Ruta global confirmada en la ejecución {best_result.run_number}: {best_result.best_distance:.2f} unidades."
    )


def route_label(route: list[int], locations: list[Location]) -> str:
    names = {location.id: location.name for location in locations}
    return " → ".join([names[0], *(names[item] for item in route), names[0]])


def render_metrics(result: GAResult, aggregate: dict) -> None:
    section_title("Panel B", "Estado de la evolución")
    columns = st.columns(4)
    cards = [
        ("Distancia inicial", f"{result.initial_distance:.2f}", "Ruta real de la población inicial", "#22D3EE"),
        ("Mejor distancia", f"{result.best_distance:.2f}", f"Ejecución {result.run_number}", "#34D399"),
        ("Mejora", f"{result.improvement_percentage:.2f}%", "Respecto a la ruta inicial", "#8B5CF6"),
        ("Tiempo", f"{result.elapsed_seconds:.3f} s", "Mejor ejecución", "#FBBF24"),
        ("Mejor generación", str(result.best_generation), "Primera aparición", "#22D3EE"),
        ("Generaciones", str(result.generations_executed), "Ciclos ejecutados", "#8B5CF6"),
        ("Convergencia", "COMPLETA", result.termination_reason, "#34D399"),
        ("Aptitud final", f"{result.best_fitness:.6f}", "1 / distancia total", "#FBBF24"),
    ]
    for index, card in enumerate(cards):
        with columns[index % 4]:
            metric_card(*card)
    if aggregate.get("run_count", 1) > 1:
        st.caption(
            f"{aggregate['run_count']} ejecuciones · Promedio: {aggregate['average_distance_between_runs']:.2f} · "
            f"Desviación estándar: {aggregate['standard_deviation']:.2f} · "
            f"Mejor ejecución: {aggregate['best_run_number']}"
        )


def render_map(locations: list[Location], result: GAResult | None) -> None:
    section_title("Panel A", "Mapa de la misión")
    selected_route = None
    map_title = "Escenario de entregas"
    distance_caption = None
    if result:
        option_map: dict[str, int | None] = {"Ruta inicial aleatoria": None}
        for generation in result.snapshots:
            label = (
                f"Resultado final · Generación {generation}"
                if generation == result.generations_executed
                else f"Evolución · Generación {generation}"
            )
            option_map[label] = generation
        labels = list(option_map)
        selected_label = st.select_slider(
            "Reproducción de la evolución",
            options=labels,
            value=labels[-1],
        )
        selected_generation = option_map[selected_label]
        if selected_generation is None:
            selected_route = result.initial_route
            distance_caption = result.initial_distance
            map_title = "Ruta inicial de la población"
        else:
            generation = int(selected_generation)
            selected_route = result.snapshots[generation]
            distance_caption = result.snapshot_distances[generation]
            map_title = f"Mejor ruta conservada · Generación {generation}"

    figure = create_route_figure(locations, selected_route, map_title)
    st.pyplot(figure, width="stretch")
    plt.close(figure)
    if distance_caption is not None:
        st.caption(f"Distancia de la ruta mostrada: {distance_caption:.2f} unidades")


def render_exports(locations: list[Location], result: GAResult, aggregate: dict) -> None:
    section_title("Salida", "Paquete de resultados")
    columns = st.columns(4)
    with columns[0]:
        st.download_button(
            "DESCARGAR RUTA CSV", route_csv_bytes(locations, result.best_route),
            "best_route.csv", "text/csv", width="stretch",
        )
    with columns[1]:
        st.download_button(
            "DESCARGAR HISTORIAL CSV", history_csv_bytes(result),
            "evolution_history.csv", "text/csv", width="stretch",
        )
    with columns[2]:
        st.download_button(
            "DESCARGAR REPORTE JSON", result_summary_bytes(result, aggregate),
            "mission_report.json", "application/json", width="stretch",
        )
    with columns[3]:
        st.download_button(
            "DESCARGAR MAPA PNG", route_figure_to_png(locations, result.best_route),
            "best_route.png", "image/png", width="stretch",
        )


initialize_state()
render_header()
config, run_count, data_source, delivery_count, seed, actions = sidebar_controls()
uploaded_file, generate_clicked, start_clicked = actions

if generate_clicked:
    prepare_scenario(data_source, delivery_count, seed, uploaded_file)

locations: list[Location] = st.session_state.locations
result: GAResult | None = st.session_state.result

top_status, top_details = st.columns([1, 4], vertical_alignment="center")
with top_status:
    render_status("MISIÓN COMPLETADA" if result else "ESCENARIO LISTO")
with top_details:
    st.caption(st.session_state.scenario_message)

if start_clicked:
    try:
        config.validate()
        execute_runs(locations, config, run_count)
        result = st.session_state.result
    except (ValueError, RuntimeError) as error:
        st.error(f"No fue posible ejecutar la misión: {error}")

map_column, info_column = st.columns([1.55, 1], gap="large")
with map_column:
    render_map(locations, result)
with info_column:
    section_title("Escenario", "Coordenadas operativas")
    st.dataframe(
        locations_to_dataframe(locations),
        width="stretch",
        hide_index=True,
        height=428,
        column_config={"x": st.column_config.NumberColumn(format="%.2f"), "y": st.column_config.NumberColumn(format="%.2f")},
    )
    st.caption(f"{len(locations) - 1} entregas · 1 vehículo · retorno obligatorio al centro")

if result:
    render_metrics(result, st.session_state.aggregate_metrics)
    chart_column, route_column = st.columns([1.55, 1], gap="large")
    with chart_column:
        evolution_figure = create_evolution_figure(result.history)
        st.pyplot(evolution_figure, width="stretch")
        plt.close(evolution_figure)
    with route_column:
        section_title("Panel D", "Secuencia de la ruta")
        st.markdown(
            f'<div class="route-sequence">{escape(route_label(result.best_route, locations))}</div>',
            unsafe_allow_html=True,
        )
        st.caption(f"El centro (id 0) se añade solo para visualizar y medir; nunca forma parte del cromosoma.")
        with st.expander("Resumen técnico de la mejor ejecución"):
            st.json(
                {
                    "ejecución": result.run_number,
                    "semilla": result.config.seed if result.config else None,
                    "aptitud": result.best_fitness,
                    "motivo_finalización": result.termination_reason,
                    "ruta_cromosoma": result.best_route,
                }
            )
    render_exports(locations, result, st.session_state.aggregate_metrics)
else:
    st.info("Configura la misión y pulsa **INICIAR EVOLUCIÓN** para calcular una ruta. El algoritmo no se ejecuta al mover controles.")
