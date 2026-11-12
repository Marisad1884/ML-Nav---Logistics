"""
gui.py  (VIEW gráfica - Tkinter)
YARD CONSOLE · Control de repartidores del almacén

Ejecutar:  python gui.py

Tema oscuro con animaciones (contadores, transición entre pantallas, indicador
"en vivo"). El estatus del repartidor se calcula SOLO según el horario de su
cajón (ver estado.py); la cuenta además puede bloquearse manualmente.
Reutiliza esquema, modelos y validaciones de los controladores existentes.
"""
import math
import tkinter as tk
from datetime import datetime
from tkinter import ttk, messagebox

import estado as est
import persistencia
from esquema import ESQUEMAS, ESTATUS_VALIDOS, ROLES_VALIDOS
from modelos import ModeloMemoria, ModeloError
from controladores import CONTROLADORES

# ------------------------------------------------------------------ estilo
FONDO = "#0A0E1A"      # fondo general
PANEL = "#111827"      # paneles / tablas
PANEL2 = "#1A2338"     # elementos elevados
BORDE = "#27324D"
TEXTO = "#E7ECF6"
MUTED = "#8793AE"
ACENTO = "#22D3EE"     # cian
ACENTO2 = "#8B5CF6"    # violeta
VERDE = "#34D399"
AMBAR = "#FBBF24"
ROJO = "#F43F5E"
GRIS_AZUL = "#7C89A6"
SELEC = "#1D2B4F"
FUENTE = "Segoe UI"

COLOR_ESTADO = {
    est.ACTIVO: VERDE, est.POR_INICIAR: AMBAR, est.FINALIZADO: GRIS_AZUL,
    est.DESHABILITADO: ROJO, est.SIN_CAJON: MUTED,
}
DIAS = ("lunes", "martes", "miércoles", "jueves", "viernes", "sábado", "domingo")


def mezclar(c1, c2, t):
    """Mezcla dos colores #RRGGBB (t=0 -> c1, t=1 -> c2)."""
    a = [int(c1[i:i + 2], 16) for i in (1, 3, 5)]
    b = [int(c2[i:i + 2], 16) for i in (1, 3, 5)]
    return "#%02x%02x%02x" % tuple(round(x + (y - x) * t) for x, y in zip(a, b))


def nombre_completo(u):
    return " ".join(p for p in (u.get("nombres"), u.get("apellido1"), u.get("apellido2")) if p)


def hhmm(valor):
    return str(valor)[:5] if valor else "—"


def barra_texto(p, n=8):
    llenos = round(p * n)
    return "█" * llenos + "░" * (n - llenos) + f" {int(p * 100):>3d}%"


# ------------------------------------------------------------------ modelos
def construir_modelos():
    usuarios = ModeloMemoria("id_usuario")
    vehiculos = ModeloMemoria("id_vehiculo", {"id_usuario_fk": usuarios})
    cajones = ModeloMemoria("id_cajon", {"id_vehiculo_fk": vehiculos})
    roles = ModeloMemoria("id_rol", {"id_usuario_fk": usuarios})
    contactos = ModeloMemoria("id_contacto", {"id_usuario_fk": usuarios})
    return {
        "usuarios": usuarios, "vehiculos": vehiculos, "cajones": cajones,
        "roles": roles, "contactos": contactos,
    }


def datos_demo(m):
    """Datos de ejemplo para que la pantalla no arranque vacía."""
    gente = [
        ("Carlos", "Ramírez", "López", "habilitado", "conductor"),
        ("María", "González", "Soto", "habilitado", "conductor"),
        ("Luis", "Hernández", None, "deshabilitado", "conductor"),
        ("Ana", "Martínez", "Ruiz", "habilitado", "conductor"),
        ("Jorge", "Torres", "Vega", "habilitado", "conductor"),
        ("Patricia", "Flores", "Díaz", "habilitado", "supervisor"),
    ]
    correos = ["carlos", "maria", "luis", "ana", "jorge", "patricia"]
    for i, (n, a1, a2, e, rol) in enumerate(gente, start=1):
        m["usuarios"].crear({"nombres": n, "apellido1": a1, "apellido2": a2, "estatus": e})
        m["roles"].crear({"rol": rol, "rol_descripcion": None, "id_usuario_fk": i})
        m["contactos"].crear({"telefono": f"618555010{i}", "email": f"{correos[i - 1]}@almacen.mx",
                              "id_usuario_fk": i})
    autos = [("NP300", "Nissan", "DGO-101-A", 1), ("Kangoo", "Renault", "DGO-202-B", 2),
             ("Transit", "Ford", "DGO-303-C", 3), ("Hilux", "Toyota", "DGO-404-D", 4),
             ("Sprinter", "Mercedes", "DGO-505-E", 5)]
    for modelo, marca, mat, uid in autos:
        m["vehiculos"].crear({"modelo": modelo, "marca": marca, "matricula": mat,
                              "descripcion_vehiculo": "Unidad de reparto", "id_usuario_fk": uid})
    cajones = [("Cajón A1", "06:00", "14:00", 124), ("Cajón A2", "08:00", "16:00", 98),
               ("Cajón B1", "12:00", "20:00", 0), ("Cajón B2", "14:00", "22:00", 143),
               ("Cajón C1", "18:00", "23:00", 87)]
    for i, (nom, ini, fin, paq) in enumerate(cajones, start=1):
        m["cajones"].crear({"nombre": nom, "hora_apertura": ini + ":00", "hora_cierre": fin + ":00",
                            "paquetes": paq, "id_vehiculo_fk": i})


