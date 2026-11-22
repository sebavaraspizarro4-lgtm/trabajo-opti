import pandas as pd
import runpy
from modelo import cargar_datos, resolver

pd.set_option("display.width", 200)


def mostrar(nombre, r, datos):
    print("\n" + "=" * 70)
    print(nombre)
    print("=" * 70)
    if r["estado"] != "Optimal":
        print("Estado:", r["estado"])
        return

    K = datos["K"]
    J = range(len(K))
    I = range(len(datos["g"]))

    abiertos = [j + 1 for j in J if r["opera"][j] == 1]
    print("Centros que operan:", abiertos)

    envio = pd.DataFrame(
        r["envio"],
        index=[f"Sector {i+1}" for i in I],
        columns=[f"Sitio {j+1}" for j in J],
    ).round(1)
    print("\nToneladas semanales sector -> sitio:")
    print(envio.to_string())

    print("\nUso de cada centro:")
    for j in J:
        if r["opera"][j]:
            carga = sum(r["envio"][i][j] for i in I)
            print(f"  Sitio {j+1}: {carga:.1f} / {K[j]} ton/sem = {100*carga/K[j]:.1f} %")

    print(f"\nCosto fijo:       {r['fijo']:.2f} MM$/año")
    print(f"Costo transporte: {r['transporte']:.2f} MM$/año")
    print(f"COSTO TOTAL:      {r['total']:.2f} MM$/año")


if __name__ == "__main__":

    runpy.run_path("generar_datos.py")
    
    datos = cargar_datos("datos.json")

    mostrar("PREGUNTA 1: MODELO BASE",
            resolver(datos), datos)

    mostrar("PREGUNTA 2: ESCENARIO NORMATIVO (humedal + uso minimo 50 %)",
            resolver(datos, humedal=True, uso_minimo=0.5), datos)


    mostrar("EXTRA: solo humedal",
            resolver(datos, humedal=True), datos)
    mostrar("EXTRA: solo uso minimo 50 %",
            resolver(datos, uso_minimo=0.5), datos)

    mostrar("PREGUNTA 4: SENSIBILIDAD (transporte +50 %)",
            resolver(datos, factor_c=1.5), datos)

    import graficos
    graficos.generar()