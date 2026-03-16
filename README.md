# Escuela de Baile — MVP en Streamlit

Aplicación web mobile-first para una escuela de baile con autenticación, navegación por categorías y niveles, y acceso privado a vídeos según el usuario.

## Funcionalidades incluidas

- Login seguro con usuario y contraseña
- Logout
- Pantalla principal con categorías:
  - Salsa
  - Bachata
  - Otros
- Pantalla secundaria con niveles:
  - Nivel básico
  - Nivel básico medio
  - Nivel intermedio
  - Nivel avanzado
- Pantalla final con vídeos autorizados para el usuario autenticado
- Datos de ejemplo funcionales
- SQLite como base de datos local
- Contraseñas almacenadas con hash bcrypt
- Interfaz mobile-first con Streamlit

## Estructura del proyecto

```text
baile_app/
├── app.py
├── requirements.txt
├── README.md
├── .gitignore
├── .streamlit/
│   └── config.toml
├── data/
│   └── dance_school.db
├── assets/
│   └── logo_placeholder.txt
└── src/
    ├── __init__.py
    ├── config.py
    ├── db.py
    ├── auth.py
    ├── styles.py
    ├── seed.py
    ├── utils.py
    └── views.py

## Escuela de Baile — V2

Versión mejorada de la app con:

- login y logout
- panel admin
- creación de usuarios desde la web
- alta de vídeos por link o subida de archivo
- permisos por usuario
- soporte para enlaces de YouTube embebidos

## Credenciales iniciales

- Admin: `admin` / `AdminDance2026!`
- María: `maria` / `Dance2026!`
- Óscar: `oscar` / `BailaSeguro2026!`

## Muy importante

Si vienes de la versión anterior, elimina la base de datos antes de arrancar:

```bash
rm -f data/dance_school.db