class _VistaNula:
    """Los controladores piden una vista; aquí solo usamos su validación."""


# ------------------------------------------------------------------ widgets base
class Boton(tk.Label):
    ESTILOS = {"primario": (ACENTO, FONDO), "secundario": (PANEL2, TEXTO),
               "peligro": (ROJO, "#FFFFFF"), "exito": (VERDE, FONDO)}

    def __init__(self, master, texto, comando, estilo="primario", **kw):
        bg, fg = self.ESTILOS[estilo]
        super().__init__(master, text=texto, bg=bg, fg=fg, font=(FUENTE, 10, "bold"),
                         padx=16, pady=8, cursor="hand2", **kw)
        self._bg, self._hover = bg, mezclar(bg, "#FFFFFF", 0.2)
        self.bind("<Enter>", lambda _e: self.config(bg=self._hover))
        self.bind("<Leave>", lambda _e: self.config(bg=self._bg))
        self.bind("<ButtonRelease-1>", lambda e: comando() if 0 <= e.x < self.winfo_width()
                  and 0 <= e.y < self.winfo_height() else None)


def entrada(master, var, ancho=30):
    return tk.Entry(master, textvariable=var, font=(FUENTE, 10), width=ancho, bg=PANEL2, fg=TEXTO,
                    insertbackground=ACENTO, relief="flat", highlightthickness=1,
                    highlightbackground=BORDE, highlightcolor=ACENTO)


class Franja(tk.Canvas):
    """Línea fina con degradado cian -> violeta."""

    def __init__(self, master, alto=3):
        super().__init__(master, height=alto, bg=FONDO, highlightthickness=0, bd=0)
        self.bind("<Configure>", self._dibujar)

    def _dibujar(self, _e=None):
        self.delete("all")
        w, h, n = self.winfo_width(), int(self["height"]), 160
        for i in range(n):
            self.create_rectangle(w * i / n, 0, w * (i + 1) / n + 1, h,
                                  fill=mezclar(ACENTO, ACENTO2, i / (n - 1)), width=0)


def tabla(master, columnas, anchos=None):
    """columnas: lista de (clave, encabezado). Devuelve (frame, treeview)."""
    marco = tk.Frame(master, bg=PANEL, highlightbackground=BORDE, highlightthickness=1)
    tv = ttk.Treeview(marco, columns=[c for c, _ in columnas], show="headings", selectmode="browse")
    for clave, enc in columnas:
        tv.heading(clave, text=enc.upper(), anchor="w")
        tv.column(clave, width=(anchos or {}).get(clave, 120), anchor="w", minwidth=40)
    sy = ttk.Scrollbar(marco, orient="vertical", command=tv.yview)
    sx = ttk.Scrollbar(marco, orient="horizontal", command=tv.xview)
    tv.configure(yscrollcommand=sy.set, xscrollcommand=sx.set)
    tv.grid(row=0, column=0, sticky="nsew")
    sy.grid(row=0, column=1, sticky="ns")
    sx.grid(row=1, column=0, sticky="ew")
    marco.rowconfigure(0, weight=1)
    marco.columnconfigure(0, weight=1)
    tv.tag_configure("par", background=mezclar(PANEL, PANEL2, 0.55))
    for clave, color in COLOR_ESTADO.items():
        tv.tag_configure(clave, foreground=color)
    tv.tag_configure("habilitado", foreground=VERDE)
    return marco, tv


def titulo_pagina(master, titulo, subtitulo):
    caja = tk.Frame(master, bg=FONDO)
    tk.Label(caja, text=titulo, font=(FUENTE, 22, "bold"), bg=FONDO, fg=TEXTO).pack(anchor="w")
    tk.Label(caja, text=subtitulo, font=(FUENTE, 10), bg=FONDO, fg=MUTED).pack(anchor="w")
    return caja


