#Como Requisito: python -m pip install "pulp==2.9.0" pandas numpy matplotlib
#Ya que en esta versión de pulp funciona la API usada.
import pandas as pd
import runpy
from modelo import cargar_datos, resolver

# Ancho de la tabla impresa en consola, para que la matriz de envíos
# (7 sectores x 9 sitios) no se corte en varias líneas.
pd.set_option("display.width", 200)


def mostrar(nombre, r, datos):
    """
    Imprime en pantalla la solución de un escenario.

    nombre : título del escenario (ej. "PREGUNTA 1: MODELO BASE")
    r      : diccionario de resultados devuelto por resolver()
    datos  : datos del problema (para leer capacidades K y generación g)
    """
    # Encabezado del escenario
    print("\n" + "=" * 70)
    print(nombre)
    print("=" * 70)

    # Si al resolver no encontró solución óptima, se avisa y se sale
    if r["estado"] != "Optimal":
        print("Estado:", r["estado"])
        return

    K = datos["K"]                  # capacidad de cada sitio (ton/semana)
    J = range(len(K))               # sitios candidatos (índices 0..8)
    I = range(len(datos["g"]))      # sectores (índices 0..6)

    # Lista de sitios que operan, numerados como en el enunciado (1..9)
    abiertos = [j + 1 for j in J if r["opera"][j] == 1]
    print("Centros que operan:", abiertos)

    # Tabla de toneladas semanales enviadas de cada sector a cada sitio
    envio = pd.DataFrame(
        r["envio"],
        index=[f"Sector {i+1}" for i in I],
        columns=[f"Sitio {j+1}" for j in J],
    ).round(1)
    print("\nToneladas semanales sector -> sitio:")
    print(envio.to_string())

    # Porcentaje de uso de cada centro que opera: carga recibida / capacidad
    print("\nUso de cada centro:")
    for j in J:
        if r["opera"][j]:
            carga = sum(r["envio"][i][j] for i in I)   # ton/semana recibidas por el sitio j
            print(f"  Sitio {j+1}: {carga:.1f} / {K[j]} ton/sem = {100*carga/K[j]:.1f} %")

    # Desglose del costo total anual (MM$/año)
    print(f"\nCosto fijo:       {r['fijo']:.2f} MM$/año")
    print(f"Costo transporte: {r['transporte']:.2f} MM$/año")
    print(f"COSTO TOTAL:      {r['total']:.2f} MM$/año")


if __name__ == "__main__":

    # Ejecuta el generador de datos del profe: imprime las tablas, guarda
    # datos.json e informe/mapa.png, y muestra el mapa base.
    runpy.run_path("generar_datos.py")

    # Carga los datos recién generados
    datos = cargar_datos("datos.json")

    # Pregunta 1: modelo base (sin condiciones adicionales)
    mostrar("PREGUNTA 1: MODELO BASE",
            resolver(datos), datos)

    # Pregunta 2: escenario normativo (humedal: a lo más uno entre sitios 1 y 4,
    # y uso mínimo de 50 % de la capacidad en todo centro que opere)
    mostrar("PREGUNTA 2: ESCENARIO NORMATIVO (humedal + uso minimo 50 %)",
            resolver(datos, humedal=True, uso_minimo=0.5), datos)

    # Casos extra para aislar qué condición provoca el cambio (Pregunta 3):
    # primero solo la restricción del humedal
    mostrar("EXTRA: solo humedal",
            resolver(datos, humedal=True), datos)
    mostrar("EXTRA: solo uso minimo 50 %",
            resolver(datos, uso_minimo=0.5), datos)

    # Pregunta 4: sensibilidad, con el costo de transporte 50 % más alto
    # (modelo de la Pregunta 1, con c multiplicado por 1.5)
    mostrar("PREGUNTA 4: SENSIBILIDAD (transporte +50 %)",
            resolver(datos, factor_c=1.5), datos)

    # Genera los mapas con flujos y los gráficos de costos y uso en informe
    import graficos
    graficos.generar()