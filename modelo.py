import json
import pulp

SEMANAS = 52               # semanas de operación al año (datos semanales se repiten)
PESOS_POR_MILLON = 1e6     # factor de conversión: $ -> millones de pesos (MM$)


def cargar_datos(ruta="datos.json"):
    """Lee los datos generados por generar_datos.py."""
    with open(ruta) as f:
        return json.load(f)


def resolver(datos, humedal=False, uso_minimo=None, factor_c=1.0):
    """
    Resuelve el problema de localización de centros de acopio.

    humedal    : si True, agrega y1 + y4 <= 1 (sitios 1 y 4 junto al humedal)
    uso_minimo : fracción mínima de la capacidad que debe procesar un centro
                 que opera (ej. 0.5). None = sin restricción.
    factor_c   : multiplicador del costo de transporte (1.5 = alza de 50 %)
    """
    g = datos["g"]                 # g[i]: generación del sector i (ton/semana)
    K = datos["K"]                 # K[j]: capacidad máxima del sitio j (ton/semana)
    F = datos["F"]                 # F[j]: costo fijo anual del sitio j (MM$/año)
    d = datos["d"]                 # d[i][j]: distancia sector i -> sitio j (km)
    c = datos["c"] * factor_c      # c: costo de transporte ($/ton-km)

    I = range(len(g))              # I: sectores (índices 0..6 = sectores 1..7)
    J = range(len(K))              # J: sitios candidatos (índices 0..8 = sitios 1..9)

    m = pulp.LpProblem("Centros_de_acopio", pulp.LpMinimize)

    if hasattr(m, "add_variable"):
        # x[i][j]: toneladas semanales del sector i enviadas al sitio j (ton/semana).
        # Es continua y no negativa: el material de un sector puede repartirse.
        x = [[m.add_variable(f"envio_{i+1}_{j+1}", lowBound=0) for j in J] for i in I]
        # y[j]: variable binaria de decisión, vale 1 si el sitio j opera, 0 si no.
        # Activa el pago del costo fijo y habilita la capacidad del sitio.
        y = [m.add_variable(f"opera_{j+1}", cat=pulp.LpBinary) for j in J]
    else:
        # x[i][j]: igual que arriba (toneladas semanales del sector i al sitio j).
        x = [[pulp.LpVariable(f"envio_{i+1}_{j+1}", lowBound=0) for j in J] for i in I]
        # y[j]: igual que arriba (1 si el sitio j opera, 0 si no).
        y = [pulp.LpVariable(f"opera_{j+1}", cat="Binary") for j in J]

    # Costo fijo anual: suma de F[j] de los sitios que operan (MM$/año).
    costo_fijo = pulp.lpSum(F[j] * y[j] for j in J)

    # Costo de transporte anual (MM$/año):
    # ton/semana * km * $/ton-km * 52 semanas/año / 1e6 = MM$/año.
    costo_transp = pulp.lpSum(
        SEMANAS * c * d[i][j] * x[i][j] / PESOS_POR_MILLON for i in I for j in J
    )

    # Objetivo: minimizar el costo total anual (fijo + transporte), en MM$/año.
    m += costo_fijo + costo_transp

    # procesar_sector_i: todo el material generado por el sector i debe
    # enviarse a algún centro, no puede quedar material sin procesar.
    for i in I:
        m += pulp.lpSum(x[i][j] for j in J) == g[i], f"procesar_sector_{i+1}"

    # capacidad_sitio_j: lo recibido por el sitio j no puede superar su
    # capacidad, y si el sitio no opera (y[j]=0) no puede recibir nada.
    for j in J:
        m += pulp.lpSum(x[i][j] for i in I) <= K[j] * y[j], f"capacidad_sitio_{j+1}"

    if humedal:
        # humedal_sitios_1_y_4: los sitios 1 y 4 colindan con un humedal
        # protegido; la autoridad permite que opere a lo más uno de ellos.
        m += y[0] + y[3] <= 1, "humedal_sitios_1_y_4"

    if uso_minimo is not None:
        # uso_minimo_sitio_j: por contrato, todo centro que opera debe procesar
        # al menos uso_minimo (50 %) de su capacidad semanal; si y[j]=0 la
        # restricción queda en 0 >= 0 y no afecta.
        for j in J:
            m += (pulp.lpSum(x[i][j] for i in I) >= uso_minimo * K[j] * y[j],
                  f"uso_minimo_sitio_{j+1}")

    if hasattr(pulp, "PULP_CBC_CMD"):
        m.solve(pulp.PULP_CBC_CMD(msg=0))
    else:
        try:
            solver = pulp.COIN_CMD(msg=0, gapRel=0)
        except TypeError:
            solver = pulp.COIN_CMD(msg=0)
        resultado = m.solve(solver)

    if hasattr(pulp, "LpStatus"):
        estado = pulp.LpStatus[m.status]
    else:
        estado = resultado.status_str
        if estado == "GapLimit" and getattr(resultado, "has_solution", False):
            estado = "Optimal"
    if estado != "Optimal":
        return {"estado": estado}

    # Se leen los valores de las variables y se calculan los costos en Python,
    # sin depender de funciones de PuLP que cambian entre versiones.
    envio = [[x[i][j].varValue or 0.0 for j in J] for i in I]
    opera = [int(round(y[j].varValue)) for j in J]

    fijo = sum(F[j] * opera[j] for j in J)                       # MM$/año
    transporte = sum(SEMANAS * c * d[i][j] * envio[i][j] / PESOS_POR_MILLON
                     for i in I for j in J)
    return {
        "estado": estado,
        "total": fijo + transporte,
        "fijo": fijo,
        "transporte": transporte,
        "opera": opera,
        "envio": envio,
    }