# ------------------------------------------------------------------ tarjeta animada
class Tarjeta(tk.Frame):
    def __init__(self, master, titulo, color):
        super().__init__(master, bg=PANEL, highlightbackground=BORDE, highlightthickness=1)
        tk.Frame(self, bg=color, width=4).pack(side="left", fill="y")
        cuerpo = tk.Frame(self, bg=PANEL)
        cuerpo.pack(side="left", fill="both", expand=True, padx=16, pady=12)
        self.lbl = tk.Label(cuerpo, text="0", font=(FUENTE, 28, "bold"), bg=PANEL, fg=color)
        self.lbl.pack(anchor="w")
        tk.Label(cuerpo, text=titulo.upper(), font=(FUENTE, 8, "bold"), bg=PANEL, fg=MUTED).pack(anchor="w")
        self._objetivo, self._mostrado, self._job = None, 0, None

    def reiniciar(self):
        self._objetivo, self._mostrado = None, 0
        self.lbl.config(text="0")

    def set(self, valor):
        if valor == self._objetivo:
            return
        self._objetivo = valor
        desde = self._mostrado
        if self._job:
            self.after_cancel(self._job)

        def paso(i):
            t = i / 20
            self._mostrado = round(desde + (valor - desde) * (1 - (1 - t) ** 3))
            self.lbl.config(text=str(self._mostrado))
            if i < 20:
                self._job = self.after(28, lambda: paso(i + 1))
        paso(1)


# ------------------------------------------------------------------ detalle
class Detalle(tk.Toplevel):
    def __init__(self, master, f):
        super().__init__(master)
        self.title("Detalle del repartidor")
        self.configure(bg=PANEL)
        self.resizable(False, False)
        self.transient(master.winfo_toplevel())
        Franja(self).pack(fill="x")
        tk.Label(self, text=f["nombre"], font=(FUENTE, 16, "bold"), bg=PANEL, fg=TEXTO).pack(anchor="w", padx=26, pady=(18, 4))
        color = COLOR_ESTADO[f["estado"]]
        tk.Label(self, text="●  " + est.ETIQUETAS[f["estado"]], font=(FUENTE, 9, "bold"), fg=color,
                 bg=mezclar(PANEL, color, 0.18), padx=10, pady=3).pack(anchor="w", padx=26)

        cuerpo = tk.Frame(self, bg=PANEL)
        cuerpo.pack(padx=26, pady=14, anchor="w")
        for i, (k, v) in enumerate((("ID", f["uid"]), ("Vehículo", f["vehiculo"]), ("Cajón", f["cajon"]),
                                    ("Horario", f["horario"]), ("Paquetes", f["paquetes"]), ("Teléfono", f["tel"]))):
            tk.Label(cuerpo, text=k.upper(), font=(FUENTE, 8, "bold"), bg=PANEL, fg=MUTED).grid(row=i, column=0, sticky="w", pady=4)
            tk.Label(cuerpo, text=str(v), font=(FUENTE, 10), bg=PANEL, fg=TEXTO).grid(row=i, column=1, sticky="w", padx=18)

        tk.Label(self, text="AVANCE DEL TURNO", font=(FUENTE, 8, "bold"), bg=PANEL, fg=MUTED).pack(anchor="w", padx=26)
        self.cv = tk.Canvas(self, width=340, height=14, bg=PANEL, highlightthickness=0)
        self.cv.pack(padx=26, pady=(4, 0), anchor="w")
        self.cv.create_rectangle(0, 3, 340, 11, fill=PANEL2, width=0)
        self.relleno = self.cv.create_rectangle(0, 3, 0, 11, fill=color, width=0)
        self.pct = tk.Label(self, text="", font=(FUENTE, 9), bg=PANEL, fg=MUTED)
        self.pct.pack(anchor="w", padx=26)
        self._animar(f["progreso"] if f["progreso"] is not None else 0.0, color)

        Boton(self, "Cerrar", self.destroy, "secundario").pack(pady=18)

    def _animar(self, objetivo, color, i=0):
        t = min(1.0, i / 25)
        p = objetivo * (1 - (1 - t) ** 3)
        self.cv.coords(self.relleno, 0, 3, 340 * p, 11)
        self.pct.config(text=f"{int(p * 100)} %")
        if i < 25:
            self.after(18, lambda: self._animar(objetivo, color, i + 1))


