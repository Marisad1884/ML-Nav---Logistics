"""
controladores.py  (CONTROLLER)
Maneja el FLUJO de la petición: pide datos a la Vista, valida la entrada,
llama al Model y devuelve el resultado a la Vista.
NUNCA contiene lógica de datos ni SQL (eso es del Model).

El Model que se le pase debe cumplir este contrato (ver modelos.py):
    listar()                -> list[dict]
    obtener(id)             -> dict | None
    crear(datos: dict)      -> id nuevo
    actualizar(id, datos)   -> None
    eliminar(id)            -> None
y lanzar ModeloError ante cualquier problema (FK inexistente, registro duplicado, etc.)
"""
from esquema import ESQUEMAS, entero_positivo
from modelos import ModeloError


class ControladorBase:
    def __init__(self, entidad, modelo, vista):
        self.entidad = entidad
        self.modelo = modelo
        self.vista = vista

    # ------------------------------------------------------ bucle del menú
    def ejecutar(self):
        acciones = {
            "1": self.listar,
            "2": self.ver,
            "3": self.crear,
            "4": self.editar,
            "5": self.eliminar,
        }
        while True:
            opcion = self.vista.menu()
            if opcion == "0":
                break
            accion = acciones.get(opcion)
            if accion is None:
                self.vista.mostrar_error("Opción no válida.")
                continue
            accion()

    # ---------------------------------------------------------------- CRUD
    def listar(self):
        try:
            registros = self.modelo.listar()
        except ModeloError as e:
            return self.vista.mostrar_error(str(e))
        self.vista.mostrar_lista(registros)

    def ver(self):
        _, registro = self._buscar("consultar")
        if registro:
            self.vista.mostrar_detalle(registro)

    def crear(self):
        datos = self.vista.pedir_datos()
        limpios, errores = self._validar(datos)
        if errores:
            return self.vista.mostrar_errores(errores)
        try:
            nuevo_id = self.modelo.crear(limpios)
        except ModeloError as e:
            return self.vista.mostrar_error(str(e))
        self.vista.mostrar_mensaje(f"{self.entidad.singular.capitalize()} creado con ID {nuevo_id}.")

    def editar(self):
        id_, registro = self._buscar("editar")
        if not registro:
            return
        datos = self.vista.pedir_datos(registro)
        # Campo en blanco = conservar el valor que ya tenía
        datos = {k: (v if v != "" else registro.get(k)) for k, v in datos.items()}
        limpios, errores = self._validar(datos)
        if errores:
            return self.vista.mostrar_errores(errores)
        try:
            self.modelo.actualizar(id_, limpios)
        except ModeloError as e:
            return self.vista.mostrar_error(str(e))
        self.vista.mostrar_mensaje(f"{self.entidad.singular.capitalize()} {id_} actualizado.")

    def eliminar(self):
        id_, registro = self._buscar("eliminar")
        if not registro:
            return
        if not self.vista.confirmar(f"¿Eliminar {self.entidad.singular} {id_}?"):
            return self.vista.mostrar_mensaje("Operación cancelada.")
        try:
            self.modelo.eliminar(id_)
        except ModeloError as e:
            return self.vista.mostrar_error(str(e))
        self.vista.mostrar_mensaje(f"{self.entidad.singular.capitalize()} {id_} eliminado.")

    # ------------------------------------------------------------ auxiliares
    def _buscar(self, accion):
        """Pide un ID, lo valida y consulta al Model. Devuelve (id, registro) o (None, None)."""
        try:
            id_ = entero_positivo(self.vista.pedir_id(accion))
        except ValueError as e:
            self.vista.mostrar_error(f"El ID {e}.")
            return None, None
        try:
            registro = self.modelo.obtener(id_)
        except ModeloError as e:
            self.vista.mostrar_error(str(e))
            return None, None
        if registro is None:
            self.vista.mostrar_error(f"No existe {self.entidad.singular} con ID {id_}.")
            return None, None
        return id_, registro

    def _validar(self, datos):
        """Devuelve (datos_limpios, errores). Si errores está vacío, todo es válido."""
        limpios, errores = {}, {}
        for campo in self.entidad.campos:
            bruto = datos.get(campo.nombre)
            if bruto is None or str(bruto).strip() == "":
                if campo.requerido:
                    errores[campo.etiqueta] = "es obligatorio"
                limpios[campo.nombre] = None
                continue
            try:
                limpios[campo.nombre] = campo.validar(str(bruto))
            except ValueError as e:
                errores[campo.etiqueta] = str(e)
        if not errores:
            errores.update(self.validar_extra(limpios))
        return limpios, errores

    def validar_extra(self, datos):
        """Reglas que involucran varios campos. Las subclases la sobrescriben."""
        return {}


# ------------------------------------------------------ controladores concretos
class UsuarioController(ControladorBase):
    pass


class VehiculoController(ControladorBase):
    pass


class CajonController(ControladorBase):
    def validar_extra(self, datos):
        if datos["hora_cierre"] <= datos["hora_apertura"]:
            return {"Hora de fin (HH:MM)": "debe ser posterior a la hora de inicio"}
        return {}


class RolController(ControladorBase):
    pass


class ContactoController(ControladorBase):
    pass


CONTROLADORES = {
    "usuarios": UsuarioController,
    "vehiculos": VehiculoController,
    "cajones": CajonController,
    "roles": RolController,
    "contactos": ContactoController,
}


# --------------------------------------------------------- controlador principal
class ControladorPrincipal:
    """Enruta la opción del menú principal hacia el controlador de cada módulo."""

    def __init__(self, vista, controladores):
        self.vista = vista
        self.controladores = controladores  # dict {"1": controlador, ...}

    def ejecutar(self):
        while True:
            opcion = self.vista.menu()
            if opcion == "0":
                self.vista.despedir()
                break
            controlador = self.controladores.get(opcion)
            if controlador is None:
                self.vista.mostrar_error("Opción no válida.")
                continue
            controlador.ejecutar()
