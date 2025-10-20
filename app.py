import streamlit as st
import os
import ffmpeg
import whisper
from transformers import pipeline
import sys
import yt_dlp
import re
import time
from urllib.parse import urlparse, parse_qs 

# --- Backend Functions ---

def clean_vtt_text(vtt_content):
    """A helper function to clean VTT subtitle text."""
    lines = vtt_content.splitlines()
    cleaned_lines = []
    for line in lines:
        if "WEBVTT" in line or "::cue" in line or "->" in line:
            continue
        line = re.sub(r'<[^>]+>', '', line)
        if line.strip():
            cleaned_lines.append(line.strip())
    return " ".join(dict.fromkeys(cleaned_lines))

def process_youtube_link(url):
    """
    Intelligently handles complex YouTube URLs, checks for subtitles, and processes the video.
    Returns a tuple: (type, data) where type is 'text' or 'audio_path'.
    """
    # --- NEW: Parse the URL to extract only the video ID ---
    try:
        parsed_url = urlparse(url)
        video_id = parse_qs(parsed_url.query)['v'][0]
        # Reconstruct a clean URL
        clean_url = f"https://www.youtube.com/watch?v={video_id}"
    except (KeyError, IndexError):
        return "error", "Invalid YouTube URL. Please make sure it's a valid video URL."
    # --- END NEW ---

    ydl_opts_check = {'quiet': True, 'skip_download': True, 'noplaylist': True} # Add noplaylist
    
    with yt_dlp.YoutubeDL(ydl_opts_check) as ydl:
        info_dict = ydl.extract_info(clean_url, download=False)
        video_id = info_dict.get('id')
        
        available_subs = info_dict.get('subtitles', {})
        available_auto_caps = info_dict.get('automatic_captions', {})
        
        lang_code = ''
        if 'en' in available_subs:
            lang_code = 'en'
        elif 'en' in available_auto_caps:
            lang_code = 'en'

        if lang_code:
            st.info("✅ English transcript found! Using the fast path.")
            ydl_opts_sub = {
                'writesubtitles': True,
                'subtitleslangs': [lang_code],
                'skip_download': True,
                'outtmpl': f'{video_id}.subs',
                'quiet': True,
                'noplaylist': True,
            }
            with yt_dlp.YoutubeDL(ydl_opts_sub) as ydl_sub:
                ydl_sub.download([clean_url])
            
            subtitle_filename = f"{video_id}.subs.{lang_code}.vtt"
            if os.path.exists(subtitle_filename):
                with open(subtitle_filename, 'r', encoding='utf-8') as f:
                    transcript_text = f.read()
                os.remove(subtitle_filename)
                return "text", clean_vtt_text(transcript_text)
    
    st.info("❌ No English transcript found. Falling back to audio transcription.")
    ydl_opts_audio = {
        'format': 'm4a/bestaudio/best', 
        'outtmpl': f'{video_id}.%(ext)s',
        'postprocessors': [{'key': 'FFmpegExtractAudio', 'preferredcodec': 'mp3', 'preferredquality': '192'}],
        'quiet': True,
        'noplaylist': True, # Ensure we don't download the whole playlist
    }
    with yt_dlp.YoutubeDL(ydl_opts_audio) as ydl_audio:
        ydl_audio.download([clean_url])
    audio_file_path = f"{video_id}.mp3"
    if os.path.exists(audio_file_path):
        return "audio_path", audio_file_path
    else:
        return "error", "Failed to download audio."

# (The other functions: get_audio_from_file, transcribe_audio, summarize_text remain the same)
def get_audio_from_file(uploaded_file):
    video_file_path = uploaded_file.name
    with open(video_file_path, "wb") as f:
        f.write(uploaded_file.getbuffer())
    audio_file_path = "temp_audio.mp3"
    try:
        ffmpeg.input(video_file_path).output(audio_file_path, acodec='libmp3lame', audio_bitrate='192k').run(overwrite_output=True, capture_stdout=True, capture_stderr=True)
    except ffmpeg.Error as e:
        st.error("An error occurred with FFmpeg.")
        st.code(e.stderr.decode())
        return None
    finally:
        if os.path.exists(video_file_path):
            os.remove(video_file_path)
    return audio_file_path

@st.cache_data
def transcribe_audio(audio_path):
    model = whisper.load_model("base")
    result = model.transcribe(audio_path, fp16=False)
    if os.path.exists(audio_path):
        os.remove(audio_path)
    return result["text"]