# ------------------------------------------------------------------ panel supervisor
class PanelSupervisor(tk.Frame):
    ORDEN_FILTRO = (("Todos", None), ("Activo", est.ACTIVO), ("Por iniciar", est.POR_INICIAR),
                    ("Finalizado", est.FINALIZADO), ("Deshabilitado", est.DESHABILITADO),
                    ("Sin cajón", est.SIN_CAJON))

    def __init__(self, master, app):
        super().__init__(master, bg=FONDO)
        self.app = app
        self.m = app.modelos
        self._filas = {}

        cab = tk.Frame(self, bg=FONDO)
        cab.pack(fill="x", padx=28, pady=(22, 10))
        titulo_pagina(cab, "Panel del supervisor",
                      "Estatus automático según el horario de cada cajón").pack(side="left")
        self.lbl_act = tk.Label(cab, text="", font=(FUENTE, 9), bg=FONDO, fg=MUTED)
        self.lbl_act.pack(side="right", anchor="s")

        fila = tk.Frame(self, bg=FONDO)
        fila.pack(fill="x", padx=22)
        self.cards = {}
        for clave, titulo, color in (("total", "Repartidores", ACENTO), ("act", "Activos ahora", VERDE),
                                     ("fuera", "Fuera de turno", AMBAR), ("des", "Deshabilitados", ROJO),
                                     ("paq", "Paquetes totales", ACENTO2)):
            c = Tarjeta(fila, titulo, color)
            c.pack(side="left", expand=True, fill="x", padx=6)
            self.cards[clave] = c

        barra = tk.Frame(self, bg=FONDO)
        barra.pack(fill="x", padx=28, pady=(16, 8))
        tk.Label(barra, text="BUSCAR", font=(FUENTE, 8, "bold"), bg=FONDO, fg=MUTED).pack(side="left")
        self.busqueda = tk.StringVar()
        self.busqueda.trace_add("write", lambda *_: self.refrescar())
        entrada(barra, self.busqueda, 26).pack(side="left", padx=(8, 18), ipady=4)
        tk.Label(barra, text="ESTADO", font=(FUENTE, 8, "bold"), bg=FONDO, fg=MUTED).pack(side="left")
        self.filtro = tk.StringVar(value="Todos")
        cb = ttk.Combobox(barra, textvariable=self.filtro, values=[n for n, _ in self.ORDEN_FILTRO],
                          state="readonly", width=15)
        cb.pack(side="left", padx=8)
        cb.bind("<<ComboboxSelected>>", lambda _e: self.refrescar())
        Boton(barra, "Bloquear / Habilitar cuenta", self.alternar_cuenta, "secundario").pack(side="right")
        Boton(barra, "Ver detalle", self.detalle).pack(side="right", padx=8)

        cols = [("id", "ID"), ("nombre", "Repartidor"), ("estado", "Estado"), ("vehiculo", "Vehículo"),
                ("cajon", "Cajón"), ("horario", "Horario"), ("turno", "Avance del turno"),
                ("paquetes", "Paquetes"), ("tel", "Teléfono")]
        marco, self.tv = tabla(self, cols, {"id": 36, "nombre": 150, "estado": 140, "vehiculo": 150, "cajon": 80,
                                            "horario": 105, "turno": 150, "paquetes": 80, "tel": 100})
        marco.pack(fill="both", expand=True, padx=28, pady=(0, 22))
        self.tv.bind("<Double-1>", lambda _e: self.detalle())

    def al_mostrar(self):
        for c in self.cards.values():
            c.reiniciar()

    # ---- datos
    def construir_filas(self):
        ahora = datetime.now()
        us, vs, cs = self.m["usuarios"].listar(), self.m["vehiculos"].listar(), self.m["cajones"].listar()
        roles, contactos = self.m["roles"].listar(), self.m["contactos"].listar()

        def con_rol(r):
            return {x["id_usuario_fk"] for x in roles if x["rol"] == r}
        supervisores, conductores = con_rol("supervisor"), con_rol("conductor")
        filas, estados_usuario = [], {}
        for u in us:
            uid = u["id_usuario"]
            if uid in supervisores and uid not in conductores:
                continue
            habil = (u.get("estatus") or "habilitado") == "habilitado"
            tel = next((c["telefono"] for c in contactos if c["id_usuario_fk"] == uid), "—")
            base = {"uid": uid, "nombre": nombre_completo(u), "tel": tel, "habil": habil}
            propias, turnos = [], []
            for v in (v for v in vs if v["id_usuario_fk"] == uid):
                veh = f'{v["marca"]} {v["modelo"]} ({v["matricula"]})'
                cajs = [c for c in cs if c["id_vehiculo_fk"] == v["id_vehiculo"]]
                for c in cajs:
                    e = est.estado_turno(c["hora_apertura"], c["hora_cierre"], ahora)
                    turnos.append(e)
                    propias.append({**base, "vehiculo": veh, "cajon": c["nombre"], "estado": e,
                                    "horario": f'{hhmm(c["hora_apertura"])} – {hhmm(c["hora_cierre"])}',
                                    "progreso": est.progreso_turno(c["hora_apertura"], c["hora_cierre"], ahora),
                                    "paquetes": c.get("paquetes") or 0})
                if not cajs:
                    propias.append({**base, "vehiculo": veh, "cajon": "—", "estado": est.SIN_CAJON,
                                    "horario": "—", "progreso": None, "paquetes": 0})
            if not propias:
                propias.append({**base, "vehiculo": "—", "cajon": "—", "estado": est.SIN_CAJON,
                                "horario": "—", "progreso": None, "paquetes": 0})
            glob = est.estado_repartidor(habil, turnos)
            if not habil:   # cuenta bloqueada: todas sus filas aparecen deshabilitadas
                for p in propias:
                    p["estado"] = est.DESHABILITADO
            estados_usuario[uid] = glob
            filas.extend(propias)
        return filas, estados_usuario

    def refrescar(self):
        filas, por_usuario = self.construir_filas()
        vals = list(por_usuario.values())
        self.cards["total"].set(len(vals))
        self.cards["act"].set(vals.count(est.ACTIVO))
        self.cards["fuera"].set(sum(v in (est.POR_INICIAR, est.FINALIZADO, est.SIN_CAJON) for v in vals))
        self.cards["des"].set(vals.count(est.DESHABILITADO))
        self.cards["paq"].set(sum(f["paquetes"] for f in filas))
        self.lbl_act.config(text="Actualizado " + datetime.now().strftime("%H:%M:%S"))

        previo = None
        sel = self.tv.selection()
        if sel and sel[0] in self._filas:
            previo = (self._filas[sel[0]]["uid"], self._filas[sel[0]]["cajon"])
        q = self.busqueda.get().strip().lower()
        objetivo = dict(self.ORDEN_FILTRO)[self.filtro.get()]
        self.tv.delete(*self.tv.get_children())
        self._filas = {}
        n = 0
        for f in filas:
            if objetivo and f["estado"] != objetivo:
                continue
            if q and q not in " ".join(str(f[k]) for k in ("nombre", "vehiculo", "cajon", "tel")).lower():
                continue
            iid = f"f{n}"
            self._filas[iid] = f
            tags = (f["estado"], "par") if n % 2 else (f["estado"],)
            turno = barra_texto(f["progreso"]) if f["progreso"] is not None and f["estado"] != est.DESHABILITADO else "—"
            self.tv.insert("", "end", iid=iid, tags=tags, values=(
                f["uid"], f["nombre"], "●  " + est.ETIQUETAS[f["estado"]], f["vehiculo"], f["cajon"],
                f["horario"], turno, f["paquetes"], f["tel"]))
            if previo == (f["uid"], f["cajon"]):
                self.tv.selection_set(iid)
            n += 1

    # ---- acciones
    def _seleccion(self):
        sel = self.tv.selection()
        if not sel:
            messagebox.showinfo("Selecciona", "Selecciona un repartidor de la tabla.", parent=self)
            return None
        return self._filas[sel[0]]

    def alternar_cuenta(self):
        f = self._seleccion()
        if not f:
            return
        nuevo = "deshabilitado" if f["habil"] else "habilitado"
        accion = "BLOQUEAR" if f["habil"] else "HABILITAR"
        if not messagebox.askyesno("Cuenta", f'¿{accion} la cuenta de {f["nombre"]}?\n\n'
                                   "Una cuenta bloqueada aparece deshabilitada sin importar su horario.", parent=self):
            return
        try:
            self.m["usuarios"].actualizar(f["uid"], {"estatus": nuevo})
        except ModeloError as e:
            return messagebox.showerror("Error", str(e), parent=self)
        self.app.guardar()
        self.refrescar()

    def detalle(self):
        f = self._seleccion()
        if f:
            Detalle(self, f)


