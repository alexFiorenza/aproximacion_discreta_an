"""
Construye el dataset final (temperatura media diaria del AMBA vs. demanda
prioritaria de gas natural del Gran Buenos Aires) a partir de:

  - datos_enargas.csv                  (demanda por licenciataria y fecha)
  - registro_temperatura365d_smn.txt   (Tmax/Tmin por estación y fecha, SMN)

Criterios adoptados
-------------------
  * Demanda:      D_i = D_MetroGAS + D_NaturgyBAN   (cobertura geográfica AMBA/GBA)
  * Temperatura:  T_i = promedio, sobre las estaciones del AMBA, de (Tmax+Tmin)/2.
                  Se promedian las principales estaciones del Área Metropolitana
                  para obtener un valor representativo del Gran Buenos Aires.

Salida: dataset.csv con columnas  fecha, T, D
"""

import csv
from collections import defaultdict

ENARGAS = "datos_enargas.csv"
TEMP = "registro_temperatura365d_smn.txt"
SALIDA = "dataset.csv"

LICENCIATARIAS_GBA = {"MetroGAS", "Naturgy BAN"}

# Estaciones del SMN representativas del Área Metropolitana de Buenos Aires
ESTACIONES_AMBA = {
    "AEROPARQUE AERO",
    "BUENOS AIRES OBSERVATORIO",
    "EZEIZA AERO",
    "EL PALOMAR AERO",
    "MORON AERO",
    "SAN FERNANDO AERO",
    "CAMPO DE MAYO AERO",
    "LA PLATA AERO",
}


def cargar_demanda():
    """Devuelve {fecha 'YYYY-MM-DD': demanda_GBA} solo si están las dos licenciatarias."""
    aporte = defaultdict(dict)  # fecha -> {licenciataria: valor}
    with open(ENARGAS, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            lic = row["licenciataria"]
            if lic in LICENCIATARIAS_GBA:
                try:
                    aporte[row["fecha"]][lic] = float(row["demanda_millones_m3d"])
                except ValueError:
                    pass
    demanda = {}
    for fecha, d in aporte.items():
        if LICENCIATARIAS_GBA.issubset(d):  # ambas presentes
            demanda[fecha] = sum(d.values())
    return demanda


def cargar_temperatura():
    """Devuelve {fecha 'YYYY-MM-DD': T_media_AMBA} promediando estaciones del AMBA."""
    acum = defaultdict(list)  # fecha -> [Tmedia por estacion]
    with open(TEMP, encoding="latin-1") as f:
        lineas = f.readlines()
    for linea in lineas[3:]:
        if len(linea) < 22:
            continue
        fecha_raw = linea[0:8].strip()
        if not fecha_raw.isdigit() or len(fecha_raw) != 8:
            continue
        nombre = linea[21:].strip()
        if nombre not in ESTACIONES_AMBA:
            continue
        tmax_s = linea[9:14].strip()
        tmin_s = linea[15:20].strip()
        if not tmax_s or not tmin_s:  # registro incompleto
            continue
        try:
            tmax = float(tmax_s)
            tmin = float(tmin_s)
        except ValueError:
            continue
        dd, mm, yyyy = fecha_raw[0:2], fecha_raw[2:4], fecha_raw[4:8]
        fecha = f"{yyyy}-{mm}-{dd}"
        acum[fecha].append((tmax + tmin) / 2.0)
    return {fecha: sum(v) / len(v) for fecha, v in acum.items()}


def main():
    demanda = cargar_demanda()
    temperatura = cargar_temperatura()
    fechas = sorted(set(demanda) & set(temperatura))

    filas = [(f, temperatura[f], demanda[f]) for f in fechas]

    with open(SALIDA, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["fecha", "T", "D"])
        for fecha, T, D in filas:
            w.writerow([fecha, f"{T:.4f}", f"{D:.4f}"])

    Ts = [r[1] for r in filas]
    Ds = [r[2] for r in filas]
    print(f"Fechas demanda GBA:        {len(demanda)}")
    print(f"Fechas temperatura AMBA:   {len(temperatura)}")
    print(f"Observaciones tras merge:  n = {len(filas)}")
    print(f"Rango fechas:              {fechas[0]}  ->  {fechas[-1]}")
    print(f"Temperatura  T: min={min(Ts):.2f}  max={max(Ts):.2f}  media={sum(Ts)/len(Ts):.2f} °C")
    print(f"Demanda      D: min={min(Ds):.2f}  max={max(Ds):.2f}  media={sum(Ds)/len(Ds):.2f} MMm3/d")
    print(f"Archivo generado: {SALIDA}")


if __name__ == "__main__":
    main()
