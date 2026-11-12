"""
persistencia.py
Guarda/carga los datos de los ModeloMemoria en un archivo JSON (datos.json)
para que la información no se pierda al cerrar la aplicación.
Cuando exista la BD real, este archivo ya no hace falta.
"""
import json
import os

RUTA = os.path.join(os.path.dirname(os.path.abspath(__file__)), "datos.json")


def guardar(modelos, ruta=RUTA):
    salida = {
        clave: {"siguiente": m._siguiente, "registros": list(m._datos.values())}
        for clave, m in modelos.items()
    }
    with open(ruta, "w", encoding="utf-8") as f:
        json.dump(salida, f, ensure_ascii=False, indent=2)


def cargar(modelos, ruta=RUTA):
    """Devuelve True si cargó datos, False si no existe el archivo o está dañado."""
    if not os.path.exists(ruta):
        return False
    try:
        with open(ruta, encoding="utf-8") as f:
            entrada = json.load(f)
        for clave, m in modelos.items():
            bloque = entrada[clave]
            m._datos = {r[m.pk]: r for r in bloque["registros"]}
            m._siguiente = bloque["siguiente"]
        return True
    except (ValueError, KeyError, OSError):
        return False
