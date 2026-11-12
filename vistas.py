"""
vistas.py  (VIEW)
Solo se encarga de PRESENTAR datos y PEDIR datos al usuario (consola).
No valida reglas de negocio ni toca la base de datos: eso es del Controller / Model.
Si después quieren cambiar a una web o a Tkinter, solo se reemplaza este archivo
mientras los métodos mantengan el mismo nombre.
"""


class Vista:
    """Vista genérica para cualquier entidad del esquema."""

    def __init__(self, entidad):
        self.entidad = entidad

    # ---------------------------------------------------------------- menú
    def menu(self):
        print(f"\n=== {self.entidad.titulo.upper()} ===")
        print("1. Listar")
        print("2. Ver detalle")
        print("3. Crear")
        print("4. Editar")
        print("5. Eliminar")
        print("0. Volver")
        return input("Opción: ").strip()

    # ----------------------------------------------------------- mostrar
    def mostrar_lista(self, registros):
        if not registros:
            print(f"\n(No hay {self.entidad.titulo.lower()} registrados)")
            return
        columnas = [self.entidad.pk] + [c.nombre for c in self.entidad.campos]
        anchos = {
            col: max(len(col), *(len(self._texto(r.get(col))) for r in registros))
            for col in columnas
        }
        encabezado = " | ".join(col.ljust(anchos[col]) for col in columnas)
        print("\n" + encabezado)
        print("-" * len(encabezado))
        for r in registros:
            print(" | ".join(self._texto(r.get(col)).ljust(anchos[col]) for col in columnas))
        print(f"\nTotal: {len(registros)}")

    def mostrar_detalle(self, registro):
        print(f"\n--- Detalle de {self.entidad.singular} ---")
        print(f"{self.entidad.pk}: {registro.get(self.entidad.pk)}")
        for c in self.entidad.campos:
            print(f"{c.etiqueta}: {self._texto(registro.get(c.nombre)) or '-'}")

    # ------------------------------------------------------------- pedir
    def pedir_id(self, accion):
        return input(f"ID del {self.entidad.singular} a {accion}: ").strip()

    def pedir_datos(self, actuales=None):
        """Devuelve un dict {campo: texto_escrito}. En edición, Enter conserva el valor actual."""
        if actuales:
            print("(Enter = conservar el valor actual)")
        datos = {}
        for c in self.entidad.campos:
            marca = "*" if c.requerido else ""
            actual = actuales.get(c.nombre) if actuales else None
            sufijo = f" [{actual}]" if actual not in (None, "") else ""
            datos[c.nombre] = input(f"{c.etiqueta}{marca}{sufijo}: ").strip()
        return datos

    def confirmar(self, pregunta):
        return input(f"{pregunta} (s/n): ").strip().lower() == "s"

    # ---------------------------------------------------------- mensajes
    def mostrar_mensaje(self, texto):
        print(f"\n[OK] {texto}")

    def mostrar_error(self, texto):
        print(f"\n[ERROR] {texto}")

    def mostrar_errores(self, errores):
        """errores: dict {etiqueta_del_campo: mensaje}"""
        print("\n[ERROR] Revisa los siguientes campos:")
        for campo, mensaje in errores.items():
            print(f"  - {campo}: {mensaje}")

    @staticmethod
    def _texto(valor):
        return "" if valor is None else str(valor)


class VistaPrincipal:
    """Menú principal que enlaza los módulos."""

    def __init__(self, titulo, opciones):
        self.titulo = titulo
        self.opciones = opciones  # lista de (numero, texto)

    def menu(self):
        print(f"\n########## {self.titulo} ##########")
        for numero, texto in self.opciones:
            print(f"{numero}. {texto}")
        print("0. Salir")
        return input("Opción: ").strip()

    def mostrar_error(self, texto):
        print(f"\n[ERROR] {texto}")

    def despedir(self):
        print("\nHasta luego.")
