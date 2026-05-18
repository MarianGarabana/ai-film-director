# 🎬 AI Film Director

A Streamlit app that turns cinematic parameters into fully-produced AI-generated videos — with dialogue, sound design, and a custom score. Built as a university GenAI course project.

---

## What it does

The app works in two stages:

**Stage 1 — Prompt Engineering with Gemini 2.5 Flash**  
You fill in cinematic parameters: subject, action, scene/setting, camera angle, camera movement, visual style, lens effect, and optional dialogue. Gemini 2.5 Flash synthesises all of them into a single coherent, production-ready Veo prompt — ensuring every keyword is used without adding concepts you didn't ask for.

**Stage 2 — Video Generation with Veo 3**  
The engineered prompt is sent to Google's Veo 3 model on Vertex AI. The app polls asynchronously and shows a live progress bar while the model renders. When done, the video plays back in a built-in screening room with metadata chips (model, resolution, duration, audio). You can download the `.mp4` or save it directly to Google Cloud Storage.

---

## Key features

| Feature | Detail |
|---|---|
| **Cinematic parameter form** | Subject, action, scene, camera angle, movement, visual style, lens effect, dialogue |
| **Style presets** | One-click presets: Noir Thriller, Sci-Fi Epic, Documentary |
| **Prompt editor** | Gemini output is fully editable before sending to Veo |
| **Prompt history** | Last 5 engineered prompts saved in session, restorable with one click |
| **Live progress bar** | Animated gradient bar with elapsed time during Veo polling |
| **Screening room** | Inline video player with model metadata chips |
| **GCS export** | Save generated video to a Google Cloud Storage bucket |
| **Cinematic dark UI** | Custom theme: charcoal background, IMDb-gold accents, Inter + JetBrains Mono fonts |

---

## What I learned in class and applied here

### 1. Multi-model pipelines
Using two models in sequence — a language model (Gemini 2.5 Flash) to preprocess and structure the input, and a generative video model (Veo 3) to produce the final output. This is a core pattern in production GenAI systems.

### 2. Prompt engineering
Constructing system prompts that constrain model output precisely: forcing inclusion of all input keywords, forbidding hallucinated concepts, and specifying output format. The meta-prompt sent to Gemini is itself an exercise in prompt engineering.

### 3. Two authentication modes in the Google GenAI ecosystem
- **API key** (`google-genai` client) — used for Gemini (available via Google AI Studio)
- **Application Default Credentials (ADC)** — used for Veo 3 on Vertex AI, which requires a GCP project and `gcloud auth application-default login`

### 4. Asynchronous long-running operations
Veo 3 generation takes 1–4 minutes. The API returns an `Operation` object immediately; the app polls `veo_client.operations.get(operation)` every 15 seconds until `operation.done` is `True`. This is the standard pattern for long-running AI workloads on GCP.

### 5. Cloud storage integration
Writing generated binary data (video bytes) directly to Google Cloud Storage using `google-cloud-storage`, constructing timestamped paths, and returning `gs://` URIs.

### 6. Streamlit for rapid GenAI prototyping
Building an interactive, stateful multi-step UI with `st.session_state`, `st.empty()` placeholders for dynamic updates, conditional rendering, and a custom theme via `.streamlit/config.toml` — all without a backend server.

---

## Tech stack

| Layer | Technology |
|---|---|
| UI | [Streamlit](https://streamlit.io) |
| Prompt engineering | Gemini 2.5 Flash (`gemini-2.5-flash`) via `google-genai` SDK |
| Video generation | Veo 3 (`veo-3.1-fast-generate-001` / `veo-3.1-generate-001`) via Vertex AI |
| Cloud storage | Google Cloud Storage (`google-cloud-storage`) |
| Auth (Gemini) | Google API key |
| Auth (Veo 3) | Application Default Credentials (ADC) |

---

## Prerequisites

- Python 3.10+
- A **Google API key** with access to Gemini 2.5 Flash ([get one at Google AI Studio](https://aistudio.google.com))
- A **GCP project** with Vertex AI API enabled and Veo 3 access
- `gcloud` CLI installed and authenticated:

```bash
gcloud auth application-default login
```

---

## Installation

```bash
git clone https://github.com/MarianGarabana/ai-film-director.git
cd ai-film-director
pip install -r requirements.txt
streamlit run app_film_director.py
```

---

## Usage

1. Enter your **Google API Key** and **GCP Project ID** in the sidebar
2. (Optional) Click a **style preset** to auto-fill the form, or fill in your own parameters
3. Click **Generate cinematic prompt** — Gemini engineers the Veo prompt from your inputs
4. Review and optionally edit the prompt in the text area
5. Click **Generate video** — Veo 3 renders the scene (1–4 min)
6. Watch the result in the **Screening room**, then download or save to GCS

### Sidebar controls

| Control | Effect |
|---|---|
| Veo 3 Fast toggle | Switches between `veo-3.1-fast-generate-001` (~1–2 min) and `veo-3.1-generate-001` (~2–4 min) |
| Duration | 4, 6, or 8 seconds |
| Aspect ratio | 16:9 (landscape) or 9:16 (vertical/mobile) |
| Resolution | 720p or 1080p |
| Auto-enhance prompt | Lets Veo's built-in enhancer further refine the prompt |
| Generate audio | Enables Veo 3's native audio and dialogue generation |

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

## Notes

- Veo 3 access requires allowlisting on your GCP project. Request access via the [Vertex AI console](https://console.cloud.google.com/vertex-ai).
- Generated videos are held in memory (`st.session_state`) for the duration of the browser session. Use the download or GCS save buttons to persist them.
- The GCS save button uses the same project ID entered for Veo. The bucket must already exist and your ADC credentials must have write access.

---

*Built for the Generative AI Applications course — Marian Garabana, 2025*
