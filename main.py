import flet as ft
import requests
import json
import os

# ===== ARCHIVO PARA GUARDAR DATOS =====
ARCHIVO_SESION = "sesion.json"

# ===== PALETA ROSA PASTEL =====
ROSA_FONDO = "#FFF0F5"      # fondo general (lavender blush)
ROSA_CLARO = "#FFD6E8"      # tarjetas / elementos secundarios
ROSA_PRINCIPAL = "#F8A5C2"  # botones, iconos principales
ROSA_OSCURO = "#E75480"     # texto de énfasis / hover
GRIS_TEXTO = "#5C4B51"      # texto principal, buen contraste sobre rosa pastel
BLANCO = "#FFFFFF"

def guardar_datos(token, id_usuario, rol):
    datos = {
        "token": token,
        "id": id_usuario,
        "rol": rol
    }
    with open(ARCHIVO_SESION, "w") as archivo:
        json.dump(datos, archivo)

def cargar_datos():
    if os.path.exists(ARCHIVO_SESION):
        with open(ARCHIVO_SESION, "r") as archivo:
            return json.load(archivo)
    return None

def borrar_datos():
    if os.path.exists(ARCHIVO_SESION):
        os.remove(ARCHIVO_SESION)

def main(page: ft.Page):
    page.title = "Login - Fake Store"
    page.horizontal_alignment = ft.CrossAxisAlignment.CENTER
    page.vertical_alignment = ft.MainAxisAlignment.CENTER
    page.theme_mode = ft.ThemeMode.LIGHT
    page.bgcolor = ROSA_FONDO
    page.theme = ft.Theme(color_scheme_seed=ROSA_PRINCIPAL)

    # Campos de texto
    txt_usuario = ft.TextField(
        label="Usuario",
        hint_text="Ej: johnd",
        width=300,
        border_color=ROSA_PRINCIPAL,
        focused_border_color=ROSA_OSCURO,
        label_style=ft.TextStyle(color=GRIS_TEXTO),
        cursor_color=ROSA_OSCURO,
        bgcolor=BLANCO,
    )
    txt_contrasena = ft.TextField(
        label="Contraseña",
        hint_text="Ej: m38rmF$",
        width=300,
        password=True,
        can_reveal_password=True,
        border_color=ROSA_PRINCIPAL,
        focused_border_color=ROSA_OSCURO,
        label_style=ft.TextStyle(color=GRIS_TEXTO),
        cursor_color=ROSA_OSCURO,
        bgcolor=BLANCO,
    )

    # Respaldo únicamente para los usuarios de prueba conocidos de FakeStoreAPI,
    # por si la llamada a /users llegara a fallar (ej. sin internet momentáneo).
    IDS_CONOCIDOS = {
        "johnd": 1,
        "mor_2314": 2,
        "kevinryan": 3,
    }

    def obtener_id_usuario(nombre_usuario):
        """Busca el id real del usuario consultando /users. Si falla, usa el respaldo."""
        try:
            respuesta = requests.get("https://fakestoreapi.com/users", timeout=5)
            if respuesta.status_code == 200:
                usuarios = respuesta.json()
                for u in usuarios:
                    if u.get("username", "").lower() == nombre_usuario.lower():
                        return u.get("id")
        except Exception:
            pass  # si falla la consulta, caemos al respaldo de abajo

        return IDS_CONOCIDOS.get(nombre_usuario.lower())

    def hay_internet():
        try:
            requests.get("https://fakestoreapi.com", timeout=3)
            return True
        except Exception:
            return False

    def mostrar_alerta(titulo, mensaje):
        alerta = ft.AlertDialog(
            title=ft.Text(titulo, color=GRIS_TEXTO),
            content=ft.Text(mensaje, color=GRIS_TEXTO),
            bgcolor=ROSA_CLARO,
            actions=[
                ft.TextButton(
                    "OK",
                    on_click=lambda e: page.close(alerta),
                    style=ft.ButtonStyle(color=ROSA_OSCURO),
                )
            ],
        )
        page.open(alerta)
        page.update()

    def cerrar_sesion(e):
        borrar_datos()
        mostrar_login()

    def mostrar_pantalla_principal(datos):
        page.controls.clear()
        page.add(
            ft.Column(
                [
                    ft.Icon(ft.Icons.CHECK_CIRCLE, size=80, color=ROSA_OSCURO),
                    ft.Text("¡Bienvenido!", size=30, weight=ft.FontWeight.BOLD, color=GRIS_TEXTO),
                    ft.Text(f"Rol: {datos['rol']}", size=20, color=ROSA_OSCURO),
                    ft.Text(f"ID de usuario: {datos['id']}", size=16, color=GRIS_TEXTO),
                    ft.Text(f"Token: {datos['token'][:20]}...", size=12, color=GRIS_TEXTO),
                    ft.ElevatedButton(
                        "Cerrar sesión",
                        on_click=cerrar_sesion,
                        bgcolor=ROSA_PRINCIPAL,
                        color=BLANCO,
                    ),
                ],
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                spacing=20,
            )
        )
        page.update()

    def iniciar_sesion(e):
        if not hay_internet():
            mostrar_alerta("Sin conexión", "No tienes internet.")
            return

        usuario = txt_usuario.value
        contrasena = txt_contrasena.value

        if not usuario or not contrasena:
            mostrar_alerta("Campos vacíos", "Llena todos los campos.")
            return

        try:
            respuesta = requests.post(
                "https://fakestoreapi.com/auth/login",
                json={"username": usuario, "password": contrasena},
            )

            # La API a veces responde 201 (Creado) en vez de 200 en el login.
            # En ambos casos el login fue exitoso, así que tratamos los dos igual.
            if respuesta.status_code in (200, 201):
                datos = respuesta.json()
                token = datos.get("token")

                if not token:
                    mostrar_alerta("Error", "La API no devolvió un token válido.")
                    return

                id_usuario = obtener_id_usuario(usuario)

                if id_usuario is None:
                    mostrar_alerta(
                        "Error",
                        f"No se pudo determinar el ID para el usuario '{usuario}'.",
                    )
                    return

                if id_usuario in (1, 2):
                    rol = "Administrador"
                elif id_usuario == 3:
                    rol = "Auditor"
                else:
                    rol = "Cliente"

                guardar_datos(token, id_usuario, rol)
                mostrar_pantalla_principal({"token": token, "id": id_usuario, "rol": rol})

            elif respuesta.status_code == 401:
                mostrar_alerta("Error", "Usuario o contraseña incorrectos.")
            else:
                mostrar_alerta("Error", f"Error {respuesta.status_code}")

        except Exception as error:
            mostrar_alerta("Error", f"No se pudo conectar: {str(error)}")

    def mostrar_login():
        page.controls.clear()
        page.add(
            ft.Column(
                [
                    ft.Icon(ft.Icons.SHOPPING_CART, size=80, color=ROSA_PRINCIPAL),
                    ft.Text("Fake Store Login", size=30, weight=ft.FontWeight.BOLD, color=GRIS_TEXTO),
                    ft.Text("Inicia sesión con tu cuenta", size=16, color=GRIS_TEXTO),
                    txt_usuario,
                    txt_contrasena,
                    ft.ElevatedButton(
                        "Iniciar Sesión",
                        on_click=iniciar_sesion,
                        width=300,
                        bgcolor=ROSA_PRINCIPAL,
                        color=BLANCO,
                    ),
                    ft.Text(
                        "IDs: 1,2=Admin | 3=Auditor | Resto=Cliente",
                        size=12,
                        italic=True,
                        color=GRIS_TEXTO,
                    ),
                    ft.Text("Usuarios: johnd / mor_2314 / kevinryan", size=12, color=GRIS_TEXTO),
                ],
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                spacing=15,
            )
        )
        page.update()

    def verificar_sesion():
        datos = cargar_datos()
        if datos:
            mostrar_pantalla_principal(datos)
        else:
            mostrar_login()

    verificar_sesion()

ft.app(target=main)