import json
import os
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

seed = 2818  # <-- reemplazar por el número asignado a su grupo\n",   

assert seed != 0, "Reemplace seed por el número asignado a su grupo"
rs = np.random.RandomState(seed)

# Coordenadas base (km) del centro de cada sector de la comuna
sector_xy = np.array([[2.0,10.0],[7.0,11.0],[12.5,10.0],[2.5,5.0],[7.5,6.0],[13.0,5.0],[8.0,1.5]])

# Generación base de material reciclable por sector (ton/semana)
generacion_base = np.array([90,120,70,150,180,100,110])

# Sector donde se ubica cada sitio candidato
sitio_sector = np.array([1,2,3,4,5,5,6,7,7])

# Coordenadas base (km) de cada sitio candidato
sitio_xy = np.array([[2.6,9.4],[6.6,10.4],[11.8,9.6],[3.2,5.4],[7.0,6.6],
                     [8.4,5.4],[12.4,5.6],[7.4,2.0],[8.8,1.8]])

# Capacidad base de cada sitio (ton/semana)
capacidad_base = np.array([200,300,160,260,320,220,200,180,160])

# Costo fijo base de operación de cada sitio (millones de pesos por año)
costo_fijo_base = np.array([60,110,50,90,120,85,70,55,50])

# Perturbación de ubicaciones (±0,6 km)
sector_xy = sector_xy + rs.uniform(-0.6, 0.6, sector_xy.shape)
sitio_xy = sitio_xy + rs.uniform(-0.6, 0.6, sitio_xy.shape)

# Perturbación de la generación (±15%)
generacion = (generacion_base*(1 + rs.uniform(-0.15, 0.15, len(generacion_base)))).astype(int)

# Perturbación de capacidades (±10%)
capacidad = (capacidad_base*(1 + rs.uniform(-0.10, 0.10, len(capacidad_base)))).astype(int)

# Perturbación de costos fijos (±20%)
costo_fijo = (costo_fijo_base*(1 + rs.uniform(-0.20, 0.20, len(costo_fijo_base)))).astype(int)

# Asegurar factibilidad (aun operando solo uno de los sitios 1 y 4)
cap_sin_humedal = capacidad.sum() - max(capacidad[0], capacidad[3])
if cap_sin_humedal < 1.1*generacion.sum():
    factor = 1.1*generacion.sum()/cap_sin_humedal
    capacidad = (capacidad*factor).astype(int) + 1

# Costo de transporte ($ por tonelada-km)
costo_ton_km = int(rs.randint(24, 35)*100)

# Distancia promedio de recorrido sector-sitio (km): distancia en línea recta
# por un factor 1,3 de recorrido por calles, con un mínimo de 0,8 km
dif = sector_xy[:, None, :] - sitio_xy[None, :, :]
distancia = np.sqrt((dif**2).sum(axis=2))*1.3
distancia = np.maximum(distancia, 0.8).round(1)

sectores = np.arange(1, 8)
df_generacion = pd.DataFrame({
    "Sector": sectores,
    "Generación (ton/semana)": generacion
})
df_generacion.loc["Total"] = ["", generacion.sum()]
print("GENERACIÓN DE MATERIAL RECICLABLE POR SECTOR")
print(df_generacion.to_string(index=False))

sitios = np.arange(1, 10)
df_sitios = pd.DataFrame({
    "Sitio": sitios,
    "Sector del sitio": sitio_sector,
    "Capacidad (ton/semana)": capacidad,
    "Costo fijo (MM$/año)": costo_fijo
})
df_sitios.loc["Total"] = ["", "", capacidad.sum(), ""]
print("\nDATOS DE LOS SITIOS CANDIDATOS")
print(df_sitios.to_string(index=False))

print(f"\nCOSTO DE TRANSPORTE: {costo_ton_km} $ por tonelada-km")

df_distancia = pd.DataFrame(distancia,
                            index=pd.Index(sectores, name="Sector \\ Sitio"),
                            columns=sitios)
print("\nDISTANCIA PROMEDIO DE RECORRIDO SECTOR-SITIO (km)")
print(df_distancia.round(1).to_string())

fig, ax = plt.subplots(figsize=(7, 6))
ax.scatter(sector_xy[:, 0], sector_xy[:, 1], s=generacion*3, alpha=0.35, label="Sector (tamaño = generación)")
for i in range(len(sectores)):
    ax.annotate(f"S{i+1}", sector_xy[i], ha="center", va="center", fontsize=11, fontweight="bold")
ax.scatter(sitio_xy[:, 0], sitio_xy[:, 1], marker="s", s=60, color="black", label="Sitio candidato")
for j in range(len(sitios)):
    ax.annotate(f"{j+1}", sitio_xy[j], xytext=(6, 6), textcoords="offset points", fontsize=10)
ax.set_xlabel("x (km)"); ax.set_ylabel("y (km)")
ax.set_title(f"Mapa de la comuna (semilla {seed})")
ax.set_aspect("equal"); ax.grid(alpha=0.3); ax.legend(loc="lower left", fontsize=9)

os.makedirs("informe", exist_ok=True)                            # crea la carpeta informe si no existe
plt.savefig("informe/mapa.png", dpi=200, bbox_inches="tight")    # guarda el mapa base como imagen para el informe

# Guarda los datos generados en datos.json, para que modelo.py y graficos.py
# los lean sin tener que volver a ejecutar el generador.
datos = {
    "g": generacion.tolist(),              # generación de cada sector (ton/semana), sectores 1..7
    "K": capacidad.tolist(),               # capacidad de cada sitio (ton/semana), sitios 1..9
    "F": costo_fijo.tolist(),              # costo fijo anual de cada sitio (M$/año), sitios 1..9
    "c": int(costo_ton_km),                # costo de transporte ($ por tonelada-km)
    "d": distancia.tolist(),               # distancias sector-sitio (km)
    "sector_sitio": sitio_sector.tolist(), # sector donde se ubica cada sitio
    "sector_xy": sector_xy.tolist(),       # coordenadas (km) de cada sector, usadas en los mapas
    "sitio_xy": sitio_xy.tolist(),         # coordenadas (km) de cada sitio, usadas en los mapas
}
with open("datos.json", "w") as f:
    json.dump(datos, f, indent=2)          

plt.show()