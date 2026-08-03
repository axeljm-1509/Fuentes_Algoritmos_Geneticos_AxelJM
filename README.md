# GENETIC ROUTE COMMANDER

**Optimización de rutas mediante algoritmos genéticos**

Aplicación académica en Python y Streamlit que resuelve una versión simplificada del problema del viajante (TSP). Un vehículo parte del centro de distribución, visita de 10 a 15 entregas exactamente una vez y regresa al centro. La interfaz presenta la simulación como un centro de mando de logística, mientras mantiene visible y separada la implementación del algoritmo genético.

## Objetivo y alcance

El proyecto demuestra de forma clara:

- representación de una solución mediante una permutación;
- creación y evaluación de una población;
- selección por torneo;
- cruce Ordered Crossover (OX);
- mutación por intercambio;
- elitismo y convergencia;
- evaluación, reproducción visual y exportación de resultados.

Las ubicaciones usan coordenadas cartesianas X/Y y distancia euclidiana. No se usan mapas en línea, APIs externas, bases de datos ni librerías que implementen el algoritmo.

## Tecnologías

- Python 3.10 o superior
- Streamlit
- NumPy
- Pandas
- Matplotlib
- Pytest

## Cómo funciona el algoritmo

### Individuo

Un cromosoma contiene únicamente los identificadores de las entregas. Por ejemplo:

```text
[4, 2, 1, 3, 5]
```

Para medirlo se construye la ruta `0 → 4 → 2 → 1 → 3 → 5 → 0`. El centro con id `0` nunca participa en cruce o mutación, por lo que permanece fijo.

### Matriz de distancias y aptitud

NumPy calcula una sola matriz de distancias por escenario. Si se solicitan varias ejecuciones, todas reutilizan esa matriz:

```text
distancia = sqrt((x2 - x1)² + (y2 - y1)²)
fitness = 1 / distancia_total
```

El código controla el caso de distancia cero. Las comparaciones internas usan la menor distancia, que equivale a la mayor aptitud.

### Selección por torneo

Se eligen al azar varios individuos distintos y gana el de menor distancia. El proceso se repite para seleccionar cada padre. El tamaño del torneo es configurable.

### Ordered Crossover (OX)

OX elige dos cortes, copia el segmento de un padre y completa las posiciones libres según el orden circular del otro. Se crean dos hijos y cada entrega aparece exactamente una vez.

### Mutación swap

Se seleccionan dos posiciones del cromosoma y se intercambian. La operación conserva la permutación válida.

### Elitismo y convergencia

Los mejores individuos pasan directamente a la generación siguiente. Por ello la mejor solución conocida nunca empeora. La ejecución finaliza al alcanzar el máximo de generaciones o al acumular el límite configurado de generaciones sin mejora.

Cada generación registra la mejor distancia, distancia promedio, aptitud, ruta y tiempo. Cada cinco generaciones se conserva una copia de la mejor ruta para el reproductor visual.

## Estructura

```text
genetic-route-commander/
├── app.py
├── requirements.txt
├── README.md
├── .gitignore
├── data/
│   └── sample_locations.csv
├── src/
│   ├── __init__.py
│   ├── models.py
│   ├── data_manager.py
│   ├── distance.py
│   ├── genetic_algorithm.py
│   ├── visualization.py
│   ├── exporters.py
│   └── ui_theme.py
└── tests/
    ├── __init__.py
    ├── conftest.py
    ├── test_distance.py
    ├── test_operators.py
    └── test_genetic_algorithm.py
```

## Instalación en Windows

Desde la carpeta del proyecto:

```powershell
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

## Ejecución

```powershell
streamlit run app.py
```

Streamlit mostrará una dirección local, normalmente `http://localhost:8501`.

## Pruebas

```powershell
pytest
```

Las pruebas no dependen de Streamlit. Verifican distancias, población inicial, ausencia del centro en el cromosoma, torneo, OX, swap, elitismo, límites de convergencia, reproducibilidad y conservación de la mejor solución.

## Datos de entrada

La aplicación puede generar de 10 a 15 entregas con una semilla o cargar un CSV. El formato es:

```csv
id,name,x,y
0,Centro de Distribución,50,50
1,Entrega 01,15,80
2,Entrega 02,70,25
```

Reglas de validación:

- deben existir exactamente las columnas `id`, `name`, `x`, `y` (se permiten columnas adicionales, pero se ignoran);
- el id `0` debe existir y representa el centro;
- los identificadores deben ser enteros, no negativos y únicos;
- no puede haber valores vacíos ni filas completamente duplicadas;
- las coordenadas deben ser numéricas y finitas;
- debe haber entre 10 y 15 entregas además del centro.

Puede probarse directamente con `data/sample_locations.csv`.

## Parámetros disponibles

| Parámetro | Predeterminado | Función |
|---|---:|---|
| Población | 100 | Rutas candidatas por generación |
| Generaciones | 300 | Máximo de ciclos evolutivos |
| Cruce | 0.90 | Probabilidad de aplicar OX |
| Mutación | 0.10 | Probabilidad de swap por hijo |
| Torneo | 3 | Candidatos que compiten por ser padre |
| Élite | 2 | Mejores individuos conservados |
| Estancamiento | 50 | Generaciones sin mejora permitidas |
| Ejecuciones | 1 | Repeticiones con semillas derivadas |

Modificar controles no inicia la búsqueda. Solo **INICIAR EVOLUCIÓN** ejecuta el algoritmo.

## Métricas y salidas

El HUD muestra distancia de una ruta real de la población inicial, mejor distancia, mejora porcentual, tiempo, mejor generación, generaciones ejecutadas, aptitud y motivo de finalización. La gráfica compara mejor distancia y promedio por generación.

Con varias ejecuciones también presenta mejor distancia global, promedio, desviación estándar y número de la mejor ejecución. Cada repetición usa una semilla derivada de la principal.

Se pueden descargar:

1. `best_route.csv`: orden, datos de cada ubicación, distancia del tramo y acumulado;
2. `evolution_history.csv`: historial de la mejor ejecución;
3. `mission_report.json`: configuración, métricas y ruta;
4. `best_route.png`: imagen de la mejor ruta.

## Guía breve para una exposición

1. Explique que es un TSP simplificado y que una ruta es una permutación sin el centro.
2. Muestre que la matriz evita recalcular distancias entre los mismos puntos.
3. Relacione menor distancia con mayor aptitud `1 / distancia`.
4. Describa torneo, OX y swap usando dos rutas cortas como ejemplo.
5. Destaque que el elitismo protege la mejor solución.
6. Genere un escenario con semilla conocida e inicie la evolución.
7. Use la gráfica y el selector de generaciones para explicar convergencia.
8. Repita varias ejecuciones para comentar la naturaleza estocástica del algoritmo.

## Limitaciones

- Usa distancia euclidiana, no calles, tráfico ni restricciones reales.
- Considera un solo vehículo, una sola capacidad implícita y visitas obligatorias.
- Un algoritmo genético aproxima una buena solución, pero no garantiza el óptimo global.
- La actualización visual ocurre cada cinco generaciones para conservar rendimiento.
- El estado vive en la sesión del navegador y no se guarda en una base de datos.

## Posibles mejoras

Podrían añadirse múltiples vehículos, ventanas horarias, capacidad, obstáculos, una búsqueda local 2-opt, comparación contra fuerza bruta para escenarios pequeños y análisis estadístico más amplio. Estas extensiones se excluyen aquí para mantener el valor didáctico y la implementación comprensible.
