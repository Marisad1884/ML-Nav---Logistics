"""
modelos.py  (MODEL de prueba)
NO es el Model real. Es un sustituto en memoria para poder probar View + Controller
sin base de datos. Cuando tengan la conexión, el Model real (con SQL) solo debe
cumplir el mismo contrato y lanzar ModeloError ante los errores:

    listar()                -> list[dict]     (cada dict con las columnas de la tabla, incluida la PK)
    obtener(id)             -> dict | None
    crear(datos: dict)      -> id nuevo
    actualizar(id, datos)   -> None
    eliminar(id)            -> None

Ejemplo: el modelo real de usuarios devolvería dicts como
    {"id_usuario": 1, "nombres": "Ana", "apellido1": "Pérez", "apellido2": None}
"""


class ModeloError(Exception):
    """Error de la capa Model (FK inexistente, duplicado, fallo de conexión, etc.)."""


class ModeloMemoria:
    def __init__(self, pk, referencias=None):
        """
        pk: nombre de la llave primaria (ej. "id_usuario")
        referencias: {"id_usuario_fk": modelo_de_usuarios} para simular las FK
        """
        self.pk = pk
        self.referencias = referencias or {}
        self._datos = {}
        self._siguiente = 1

    def listar(self):
        return [dict(r) for r in self._datos.values()]

    def obtener(self, id_):
        registro = self._datos.get(id_)
        return dict(registro) if registro else None

    def crear(self, datos):
        self._revisar_fk(datos)
        nuevo_id = self._siguiente
        self._siguiente += 1
        self._datos[nuevo_id] = {self.pk: nuevo_id, **datos}
        return nuevo_id

    def actualizar(self, id_, datos):
        if id_ not in self._datos:
            raise ModeloError(f"No existe el registro {id_}.")
        self._revisar_fk(datos)
        self._datos[id_].update(datos)

    def eliminar(self, id_):
        if id_ not in self._datos:
            raise ModeloError(f"No existe el registro {id_}.")
        del self._datos[id_]

    def _revisar_fk(self, datos):
        for columna, modelo_padre in self.referencias.items():
            valor = datos.get(columna)
            if valor is not None and modelo_padre.obtener(valor) is None:
                raise ModeloError(f"El ID {valor} de '{columna}' no existe.")