# ------------------------------------------------------------------ formulario
class Formulario(tk.Toplevel):
    def __init__(self, crud, registro=None):
        super().__init__(crud)
        self.crud = crud
        self.registro = registro
        self.entidad = crud.entidad
        accion = "Editar " if registro else "Nuevo "
        self.title(accion + self.entidad.singular)
        self.configure(bg=PANEL)
        self.resizable(False, False)
        self.transient(crud.winfo_toplevel())
        self.grab_set()

        Franja(self).pack(fill="x")
        tk.Label(self, text=accion + self.entidad.singular, font=(FUENTE, 15, "bold"),
                 bg=PANEL, fg=TEXTO).pack(anchor="w", padx=26, pady=(16, 0))
        cuerpo = tk.Frame(self, bg=PANEL)
        cuerpo.pack(padx=26, pady=14)
        self.vars = {}
        for i, c in enumerate(self.entidad.campos):
            tk.Label(cuerpo, text=(c.etiqueta + (" *" if c.requerido else "")), font=(FUENTE, 9),
                     bg=PANEL, fg=MUTED).grid(row=i, column=0, sticky="e", pady=6, padx=(0, 12))
            var = tk.StringVar()
            valores = self._opciones(c)
            if valores is not None:
                w = ttk.Combobox(cuerpo, textvariable=var, values=valores, state="readonly", width=34)
            else:
                w = entrada(cuerpo, var, 37)
            w.grid(row=i, column=1, pady=6, ipady=3 if valores is None else 0)
            actual = registro.get(c.nombre) if registro else None
            if actual not in (None, ""):
                var.set(self._mostrar_valor(c, actual, valores))
            elif valores and c.nombre == "estatus":
                var.set("habilitado")
            self.vars[c.nombre] = var

        pie = tk.Frame(self, bg=PANEL)
        pie.pack(pady=(0, 18))
        Boton(pie, "Guardar", self.guardar, "exito").pack(side="left", padx=6)
        Boton(pie, "Cancelar", self.destroy, "secundario").pack(side="left", padx=6)
        self.bind("<Escape>", lambda _e: self.destroy())

    def _opciones(self, campo):
        if campo.nombre == "estatus":
            return list(ESTATUS_VALIDOS)
        if campo.nombre == "rol":
            return list(ROLES_VALIDOS)
        if campo.nombre.endswith("_fk"):
            return ([""] if not campo.requerido else []) + self.crud.app.opciones_fk(campo.nombre)
        return None

    def _mostrar_valor(self, campo, valor, valores):
        if campo.nombre.endswith("_fk") and valores:
            return next((o for o in valores if o.split(" - ")[0] == str(valor)), str(valor))
        return str(valor)

    def guardar(self):
        datos = {}
        for k, v in self.vars.items():
            texto = v.get().strip()
            datos[k] = texto.split(" - ")[0] if k.endswith("_fk") else texto
        limpios, errores = self.crud.ctrl._validar(datos)
        if errores:
            msg = "\n".join(f"• {c}: {e}" for c, e in errores.items())
            return messagebox.showwarning("Revisa los campos", msg, parent=self)
        try:
            if self.registro:
                self.crud.modelo.actualizar(self.registro[self.entidad.pk], limpios)
            else:
                self.crud.modelo.crear(limpios)
        except ModeloError as e:
            return messagebox.showerror("Error", str(e), parent=self)
        self.crud.app.guardar()
        self.crud.refrescar()
        self.destroy()


