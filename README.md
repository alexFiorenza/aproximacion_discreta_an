# Aproximación discreta por mínimos cuadrados

Trabajo práctico de **Análisis Numérico** (UTN FRBA). Se estudia la relación entre la
**demanda prioritaria de gas natural** del Gran Buenos Aires y la **temperatura media
diaria**, ajustando los datos por el método de **mínimos cuadrados**.

## Datos

A partir de dos fuentes reales se construye el dataset (`dataset.csv`), cruzando ambas por fecha:

- **Demanda** — `datos_enargas.csv` (ENARGAS). Por cada fecha se suma la demanda de las
  licenciatarias que abastecen el AMBA: `D = MetroGAS + Naturgy BAN`.
- **Temperatura** — `registro_temperatura365d_smn.txt` (SMN). Por cada estación del AMBA se
  calcula `(Tmax + Tmin) / 2` y se promedian las 8 estaciones para obtener la temperatura
  media diaria representativa del Gran Buenos Aires.

Resultado: **n = 351** observaciones (jun-2025 a may-2026).

## Modelos ajustados

Se ajustan y comparan tres modelos:

| Modelo | Función | RMSE | R² |
|---|---|---|---|
| Lineal | `f1(T) = a + bT` | 3,11 | 0,811 |
| **Cuadrático** (seleccionado) | `f2(T) = a + bT + cT²` | **2,41** | **0,886** |
| Exponencial | `f3(T) = A·e^(BT)` | 2,57 | 0,871 |

El exponencial se resuelve por transformación logarítmica (`ln D = ln A + BT`). La
comparación usa **SSE**, **RMSE** y **R²**. Se selecciona el cuadrático (menor RMSE) y se
estima la demanda para `T₀ = 8 °C` → **D ≈ 25,37 MM m³/día**.

## Cómo reproducir

```bash
python -m venv .venv && source .venv/bin/activate
pip install numpy matplotlib aquarel

python procesar_datos.py   # genera dataset.csv
python analisis.py         # genera figures/ y tables/
```

Luego se compila el informe:

```bash
latexmk -pdf draft.tex
```

## Estructura

```
procesar_datos.py   construcción del dataset (cruce de fuentes)
analisis.py         ajuste, métricas, figuras y tablas
draft.tex           informe en LaTeX
dataset.csv         datos finales (fecha, T, D)
figures/            nube de puntos, modelos ajustados, residuos
tables/             tablas .tex (sumas, coeficientes, métricas, etc.)
```
