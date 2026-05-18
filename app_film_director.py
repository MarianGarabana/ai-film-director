import time
import streamlit as st
from datetime import datetime
from google import genai
from google.genai import types
from google.cloud import storage

import json, os
if "gcp" in st.secrets:
    info = json.loads(st.secrets["gcp"]["GOOGLE_APPLICATION_CREDENTIALS_JSON"])
    with open("/tmp/gcp_key.json", "w") as f:
        json.dump(info, f)
    os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "/tmp/gcp_key.json"
def save_video_to_gcs(bucket_name, data):
    try:
        client = storage.Client(project=bucket_name)
        bucket = client.bucket(bucket_name)
        filename = f"film-director/{datetime.now().strftime('%Y%m%d_%H%M%S')}.mp4"
        blob = bucket.blob(filename)
        blob.upload_from_string(data, content_type="video/mp4")
        return f"gs://{bucket_name}/{filename}"
    except Exception as e:
        return f"Error: {e}"


# ── Page config ────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="AI Film Director",
    page_icon=":material/movie:",
    layout="wide",
)

# ── CSS (only what config.toml can't do) ───────────────────────────────────────
st.html("""<style>
/* Primary button: gold bg needs dark text for contrast */
button[kind="primary"] {
    color: #0f0f0f !important;
    font-weight: 700 !important;
}
/* Step badge */
.fd-step {
    display: flex;
    align-items: center;
    gap: 12px;
    margin: 8px 0 2px;
}
.fd-step-num {
    width: 32px;
    height: 32px;
    background: #f5c518;
    color: #0f0f0f;
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
    font-weight: 800;
    font-size: 15px;
    flex-shrink: 0;
}
.fd-step-label {
    color: #f5c518;
    font-size: 18px;
    font-weight: 700;
    letter-spacing: -0.3px;
}
/* Prompt textarea → screenplay feel */
[data-testid="stTextArea"] textarea {
    font-family: 'JetBrains Mono', 'Fira Code', monospace !important;
    line-height: 1.75 !important;
    font-size: 13px !important;
}
/* Progress bar */
.fd-progress-wrap {
    border-radius: 8px;
    padding: 14px 18px;
    margin: 4px 0;
    background: #1a1a1a;
    border: 1px solid #2a2a2a;
}
.fd-progress-label {
    font-size: 13px;
    margin-bottom: 10px;
    display: flex;
    justify-content: space-between;
    color: #aaa;
}
.fd-progress-track {
    border-radius: 4px;
    height: 6px;
    overflow: hidden;
    background: #2a2a2a;
}
.fd-progress-fill {
    height: 6px;
    background: linear-gradient(90deg, #f5c518, #ff8c00);
    border-radius: 4px;
}
/* Metadata chips */
.fd-chips {
    display: flex;
    flex-wrap: wrap;
    gap: 8px;
    margin-top: 12px;
    padding-bottom: 4px;
}
.fd-chip {
    border-radius: 20px;
    padding: 4px 12px;
    font-size: 12px;
    color: #888;
    border: 1px solid #2a2a2a;
    background: #1a1a1a;
}
.fd-chip b { color: #f5c518; }
</style>""")

# ── Header ─────────────────────────────────────────────────────────────────────
st.title(":material/movie: AI Film Director")
st.caption(
    "Gemini 2.5 Flash engineers your cinematic prompt · "
    "Veo 3 generates the scene with audio"
)

# ── Sidebar ────────────────────────────────────────────────────────────────────
with st.sidebar:
    st.subheader(":material/settings: Settings")

    st.caption("AUTHENTICATION")
    api_key = st.text_input(
        "Google API Key", type="password", placeholder="AIza...",
        help="Used by Gemini for prompt engineering."
    )
    project_id = st.text_input(
        "GCP Project ID", value="genai-marian",
        help="Used by Veo 3 (Vertex AI)."
    )

    st.warning(
        "**Veo 3 requires Vertex AI ADC.**\n\n"
        "Run once in your terminal:\n\n"
        "```\ngcloud auth application-default login\n```",
        icon=":material/warning:",
    )

    st.caption("GENERATION")
    use_fast_model = st.toggle("Veo 3 Fast (lower latency)", value=True)
    duration = st.select_slider("Duration (seconds)", options=[4, 6, 8], value=6)
    aspect_ratio = st.radio("Aspect ratio", ["16:9", "9:16"], horizontal=True)
    resolution = st.selectbox("Resolution", ["720p", "1080p"], index=0)
    enhance_prompt = st.toggle("Auto-enhance prompt (Veo built-in)", value=True)
    generate_audio = st.toggle("Generate audio & dialogue", value=True)

    st.caption("EXPECTED WAIT TIMES")
    st.caption("**Veo 3 Fast:** ~1–2 min &nbsp;&nbsp;·&nbsp;&nbsp; **Veo 3 Pro:** ~2–4 min")