# ------------------------------------------------------------------ CRUD genérico
class CrudFrame(tk.Frame):
    def __init__(self, master, app, clave):
        super().__init__(master, bg=FONDO)
        self.app = app
        self.entidad = ESQUEMAS[clave]
        self.modelo = app.modelos[clave]
        self.ctrl = CONTROLADORES[clave](self.entidad, self.modelo, _VistaNula())

        cab = tk.Frame(self, bg=FONDO)
        cab.pack(fill="x", padx=28, pady=(22, 12))
        titulo_pagina(cab, self.entidad.titulo, f"Administración de {self.entidad.titulo.lower()}").pack(side="left")
        barra = tk.Frame(cab, bg=FONDO)
        barra.pack(side="right", anchor="s")
        Boton(barra, "+ Nuevo", self.nuevo).pack(side="left")
        Boton(barra, "Editar", self.editar, "secundario").pack(side="left", padx=8)
        Boton(barra, "Eliminar", self.eliminar, "peligro").pack(side="left")

        cols = [(self.entidad.pk, "ID")] + [(c.nombre, c.etiqueta.split(" (")[0]) for c in self.entidad.campos]
        marco, self.tv = tabla(self, cols, {self.entidad.pk: 60})
        marco.pack(fill="both", expand=True, padx=28, pady=(0, 22))
        self.tv.bind("<Double-1>", lambda _e: self.editar())

    def refrescar(self):
        self.tv.delete(*self.tv.get_children())
        cols = [self.entidad.pk] + [c.nombre for c in self.entidad.campos]
        for i, r in enumerate(self.modelo.listar()):
            vals = []
            for c in cols:
                v = r.get(c)
                vals.append(hhmm(v) if c.startswith("hora_") else ("" if v is None else v))
            e = r.get("estatus")
            tags = ((e,) if e in ESTATUS_VALIDOS else ()) + (("par",) if i % 2 else ())
            self.tv.insert("", "end", iid=str(r[self.entidad.pk]), values=vals, tags=tags)

    def _id_sel(self):
        sel = self.tv.selection()
        if not sel:
            messagebox.showinfo("Selecciona", f"Selecciona un {self.entidad.singular} de la tabla.", parent=self)
            return None
        return int(sel[0])

    def nuevo(self):
        Formulario(self)

    def editar(self):
        id_ = self._id_sel()
        if id_ is None:
            return
        reg = self.modelo.obtener(id_)
        if reg:
            Formulario(self, reg)

    def eliminar(self):
        id_ = self._id_sel()
        if id_ is None:
            return
        if not messagebox.askyesno("Eliminar", f"¿Eliminar {self.entidad.singular} {id_}?", parent=self):
            return
        try:
            self.modelo.eliminar(id_)
        except ModeloError as e:
            return messagebox.showerror("Error", str(e), parent=self)
        self.app.guardar()
        self.refrescar()