@st.cache_data
def summarize_text(text):
    summarizer = pipeline("summarization", model="sshleifer/distilbart-cnn-12-6")
    max_chunk = 1024
    if not text.strip():
        return "The transcript was empty, so no summary could be generated."
    chunks = [text[i:i + max_chunk] for i in range(0, len(text), max_chunk)]
    summary_parts = [summarizer(chunk, max_length=130, min_length=30, do_sample=False)[0]['summary_text'] for chunk in chunks]
    return ' '.join(summary_parts)
#--- frontend
st.set_page_config(
    page_title="YouTube Video Summarizer",
    page_icon="🎬",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# --- Custom CSS Styling with Gradient Background & Frosted Glass ---
# --- Custom CSS Styling with Gradient Background & Frosted Glass ---
st.markdown("""
<style>
    /* Import Google Font */
    @import url('https://fonts.googleapis.com/css2?family=Poppins:wght@400;600;700&display=swap');

    /* General Body Styles */
    body {
        font-family: 'Poppins', sans-serif;
        color: #1b263b;
    }

    /* App background gradient */
    .stApp {
        background-image: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
        background-attachment: fixed;
        background-size: cover;
    }

    /* Hide Streamlit header/footer */
    header {visibility: hidden;}
    footer {visibility: hidden;}
    
    /* Main content padding */
    .main .block-container {
        padding-top: 2rem;
        padding-bottom: 2rem;
    }

    /* Title styling */
    .title-container {
        display: flex;
        align-items: center;
        justify-content: center;
        margin-bottom: 0.5rem;
    }

    .title {
        font-size: 2.8rem;
        font-weight: 700;
        color: #1b263b;
        padding-left: 10px;
    }

    .subtitle {
        text-align: center;
        color: #415a77;
        font-size: 1.1rem;
        margin-bottom: 2rem;
    }

    /* Frosted glass container */
    .input-container, .output-box {
        background: rgba(255, 255, 255, 0.65);
        backdrop-filter: blur(12px);
        -webkit-backdrop-filter: blur(12px);
        border-radius: 16px;
        padding: 2rem;
        border: 1px solid rgba(255, 255, 255, 0.25);
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
        margin-bottom: 2rem;
    }

    /* Input styling */
    .stTextInput > div > div > input {
        border-radius: 12px;
        border: 1px solid #dcdcdc;
        background-color: #ffffff;
    }

    /* Button styling */
    .stButton > button {
        background-color: #1b263b;
        color: white;
        border: none;
        border-radius: 12px;
        padding: 0.8rem 1.5rem;
        font-weight: 600;
        font-size: 1rem;
        width: 100%;
        transition: all 0.2s ease;
    }

    .stButton > button:hover {
        background-color: #415a77;
        transform: translateY(-2px);
    }

    .stButton > button:active {
        background-color: #0d131c;
        transform: translateY(0);
    }

    /* Tabs */
    .stTabs [data-baseweb="tab-list"] {
        gap: 24px;
        justify-content: center;
    }

    .stTabs [data-baseweb="tab"] {
        height: 50px;
        background-color: transparent;
        padding: 0 10px;
        font-weight: 600;
        color: #415a77;
    }

    .stTabs [aria-selected="true"] {
        background-color: rgba(255, 255, 255, 0.8);
        border-radius: 8px;
        color: #1b263b;
    }

    /* --- Vibrant Status Boxes --- */
    div[data-testid="stStatusWidget"] {
        border-radius: 14px !important;
        padding: 1rem 1.3rem !important;
        backdrop-filter: blur(14px);
        -webkit-backdrop-filter: blur(14px);
        border: 1px solid rgba(255, 255, 255, 0.35);
        box-shadow: 0 4px 14px rgba(27, 38, 59, 0.25);
        animation: fadeInBox 0.4s ease-in-out;
    }

    /* Info - deep blue glass */
    div[data-testid="stStatusWidget"][class*="stAlertInfo"] {
        background: linear-gradient(135deg, rgba(65, 90, 119, 0.85), rgba(100, 125, 150, 0.75)) !important;
        color: #ffffff !important;
        font-weight: 500;
    }

    /* Success - vibrant green */
    div[data-testid="stStatusWidget"][class*="stAlertSuccess"] {
        background: linear-gradient(135deg, rgba(72, 187, 120, 0.9), rgba(56, 161, 105, 0.8)) !important;
        color: #ffffff !important;
        font-weight: 500;
    }

    /* Warning - bright orange */
    div[data-testid="stStatusWidget"][class*="stAlertWarning"] {
        background: linear-gradient(135deg, rgba(255, 159, 67, 0.9), rgba(255, 125, 0, 0.8)) !important;
        color: #ffffff !important;
        font-weight: 500;
    }

    /* Error - strong red */
    div[data-testid="stStatusWidget"][class*="stAlertError"] {
        background: linear-gradient(135deg, rgba(231, 76, 60, 0.9), rgba(192, 57, 43, 0.8)) !important;
        color: #ffffff !important;
        font-weight: 500;
    }

    @keyframes fadeInBox {
        from {opacity: 0; transform: translateY(8px);}
        to {opacity: 1; transform: translateY(0);}
    }
</style>
""", unsafe_allow_html=True)


# --- App Header ---
st.markdown("""
<div class="title-container">
    <svg height="45" viewBox="0 0 100 70" width="60" fill="#FF0000" style="vertical-align: middle;">
        <path d="M98.2,11.3c-1.2-4.3-4.6-7.7-8.9-8.9C80.3,0,50,0,50,0S19.7,0,10.7,2.3C6.4,3.5,3,6.9,1.8,11.3C0,19.3,0,35,0,35s0,15.7,1.8,23.7c1.2,4.3,4.6,7.7,8.9,8.9C19.7,70,50,70,50,70s30.3,0,39.3-2.3c4.3-1.2,7.7-4.6,8.9-8.9C100,50.7,100,35,100,35S100,19.3,98.2,11.3z M40,50V20l26,15L40,50z"></path>
    </svg>
    <div class="title">YouTube Video Summarizer</div>
</div>
<p class="subtitle">Get instant summaries and transcripts from any YouTube video link.</p>
""", unsafe_allow_html=True)




# --- Input Section ---
st.markdown("### 🎬 Choose Your Input Method")
input_option = st.radio("", ("YouTube URL", "Upload Video File"), horizontal=True)

st.markdown("---")

if input_option == "YouTube URL":
    youtube_link = st.text_input("🔗 Enter a YouTube Video URL:")
    generate_btn = st.button("🎯 Generate Summary from URL", use_container_width=True)

    if generate_btn:
        if youtube_link:
            progress = st.progress(0)
            st.info("🔍 Step 1/3: Checking for transcripts or audio...")

            result_type, result_data = process_youtube_link(youtube_link)
            progress.progress(33)

            if result_type == "text":
                transcript = result_data
                st.success("✅ Found existing English transcript.")
            elif result_type == "audio_path":
                audio_path = result_data
                st.warning("🎧 No transcript found. Transcribing audio...")
                transcript = transcribe_audio(audio_path)
            else:
                st.error(result_data)
                st.stop()

            progress.progress(66)
            st.info("🧠 Step 2/3: Summarizing transcript...")

            summary = summarize_text(transcript)
            progress.progress(100)

            st.success("✅ Summary generated successfully!")
            col1, col2 = st.columns([1.5, 1])

            with col1:
                st.markdown('<div class="summary-box"><h3>📜 Summary</h3></div>', unsafe_allow_html=True)
                st.write(summary)

            with col2:
                with st.expander("🗒️ View Full Transcript"):
                    st.write(transcript)
        else:
            st.warning("⚠️ Please enter a valid YouTube URL.")

# --- File Upload Section ---
else:
    uploaded_file = st.file_uploader("📁 Upload a video file (MP4, MOV, AVI, MKV):", type=["mp4", "mov", "avi", "mkv"])
    generate_btn = st.button("🎯 Generate Summary from File", use_container_width=True)

    if generate_btn:
        if uploaded_file:
            progress = st.progress(0)
            st.info("🎶 Step 1/2: Extracting audio from video...")

            audio_path = get_audio_from_file(uploaded_file)
            progress.progress(50)

            if audio_path and os.path.exists(audio_path):
                st.info("🧠 Step 2/2: Transcribing and summarizing text...")
                transcript = transcribe_audio(audio_path)
                summary = summarize_text(transcript)
                progress.progress(100)

                st.success("✅ Summary generated successfully!")

                col1, col2 = st.columns([1.5, 1])

                with col1:
                    st.markdown('<div class="summary-box"><h3>📜 Summary</h3></div>', unsafe_allow_html=True)
                    st.write(summary)

                with col2:
                    with st.expander("🗒️ View Full Transcript"):
                        st.write(transcript)
            else:
                st.error("❌ Could not extract audio. Try another file.")
        else:
            st.warning("⚠️ Please upload a video file first.")