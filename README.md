```markdown
# 🚀 AI YouTube Video Summarizer

An intelligent web application built with Python and Streamlit that generates concise summaries from YouTube videos or local video files. The app uses OpenAI's Whisper for transcription and a Hugging Face Transformer for summarization.

<img width="1600" height="850" alt="image" src="https://github.com/user-attachments/assets/8b304205-fa87-4c89-9948-823ef4320183" />


---

## Key Features ✨

- **Dual Input Support**: Accepts both YouTube URLs and direct video file uploads (MP4, MOV, etc.).
- **Intelligent Transcript Fetching**: Automatically uses existing YouTube transcripts when available for a significantly faster summary.
- **AI-Powered Core**: Leverages OpenAI's Whisper for highly accurate speech-to-text and a Transformer model for high-quality summarization.
- **Custom Interactive UI**: A polished, user-friendly interface with a custom purple theme built using Streamlit.

---

## Tech Stack 🛠️

- **Language**: Python
- **Web Framework**: Streamlit
- **AI Models**:
  - OpenAI Whisper (Speech-to-Text)
  - Hugging Face Transformers (Summarization)
- **Core Libraries**:
  - `yt-dlp` (YouTube Processing)
  - `ffmpeg-python` (Audio Extraction)

---

## Setup & Installation

To run this project locally, follow these steps:

**1. Clone the repository:**
```bash
git clone https://github.com/your-username/YouTube-Video-Summarizer.git
cd YouTube-Video-Summarizer
Remember to replace your-username with your actual GitHub username.

**2. Create and activate a virtual environment:**

```Bash

# For Windows
python -m venv venv
.\venv\Scripts\activate
```Bash

# For macOS/Linux
python3 -m venv venv
source venv/bin/activate
**3. Install the required libraries:**

```Bash

pip install -r requirements.txt
Note: This project also requires FFmpeg. Please ensure it is installed on your system and accessible from your command line.