# ------------------------------------------------------------------ menú lateral
class ItemMenu(tk.Frame):
    def __init__(self, master, icono, texto, comando):
        super().__init__(master, bg=PANEL, cursor="hand2")
        self.barra = tk.Frame(self, bg=PANEL, width=4)
        self.barra.pack(side="left", fill="y")
        self.ico = tk.Label(self, text=icono, font=(FUENTE, 12), bg=PANEL, fg=MUTED, width=3, pady=11)
        self.ico.pack(side="left")
        self.txt = tk.Label(self, text=texto, font=(FUENTE, 11), bg=PANEL, fg=TEXTO, anchor="w")
        self.txt.pack(side="left", fill="x", expand=True)
        self.activo = False
        for w in (self, self.ico, self.txt):
            w.bind("<Enter>", lambda _e: self._pintar(True))
            w.bind("<Leave>", lambda _e: self._pintar(False))
            w.bind("<Button-1>", lambda _e: comando())

    def _pintar(self, hover):
        bg = PANEL2 if (self.activo or hover) else PANEL
        for w in (self, self.ico, self.txt):
            w.config(bg=bg)
        self.barra.config(bg=ACENTO if self.activo else bg)
        self.ico.config(fg=ACENTO if self.activo else MUTED)
        self.txt.config(fg=TEXTO if (self.activo or hover) else "#B6C0D6")

    def activar(self, valor):
        self.activo = valor
        self._pintar(False)


