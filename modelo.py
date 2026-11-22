import json
import pulp

SEMANAS = 52          
PESOS_POR_MM = 1e6    


def cargar_datos(ruta="datos.json"):
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
    g = datos["g"]                
    K = datos["K"]                 
    F = datos["F"]                 
    d = datos["d"]                 
    c = datos["c"] * factor_c      

    I = range(len(g))             
    J = range(len(K))             

    m = pulp.LpProblem("Centros_de_acopio", pulp.LpMinimize)

    x = [[pulp.LpVariable(f"envio_{i+1}_{j+1}", lowBound=0) for j in J] for i in I]
    y = [pulp.LpVariable(f"opera_{j+1}", cat="Binary") for j in J]  

    costo_fijo = pulp.lpSum(F[j] * y[j] for j in J)

    costo_transp = pulp.lpSum(
        SEMANAS * c * d[i][j] * x[i][j] / PESOS_POR_MM for i in I for j in J
    )
    m += costo_fijo + costo_transp

    for i in I:
        m += pulp.lpSum(x[i][j] for j in J) == g[i], f"procesar_sector_{i+1}"

    for j in J:
        m += pulp.lpSum(x[i][j] for i in I) <= K[j] * y[j], f"capacidad_sitio_{j+1}"

    if humedal:
        m += y[0] + y[3] <= 1, "humedal_sitios_1_y_4"
    if uso_minimo is not None:
        for j in J:
            m += (pulp.lpSum(x[i][j] for i in I) >= uso_minimo * K[j] * y[j],
                  f"uso_minimo_sitio_{j+1}")

    m.solve(pulp.PULP_CBC_CMD(msg=0))

    estado = pulp.LpStatus[m.status]
    if estado != "Optimal":
        return {"estado": estado}

    envio = [[x[i][j].value() or 0.0 for j in J] for i in I]
    return {
        "estado": estado,
        "total": pulp.value(m.objective),
        "fijo": pulp.value(costo_fijo),
        "transporte": pulp.value(costo_transp),
        "opera": [int(round(y[j].value())) for j in J],
        "envio": envio,
    }