# Elocution Coach

A simple Streamlit app for practising articulate spoken English. Get a random topic, focus on one communication skill, speak for 1–2 minutes, and receive a score with concrete areas to improve.

Built for non-native English speakers in the UK who want clearer, more confident communication. Coaching draws on well-known public principles (simplicity, connecting, storytelling, conviction, preparation) — paraphrased for practice, not copied from any book.

## Features

- Random practice topics (everyday UK life, work, opinions, storytelling)
- One focus skill per round with a short prep tip
- Record audio in the browser or paste a transcript
- AI coaching via OpenAI (Whisper transcription + structured feedback) when an API key is set
- Heuristic fallback scoring if no API key is available
- Light in-session history of recent rounds

## Run locally

```bash
python -m venv .venv

# Windows
.venv\Scripts\activate

# macOS / Linux
source .venv/bin/activate

pip install -r requirements.txt
copy .env.example .env   # Windows
# cp .env.example .env   # macOS / Linux
```

Edit `.env` and set your key:

```
OPENAI_API_KEY=sk-your-key-here
```

Then start the app:

```bash
streamlit run app.py
```

Open the URL Streamlit prints (usually http://localhost:8501).

Without an API key the app still runs: paste a transcript and use heuristic scoring. With a key, you can record audio for Whisper transcription and richer AI feedback.

## Deploy on Streamlit Community Cloud (from GitHub)

1. Create a GitHub repository and push this project (include `app.py`, `requirements.txt`, `src/`, and `.streamlit/config.toml`; do **not** commit `.env`).
2. Go to [share.streamlit.io](https://share.streamlit.io) and sign in with GitHub.
3. Click **New app**, select your repo, branch (e.g. `main`), and set the main file path to `app.py`.
4. Under **Advanced settings** / **Secrets**, add:

```toml
OPENAI_API_KEY = "sk-your-key-here"
```

5. Deploy. Streamlit Cloud will install dependencies from `requirements.txt` and run the app.

Optional: set `OPENAI_MODEL` in secrets or the environment (default `gpt-4o-mini`).

## Project layout

```
app.py                 # Streamlit UI
requirements.txt
.env.example
.streamlit/config.toml
src/
  topics.py            # Topics + focus skills
  coach.py             # OpenAI transcription & coaching
  scoring.py           # Heuristic fallback
  history.py           # Session history helpers
```

## Privacy note

When AI mode is enabled, audio/transcripts are sent to OpenAI for transcription and coaching. Do not record sensitive personal information.
