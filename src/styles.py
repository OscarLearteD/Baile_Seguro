import streamlit as st


def inject_global_styles() -> None:
    """
    Estilos globales para una apariencia mobile-first más limpia.
    Paleta extraída del logo: dorados/champagne sobre carbón oscuro.

    COLOR_PRIMARY  : #cca865  (dorado)
    COLOR_SECONDARY: #d6ba85  (dorado claro)
    COLOR_ACCENT   : #ae9f84  (taupe)
    COLOR_DARK     : #393836  (carbón)
    COLOR_MID      : #746f6a  (gris cálido)
    COLOR_LIGHT    : #e9dfcd  (crema)
    COLOR_CREAM    : #faf7f2  (crema muy claro, fondo)
    """
    st.markdown(
        """
        <style>
        /* ------------------------------------------------------------------ */
        /* Fondo general — crema muy suave que evoca el tono del logo         */
        /* ------------------------------------------------------------------ */
        .stApp {
            background: linear-gradient(180deg, #faf7f2 0%, #f5f0e8 40%, #ffffff 100%);
        }

        .block-container {
            max-width: 820px;
            padding-top: 1rem;
            padding-bottom: 3rem;
        }

        /* ------------------------------------------------------------------ */
        /* Hero card — carbón oscuro con destello dorado                      */
        /* ------------------------------------------------------------------ */
        .hero-card {
            background:
                radial-gradient(ellipse at top right, rgba(204,168,101,0.18) 0%, transparent 60%),
                linear-gradient(135deg, #1a1917 0%, #2e2b28 55%, #393836 100%);
            color: white;
            padding: 1.4rem;
            border-radius: 24px;
            margin-bottom: 1rem;
            box-shadow: 0 18px 40px rgba(57, 56, 54, 0.28);
            border: 1px solid rgba(204,168,101,0.15);
        }

        .hero-title {
            font-size: 1.6rem;
            font-weight: 800;
            line-height: 1.15;
            margin-bottom: 0.35rem;
        }

        .hero-subtitle {
            font-size: 0.98rem;
            opacity: 0.88;
            line-height: 1.45;
            color: #e9dfcd;
        }

        /* ------------------------------------------------------------------ */
        /* Labels y cabeceras de sección                                      */
        /* ------------------------------------------------------------------ */
        .section-label {
            font-size: 0.8rem;
            font-weight: 700;
            text-transform: uppercase;
            letter-spacing: 0.06em;
            color: #9a7a3f;
            margin: 0.6rem 0 0.4rem 0;
            padding-left: 0.65rem;
            border-left: 3px solid #cca865;
        }

        .breadcrumb {
            font-size: 0.92rem;
            color: #746f6a;
            margin-bottom: 0.75rem;
        }

        /* ------------------------------------------------------------------ */
        /* Tarjetas de vídeo y admin                                          */
        /* ------------------------------------------------------------------ */
        .video-card,
        .admin-card {
            background: white;
            border: 1px solid #e9dfcd;
            border-left: 4px solid #cca865;
            border-radius: 22px;
            padding: 1rem;
            margin-bottom: 1rem;
            box-shadow: 0 10px 24px rgba(57, 56, 54, 0.07);
            transition: box-shadow 0.18s ease;
        }

        .video-card:hover,
        .admin-card:hover {
            box-shadow: 0 16px 32px rgba(204, 168, 101, 0.14);
        }

        .video-title {
            font-size: 1.05rem;
            font-weight: 700;
            color: #1a1917;
            margin-bottom: 0.2rem;
        }

        .video-meta {
            color: #746f6a;
            font-size: 0.9rem;
            margin-bottom: 0.5rem;
        }

        .empty-state {
            background: rgba(255,255,255,0.92);
            border: 1px dashed #c5b28e;
            border-radius: 22px;
            padding: 1.2rem;
            text-align: center;
            color: #746f6a;
        }

        .small-note {
            color: #746f6a;
            font-size: 0.9rem;
        }

        /* ------------------------------------------------------------------ */
        /* Botones — dorado en hover, suave sobre blanco                      */
        /* ------------------------------------------------------------------ */
        div[data-testid="stButton"] > button {
            width: 100%;
            min-height: 52px;
            border-radius: 18px;
            border: 1px solid #e9dfcd;
            background: white;
            color: #1a1917;
            font-weight: 700;
            font-size: 1rem;
            box-shadow: 0 10px 24px rgba(57, 56, 54, 0.06);
            transition: all 0.18s ease;
        }

        div[data-testid="stButton"] > button:hover {
            border-color: #cca865;
            transform: translateY(-1px);
            box-shadow: 0 16px 28px rgba(204, 168, 101, 0.18);
            color: #9a7a3f;
        }

        /* Botón primario (tipo filled) */
        div[data-testid="stButton"] > button[kind="primary"] {
            background: linear-gradient(135deg, #cca865 0%, #d6ba85 100%);
            color: #1a1917;
            border: none;
            box-shadow: 0 10px 24px rgba(204, 168, 101, 0.28);
        }

        div[data-testid="stButton"] > button[kind="primary"]:hover {
            background: linear-gradient(135deg, #b8934d 0%, #cca865 100%);
            box-shadow: 0 16px 32px rgba(204, 168, 101, 0.38);
            color: #1a1917;
        }

        /* Botón play dentro de tarjetas de vídeo */
        .video-card div[data-testid="stButton"] > button {
            background: linear-gradient(135deg, #393836 0%, #746f6a 100%) !important;
            color: #e9dfcd !important;
            border: none !important;
            min-height: 44px !important;
            font-size: 1rem !important;
            letter-spacing: 0.04em !important;
        }
        .video-card div[data-testid="stButton"] > button:hover {
            background: linear-gradient(135deg, #cca865 0%, #d6ba85 100%) !important;
            color: #1a1917 !important;
            border: none !important;
            transform: translateY(-1px);
        }

        div[data-testid="stForm"] {
            background: rgba(255, 255, 255, 0.97);
            border: 1px solid #e9dfcd;
            border-radius: 24px;
            padding: 1rem;
            box-shadow: 0 16px 34px rgba(57, 56, 54, 0.08);
        }

        iframe {
            border-radius: 18px;
            overflow: hidden;
        }

        /* ------------------------------------------------------------------ */
        /* Calendario mensual                                                  */
        /* ------------------------------------------------------------------ */

        [data-testid="stVerticalBlockBorderWrapper"] {
            border-radius: 22px !important;
            border-color: #e9dfcd !important;
            box-shadow: 0 10px 24px rgba(57, 56, 54, 0.06) !important;
            background: white !important;
            margin-bottom: 1rem !important;
        }

        [data-testid="stTextInput"]:has(input[placeholder^="vplay_"]) {
            position: absolute !important;
            opacity: 0 !important;
            pointer-events: none !important;
            height: 1px !important;
            overflow: hidden !important;
        }

        [data-testid="stHorizontalBlock"]:has(
            > [data-testid="stColumn"]:nth-child(7)
        ) {
            display: grid !important;
            grid-template-columns: repeat(7, 1fr) !important;
            gap: 3px !important;
            width: 100% !important;
            flex-wrap: nowrap !important;
        }

        [data-testid="stHorizontalBlock"]:has(
            > [data-testid="stColumn"]:nth-child(7)
        ) > [data-testid="stColumn"] {
            min-width: 0 !important;
            width: auto !important;
            flex: none !important;
            overflow: hidden !important;
            padding: 0 !important;
        }

        [data-testid="stHorizontalBlock"]:has(
            > [data-testid="stColumn"]:nth-child(7)
        ) [data-testid="stButton"] > button {
            min-height: 40px !important;
            height: 40px !important;
            padding: 0 2px !important;
            font-size: 0.78rem !important;
            font-weight: 600 !important;
            border-radius: 8px !important;
            box-shadow: none !important;
            min-width: 0 !important;
            overflow: hidden !important;
            white-space: nowrap !important;
            line-height: 1 !important;
        }

        .cal-month-title {
            text-align: center;
            font-size: 1rem;
            font-weight: 800;
            color: #1a1917;
            padding: 0.4rem 0 0.1rem 0;
            line-height: 1.3;
            width: 100%;
        }

        .cal-today-hint {
            text-align: center;
            font-size: 0.75rem;
            color: #cca865;
            font-weight: 600;
            margin-bottom: 0.4rem;
            width: 100%;
        }

        /* Cabeceras L M X J V S D */
        .cal-day-header {
            text-align: center;
            font-size: 0.65rem;
            font-weight: 700;
            text-transform: uppercase;
            letter-spacing: 0.04em;
            color: #9a7a3f;
            padding: 0.2rem 0;
        }

        /* Celda vacía (día fuera del mes) */
        .cal-empty {
            min-height: 40px;
            height: 40px;
            display: block;
        }

        /* Día de vacaciones — no interactivo, visualmente apagado */
        .cal-vacation {
            min-height: 40px;
            height: 40px;
            display: flex;
            align-items: center;
            justify-content: center;
            border-radius: 8px;
            background: rgba(174, 159, 132, 0.12);
            color: #ae9f84;
            font-size: 0.78rem;
            font-weight: 500;
            opacity: 0.55;
            cursor: default;
            user-select: none;
        }

        /* Separador visual entre secciones del dashboard */
        .section-divider {
            border: none;
            border-top: 1px solid #e9dfcd;
            margin: 1.25rem 0;
        }

        /* ------------------------------------------------------------------ */
        /* Pantalla del día — franjas horarias y tarjetas de slot              */
        /* ------------------------------------------------------------------ */

        .time-block-header {
            background: linear-gradient(135deg, #393836 0%, #746f6a 100%);
            color: #e9dfcd;
            font-weight: 700;
            font-size: 1rem;
            padding: 0.55rem 1.1rem;
            border-radius: 14px;
            margin: 1.1rem 0 0.5rem 0;
            text-align: center;
            letter-spacing: 0.03em;
            border-left: 4px solid #cca865;
        }

        .slot-empty {
            background: rgba(255,255,255,0.85);
            border: 1px dashed #c5b28e;
            border-radius: 14px;
            padding: 0.6rem 1rem;
            text-align: center;
            color: #ae9f84;
            font-size: 0.88rem;
            margin-bottom: 0.4rem;
        }

        @media (max-width: 640px) {
            .block-container {
                padding-left: 0.85rem;
                padding-right: 0.85rem;
            }

            .hero-title {
                font-size: 1.35rem;
            }

            .cal-month-title {
                font-size: 0.92rem;
            }
        }
        </style>
        """,
        unsafe_allow_html=True,
    )
