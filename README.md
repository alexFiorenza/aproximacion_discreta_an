# Aproximación discreta por mínimos cuadrados

Trabajo práctico de **Análisis Numérico** (UTN FRBA). Se estudia la relación entre la
**demanda prioritaria de gas natural** del Gran Buenos Aires y la **temperatura media
diaria**, ajustando los datos por el método de **mínimos cuadrados**.

## Enlaces

- **Presentación del trabajo:** [YouTube](https://youtu.be/oGs5gnDfWcA?si=8vU9Bn-2B6IV6T6-)
- **Código fuente, datos y material reproducible:** [github.com/alexFiorenza/aproximacion_discreta_an](https://github.com/alexFiorenza/aproximacion_discreta_an)
- **Informe:** `tp.tex` (compilar con `latexmk -pdf tp.tex` para obtener `tp.pdf`)

Los valores numéricos del informe (sumas, coeficientes, métricas, estimación final), así
como las figuras y tablas LaTeX, se generan automáticamente con `analisis.py`.

## Datos

A partir de dos fuentes reales se construye el dataset (`dataset.csv`), cruzando ambas por
fecha. La preparación está automatizada en `procesar_datos.py`.

| Fuente | Archivo | Descripción |
|---|---|---|
| ENARGAS | `datos_enargas.csv` | Demanda prioritaria por licenciataria y fecha |
| SMN | `registro_temperatura365d_smn.txt` | Registro diario de temperatura en estaciones del AMBA |

Criterios aplicados:

- **Demanda** — Por cada fecha se suma la demanda de las licenciatarias que abastecen el
  AMBA: `D = MetroGAS + Naturgy BAN`. Solo se conservan fechas con registro en ambas.
- **Temperatura** — Por cada estación se calcula `(Tmax + Tmin) / 2` y se promedian las 8
  estaciones del AMBA (Aeroparque, Observatorio Central de Buenos Aires, Ezeiza, El Palomar,
  Morón, San Fernando, Campo de Mayo y La Plata).

Resultado: **n = 351** observaciones (jun-2025 a may-2026), columnas `fecha`, `T`, `D`.

## Modelos ajustados

Se ajustan y comparan tres modelos (implementados en `analisis.py`):

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
latexmk -pdf tp.tex        # compila el informe
```

Orden recomendado:

1. `procesar_datos.py` — lee los datos de ENARGAS y SMN, aplica los criterios descriptos
   y genera `dataset.csv`.
2. `analisis.py` — resuelve los sistemas normales, calcula coeficientes y métricas, y
   exporta las tablas `.tex` y los gráficos en `figures/`.
3. `latexmk -pdf tp.tex` — compila el informe incorporando las tablas y figuras generadas.

## Estructura del repositorio

| Archivo o carpeta | Descripción |
|---|---|
| `procesar_datos.py` | Construcción de `dataset.csv` a partir de ENARGAS y SMN |
| `analisis.py` | Ajuste de modelos, métricas, figuras y tablas LaTeX |
| `datos_enargas.csv` | Datos de demanda prioritaria (ENARGAS) |
| `registro_temperatura365d_smn.txt` | Registro de temperatura (SMN) |
| `dataset.csv` | Dataset final (`fecha`, `T`, `D`) |
| `tp.tex` | Fuente LaTeX del informe |
| `presentacion.html` | Presentación del trabajo (HTML, un solo archivo) |
| `figures/` | Nube de puntos, modelos ajustados y residuos |
| `tables/` | Tablas `.tex` (sumas, coeficientes, métricas, estimación final, etc.) |

## Fuentes originales

- [ENARGAS — Estimación de la Demanda Prioritaria](https://www.enargas.gob.ar/secciones/transporte-y-distribucion/dod-estimacion-demanda-prioritaria.php)
- [ENARGAS — Datos históricos CSV](https://www.enargas.gob.ar/secciones/transporte-y-distribucion/estimacion-demanda-prioritaria/estimacion_demanda_prioritaria.csv)
- [Datos Argentina — Partes diarios de gas natural](https://datos.gob.ar/ar/dataset/energia-partes-diarios-gas-natural)
- [SMN — Datos meteorológicos](https://datos.gob.ar/dataset/smn-datos-meteorologicos-horarios)
