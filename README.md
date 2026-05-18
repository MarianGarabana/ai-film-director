# 🎬 AI Film Director

A Streamlit app that turns cinematic parameters into AI-generated videos. Built as a university GenAI course project.

---

## Two modes — pick what you have

| | Easy mode | Full mode |
|---|---|---|
| **What you need** | Google API key only | Google API key + GCP project |
| **Video model** | Veo 2 | Veo 3.1 |
| **Audio & dialogue** | ❌ | ✅ |
| **Setup time** | ~5 minutes | ~20 minutes |
| **Cost** | Free tier available | GCP billing required |

Start with Easy mode if you're new. Upgrade to Full mode when you want Veo 3 + audio.

---

## How it works

**Stage 1 — Prompt engineering (Gemini 2.5 Flash)**
Fill in the cinematic form: subject, action, scene, camera angle, movement, visual style, lens effect, optional dialogue. Gemini synthesises all of them into a single production-ready Veo prompt — every keyword included, no invented concepts.

**Stage 2 — Video generation**
- *Easy mode*: sends the prompt to Veo 2 via Google AI API (your key, your quota)
- *Full mode*: sends to Veo 3.1 on Vertex AI (your GCP project, your billing)

The app polls every 15 seconds and shows a live progress bar. When done, the video plays inline in a screening room with metadata chips. Download as `.mp4` or save to GCS.

---

## Setup — Easy mode (beginners, start here)

### Step 1 — Create a Google account
If you don't have one: [accounts.google.com/signup](https://accounts.google.com/signup). Free, takes 2 minutes.

