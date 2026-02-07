import time, random
from multiprocessing import cpu_count, get_context
_HORARIOS = None
_REPS = 1

def generar_horario(num_sesiones, semilla):
    random.seed(semilla)
    horario = []
    for i in range(num_sesiones):
        grupo = i % 20
        salon = i % 15
        dia = random.randint(0, 4)
        inicio = random.randint(7, 19)
        duracion = random.choice([1, 2])
        fin = inicio + duracion
        if fin > 21:
            fin = 21
        horario.append((grupo, salon, dia, inicio, fin))
    return horario
def _contar_solapes(intervalos):
    if len(intervalos) < 2:
        return 0
    intervalos.sort()
    conflictos = 0
    ultimo_fin = intervalos[0][1]
    for inicio, fin in intervalos[1:]:
        if inicio < ultimo_fin:
            conflictos += 1
            ultimo_fin = max(ultimo_fin, fin)
        else:
            ultimo_fin = fin
    return conflictos
def validar_horario(horario, hora_max=21):
    por_grupo = {}
    por_salon = {}
    fuera_jornada = 0
    for grupo, salon, dia, inicio, fin in horario:
        if fin > hora_max:
            fuera_jornada += 1
        por_grupo.setdefault((dia, grupo), []).append((inicio, fin))
        por_salon.setdefault((dia, salon), []).append((inicio, fin))
    conflictos_grupo = sum(_contar_solapes(lst) for lst in por_grupo.values())
    conflictos_salon = sum(_contar_solapes(lst) for lst in por_salon.values())
    return conflictos_grupo + conflictos_salon + fuera_jornada
def _init_worker(horarios, repeticiones):
    global _HORARIOS, _REPS
    _HORARIOS = horarios
    _REPS = repeticiones

def _validar_idx(idx):
    assert _HORARIOS is not None
    h = _HORARIOS[idx]
    if _REPS == 1:
        return validar_horario(h)
    return sum(validar_horario(h) for _ in range(_REPS))

def ejecutar_serial(lista_horarios, repeticiones=1):
    t0 = time.perf_counter()
    if repeticiones == 1:
        resultados = [validar_horario(h) for h in lista_horarios]
    else:
        resultados = [sum(validar_horario(h) for _ in range(repeticiones)) for h in lista_horarios]
    return time.perf_counter() - t0, resultados
def ejecutar_paralelo(lista_horarios, num_procesos, repeticiones=1, pool=None):
    t0 = time.perf_counter()
    p = max(1, min(num_procesos, cpu_count()))
    n = len(lista_horarios)
    indices = range(n)
    chunksize = max(1, n // p)
    if pool is None:
        ctx = get_context("spawn")
        with ctx.Pool(processes=p, initializer=_init_worker, initargs=(lista_horarios, repeticiones)) as pool:
            resultados = pool.map(_validar_idx, indices, chunksize=chunksize)
    else:
        resultados = pool.map(_validar_idx, indices, chunksize=chunksize)
    return time.perf_counter() - t0, resultados
def ejecutar_experimento(num_horarios=50, sesiones_por_horario=200, num_procesos=8, repeticiones=20):
    p = max(1, min(num_procesos, cpu_count()))
    print("Configuración:", num_horarios, "horarios x", sesiones_por_horario, "sesiones")
    print("Procesos:", p, "| Repeticiones:", repeticiones)
    lista_horarios = [generar_horario(sesiones_por_horario, 1000 + i) for i in range(num_horarios)]
    objetivo = 2.0
    for _ in range(6):
        t_serial, res_s = ejecutar_serial(lista_horarios, repeticiones)
        if t_serial >= objetivo:
            break
        repeticiones *= 2
    if t_serial < objetivo:
        t_serial, res_s = ejecutar_serial(lista_horarios, repeticiones)
    print("Tiempo serial:", round(t_serial, 3), "seg")
    print("Repeticiones ajustadas:", repeticiones)
    ctx = get_context("spawn")
    with ctx.Pool(processes=p, initializer=_init_worker, initargs=(lista_horarios, repeticiones)) as pool:
        tam_warm = max(1, len(lista_horarios) // p)
        pool.map(_validar_idx, range(tam_warm), chunksize=1)
        t_par, res_p = ejecutar_paralelo(lista_horarios, p, repeticiones, pool)
    print("Tiempo paralelo:", round(t_par, 3), "seg")
    assert res_s == res_p, "Error: serial y paralelo no coinciden"
    speedup = t_serial / t_par if t_par > 0 else float("inf")
    eficiencia = (speedup / p) * 100
    overhead = t_par - (t_serial / p)
    print("Speedup:", round(speedup, 2), "x")
    print("Eficiencia:", round(eficiencia, 1), "%")
    print("Overhead:", round(overhead, 3), "seg")
    return t_serial, t_par, speedup, eficiencia, overhead

if __name__ == "__main__":
    ejecutar_experimento(num_horarios=100, sesiones_por_horario=200, num_procesos=4)
