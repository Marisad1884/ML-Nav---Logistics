# YARD CONSOLE · Integradora

Registro de repartidores del almacén: cajón, paquetes, horario y estatus, con panel para el supervisor.

## Ejecutar
    python gui.py      # interfaz gráfica (Tkinter, tema oscuro)
    python main.py     # versión de consola original

Requiere Python 3.8+ con Tkinter (incluido en Windows/macOS; en Linux: `sudo apt install python3-tk`).

## Publicar en GitHub Pages
GitHub Pages no ejecuta Python ni Tkinter. Para usar la aplicación desde el navegador, abre `index.html` localmente o publica la carpeta del proyecto con GitHub Pages (Settings → Pages → Deploy from a branch, selecciona la rama y la carpeta raíz). Esta versión web funciona sin servidor y guarda sus cambios en el almacenamiento local del navegador; esos datos no se comparten entre dispositivos ni se sincronizan con `datos.json`.

## Estatus automático
Se calcula según el horario del cajón (estado.py), no se guarda:
- activo: hora actual entre inicio (incluido) y fin (excluido). Ej. 13:00–17:00 -> activo a las 13:00, deja de estarlo a las 17:00
- por iniciar / finalizado: antes del inicio / desde el fin
- sin cajón: sin cajón asignado
- deshabilitado: cuenta bloqueada manualmente por el supervisor (campo `estatus` del usuario)

## Archivos
- esquema.py · tablas, campos y validaciones
- modelos.py · modelo en memoria (reemplazable por SQL)
- controladores.py · flujo y validación
- vistas.py · vista de consola
- gui.py · vista gráfica + panel supervisor
- index.html · versión web estática para navegador y GitHub Pages
- estado.py · lógica del estatus por horario
- persistencia.py · guarda los datos en `datos.json`