# ------------------------------------------------------------------ aplicación
class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("YARD CONSOLE · Control de repartidores")
        self.geometry("1280x760")
        self.minsize(1100, 640)
        self.configure(bg=FONDO)

        self.modelos = construir_modelos()
        if not persistencia.cargar(self.modelos):
            datos_demo(self.modelos)
            persistencia.guardar(self.modelos)

        self._estilo()
        self._encabezado()
        Franja(self).pack(fill="x")
        cuerpo = tk.Frame(self, bg=FONDO)
        cuerpo.pack(fill="both", expand=True)

        menu = tk.Frame(cuerpo, bg=PANEL, width=220)
        menu.pack(side="left", fill="y")
        menu.pack_propagate(False)
        tk.Frame(cuerpo, bg=BORDE, width=1).pack(side="left", fill="y")
        self.contenido = tk.Frame(cuerpo, bg=FONDO)
        self.contenido.pack(side="right", fill="both", expand=True)

        self.paginas = {"supervisor": PanelSupervisor(self.contenido, self)}
        for clave in ESQUEMAS:
            self.paginas[clave] = CrudFrame(self.contenido, self, clave)

        iconos = {"supervisor": "📊", "usuarios": "👤", "vehiculos": "🚚", "cajones": "📦",
                  "roles": "🛡", "contactos": "📞"}
        tk.Label(menu, text="NAVEGACIÓN", font=(FUENTE, 8, "bold"), bg=PANEL, fg=MUTED).pack(anchor="w", padx=22, pady=(22, 8))
        self.items = {}
        nombres = [("supervisor", "Panel supervisor")] + [(k, ESQUEMAS[k].titulo) for k in ESQUEMAS]
        for clave, texto in nombres:
            it = ItemMenu(menu, iconos[clave], texto, lambda c=clave: self.mostrar(c))
            it.pack(fill="x")
            self.items[clave] = it

        self.actual, self._anim, self._n = None, None, 0
        self.mostrar("supervisor")
        self._pulso(0)
        self._tick()

    # ---- estilo ttk
    def _estilo(self):
        s = ttk.Style(self)
        s.theme_use("clam")
        s.configure("Treeview", rowheight=34, font=(FUENTE, 10), background=PANEL, fieldbackground=PANEL,
                    foreground=TEXTO, borderwidth=0, relief="flat", bordercolor=PANEL,
                    lightcolor=PANEL, darkcolor=PANEL)
        s.configure("Treeview.Heading", font=(FUENTE, 8, "bold"), background=PANEL2, foreground=ACENTO,
                    relief="flat", padding=(8, 10), borderwidth=0)
        s.map("Treeview.Heading", background=[("active", BORDE)])
        s.map("Treeview", background=[("selected", SELEC)])
        for o in ("Vertical", "Horizontal"):
            s.configure(f"{o}.TScrollbar", background=BORDE, troughcolor=PANEL, bordercolor=PANEL,
                        arrowcolor=MUTED, lightcolor=BORDE, darkcolor=BORDE, relief="flat")
            s.map(f"{o}.TScrollbar", background=[("active", MUTED)])
        s.configure("TCombobox", fieldbackground=PANEL2, background=BORDE, foreground=TEXTO,
                    arrowcolor=ACENTO, bordercolor=BORDE, lightcolor=PANEL2, darkcolor=PANEL2,
                    selectbackground=PANEL2, selectforeground=TEXTO, padding=4)
        s.map("TCombobox", fieldbackground=[("readonly", PANEL2)], foreground=[("readonly", TEXTO)],
              selectbackground=[("readonly", PANEL2)], selectforeground=[("readonly", TEXTO)])
        self.option_add("*TCombobox*Listbox.background", PANEL2)
        self.option_add("*TCombobox*Listbox.foreground", TEXTO)
        self.option_add("*TCombobox*Listbox.selectBackground", ACENTO)
        self.option_add("*TCombobox*Listbox.selectForeground", FONDO)
        self.option_add("*TCombobox*Listbox.font", (FUENTE, 10))

    # ---- encabezado
    def _encabezado(self):
        top = tk.Frame(self, bg=FONDO, height=70)
        top.pack(fill="x")
        top.pack_propagate(False)
        logo = tk.Canvas(top, width=46, height=46, bg=FONDO, highlightthickness=0)
        logo.pack(side="left", padx=(24, 12), pady=12)
        pts = [(23 + 21 * math.cos(math.radians(60 * i - 90)), 23 + 21 * math.sin(math.radians(60 * i - 90)))
               for i in range(6)]
        logo.create_polygon(pts, fill=PANEL2, outline=ACENTO, width=2)
        logo.create_text(23, 23, text="YC", fill=ACENTO, font=(FUENTE, 11, "bold"))
        tit = tk.Frame(top, bg=FONDO)
        tit.pack(side="left")
        tk.Label(tit, text="YARD CONSOLE", font=(FUENTE, 17, "bold"), bg=FONDO, fg=TEXTO).pack(anchor="w")
        tk.Label(tit, text="Control de almacén y repartidores", font=(FUENTE, 9), bg=FONDO, fg=MUTED).pack(anchor="w")

        der = tk.Frame(top, bg=FONDO)
        der.pack(side="right", padx=26)
        fila = tk.Frame(der, bg=FONDO)
        fila.pack(anchor="e")
        self.punto = tk.Label(fila, text="●", font=(FUENTE, 10), bg=FONDO, fg=VERDE)
        self.punto.pack(side="left")
        tk.Label(fila, text=" EN VIVO   ", font=(FUENTE, 8, "bold"), bg=FONDO, fg=MUTED).pack(side="left")
        self.reloj = tk.Label(fila, text="", font=(FUENTE, 17, "bold"), bg=FONDO, fg=ACENTO)
        self.reloj.pack(side="left")
        self.fecha = tk.Label(der, text="", font=(FUENTE, 9), bg=FONDO, fg=MUTED)
        self.fecha.pack(anchor="e")

    # ---- animaciones / reloj
    def _pulso(self, i):
        t = 0.5 + 0.5 * math.sin(i / 6)
        self.punto.config(fg=mezclar(FONDO, VERDE, 0.25 + 0.75 * t))
        self.after(50, lambda: self._pulso(i + 1))

    def _tick(self):
        ahora = datetime.now()
        self.reloj.config(text=ahora.strftime("%H:%M:%S"))
        self.fecha.config(text=f"{DIAS[ahora.weekday()]} {ahora.day:02d}/{ahora.month:02d}/{ahora.year}".capitalize())
        self._n += 1
        if self._n % 5 == 0 and self.actual == "supervisor":
            self.paginas["supervisor"].refrescar()
        self.after(1000, self._tick)

    def mostrar(self, clave):
        if self._anim:
            self.after_cancel(self._anim)
        for k, p in self.paginas.items():
            p.place_forget()
            self.items[k].activar(False)
        self.items[clave].activar(True)
        self.actual = clave
        pagina = self.paginas[clave]
        if hasattr(pagina, "al_mostrar"):
            pagina.al_mostrar()
        pagina.refrescar()
        pagina.place(x=48, y=0, relwidth=1, relheight=1)

        def paso(i):
            t = i / 12
            pagina.place_configure(x=round(48 * (1 - t) ** 3))
            if i < 12:
                self._anim = self.after(16, lambda: paso(i + 1))
        paso(1)

    def opciones_fk(self, columna):
        if columna == "id_usuario_fk":
            return [f'{u["id_usuario"]} - {nombre_completo(u)}' for u in self.modelos["usuarios"].listar()]
        if columna == "id_vehiculo_fk":
            return [f'{v["id_vehiculo"]} - {v["marca"]} {v["modelo"]} ({v["matricula"]})'
                    for v in self.modelos["vehiculos"].listar()]
        return []

    def guardar(self):
        persistencia.guardar(self.modelos)


if __name__ == "__main__":
    App().mainloop()
