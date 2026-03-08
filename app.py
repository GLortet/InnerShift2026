from __future__ import annotations

from typing import Any

import streamlit as st

from config import (
    APP_BASELINE,
    APP_NAME,
    APP_SUBTITLE,
    MIN_TRANSCRIPTION_WORDS,
    SCORE_LABELS,
    STYLES_DIR,
    UI_NAVIGATION,
)
from modules.audio_processing import detect_audio_mime_type, load_audio_bytes, save_streamlit_audio
from modules.nlp_analysis import analyze_transcript
from modules.profile_manager import load_profile, rebuild_profile
from modules.report_generator import generate_report
from modules.session_manager import (
    attach_analysis,
    attach_audio,
    attach_report,
    attach_transcription,
    create_session,
    get_preferred_audio_path,
    get_report_path,
    list_sessions,
    load_session,
    update_session_title,
    update_transcription_text,
)
from modules.storage import initialize_storage
from modules.transcription import TranscriptionError, transcribe_audio
from modules.utils import count_words, format_display_datetime, truncate_text
from modules.visualizations import build_profile_history_chart, build_scores_chart, build_theme_chart

st.set_page_config(
    page_title=APP_NAME,
    page_icon="I",
    layout="wide",
    initial_sidebar_state="expanded",
)


def load_branding() -> None:
    style_path = STYLES_DIR / "brand.css"
    if style_path.exists():
        st.markdown(f"<style>{style_path.read_text(encoding='utf-8')}</style>", unsafe_allow_html=True)


@st.cache_data(show_spinner=False)
def cached_audio_preview(path_value: str | None) -> bytes | None:
    return load_audio_bytes(path_value)


@st.cache_data(show_spinner=False)
def cached_scores_chart(serialized_scores: tuple[tuple[str, int], ...]) -> bytes | None:
    return build_scores_chart(dict(serialized_scores))


@st.cache_data(show_spinner=False)
def cached_theme_chart(serialized_themes: tuple[tuple[str, int], ...]) -> bytes | None:
    theme_payload = [{"theme": theme, "count": count} for theme, count in serialized_themes]
    return build_theme_chart(theme_payload)


@st.cache_data(show_spinner=False)
def cached_profile_history_chart(profile_signature: tuple[tuple[str, tuple[int, ...]], ...]) -> bytes | None:
    score_trends = {
        metric: [{"value": value, "title": f"S{index + 1}"} for index, value in enumerate(values)]
        for metric, values in profile_signature
    }
    return build_profile_history_chart({"score_trends": score_trends})


def initialize_app_state() -> None:
    initialize_storage()
    if "nav_selection" not in st.session_state:
        st.session_state.nav_selection = UI_NAVIGATION[0]
    if "active_session_id" not in st.session_state:
        sessions = list_sessions()
        st.session_state.active_session_id = sessions[0]["id"] if sessions else None
    if "draft_session_title" not in st.session_state:
        st.session_state.draft_session_title = ""


def go_to(page_name: str) -> None:
    st.session_state.nav_selection = page_name
    st.rerun()


def get_active_session() -> dict[str, Any] | None:
    session_id = st.session_state.get("active_session_id")
    return load_session(session_id)


def ensure_transcript_editor_seed(session: dict[str, Any]) -> str:
    editor_key = f"transcript_editor_{session['id']}"
    source_key = f"{editor_key}_source"
    source_text = session.get("transcription", {}).get("text", "")
    if st.session_state.get(source_key) != source_text:
        st.session_state[editor_key] = source_text
        st.session_state[source_key] = source_text
    return editor_key


def session_status_label(session: dict[str, Any]) -> str:
    return {
        "created": "Creee",
        "audio_ready": "Audio pret",
        "transcribed": "Transcrite",
        "analyzed": "Analysee",
        "reported": "Rapport genere",
    }.get(session.get("status"), session.get("status", "Inconnue"))


def render_signal_list(title: str, signals: list[dict[str, Any]]) -> None:
    st.markdown(f"#### {title}")
    if not signals:
        st.caption("Aucun signal distinctif releve pour cette rubrique.")
        return
    for signal in signals:
        evidence = " | ".join(signal.get("evidence", [])[:2])
        st.markdown(f"- **{signal['signal'].capitalize()}** ({signal['level']})")
        if evidence:
            st.caption(evidence)


