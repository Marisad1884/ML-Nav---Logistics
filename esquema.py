"""
esquema.py
Describe las 5 tablas del diagrama (campos, etiquetas y validaciones).
Lo usan tanto las Vistas (para saber qué pedir/mostrar) como los
Controladores (para validar lo que escribe el usuario).
Los nombres de campo son EXACTAMENTE los nombres de columna de la BD.
"""
import re
from dataclasses import dataclass
from datetime import datetime
from typing import Callable, Tuple

ROLES_VALIDOS = ("conductor", "supervisor")
ESTATUS_VALIDOS = ("habilitado", "deshabilitado")


# ---------------------------------------------------------------- validadores
# Cada validador recibe un str, devuelve el valor limpio o lanza ValueError.
def texto(max_len=100):
    def _validar(valor):
        valor = valor.strip()
        if len(valor) > max_len:
            raise ValueError(f"máximo {max_len} caracteres")
        return valor
    return _validar


def entero_positivo(valor):
    valor = str(valor).strip()
    if not valor.isdigit() or int(valor) <= 0:
        raise ValueError("debe ser un número entero positivo")
    return int(valor)


def telefono(valor):
    solo_digitos = re.sub(r"[\s\-()]", "", valor)
    if not re.fullmatch(r"\d{10}", solo_digitos):
        raise ValueError("debe tener 10 dígitos")
    return solo_digitos


def correo(valor):
    valor = valor.strip()
    if not re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", valor):
        raise ValueError("correo no válido (ej. nombre@dominio.com)")
    return valor.lower()


def hora(valor):
    for formato in ("%H:%M", "%H:%M:%S"):
        try:
            return datetime.strptime(valor.strip(), formato).strftime("%H:%M:%S")
        except ValueError:
            continue
    raise ValueError("formato de hora inválido, usa HH:MM (ej. 08:30)")


def rol(valor):
    valor = valor.strip().lower()
    if valor not in ROLES_VALIDOS:
        raise ValueError("debe ser: " + " o ".join(ROLES_VALIDOS))
    return valor


def entero_no_negativo(valor):
    valor = str(valor).strip()
    if not valor.isdigit():
        raise ValueError("debe ser un número entero (0 o más)")
    return int(valor)


def estatus(valor):
    valor = valor.strip().lower()
    if valor not in ESTATUS_VALIDOS:
        raise ValueError("debe ser: " + " o ".join(ESTATUS_VALIDOS))
    return valor


# ------------------------------------------------------------------- esquema
@dataclass(frozen=True)
class Campo:
    nombre: str                      # nombre de la columna en la BD
    etiqueta: str                    # texto que ve el usuario
    validar: Callable = texto()      # función de validación
    requerido: bool = True


@dataclass(frozen=True)
class Entidad:
    clave: str                       # nombre de la tabla
    titulo: str                      # plural para menús
    singular: str
    pk: str                          # llave primaria
    campos: Tuple[Campo, ...]        # columnas editables (sin la PK)


ESQUEMAS = {
    "usuarios": Entidad(
        clave="usuarios", titulo="Usuarios", singular="usuario", pk="id_usuario",
        campos=(
            Campo("nombres", "Nombre(s)", texto(100)),
            Campo("apellido1", "Primer apellido", texto(100)),
            Campo("apellido2", "Segundo apellido", texto(100), requerido=False),
            Campo("estatus", "Estatus (habilitado/deshabilitado)", estatus),
        ),
    ),
    "vehiculos": Entidad(
        clave="vehiculos", titulo="Vehículos", singular="vehículo", pk="id_vehiculo",
        campos=(
            Campo("modelo", "Modelo", texto(50)),
            Campo("marca", "Marca", texto(50)),
            Campo("matricula", "Matrícula", texto(20)),
            Campo("descripcion_vehiculo", "Descripción", texto(255), requerido=False),
            Campo("id_usuario_fk", "ID del usuario (conductor)", entero_positivo),
        ),
    ),
    "cajones": Entidad(
        clave="cajones", titulo="Cajones", singular="cajón", pk="id_cajon",
        campos=(
            Campo("nombre", "Nombre del cajón", texto(50)),
            Campo("hora_apertura", "Hora de inicio (HH:MM)", hora),
            Campo("hora_cierre", "Hora de fin (HH:MM)", hora),
            Campo("paquetes", "Paquetes entregados", entero_no_negativo),
            Campo("id_vehiculo_fk", "ID del vehículo asignado", entero_positivo,
                  requerido=False),
        ),
    ),
    "roles": Entidad(
        clave="roles", titulo="Roles", singular="rol", pk="id_rol",
        campos=(
            Campo("rol", "Rol (conductor/supervisor)", rol),
            Campo("rol_descripcion", "Descripción del rol", texto(255), requerido=False),
            Campo("id_usuario_fk", "ID del usuario", entero_positivo),
        ),
    ),
    "contactos": Entidad(
        clave="contactos", titulo="Contactos", singular="contacto", pk="id_contacto",
        campos=(
            Campo("telefono", "Teléfono (10 dígitos)", telefono),
            Campo("email", "Correo electrónico", correo),
            Campo("id_usuario_fk", "ID del usuario", entero_positivo),
        ),
    ),
}
