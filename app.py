"""Elocution Coach — practice speaking with structured feedback."""

from __future__ import annotations

import sys
from pathlib import Path

import streamlit as st
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

load_dotenv(ROOT / ".env")

from src.coach import coach_transcript, has_openai, transcribe_audio
from src.history import make_history_entry
from src.topics import FocusSkill, pick_practice

st.set_page_config(
    page_title="Elocution Coach",
    page_icon="🎙️",
    layout="centered",
    initial_sidebar_state="collapsed",
)

CUSTOM_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Fraunces:opsz,wght@9..144,500;9..144,700&family=Source+Sans+3:wght@400;600&display=swap');

html, body, [class*="css"] {
  font-family: "Source Sans 3", sans-serif;
}
.hero-brand {
  font-family: "Fraunces", Georgia, serif;
  font-size: 2.4rem;
  font-weight: 700;
  color: #1B4D3E;
  letter-spacing: -0.02em;
  margin-bottom: 0.15rem;
}
.hero-sub {
  color: #4A5560;
  font-size: 1.05rem;
  margin-bottom: 1.5rem;
}
.topic-block {
  background: linear-gradient(145deg, #EDE8DF 0%, #E2D9CC 100%);
  border-left: 4px solid #1B4D3E;
  padding: 1.1rem 1.25rem;
  margin: 0.75rem 0 1rem 0;
}
.topic-label {
  font-size: 0.75rem;
  text-transform: uppercase;
  letter-spacing: 0.08em;
  color: #5C6B63;
  margin-bottom: 0.35rem;
}
.topic-text {
  font-family: "Fraunces", Georgia, serif;
  font-size: 1.35rem;
  color: #1A1A1A;
  line-height: 1.35;
}
.skill-chip {
  display: inline-block;
  margin-top: 0.75rem;
  font-size: 0.9rem;
  color: #1B4D3E;
  font-weight: 600;
}
.tip-text {
  color: #3D4A44;
  font-size: 0.95rem;
  margin-top: 0.4rem;
}
.score-big {
  font-family: "Fraunces", Georgia, serif;
  font-size: 3rem;
  color: #1B4D3E;
  line-height: 1;
}
div[data-testid="stMetricValue"] {
  font-family: "Fraunces", Georgia, serif;
}
</style>
"""


def init_state() -> None:
    if "topic" not in st.session_state:
        topic, skill = pick_practice()
        st.session_state.topic = topic
        st.session_state.skill = skill
    if "history" not in st.session_state:
        st.session_state.history = []
    if "last_result" not in st.session_state:
        st.session_state.last_result = None
    if "transcript" not in st.session_state:
        st.session_state.transcript = ""
    if "practice_id" not in st.session_state:
        st.session_state.practice_id = 0


def new_practice() -> None:
    topic, skill = pick_practice()
    st.session_state.topic = topic
    st.session_state.skill = skill
    st.session_state.last_result = None
    st.session_state.transcript = ""
    st.session_state.practice_id += 1


def render_header() -> None:
    st.markdown(CUSTOM_CSS, unsafe_allow_html=True)
    st.markdown('<div class="hero-brand">Elocution Coach</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="hero-sub">Practise articulate English — one topic, one skill, honest feedback.</div>',
        unsafe_allow_html=True,
    )


def render_topic(topic: str, skill: FocusSkill) -> None:
    st.markdown(
        f"""
        <div class="topic-block">
          <div class="topic-label">Your topic</div>
          <div class="topic-text">{topic}</div>
          <div class="skill-chip">Focus skill · {skill.name}</div>
          <div class="tip-text">{skill.tip}</div>
          <div class="tip-text"><em>Cue: {skill.cue}</em></div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_result(result) -> None:
    st.markdown("### Your rating")
    col_score, col_meta = st.columns([1, 2])
    with col_score:
        st.markdown(
            f'<div class="score-big">{result.overall}<span style="font-size:1.2rem">/10</span></div>',
            unsafe_allow_html=True,
        )
        st.caption(f"Scored via {result.source}")
    with col_meta:
        d = result.dimensions
        m1, m2, m3 = st.columns(3)
        m1.metric("Clarity", d.clarity)
        m2.metric("Structure", d.structure)
        m3.metric("Pace / fillers", d.pace_and_fillers)
        m4, m5, _ = st.columns(3)
        m4.metric("On topic", d.topic_connection)
        m5.metric("Focus skill", d.focus_skill)

    if result.overall_reason:
        st.caption(result.overall_reason)

    st.markdown("#### Score breakdown — why")
    breakdown = result.dimension_breakdown or []
    if breakdown:
        # Show weakest dimensions first so the learner knows what to practise.
        ordered = sorted(breakdown, key=lambda item: (item.score, item.label))
        for item in ordered:
            st.markdown(f"**{item.label} — {item.score}/10**  \n{item.reason}")
    else:
        st.caption("Detailed reasons were not available for this round.")

    st.markdown("#### Areas to improve")
    for item in result.improvements:
        st.markdown(f"- {item}")

    st.markdown("#### Stronger line to try")
    st.info(result.rewrite_tip)

    if result.notes:
        with st.expander("Coach notes"):
            for note in result.notes:
                st.write(f"· {note}")


def main() -> None:
    init_state()
    render_header()

    topic: str = st.session_state.topic
    skill: FocusSkill = st.session_state.skill

    top_cols = st.columns([1, 1])
    with top_cols[0]:
        if st.button("New practice", use_container_width=True, type="primary"):
            new_practice()
            st.rerun()
    with top_cols[1]:
        mode = "AI coach ready" if has_openai() else "Heuristic mode (add OPENAI_API_KEY for richer feedback)"
        st.caption(mode)

    render_topic(topic, skill)

    st.markdown("Speak for about **1–2 minutes**. Record below, or paste a transcript.")

    practice_id = st.session_state.practice_id
    audio_key = f"practice_audio_{practice_id}"
    transcript_key = f"practice_transcript_{practice_id}"

    audio = None
    if hasattr(st, "audio_input"):
        audio = st.audio_input("Record your practice", key=audio_key)
    else:
        st.warning("This Streamlit version has no audio input — paste a transcript instead.")

    transcript_input = st.text_area(
        "Or paste your transcript",
        key=transcript_key,
        height=140,
        placeholder="Paste what you said here if you prefer typing, or after recording…",
    )

    if st.button("Rate my elocution", type="primary", use_container_width=True):
        transcript = (transcript_input or "").strip()
        with st.spinner("Listening and coaching…"):
            if audio is not None and hasattr(audio, "getvalue"):
                audio_bytes = audio.getvalue()
                if audio_bytes and has_openai():
                    try:
                        transcript = transcribe_audio(audio_bytes, getattr(audio, "name", "recording.wav"))
                    except Exception as exc:  # noqa: BLE001
                        st.error(f"Could not transcribe audio: {exc}")
                        if not transcript:
                            st.stop()
                elif audio_bytes and not transcript:
                    st.warning(
                        "Audio recorded, but no API key for transcription. "
                        "Paste a transcript or set OPENAI_API_KEY."
                    )
                    st.stop()

            if not transcript:
                st.warning("Add a recording (with API key) or paste a transcript first.")
                st.stop()

            st.session_state.transcript = transcript
            result = coach_transcript(transcript, topic, skill)
            st.session_state.last_result = result
            st.session_state.history.insert(
                0,
                make_history_entry(topic, skill, result, transcript),
            )
            st.session_state.history = st.session_state.history[:12]

    if st.session_state.transcript:
        with st.expander("Transcript", expanded=False):
            st.write(st.session_state.transcript)

    if st.session_state.last_result is not None:
        render_result(st.session_state.last_result)

    if st.session_state.history:
        st.markdown("### This session")
        for entry in st.session_state.history:
            st.markdown(
                f"**{entry['overall']}/10** · {entry['skill']} · {entry['time']}  \n"
                f"{entry['topic']}"
            )


if __name__ == "__main__":
    main()
