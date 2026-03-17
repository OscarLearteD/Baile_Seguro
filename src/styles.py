import streamlit as st


def inject_global_styles() -> None:
    """
    Estilos globales para una apariencia mobile-first más limpia.
    Incluye estilos para el calendario mensual y las pantallas de slots.
    """
    st.markdown(
        """
        <style>
        .stApp {
            background: linear-gradient(180deg, #fdf2f8 0%, #f8fafc 25%, #ffffff 100%);
        }

        .block-container {
            max-width: 820px;
            padding-top: 1rem;
            padding-bottom: 3rem;
        }

        .hero-card {
            background: linear-gradient(135deg, #111827 0%, #1f2937 55%, #312e81 100%);
            color: white;
            padding: 1.4rem;
            border-radius: 24px;
            margin-bottom: 1rem;
            box-shadow: 0 18px 40px rgba(17, 24, 39, 0.18);
        }

        .hero-title {
            font-size: 1.6rem;
            font-weight: 800;
            line-height: 1.15;
            margin-bottom: 0.35rem;
        }

        .hero-subtitle {
            font-size: 0.98rem;
            opacity: 0.92;
            line-height: 1.45;
        }

        .section-label {
            font-size: 0.8rem;
            font-weight: 700;
            text-transform: uppercase;
            letter-spacing: 0.06em;
            color: #7c3aed;
            margin: 0.6rem 0 0.4rem 0;
        }

        .breadcrumb {
            font-size: 0.92rem;
            color: #6b7280;
            margin-bottom: 0.75rem;
        }

        .video-card,
        .admin-card {
            background: white;
            border: 1px solid #e5e7eb;
            border-radius: 22px;
            padding: 1rem;
            margin-bottom: 1rem;
            box-shadow: 0 10px 24px rgba(15, 23, 42, 0.06);
        }

        .video-title {
            font-size: 1.05rem;
            font-weight: 700;
            color: #111827;
            margin-bottom: 0.2rem;
        }

        .video-meta {
            color: #6b7280;
            font-size: 0.9rem;
            margin-bottom: 0.5rem;
        }

        .empty-state {
            background: rgba(255,255,255,0.92);
            border: 1px dashed #d1d5db;
            border-radius: 22px;
            padding: 1.2rem;
            text-align: center;
            color: #4b5563;
        }

        .small-note {
            color: #6b7280;
            font-size: 0.9rem;
        }

        /* Botones globales: full-width, buenos para móvil */
        div[data-testid="stButton"] > button {
            width: 100%;
            min-height: 52px;
            border-radius: 18px;
            border: 1px solid #e5e7eb;
            background: white;
            color: #111827;
            font-weight: 700;
            font-size: 1rem;
            box-shadow: 0 10px 24px rgba(15, 23, 42, 0.05);
            transition: all 0.18s ease;
        }

        div[data-testid="stButton"] > button:hover {
            border-color: #c084fc;
            transform: translateY(-1px);
            box-shadow: 0 16px 28px rgba(139, 92, 246, 0.12);
            color: #6d28d9;
        }

        div[data-testid="stForm"] {
            background: rgba(255, 255, 255, 0.95);
            border: 1px solid #e5e7eb;
            border-radius: 24px;
            padding: 1rem;
            box-shadow: 0 16px 34px rgba(15, 23, 42, 0.08);
        }

        iframe {
            border-radius: 18px;
            overflow: hidden;
        }

        /* ------------------------------------------------------------------ */
        /* Calendario mensual                                                  */
        /* ------------------------------------------------------------------ */

        .cal-wrapper {
            background: white;
            border: 1px solid #e5e7eb;
            border-radius: 22px;
            padding: 1rem 0.5rem 0.75rem 0.5rem;
            box-shadow: 0 10px 24px rgba(15, 23, 42, 0.05);
            margin-bottom: 1rem;
        }

        .cal-month-title {
            text-align: center;
            font-size: 1rem;
            font-weight: 800;
            color: #111827;
            padding: 0.4rem 0 0.1rem 0;
            line-height: 1.3;
        }

        .cal-today-hint {
            text-align: center;
            font-size: 0.75rem;
            color: #ec4899;
            font-weight: 600;
            margin-bottom: 0.2rem;
        }

        .cal-day-header {
            text-align: center;
            font-size: 0.72rem;
            font-weight: 700;
            text-transform: uppercase;
            letter-spacing: 0.04em;
            color: #7c3aed;
            padding: 0.35rem 0;
        }

        .cal-empty {
            min-height: 44px;
            display: block;
        }

        /* Separador visual entre secciones del dashboard */
        .section-divider {
            border: none;
            border-top: 1px solid #e5e7eb;
            margin: 1.25rem 0;
        }

        /* ------------------------------------------------------------------ */
        /* Pantalla del día — franjas horarias y tarjetas de slot              */
        /* ------------------------------------------------------------------ */

        .time-block-header {
            background: linear-gradient(135deg, #312e81 0%, #4c1d95 100%);
            color: white;
            font-weight: 700;
            font-size: 1rem;
            padding: 0.55rem 1.1rem;
            border-radius: 14px;
            margin: 1.1rem 0 0.5rem 0;
            text-align: center;
            letter-spacing: 0.03em;
        }

        .slot-empty {
            background: rgba(255,255,255,0.85);
            border: 1px dashed #d1d5db;
            border-radius: 14px;
            padding: 0.6rem 1rem;
            text-align: center;
            color: #9ca3af;
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
