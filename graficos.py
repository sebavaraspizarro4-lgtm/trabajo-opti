import os
import matplotlib.pyplot as plt
from modelo import cargar_datos, resolver


def dibujar_mapa(datos, r, titulo, archivo):
    """Mapa con sectores, sitios (abiertos/cerrados) y flechas de flujo."""
    # Coordenadas (km) de sectores y sitios, y generación de cada sector
    sxy, kxy, g = datos["sector_xy"], datos["sitio_xy"], datos["g"]
    I, J = range(len(g)), range(len(datos["K"]))   # sectores y sitios

    fig, ax = plt.subplots(figsize=(7.5, 6.5))

    # Flechas sector a sitio, con grosor proporcional a las toneladas enviadas.
    # Solo se dibujan los envíos mayores a 0,5 ton/semana.
    for i in I:
        for j in J:
            q = r["envio"][i][j]    # ton/semana del sector i al sitio j
            if q > 0.5:
                ax.annotate("", xy=kxy[j], xytext=sxy[i],
                            arrowprops=dict(arrowstyle="->", color="tab:blue",
                                            lw=0.6 + q / 45, alpha=0.65,
                                            shrinkA=6, shrinkB=6))

    # Sectores: círculos verdes cuyo tamaño es proporcional a la generación
    ax.scatter([p[0] for p in sxy], [p[1] for p in sxy],
               s=[v * 3 for v in g], alpha=0.30, color="tab:green",
               label="Sector (tamaño = generación)")
    for i in I:
        ax.annotate(f"S{i+1}", sxy[i], ha="center", va="center",
                    fontsize=10, fontweight="bold")

    # Sitios: cuadrado rojo relleno = opera; cuadrado gris vacío = cerrado
    for j in J:
        if r["opera"][j]:
            ax.scatter(*kxy[j], marker="s", s=90, color="tab:red", zorder=3)
        else:
            ax.scatter(*kxy[j], marker="s", s=60, facecolors="none",
                       edgecolors="gray", zorder=3)
        # Número del sitio junto a su marcador
        ax.annotate(f"{j+1}", kxy[j], xytext=(6, 6),
                    textcoords="offset points", fontsize=10)

    # Entradas vacías, solo para que la leyenda muestre los dos tipos de sitio
    ax.scatter([], [], marker="s", s=90, color="tab:red", label="Sitio que opera")
    ax.scatter([], [], marker="s", s=60, facecolors="none",
               edgecolors="gray", label="Sitio cerrado")

    # Ejes, título con el costo total, cuadrícula y leyenda
    ax.set_xlabel("x (km)")
    ax.set_ylabel("y (km)")
    ax.set_title(f"{titulo}\nCosto total: {r['total']:.1f} MM$/año")
    ax.set_aspect("equal")      # misma escala en x e y para no deformar distancias
    ax.grid(alpha=0.3)
    ax.legend(loc="lower left", fontsize=8)
    fig.savefig(archivo, dpi=200, bbox_inches="tight")
    plt.close(fig)              # libera memoria y evita abrir ventanas


def grafico_costos(resultados, archivo):
    """Barras apiladas: costo fijo + transporte por escenario."""
    nombres = list(resultados.keys())
    fijo = [resultados[n]["fijo"] for n in nombres]          # M$/año
    transp = [resultados[n]["transporte"] for n in nombres]  # M$/año
    total = [resultados[n]["total"] for n in nombres]        # M$/año

    fig, ax = plt.subplots(figsize=(7, 5))
    # Barra de costo fijo y la de transporte 
    ax.bar(nombres, fijo, label="Costo fijo", color="tab:orange")
    ax.bar(nombres, transp, bottom=fijo, label="Costo de transporte",
           color="tab:blue")
    # Costo total escrito sobre cada barra
    for k, n in enumerate(nombres):
        ax.text(k, total[k] + 8, f"{total[k]:.1f}", ha="center", fontweight="bold")
    ax.set_ylabel("MM$/año")
    ax.set_title("Costo total anual por escenario")
    ax.set_ylim(0, max(total) * 1.12)  
    ax.legend()
    ax.grid(axis="y", alpha=0.3)
    fig.savefig(archivo, dpi=200, bbox_inches="tight")
    plt.close(fig)


def grafico_uso(datos, resultados, archivo):
    """Uso (%) de cada centro que opera, por escenario."""
    K = datos["K"]                                  # capacidad de cada sitio (ton/semana)
    I, J = range(len(datos["g"])), range(len(K))
    # Un panel por escenario, con el mismo eje vertical para poder compararlos
    fig, axs = plt.subplots(1, len(resultados), figsize=(5 * len(resultados), 4),
                            sharey=True)
    for ax, (nombre, r) in zip(axs, resultados.items()):
        sitios = [j for j in J if r["opera"][j]]    # solo los centros que operan
        # Uso (%) = toneladas recibidas por el sitio / capacidad * 100
        uso = [100 * sum(r["envio"][i][j] for i in I) / K[j] for j in sitios]
        ax.bar([f"S{j+1}" for j in sitios], uso, color="tab:purple")
        # Línea del mínimo contractual de 50 %, como referencia
        ax.axhline(50, color="red", ls="--", lw=1, label="Mínimo 50 %")
        ax.set_title(nombre)
        ax.set_ylim(0, 110)
        ax.grid(axis="y", alpha=0.3)
    axs[0].set_ylabel("Uso de la capacidad (%)")
    axs[0].legend(fontsize=8)
    fig.savefig(archivo, dpi=200, bbox_inches="tight")
    plt.close(fig)


def generar():
    """Resuelve los tres escenarios principales y guarda todas las figuras."""
    os.makedirs("informe", exist_ok=True)   # crea la carpeta si no existe
    datos = cargar_datos("datos.json")

    # Escenarios que se grafican: base (P1), normativo (P2) y sensibilidad (P4)
    resultados = {
        "P1: base": resolver(datos),
        "P2: normativo": resolver(datos, humedal=True, uso_minimo=0.5),
        "P4: transporte +50 %": resolver(datos, factor_c=1.5),
    }

    dibujar_mapa(datos, resultados["P1: base"],
                 "P1: modelo base", "informe/mapa_p1.png")
    dibujar_mapa(datos, resultados["P2: normativo"],
                 "P2: escenario normativo", "informe/mapa_p2.png")
    dibujar_mapa(datos, resultados["P4: transporte +50 %"],
                 "P4: transporte +50 %", "informe/mapa_p4.png")
    grafico_costos(resultados, "informe/costos.png")
    grafico_uso(datos, resultados, "informe/uso.png")
    print("\nGráficos guardados en la carpeta informe/")


if __name__ == "__main__":
    generar()