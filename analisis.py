#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Ajuste por mínimos cuadrados de la demanda prioritaria de gas natural (GBA)
en función de la temperatura media diaria (AMBA).

Modelos:
  Lineal:       f1(T) = a + b T
  Cuadrático:   f2(T) = a + b T + c T^2
  Exponencial:  f3(T) = A e^{B T}   (vía transformación Y = ln D, lineal en T)

Genera:
  figures/nube_puntos.png, figures/modelos_ajustados.png, figures/residuos.png
  tables/datos_muestra.tex, tables/sumas_lineal.tex, tables/sumas_cuadratico.tex,
  tables/sumas_exponencial.tex, tables/coeficientes.tex, tables/metricas.tex,
  tables/estimacion_final.tex

E imprime por pantalla todos los valores numéricos para completar draft.tex.
"""

import csv
import math
import os
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from aquarel import load_theme

DATASET = "dataset.csv"
T0 = 8.0  # temperatura para la estimación final [°C]

os.makedirs("figures", exist_ok=True)
os.makedirs("tables", exist_ok=True)

# Estilo de figuras: theme "scientific" de aquarel
theme = load_theme("scientific")
theme.apply()
# se conserva alta resolución para inclusión en LaTeX
plt.rcParams.update({"figure.dpi": 150, "savefig.dpi": 150})
C_DATA = "#003A70"   # utnblue
C_LIN = "#D55E00"
C_CUAD = "#009E73"
C_EXP = "#CC79A7"


# ------------------------------------------------------------------ utilidades
def num(x, d=2):
    """Número con punto decimal (lo convierte siunitx \\num) y d decimales."""
    return f"{x:.{d}f}"


def signo(x, d):
    """Devuelve ('+'|'-', |x| formateado) para construir expresiones a+bT."""
    return ("-" if x < 0 else "+"), f"{abs(x):.{d}f}"


# --------------------------------------------------------------------- cargar
fechas, T, D = [], [], []
with open(DATASET, newline="", encoding="utf-8") as f:
    for row in csv.DictReader(f):
        fechas.append(row["fecha"])
        T.append(float(row["T"]))
        D.append(float(row["D"]))
T = np.array(T)
D = np.array(D)
n = len(T)

# --------------------------------------------------------------------- sumas
ST = T.sum()
ST2 = (T**2).sum()
ST3 = (T**3).sum()
ST4 = (T**4).sum()
SD = D.sum()
STD = (T * D).sum()
ST2D = (T**2 * D).sum()
Dbar = D.mean()

# log para exponencial
Y = np.log(D)
SY = Y.sum()
STY = (T * Y).sum()

# ----------------------------------------------------------- modelo lineal
# [[n, ST],[ST, ST2]] [a,b] = [SD, STD]
Mlin = np.array([[n, ST], [ST, ST2]])
blin = np.array([SD, STD])
a_lin, b_lin = np.linalg.solve(Mlin, blin)
# verificación por fórmula cerrada
det = n * ST2 - ST * ST
a_chk = (SD * ST2 - ST * STD) / det
b_chk = (n * STD - ST * SD) / det
assert abs(a_lin - a_chk) < 1e-6 and abs(b_lin - b_chk) < 1e-6

# -------------------------------------------------------- modelo cuadrático
Mcua = np.array([[n, ST, ST2],
                 [ST, ST2, ST3],
                 [ST2, ST3, ST4]])
bcua = np.array([SD, STD, ST2D])
a_cua, b_cua, c_cua = np.linalg.solve(Mcua, bcua)

# ------------------------------------------------------- modelo exponencial
# Lineal sobre (T, Y): [[n, ST],[ST, ST2]] [alpha, B] = [SY, STY]
Mexp = np.array([[n, ST], [ST, ST2]])
bexp = np.array([SY, STY])
alpha, B_exp = np.linalg.solve(Mexp, bexp)
A_exp = math.exp(alpha)

# --------------------------------------------------------------- funciones
f_lin = lambda t: a_lin + b_lin * t
f_cua = lambda t: a_cua + b_cua * t + c_cua * t**2
f_exp = lambda t: A_exp * np.exp(B_exp * t)


def metricas(pred):
    r = D - pred
    sse = float((r**2).sum())
    rmse = math.sqrt(sse / n)
    sst = float(((D - Dbar)**2).sum())
    r2 = 1 - sse / sst
    return sse, rmse, r2


sse_l, rmse_l, r2_l = metricas(f_lin(T))
sse_c, rmse_c, r2_c = metricas(f_cua(T))
sse_e, rmse_e, r2_e = metricas(f_exp(T))

modelos = {
    "Lineal": (rmse_l, sse_l, r2_l, f_lin),
    "Cuadrático": (rmse_c, sse_c, r2_c, f_cua),
    "Exponencial": (rmse_e, sse_e, r2_e, f_exp),
}
seleccionado = min(modelos, key=lambda k: modelos[k][0])
f_sel = modelos[seleccionado][3]
D_T0 = float(f_sel(T0))

# estimaciones de cada modelo en T0 (para referencia)
est = {"Lineal": float(f_lin(T0)), "Cuadrático": float(f_cua(T0)),
       "Exponencial": float(f_exp(T0))}

Tmin, Tmax = float(T.min()), float(T.max())

# =============================================================== FIGURAS
# 1) Nube de puntos
fig, ax = plt.subplots(figsize=(8, 5))
ax.scatter(T, D, s=18, color=C_DATA, alpha=0.7, edgecolors="white", linewidths=0.4)
ax.set_xlabel(r"Temperatura media $T$ [$^\circ$C]")
ax.set_ylabel(r"Demanda $D$ [MM m$^3$/día]")
ax.set_title("Demanda prioritaria de gas natural (GBA) vs. temperatura media (AMBA)")
theme.apply_transforms()
fig.tight_layout()
fig.savefig("figures/nube_puntos.png")
plt.close(fig)

# 2) Modelos ajustados
fig, ax = plt.subplots(figsize=(8.5, 5.3))
ax.scatter(T, D, s=16, color=C_DATA, alpha=0.45, edgecolors="white",
           linewidths=0.3, label="Datos observados", zorder=2)
tt = np.linspace(Tmin, Tmax, 400)
ax.plot(tt, f_lin(tt), color=C_LIN, lw=2,
        label=fr"Lineal: $f_1(T)={a_lin:.2f}{b_lin:+.3f}\,T$", zorder=3)
ax.plot(tt, f_cua(tt), color=C_CUAD, lw=2,
        label=fr"Cuadrático: $f_2(T)={a_cua:.2f}{b_cua:+.3f}\,T{c_cua:+.4f}\,T^2$", zorder=4)
ax.plot(tt, f_exp(tt), color=C_EXP, lw=2,
        label=fr"Exponencial: $f_3(T)={A_exp:.2f}\,e^{{{B_exp:.4f}\,T}}$", zorder=5)
ax.set_xlabel(r"Temperatura media $T$ [$^\circ$C]")
ax.set_ylabel(r"Demanda $D$ [MM m$^3$/día]")
ax.set_title("Modelos ajustados por mínimos cuadrados")
ax.legend(fontsize=9, framealpha=0.95)
theme.apply_transforms()
fig.tight_layout()
fig.savefig("figures/modelos_ajustados.png")
plt.close(fig)

# 3) Residuos (un subplot por modelo)
fig, axs = plt.subplots(1, 3, figsize=(13, 4.2), sharey=True)
for ax, (nombre, col, fmod) in zip(
        axs, [("Lineal", C_LIN, f_lin), ("Cuadrático", C_CUAD, f_cua),
              ("Exponencial", C_EXP, f_exp)]):
    r = D - fmod(T)
    ax.scatter(T, r, s=14, color=col, alpha=0.6, edgecolors="white", linewidths=0.3)
    ax.axhline(0, color="black", lw=1)
    ax.set_title(nombre)
    ax.set_xlabel(r"$T$ [$^\circ$C]")
axs[0].set_ylabel(r"Residuo $r_i = D_i - f(T_i)$ [MM m$^3$/día]")
fig.suptitle("Residuos de los modelos ajustados", y=1.02, fontsize=12)
theme.apply_transforms()
fig.tight_layout()
fig.savefig("figures/residuos.png", bbox_inches="tight")
plt.close(fig)

# =============================================================== TABLAS
def escribir(path, contenido):
    with open(path, "w", encoding="utf-8") as f:
        f.write(contenido)


# --- datos_muestra.tex : muestra representativa (12 filas espaciadas por fecha)
idx = np.linspace(0, n - 1, 12).round().astype(int)
filas = []
for i in idx:
    filas.append(f"{fechas[i]} & \\num{{{T[i]:.2f}}} & \\num{{{D[i]:.2f}}} \\\\")
datos_muestra = (
    "\\begin{tabular}{l r r}\n\\toprule\n"
    "Fecha & $T_i$ ($^\\circ$C) & $D_i$ (MM m$^3$/día) \\\\\n\\midrule\n"
    + "\n".join(filas) +
    "\n\\bottomrule\n\\end{tabular}\n"
)
escribir("tables/datos_muestra.tex", datos_muestra)

# --- sumas_lineal.tex
sumas_lineal = (
    "\\begin{tabular}{l r}\n\\toprule\n"
    "Cantidad & Valor \\\\\n\\midrule\n"
    f"$n$ & \\num{{{n}}} \\\\\n"
    f"$\\sum T_i$ & \\num{{{ST:.2f}}} \\\\\n"
    f"$\\sum T_i^2$ & \\num{{{ST2:.2f}}} \\\\\n"
    f"$\\sum D_i$ & \\num{{{SD:.2f}}} \\\\\n"
    f"$\\sum T_i D_i$ & \\num{{{STD:.2f}}} \\\\\n"
    "\\bottomrule\n\\end{tabular}\n"
)
escribir("tables/sumas_lineal.tex", sumas_lineal)

# --- sumas_cuadratico.tex
sumas_cuad = (
    "\\begin{tabular}{l r}\n\\toprule\n"
    "Cantidad & Valor \\\\\n\\midrule\n"
    f"$n$ & \\num{{{n}}} \\\\\n"
    f"$\\sum T_i$ & \\num{{{ST:.2f}}} \\\\\n"
    f"$\\sum T_i^2$ & \\num{{{ST2:.2f}}} \\\\\n"
    f"$\\sum T_i^3$ & \\num{{{ST3:.2f}}} \\\\\n"
    f"$\\sum T_i^4$ & \\num{{{ST4:.2f}}} \\\\\n"
    f"$\\sum D_i$ & \\num{{{SD:.2f}}} \\\\\n"
    f"$\\sum T_i D_i$ & \\num{{{STD:.2f}}} \\\\\n"
    f"$\\sum T_i^2 D_i$ & \\num{{{ST2D:.2f}}} \\\\\n"
    "\\bottomrule\n\\end{tabular}\n"
)
escribir("tables/sumas_cuadratico.tex", sumas_cuad)

# --- sumas_exponencial.tex  (Y_i = ln D_i)
sumas_exp = (
    "\\begin{tabular}{l r}\n\\toprule\n"
    "Cantidad & Valor \\\\\n\\midrule\n"
    f"$n$ & \\num{{{n}}} \\\\\n"
    f"$\\sum T_i$ & \\num{{{ST:.2f}}} \\\\\n"
    f"$\\sum T_i^2$ & \\num{{{ST2:.2f}}} \\\\\n"
    f"$\\sum Y_i$ & \\num{{{SY:.4f}}} \\\\\n"
    f"$\\sum T_i Y_i$ & \\num{{{STY:.4f}}} \\\\\n"
    "\\bottomrule\n\\end{tabular}\n"
    "\n% Y_i = ln(D_i)\n"
)
escribir("tables/sumas_exponencial.tex", sumas_exp)

# --- coeficientes.tex
s_b, v_b = signo(b_lin, 4)
s_bc, v_bc = signo(b_cua, 4)
s_cc, v_cc = signo(c_cua, 5)
coef = (
    "\\begin{tabular}{l l}\n\\toprule\n"
    "Modelo & Función ajustada \\\\\n\\midrule\n"
    f"Lineal & $f_1(T)=\\num{{{a_lin:.4f}}} {s_b} \\num{{{v_b}}}\\,T$ \\\\\n"
    f"Cuadrático & $f_2(T)=\\num{{{a_cua:.4f}}} {s_bc} \\num{{{v_bc}}}\\,T {s_cc} \\num{{{v_cc}}}\\,T^2$ \\\\\n"
    f"Exponencial & $f_3(T)=\\num{{{A_exp:.4f}}}\\,e^{{\\num{{{B_exp:.5f}}}\\,T}}$ \\\\\n"
    "\\bottomrule\n\\end{tabular}\n"
)
escribir("tables/coeficientes.tex", coef)

# --- metricas.tex
def fila_metrica(nombre, sse, rmse, r2):
    marca = r"\;$\star$" if nombre == seleccionado else ""
    return (f"{nombre}{marca} & \\num{{{sse:.2f}}} & \\num{{{rmse:.4f}}} "
            f"& \\num{{{r2:.4f}}} \\\\")

metr = (
    "\\begin{tabular}{l r r r}\n\\toprule\n"
    "Modelo & SSE & RMSE & $R^2$ \\\\\n\\midrule\n"
    + fila_metrica("Lineal", sse_l, rmse_l, r2_l) + "\n"
    + fila_metrica("Cuadrático", sse_c, rmse_c, r2_c) + "\n"
    + fila_metrica("Exponencial", sse_e, rmse_e, r2_e) + "\n"
    + "\\bottomrule\n\\end{tabular}\n"
    "\n% El modelo marcado con $\\star$ es el seleccionado (menor RMSE).\n"
)
escribir("tables/metricas.tex", metr)

# --- estimacion_final.tex
estim = (
    "\\begin{tabular}{l r}\n\\toprule\n"
    "Concepto & Valor \\\\\n\\midrule\n"
    f"Modelo seleccionado & {seleccionado} \\\\\n"
    f"$T_0$ & \\num{{{T0:.0f}}} $^\\circ$C \\\\\n"
    f"$D(T_0)$ & \\num{{{D_T0:.2f}}} MM m$^3$/día \\\\\n"
    "\\bottomrule\n\\end{tabular}\n"
)
escribir("tables/estimacion_final.tex", estim)

# =============================================================== RESUMEN
def linea(*a):
    print(*a)

print("=" * 64)
print("VALORES PARA COMPLETAR draft.tex")
print("=" * 64)
print(f"n = {n}")
print(f"T0 = {T0:.0f} °C   (rango observado: {Tmin:.2f} a {Tmax:.2f} °C)")
print(f"Dbar = {Dbar:.4f}")
print("-" * 64)
print("SUMAS:")
print(f"  ST  = {ST:.4f}")
print(f"  ST2 = {ST2:.4f}")
print(f"  ST3 = {ST3:.4f}")
print(f"  ST4 = {ST4:.4f}")
print(f"  SD  = {SD:.4f}")
print(f"  STD = {STD:.4f}")
print(f"  ST2D= {ST2D:.4f}")
print(f"  SY  = {SY:.6f}   (Y=lnD)")
print(f"  STY = {STY:.6f}")
print("-" * 64)
print("LINEAL  f1(T)=a+bT")
print(f"  Sistema: [[{n}, {ST:.2f}],[{ST:.2f}, {ST2:.2f}]] = [{SD:.2f}, {STD:.2f}]")
print(f"  a = {a_lin:.6f}")
print(f"  b = {b_lin:.6f}")
print(f"  SSE={sse_l:.4f}  RMSE={rmse_l:.6f}  R2={r2_l:.6f}")
print("-" * 64)
print("CUADRÁTICO  f2(T)=a+bT+cT^2")
print(f"  Sistema 3x3:")
print(f"    [{n:>12.2f} {ST:>14.2f} {ST2:>16.2f}] [{SD:>14.2f}]")
print(f"    [{ST:>12.2f} {ST2:>14.2f} {ST3:>16.2f}] [{STD:>14.2f}]")
print(f"    [{ST2:>12.2f} {ST3:>14.2f} {ST4:>16.2f}] [{ST2D:>14.2f}]")
print(f"  a = {a_cua:.6f}")
print(f"  b = {b_cua:.6f}")
print(f"  c = {c_cua:.8f}")
print(f"  SSE={sse_c:.4f}  RMSE={rmse_c:.6f}  R2={r2_c:.6f}")
print("-" * 64)
print("EXPONENCIAL  f3(T)=A e^{BT}   (Y=lnD => Y=alpha+BT)")
print(f"  Sistema: [[{n}, {ST:.2f}],[{ST:.2f}, {ST2:.2f}]] = [{SY:.4f}, {STY:.4f}]")
print(f"  alpha = {alpha:.6f}")
print(f"  B     = {B_exp:.8f}")
print(f"  A = e^alpha = {A_exp:.6f}")
print(f"  SSE={sse_e:.4f}  RMSE={rmse_e:.6f}  R2={r2_e:.6f}")
print("-" * 64)
print(f"MODELO SELECCIONADO (menor RMSE): {seleccionado}")
print(f"Estimaciones en T0={T0:.0f}°C:  "
      f"lineal={est['Lineal']:.4f}  cuad={est['Cuadrático']:.4f}  exp={est['Exponencial']:.4f}")
print(f"D(T0) con modelo seleccionado = {D_T0:.4f} MM m3/día")
print("=" * 64)
print("OK: figuras en figures/  y tablas en tables/")
