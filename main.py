"""
main.py
Une Model + View + Controller. Para conectar la BD real, solo cambia las 5 líneas
de "modelos" por los modelos reales (los que hagan SQL); View y Controller no cambian.
"""
from esquema import ESQUEMAS
from modelos import ModeloMemoria
from vistas import Vista, VistaPrincipal
from controladores import CONTROLADORES, ControladorPrincipal


def construir_aplicacion():
    # ---- MODELS (aquí se reemplazan por los reales cuando exista la conexión) ----
    usuarios = ModeloMemoria("id_usuario")
    vehiculos = ModeloMemoria("id_vehiculo", {"id_usuario_fk": usuarios})
    cajones = ModeloMemoria("id_cajon", {"id_vehiculo_fk": vehiculos})
    roles = ModeloMemoria("id_rol", {"id_usuario_fk": usuarios})
    contactos = ModeloMemoria("id_contacto", {"id_usuario_fk": usuarios})
    modelos = {
        "usuarios": usuarios,
        "vehiculos": vehiculos,
        "cajones": cajones,
        "roles": roles,
        "contactos": contactos,
    }

    # ---- VIEW + CONTROLLER por cada tabla ----
    controladores = {}
    opciones = []
    for numero, clave in enumerate(ESQUEMAS, start=1):
        entidad = ESQUEMAS[clave]
        vista = Vista(entidad)
        controladores[str(numero)] = CONTROLADORES[clave](entidad, modelos[clave], vista)
        opciones.append((numero, entidad.titulo))

    vista_principal = VistaPrincipal("YARD CONSOLE", opciones)
    return ControladorPrincipal(vista_principal, controladores)


if __name__ == "__main__":
    construir_aplicacion().ejecutar()
