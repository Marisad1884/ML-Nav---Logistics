"""
estado.py
Calcula el estatus de un repartidor según el horario de su cajón.

Regla:
  - Si su cuenta está DESHABILITADA (bloqueo manual del supervisor) -> deshabilitado.
  - Si la hora actual está entre hora_apertura (inclusive) y hora_cierre (exclusive) -> activo.
  - Antes de la hora de inicio -> por_iniciar.
  - A partir de la hora de fin -> finalizado.
  - Sin cajón asignado -> sin_cajon.

Ejemplo: turno de 13:00 a 17:00 -> activo a las 13:00, ya NO activo a las 17:00.
No se guarda nada: el estado se calcula cada vez que se consulta.
"""
from datetime import datetime, time

ACTIVO = "activo"
POR_INICIAR = "por_iniciar"
FINALIZADO = "finalizado"
DESHABILITADO = "deshabilitado"
SIN_CAJON = "sin_cajon"

ETIQUETAS = {
    ACTIVO: "ACTIVO",
    POR_INICIAR: "POR INICIAR",
    FINALIZADO: "FINALIZADO",
    DESHABILITADO: "DESHABILITADO",
    SIN_CAJON: "SIN CAJÓN",
}


def _a_hora(valor):
    """Acepta 'HH:MM', 'HH:MM:SS' o datetime.time."""
    if isinstance(valor, time):
        return valor
    partes = [int(p) for p in str(valor).split(":")]
    while len(partes) < 3:
        partes.append(0)
    return time(partes[0], partes[1], partes[2])


def _segundos(t):
    return t.hour * 3600 + t.minute * 60 + t.second


def estado_turno(apertura, cierre, ahora=None):
    ahora = ahora or datetime.now()
    ya = _segundos(ahora.time())
    if ya < _segundos(_a_hora(apertura)):
        return POR_INICIAR
    if ya >= _segundos(_a_hora(cierre)):
        return FINALIZADO
    return ACTIVO


def progreso_turno(apertura, cierre, ahora=None):
    """Avance del turno de 0.0 a 1.0."""
    ahora = ahora or datetime.now()
    a, c, ya = _segundos(_a_hora(apertura)), _segundos(_a_hora(cierre)), _segundos(ahora.time())
    if c <= a:
        return 0.0
    return min(1.0, max(0.0, (ya - a) / (c - a)))


def estado_repartidor(habilitado, estados_turno):
    """Estado global de una persona a partir del estado de cada uno de sus turnos."""
    if not habilitado:
        return DESHABILITADO
    for prioridad in (ACTIVO, POR_INICIAR, FINALIZADO):
        if prioridad in estados_turno:
            return prioridad
    return SIN_CAJON