# ── Session state ──────────────────────────────────────────────────────────────
st.session_state.setdefault("engineered_prompt", "")
st.session_state.setdefault("video_bytes", None)
st.session_state.setdefault("prompt_history", [])
st.session_state.setdefault("last_video_meta", {})

# ── Style presets ──────────────────────────────────────────────────────────────
PRESETS = {
    "🕵️ Noir Thriller": {
        "fd_subject": "a weary detective",
        "fd_action": "examines a crime scene in silence",
        "fd_scene": "rain-soaked neon alley at midnight",
        "fd_camera_angle": "Low-Angle Shot",
        "fd_camera_movement": "Dolly (In)",
        "fd_style": "Film Noir",
        "fd_lens": "Shallow Depth of Field",
        "fd_dialogue": "",
    },
    "🚀 Sci-Fi Epic": {
        "fd_subject": "a lone astronaut",
        "fd_action": "discovers a glowing alien artifact",
        "fd_scene": "the desolate surface of an alien planet",
        "fd_camera_angle": "Wide Shot",
        "fd_camera_movement": "Crane Shot",
        "fd_style": "Sci-Fi",
        "fd_lens": "Lens Flare",
        "fd_dialogue": "This changes everything.",
    },
    "🎙️ Documentary": {
        "fd_subject": "an elderly craftsman",
        "fd_action": "carefully restores an antique clock",
        "fd_scene": "a dusty workshop filled with timepieces",
        "fd_camera_angle": "Close-Up",
        "fd_camera_movement": "Static Shot",
        "fd_style": "Documentary",
        "fd_lens": "Rack Focus",
        "fd_dialogue": "",
    },
}

_preset_cols = st.columns(len(PRESETS))
for _col, (_name, _vals) in zip(_preset_cols, PRESETS.items()):
    with _col:
        if st.button(_name, key=f"preset_{_name}", use_container_width=True):
            for k, v in _vals.items():
                st.session_state[k] = v
            st.session_state["engineered_prompt"] = ""
            st.session_state["video_bytes"] = None
            st.rerun()

# ── Scene parameters ───────────────────────────────────────────────────────────
st.markdown(
    '<div class="fd-step">'
    '<div class="fd-step-num">🎭</div>'
    '<div class="fd-step-label">Scene parameters</div>'
    '</div>',
    unsafe_allow_html=True,
)

with st.container(border=True):
    col1, col2 = st.columns(2)

    with col1:
        subject = st.text_input(
            "Subject",
            placeholder="a seasoned detective, a robot chef, a lone astronaut…",
            key="fd_subject",
        )
        action = st.text_input(
            "Action",
            placeholder="piecing together clues, plating ramen perfectly, floating in silence…",
            key="fd_action",
        )
        scene = st.text_input(
            "Scene / Setting",
            placeholder="in a rain-soaked neon alley, a tiny Tokyo kitchen, the surface of Mars…",
            key="fd_scene",
        )
        dialogue = st.text_input(
            "Dialogue (optional)",
            placeholder="'I've been expecting you.' / 'This changes everything.'",
            key="fd_dialogue",
        )

    with col2:
        camera_angle = st.selectbox(
            "Camera angle",
            [
                "None", "Eye-Level Shot", "Low-Angle Shot", "High-Angle Shot",
                "Bird's-Eye View", "Dutch Angle", "Close-Up", "Extreme Close-Up",
                "Medium Shot", "Over-the-Shoulder Shot", "Wide Shot", "Establishing Shot",
            ],
            key="fd_camera_angle",
        )
        camera_movement = st.selectbox(
            "Camera movement",
            [
                "None", "Static Shot", "Pan (left)", "Pan (right)",
                "Dolly (In)", "Dolly (Out)", "Zoom (In)", "Zoom (Out)",
                "Handheld", "Arc Shot", "Crane Shot", "Whip Pan",
            ],
            key="fd_camera_movement",
        )
        style = st.selectbox(
            "Visual style",
            [
                "None", "Cinematic", "Photorealistic", "Film Noir",
                "Documentary", "Sci-Fi", "Fantasy", "Neo-Noir",
                "Vintage 35mm Film", "Animation",
            ],
            key="fd_style",
        )
        lens_effect = st.selectbox(
            "Lens effect",
            [
                "None", "Shallow Depth of Field", "Bokeh", "Wide-Angle (24mm)",
                "Telephoto (85mm)", "Lens Flare", "Rack Focus", "Fisheye",
            ],
            key="fd_lens",
        )

