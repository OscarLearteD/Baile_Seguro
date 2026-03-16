import streamlit as st


def inject_global_styles() -> None:
    """
    Estilos globales para una apariencia mobile-first más limpia.
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

        div[data-testid="stButton"] > button {
            width: 100%;
            min-height: 62px;
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

        @media (max-width: 640px) {
            .block-container {
                padding-left: 0.85rem;
                padding-right: 0.85rem;
            }

            .hero-title {
                font-size: 1.35rem;
            }
        }
        </style>
        """,
        unsafe_allow_html=True,
    )