def render_analysis_results(analysis: dict[str, Any]) -> None:
    st.markdown(
        f"""
        <div class="soft-panel">
            <div class="eyebrow">Resume</div>
            <h3 style="margin-bottom:0.4rem; color:#1E3A4C;">Lecture de la session</h3>
            <p class="section-note" style="margin:0;">{analysis.get('summary', '')}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    score_columns = st.columns(5)
    for column, (metric, value) in zip(score_columns, analysis.get("scores", {}).items()):
        column.metric(SCORE_LABELS.get(metric, metric), f"{value}/100")

    score_chart = cached_scores_chart(tuple(analysis.get("scores", {}).items()))
    theme_chart = cached_theme_chart(tuple((item["theme"], item["count"]) for item in analysis.get("dominant_themes", [])))
    chart_left, chart_right = st.columns(2)
    with chart_left:
        st.markdown("#### Indicateurs")
        if score_chart:
            st.image(score_chart, use_container_width=True)
    with chart_right:
        st.markdown("#### Themes dominants")
        if theme_chart:
            st.image(theme_chart, use_container_width=True)

    left, right = st.columns(2)
    with left:
        st.markdown("#### Idees majeures")
        for idea in analysis.get("major_ideas", []):
            st.markdown(f"- {idea}")
        st.markdown("#### Tensions ou contradictions")
        if analysis.get("tensions"):
            for item in analysis.get("tensions", []):
                st.markdown(f"- {item}")
        else:
            st.caption("Aucune tension explicite n'a ete detectee de maniere robuste.")
    with right:
        st.markdown("#### Pistes d'action")
        for item in analysis.get("recommendations", []):
            st.markdown(f"- {item}")
        st.markdown("#### Mots-cles")
        chips = "".join(
            f"<span class='chip'>{keyword['term']}</span>"
            for keyword in analysis.get("keyword_frequencies", [])[:8]
        )
        st.markdown(f"<div class='chip-row'>{chips}</div>", unsafe_allow_html=True)

    signal_left, signal_right, signal_third = st.columns(3)
    with signal_left:
        render_signal_list("Signaux emotionnels", analysis.get("emotional_signals", []))
    with signal_right:
        render_signal_list("Signaux cognitifs", analysis.get("cognitive_signals", []))
    with signal_third:
        render_signal_list("Signaux d'action", analysis.get("action_signals", []))

    st.markdown("#### Phrases saillantes")
    quotes = analysis.get("quotes_or_salient_sentences", [])
    if not quotes:
        st.caption("Aucune phrase saillante n'a ete selectionnee.")
    for quote in quotes:
        st.markdown(f"<div class='quote-block'>\"{quote}\"</div>", unsafe_allow_html=True)


def render_home() -> None:
    st.markdown(
        f"""
        <div class="hero-card">
            <div class="kicker">Inner reflection companion</div>
            <h1 style="margin:0 0 0.4rem 0;">{APP_NAME}</h1>
            <p style="font-size:1.05rem; max-width:760px; margin:0 0 0.7rem 0;">{APP_SUBTITLE}</p>
            <p style="margin:0; opacity:0.85;">{APP_BASELINE}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    intro_left, intro_right = st.columns([1.15, 0.85])
    with intro_left:
        st.markdown(
            """
            <div class="soft-panel">
                <div class="eyebrow">Parcours</div>
                <h3 style="margin:0 0 0.6rem 0; color:#1E3A4C;">Une experience de clarification tangible</h3>
                <p class="section-note">InnerShift capture une parole libre, la rend lisible, met en relief les themes dominants, les tensions du moment et les leviers d'action a consolider.</p>
                <div class="subtle-divider"></div>
                <p class="section-note"><strong>1.</strong> Enregistrer ou importer un audio.</p>
                <p class="section-note"><strong>2.</strong> Obtenir une transcription modifiable.</p>
                <p class="section-note"><strong>3.</strong> Lancer une analyse heuristique sobre et structuree.</p>
                <p class="section-note"><strong>4.</strong> Generer un PDF premium et suivre l'evolution du profil.</p>
            </div>
            """,
            unsafe_allow_html=True,
        )
        if st.button("Demarrer une nouvelle session", type="primary"):
            st.session_state.active_session_id = None
            st.session_state.draft_session_title = ""
            go_to("Nouvelle session")

    with intro_right:
        st.markdown(
            """
            <div class="metric-panel">
                <div class="eyebrow">Positionnement</div>
                <h3 style="margin:0 0 0.7rem 0; color:#1E3A4C;">Ni chatbot gadget, ni oracle.</h3>
                <p class="section-note">Le rendu privilegie la clarte, la profondeur et la prudence. Les scores sont heuristiques, les formulations restent exploratoires, et le PDF agit comme une piece de restitution credible et montrable.</p>
            </div>
            """,
            unsafe_allow_html=True,
        )
        st.markdown("#### Principes")
        st.markdown("- ton calme, professionnel et utile")
        st.markdown("- lecture de tendances, pas de diagnostic")
        st.markdown("- architecture modulaire prete a evoluer")


def render_new_session() -> None:
    session = get_active_session()
    st.markdown("## Nouvelle session")
    st.caption("Creer une session, capturer l'audio, transcrire puis analyser le contenu de facon structuree.")

    if session is None:
        st.markdown("### Demarrer une nouvelle session")
        st.text_input("Titre de session", key="draft_session_title", placeholder="Ex. Clarifier mon prochain pivot")
        if st.button("Creer la session", type="primary"):
            new_session = create_session(st.session_state.draft_session_title)
            st.session_state.active_session_id = new_session["id"]
            go_to("Nouvelle session")
        return

    title_key = f"title_editor_{session['id']}"
    if title_key not in st.session_state:
        st.session_state[title_key] = session.get("title", "")

    info_col, action_col = st.columns([4, 1])
    with info_col:
        st.text_input("Titre de session", key=title_key)
        st.caption(f"Creee le {format_display_datetime(session.get('created_at'))} · Statut : {session_status_label(session)}")
    with action_col:
        st.write("")
        st.write("")
        if st.button("Nouvelle vierge"):
            st.session_state.active_session_id = None
            st.session_state.draft_session_title = ""
            go_to("Nouvelle session")

    if st.session_state[title_key].strip() and st.session_state[title_key].strip() != session.get("title"):
        if st.button("Renommer la session"):
            update_session_title(session, st.session_state[title_key])
            st.success("Titre mis a jour.")
            st.rerun()

    st.markdown("### 1. Capture audio")
    capture_col, upload_col = st.columns(2)
    with capture_col:
        st.markdown("#### Microphone")
        if hasattr(st, "audio_input"):
            microphone_audio = st.audio_input("Enregistrer une note vocale", key=f"audio_input_{session['id']}")
            if st.button("Sauvegarder l'enregistrement", key=f"save_mic_{session['id']}", disabled=microphone_audio is None):
                try:
                    audio_payload = save_streamlit_audio(microphone_audio, session["id"], "microphone")
                    attach_audio(session, audio_payload)
                    st.success("Enregistrement sauvegarde.")
                    st.rerun()
                except Exception as exc:
                    st.error(str(exc))
        else:
            st.info("Cette version de Streamlit ne prend pas en charge `st.audio_input`. Utilisez l'import de fichier a droite.")

    with upload_col:
        st.markdown("#### Import")
        uploaded_audio = st.file_uploader(
            "Importer un fichier audio",
            type=["wav", "mp3", "m4a", "mp4", "mpeg"],
            key=f"upload_audio_{session['id']}",
        )
        if st.button("Importer ce fichier", key=f"save_upload_{session['id']}", disabled=uploaded_audio is None):
            try:
                audio_payload = save_streamlit_audio(uploaded_audio, session["id"], "upload")
                attach_audio(session, audio_payload)
                st.success("Fichier audio importe.")
                st.rerun()
            except Exception as exc:
                st.error(str(exc))

    session = get_active_session() or session
    audio_info = session.get("audio", {})
    if audio_info:
        st.markdown("#### Audio actif")
        audio_bytes = cached_audio_preview(audio_info.get("original_path"))
        if audio_bytes:
            st.audio(audio_bytes, format=audio_info.get("mime_type") or detect_audio_mime_type(audio_info.get("original_path") or "sample.wav"))
        meta_col1, meta_col2, meta_col3 = st.columns(3)
        meta_col1.metric("Format", (audio_info.get("format") or "?").upper())
        duration_display = f"{audio_info.get('duration_seconds', 0):.1f}s" if audio_info.get("duration_seconds") else "N/A"
        meta_col2.metric("Duree", duration_display)
        size_display = f"{audio_info.get('size_bytes', 0) / 1024:.1f} KB" if audio_info.get("size_bytes") else "N/A"
        meta_col3.metric("Taille", size_display)
        for warning in audio_info.get("warnings", []):
            st.caption(f"Note audio : {warning}")

    st.markdown("### 2. Transcription")
    language_choice = st.selectbox(
        "Langue attendue",
        options=["auto", "fr", "en"],
        format_func=lambda value: {"auto": "Detection automatique", "fr": "Francais", "en": "Anglais"}[value],
        key=f"language_choice_{session['id']}",
    )

    if st.button("Transcrire l'audio", type="primary", disabled=not bool(audio_info), key=f"transcribe_button_{session['id']}"):
        audio_path = get_preferred_audio_path(session)
        if not audio_path:
            st.error("Aucun fichier audio exploitable n'est disponible pour cette session.")
        else:
            try:
                with st.spinner("Transcription Whisper en cours..."):
                    transcription_payload = transcribe_audio(audio_path, None if language_choice == "auto" else language_choice)
                attach_transcription(session, transcription_payload)
                st.success("Transcription terminee.")
                st.rerun()
            except TranscriptionError as exc:
                st.error(str(exc))

    session = get_active_session() or session
    transcription = session.get("transcription", {})
    if transcription.get("text"):
        editor_key = ensure_transcript_editor_seed(session)
        st.text_area(
            "Transcription editable",
            key=editor_key,
            height=240,
            help="Vous pouvez corriger legerement la transcription avant l'analyse.",
        )
        edit_col, info_col = st.columns([1, 3])
        with edit_col:
            if st.button("Enregistrer la correction", key=f"save_transcript_{session['id']}"):
                updated_text = st.session_state.get(editor_key, "")
                updated_session = update_transcription_text(
                    session,
                    updated_text,
                    edited=updated_text.strip() != transcription.get("text", "").strip(),
                )
                st.session_state[editor_key] = updated_session.get("transcription", {}).get("text", "")
                st.success("Transcription mise a jour.")
                st.rerun()
        with info_col:
            st.caption(f"Langue detectee : {transcription.get('language', 'N/A')} · {transcription.get('word_count', 0)} mots")
        for warning in transcription.get("warnings", []):
            st.caption(f"Note transcription : {warning}")

    st.markdown("### 3. Analyse")
    current_transcript_text = session.get("transcription", {}).get("text", "")
    if current_transcript_text:
        editor_key = ensure_transcript_editor_seed(session)
        current_transcript_text = st.session_state.get(editor_key, current_transcript_text)

    if current_transcript_text and count_words(current_transcript_text) < MIN_TRANSCRIPTION_WORDS:
        st.info(f"Le texte contient moins de {MIN_TRANSCRIPTION_WORDS} mots. L'analyse reste possible, mais la lecture sera plus fragile.")

    if st.button("Analyser la session", type="primary", disabled=not bool(current_transcript_text.strip()), key=f"analyze_button_{session['id']}"):
        if current_transcript_text.strip() != transcription.get("text", "").strip():
            update_transcription_text(session, current_transcript_text, edited=True)
            session = get_active_session() or session
        analysis_payload = analyze_transcript(current_transcript_text)
        attach_analysis(session, analysis_payload)
        rebuild_profile()
        st.success("Analyse terminee et profil mis a jour.")
        st.rerun()

    session = get_active_session() or session
    analysis = session.get("analysis", {})
    if analysis:
        render_analysis_results(analysis)
        if st.button("Generer le rapport PDF", key=f"generate_pdf_{session['id']}"):
            try:
                profile = rebuild_profile()
                report_payload = generate_report(session, profile)
                attach_report(session, report_payload)
                st.success("Rapport PDF genere.")
                go_to("Rapport")
            except Exception as exc:
                st.error(f"Generation du PDF impossible : {exc}")


def render_report() -> None:
    session = get_active_session()
    st.markdown("## Rapport")
    if not session:
        st.info("Aucune session active. Ouvrez une session depuis l'historique ou creez-en une nouvelle.")
        return

    analysis = session.get("analysis", {})
    if not analysis:
        st.warning("Cette session n'a pas encore ete analysee.")
        return

    report_path = get_report_path(session)
    st.markdown(
        f"""
        <div class="soft-panel">
            <div class="eyebrow">Session active</div>
            <h3 style="margin:0 0 0.4rem 0; color:#1E3A4C;">{session.get('title')}</h3>
            <p class="section-note" style="margin:0;">{analysis.get('summary', '')}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    if not report_path or not report_path.exists():
        if st.button("Generer le PDF maintenant", type="primary"):
            profile = rebuild_profile()
            report_payload = generate_report(session, profile)
            attach_report(session, report_payload)
            st.success("Rapport genere.")
            st.rerun()
        return

    st.markdown("#### Contenu du rapport")
    st.markdown("- couverture editoriale et contexte de session")
    st.markdown("- resume executif, idees fortes et tensions")
    st.markdown("- indicateurs heuristiques, themes et visualisations")
    st.markdown("- extraits saillants, profil evolutif et note methodologique")

    with report_path.open("rb") as handle:
        pdf_bytes = handle.read()
    st.download_button(
        label="Telecharger le rapport PDF",
        data=pdf_bytes,
        file_name=report_path.name,
        mime="application/pdf",
        type="primary",
    )
    st.caption(f"Derniere generation : {format_display_datetime(session.get('report', {}).get('generated_at'))}")


def render_history() -> None:
    sessions = list_sessions()
    st.markdown("## Historique")
    if not sessions:
        st.info("Aucune session enregistree pour l'instant.")
        return

    for session in sessions:
        top_theme = (session.get("analysis", {}).get("dominant_themes") or [{}])[0].get("theme") or "Theme a venir"
        with st.container(border=True):
            info_col, summary_col, actions_col = st.columns([2.5, 2.5, 1.4])
            with info_col:
                st.markdown(f"### {session.get('title')}")
                st.caption(f"{format_display_datetime(session.get('created_at'))} · {session_status_label(session)}")
                st.caption(f"Theme principal : {top_theme}")
            with summary_col:
                summary = session.get("analysis", {}).get("summary") or "Session encore en preparation."
                st.write(truncate_text(summary, 220))
            with actions_col:
                if st.button("Ouvrir", key=f"open_session_{session['id']}"):
                    st.session_state.active_session_id = session["id"]
                    go_to("Nouvelle session")
                if session.get("analysis") and st.button("PDF", key=f"regen_pdf_{session['id']}"):
                    try:
                        profile = rebuild_profile()
                        report_payload = generate_report(session, profile)
                        attach_report(session, report_payload)
                        st.session_state.active_session_id = session["id"]
                        st.success("PDF regenere.")
                        st.rerun()
                    except Exception as exc:
                        st.error(str(exc))


def render_profile() -> None:
    profile = load_profile()
    st.markdown("## Profil utilisateur")
    if st.button("Recalculer le profil"):
        profile = rebuild_profile()
        st.success("Profil recalcule.")

    metric_col1, metric_col2, metric_col3 = st.columns(3)
    metric_col1.metric("Sessions analysees", profile.get("session_count", 0))
    top_theme = (profile.get("top_themes") or [{}])[0].get("theme") or "N/A"
    top_tone = (profile.get("recurring_tones") or [{}])[0].get("signal") or "N/A"
    metric_col2.metric("Theme le plus frequent", top_theme)
    metric_col3.metric("Tonalite recurrente", top_tone)

    profile_signature = tuple(
        (metric, tuple(point["value"] for point in history))
        for metric, history in sorted(profile.get("score_trends", {}).items())
    )
    history_chart = cached_profile_history_chart(profile_signature)
    if history_chart:
        st.image(history_chart, use_container_width=True)

    left, right = st.columns(2)
    with left:
        st.markdown("### Themes recurrents")
        for item in profile.get("top_themes", []):
            st.markdown(f"- {item['theme']} ({item['count']})")
        st.markdown("### Mots-cles dominants")
        chips = "".join(f"<span class='chip'>{item['term']}</span>" for item in profile.get("top_keywords", [])[:12])
        st.markdown(f"<div class='chip-row'>{chips}</div>", unsafe_allow_html=True)
    with right:
        st.markdown("### Signaux de progression")
        for signal in profile.get("progress_signals", []):
            st.markdown(f"- {signal}")
        st.markdown("### Recommandations recentes")
        for item in profile.get("recent_recommendations", [])[:5]:
            st.markdown(f"- {item}")

    st.markdown("### Sessions recentes")
    for item in profile.get("recent_sessions", []):
        st.markdown(f"- **{item['title']}** · {format_display_datetime(item['created_at'])} · {item.get('top_theme') or 'Theme a venir'}")


def main() -> None:
    load_branding()
    initialize_app_state()

    with st.sidebar:
        st.markdown(f"## {APP_NAME}")
        st.caption("Clarification conversationnelle et rapport editorial local.")
        st.radio("Navigation", UI_NAVIGATION, key="nav_selection")

    selected_page = st.session_state.nav_selection
    if selected_page == "Accueil":
        render_home()
    elif selected_page == "Nouvelle session":
        render_new_session()
    elif selected_page == "Rapport":
        render_report()
    elif selected_page == "Historique":
        render_history()
    elif selected_page == "Profil utilisateur":
        render_profile()


if __name__ == "__main__":
    main()