st.markdown("<br>", unsafe_allow_html=True)

# ── Step 1: Engineer the prompt ────────────────────────────────────────────────
st.markdown(
    '<div class="fd-step">'
    '<div class="fd-step-num">1</div>'
    '<div class="fd-step-label">Engineer your prompt with Gemini 2.5 Flash</div>'
    '</div>',
    unsafe_allow_html=True,
)

engineer_clicked = st.button(
    "Generate cinematic prompt",
    icon=":material/edit:",
    type="secondary",
    disabled=not (subject and action),
)

if engineer_clicked:
    if not api_key:
        st.error("Enter your Google API Key in the sidebar.")
        st.stop()

    # Collect keywords — skip "None" values
    core_keywords = [k for k in [subject, action, scene] if k.strip()]
    optional_keywords = [
        k for k in [camera_angle, camera_movement, style, lens_effect]
        if k and k != "None"
    ]
    all_keywords = core_keywords + optional_keywords
    if dialogue.strip():
        all_keywords.append(f'Character says: "{dialogue.strip()}"')

    gemini_prompt = (
        "You are an expert video prompt engineer for Google's Veo 3 model. "
        "Your task is to construct the most effective and cinematic prompt string "
        "using the following keywords. Every single keyword MUST be included. "
        "Synthesize them into a single, cohesive, vivid cinematic instruction. "
        "Do NOT add new core concepts not present in the keywords. "
        "Output ONLY the final prompt string — no intro, no explanation.\n\n"
        f"Mandatory Keywords: {', '.join(all_keywords)}"
    )

    with st.spinner("Gemini 2.5 Flash is writing your cinematic prompt…"):
        try:
            gemini_client = genai.Client(api_key=api_key)
            response = gemini_client.models.generate_content(
                model="gemini-2.5-flash",
                contents=gemini_prompt,
            )
            new_prompt = response.text.strip()
            st.session_state.engineered_prompt = new_prompt
            st.session_state.video_bytes = None  # reset old video on new prompt
            if new_prompt and new_prompt not in st.session_state.prompt_history:
                st.session_state.prompt_history.insert(0, new_prompt)
                st.session_state.prompt_history = st.session_state.prompt_history[:5]
        except Exception as e:
            st.error(f"Prompt engineering error: {e}")

# Editable prompt box
if st.session_state.engineered_prompt:
    st.session_state.engineered_prompt = st.text_area(
        "Engineered prompt (editable)",
        value=st.session_state.engineered_prompt,
        height=130,
        key="prompt_editor",
    )

    if len(st.session_state.prompt_history) > 1:
        with st.expander(
            f"Prompt history ({len(st.session_state.prompt_history)} saved)",
            icon=":material/history:",
        ):
            for i, p in enumerate(st.session_state.prompt_history):
                col_h, col_restore = st.columns([5, 1])
                with col_h:
                    st.caption(f"#{i + 1} · {p[:120]}{'…' if len(p) > 120 else ''}")
                with col_restore:
                    if st.button("Use", key=f"restore_{i}"):
                        st.session_state.engineered_prompt = p
                        st.rerun()

st.markdown("<br>", unsafe_allow_html=True)