### Step 2 — Get a Google AI Studio API key
1. Go to [aistudio.google.com](https://aistudio.google.com)
2. Sign in with your Google account
3. Click **Get API key** → **Create API key**
4. Copy the key (starts with `AIza...`) — save it somewhere safe

### Step 3 — Install Python
If you don't have Python: download it at [python.org/downloads](https://www.python.org/downloads). Install version **3.10 or newer**.

To check if Python is already installed, open a terminal and run:
```bash
python --version
```

### Step 4 — Download and run the app

```bash
# Clone the repo
git clone https://github.com/MarianGarabana/ai-film-director.git
cd ai-film-director

# Install dependencies
pip install -r requirements.txt

# Run the app
streamlit run app_film_director.py
```

Your browser will open automatically at `http://localhost:8501`.

### Step 5 — Use the app
1. Paste your API key in the sidebar under **Google API Key**
2. Leave **GCP Project ID** empty
3. Fill in the scene parameters (or click a preset)
4. Click **Generate cinematic prompt**, then **Generate video**
5. Wait ~2 minutes — Veo 2 is rendering your scene

---

## Setup — Full mode (Veo 3 + audio)

Requires a Google Cloud account with billing enabled and Veo 3 access approved.

### Step 1 — Complete Easy mode setup first

### Step 2 — Create a Google Cloud account
1. Go to [cloud.google.com](https://cloud.google.com) → **Get started for free**
2. A credit card is required for verification (free tier gives $300 in credits)

### Step 3 — Create a GCP project
1. Go to [console.cloud.google.com](https://console.cloud.google.com)
2. Click the project dropdown at the top → **New Project**
3. Name it (e.g. `my-veo-project`) → **Create**
4. Note your **Project ID** (shown under the project name)

### Step 4 — Enable Vertex AI API
1. In GCP Console, go to **APIs & Services → Library**
2. Search `Vertex AI API` → click it → **Enable**

### Step 5 — Request Veo 3 access
Veo 3 requires allowlisting. Fill out the request form in the [Vertex AI console](https://console.cloud.google.com/vertex-ai). Google typically approves within a few days.

### Step 6 — Install and authenticate gcloud CLI
1. Download at [cloud.google.com/sdk/docs/install](https://cloud.google.com/sdk/docs/install)
2. Run:
```bash
gcloud auth application-default login
```
This opens a browser — sign in with the Google account that owns your GCP project.

### Step 7 — Use the app
Same as Easy mode, but enter your **Project ID** in the sidebar. The app automatically switches to Veo 3 + audio.

---

## Key features

| Feature | Detail |
|---|---|
| **Cinematic parameter form** | Subject, action, scene, camera angle, movement, visual style, lens effect, dialogue |
| **Style presets** | One-click presets: Noir Thriller, Sci-Fi Epic, Documentary |
| **Prompt editor** | Gemini output is fully editable before sending to Veo |
| **Prompt history** | Last 5 engineered prompts saved per session, restorable with one click |
| **Live progress bar** | Animated gradient bar with elapsed time during generation |
| **Screening room** | Inline video player with model metadata chips |
| **GCS export** | Save generated video to Google Cloud Storage (Full mode) |
| **Cinematic dark UI** | Charcoal background, IMDb-gold accents, Inter + JetBrains Mono fonts |

---

## What I learned in class and applied here

### 1. Multi-model pipelines
Two models in sequence: Gemini 2.5 Flash preprocesses and structures the input; Veo generates the final video. Core pattern in production GenAI systems.

### 2. Prompt engineering
Constructing system prompts that constrain output precisely — forcing inclusion of all keywords, forbidding hallucinated concepts, enforcing output format. The meta-prompt sent to Gemini is itself an exercise in prompt engineering.

### 3. Two authentication modes in the Google GenAI ecosystem
- **API key** — used for Gemini and Veo 2 via Google AI Studio (simple, no GCP needed)
- **Application Default Credentials (ADC)** — used for Veo 3 on Vertex AI (requires a GCP project and `gcloud auth application-default login`)

### 4. Asynchronous long-running operations
Video generation takes 1–4 minutes. The API returns an `Operation` object immediately; the app polls `veo_client.operations.get(operation)` every 15 seconds until `operation.done` is `True`. Standard pattern for long-running AI workloads on GCP.

### 5. Cloud storage integration
Writing generated binary data directly to Google Cloud Storage using `google-cloud-storage`, constructing timestamped paths, returning `gs://` URIs.

### 6. Streamlit for rapid GenAI prototyping
Stateful multi-step UI with `st.session_state`, `st.empty()` for dynamic updates, conditional rendering, custom theme via `.streamlit/config.toml` — no backend server.

---

## Sidebar controls

| Control | Effect |
|---|---|
| Google API Key | Required for Gemini (both modes) and Veo 2 (Easy mode) |
| GCP Project ID | Optional — leave empty for Easy mode, fill for Full mode (Veo 3) |
| Veo 3 Fast toggle | Full mode only — `veo-3.1-fast-generate-001` (~1–2 min) vs `veo-3.1-generate-001` (~2–4 min) |
| Duration | 4, 6, or 8 seconds |
| Aspect ratio | 16:9 (landscape) or 9:16 (vertical/mobile) |
| Resolution | 720p or 1080p |
| Auto-enhance prompt | Lets Veo's built-in enhancer refine the prompt further |
| Generate audio | Full mode only — enables Veo 3's native audio and dialogue |

---

## Tech stack

| Layer | Technology |
|---|---|
| UI | [Streamlit](https://streamlit.io) |
| Prompt engineering | Gemini 2.5 Flash via `google-genai` SDK |
| Video (Easy mode) | Veo 2 (`veo-2.0-generate-001`) via Google AI API key |
| Video (Full mode) | Veo 3.1 (`veo-3.1-fast-generate-001`) via Vertex AI |
| Cloud storage | Google Cloud Storage (`google-cloud-storage`) |

---

## Project structure

```
ai-film-director/
├── app_film_director.py   # Main Streamlit app
├── .streamlit/
│   └── config.toml        # Cinematic dark theme
├── requirements.txt
└── .gitignore
```

---

## Troubleshooting

**`403 PERMISSION_DENIED` on Veo 3**
Your service account or ADC credentials lack the Vertex AI User role. Go to GCP IAM → grant `roles/aiplatform.user` to your principal.

**`404 NOT_FOUND` for Veo model**
Veo 3 is not accessible via API key — enter a GCP Project ID in the sidebar to switch to Vertex AI mode.

**`generate_audio` parameter error**
Audio is only supported in Full mode (Vertex AI). Leave GCP Project ID empty to use Easy mode, or fill it in to enable audio.

**App won't start**
Make sure Python 3.10+ is installed and all dependencies are installed: `pip install -r requirements.txt`

---

*Built for the Generative AI Applications course — Marian Garabana, 2025*