# ── Step 2: Generate video ─────────────────────────────────────────────────────
st.markdown(
    '<div class="fd-step">'
    '<div class="fd-step-num">2</div>'
    '<div class="fd-step-label">Generate video with Veo 3</div>'
    '</div>',
    unsafe_allow_html=True,
)

model_id = "veo-3.1-fast-generate-001" if use_fast_model else "veo-3.1-generate-001"
expected_seconds = 90 if use_fast_model else 210

st.badge(
    model_id,
    icon=":material/bolt:" if use_fast_model else ":material/hd:",
    color="orange" if use_fast_model else "blue",
)

generate_clicked = st.button(
    "Generate video",
    icon=":material/movie:",
    type="primary",
    disabled=not st.session_state.engineered_prompt,
)

if generate_clicked:
    if not project_id:
        st.error("Enter your GCP Project ID in the sidebar (needed for Veo 3 / Vertex AI).")
        st.stop()

    status_box = st.empty()
    status_box.info(f"Submitting to **{model_id}**…", icon=":material/movie:")

    try:
        # Veo 3 runs on us-central1, not global
        veo_client = genai.Client(
            vertexai=True, project=project_id, location="us-central1"
        )

        operation = veo_client.models.generate_videos(
            model=model_id,
            prompt=st.session_state.engineered_prompt,
            config=types.GenerateVideosConfig(
                aspect_ratio=aspect_ratio,
                number_of_videos=1,
                duration_seconds=duration,
                resolution=resolution,
                person_generation="allow_adult",
                enhance_prompt=enhance_prompt,
                generate_audio=generate_audio,
            ),
        )

        # Poll until done
        elapsed = 0
        while not operation.done:
            time.sleep(15)
            elapsed += 15
            operation = veo_client.operations.get(operation)
            pct = min(int((elapsed / expected_seconds) * 100), 95)
            status_box.markdown(
                f'<div class="fd-progress-wrap">'
                f'<div class="fd-progress-label">'
                f'<span>Generating with <strong style="color:#e0e0e0">{model_id}</strong>…</span>'
                f'<span style="color:#f5c518;font-weight:600">{elapsed}s elapsed</span>'
                f'</div>'
                f'<div class="fd-progress-track">'
                f'<div class="fd-progress-fill" style="width:{pct}%"></div>'
                f'</div>'
                f'</div>',
                unsafe_allow_html=True,
            )

        status_box.empty()

        if operation.response:
            video = operation.result.generated_videos[0]
            st.session_state.video_bytes = video.video.video_bytes
            st.session_state.last_video_meta = {
                "model": model_id,
                "duration": f"{duration}s",
                "aspect ratio": aspect_ratio,
                "resolution": resolution,
                "audio": "yes" if generate_audio else "no",
                "generated": datetime.now().strftime("%H:%M:%S"),
            }
            st.success("Video ready!", icon=":material/check_circle:")
        else:
            st.error("Generation completed but returned no video. Check your GCP quota.")

    except Exception as e:
        st.error(f"Video generation error: {e}")

# ── Screening room ─────────────────────────────────────────────────────────────
if st.session_state.video_bytes:
    st.markdown(
        '<div class="fd-step">'
        '<div class="fd-step-num">🎞️</div>'
        '<div class="fd-step-label">Screening room</div>'
        '</div>',
        unsafe_allow_html=True,
    )

    with st.container(border=True):
        st.video(st.session_state.video_bytes)

        if st.session_state.last_video_meta:
            chips_html = "".join(
                f'<div class="fd-chip">{k}: <b>{v}</b></div>'
                for k, v in st.session_state.last_video_meta.items()
            )
            st.markdown(
                f'<div class="fd-chips">{chips_html}</div>',
                unsafe_allow_html=True,
            )

    col_dl, col_gcs = st.columns(2)
    with col_dl:
        st.download_button(
            label="⬇️ Download video (.mp4)",
            data=st.session_state.video_bytes,
            file_name="ai_film_director.mp4",
            mime="video/mp4",
            use_container_width=True,
        )
    with col_gcs:
        if st.button("☁️ Save to GCS", use_container_width=True):
            gcs_path = save_video_to_gcs(project_id, st.session_state.video_bytes)
            if gcs_path.startswith("gs://"):
                st.toast(f"Saved: `{gcs_path}`", icon=":material/check:")
            else:
                st.error(gcs_path)
