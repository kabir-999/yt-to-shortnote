import os
import google.generativeai as genai
from flask import Flask, request, jsonify, render_template
from dotenv import load_dotenv
from youtube_transcript_api import YouTubeTranscriptApi, TranscriptsDisabled, NoTranscriptFound
import requests

# Load environment variables
load_dotenv()

# Initialize Flask app
app = Flask(__name__)

# Configure Gemini API
api_key = os.getenv("GEMINI_API_KEY")
if not api_key:
    raise ValueError("GEMINI_API_KEY is missing in environment variables.")
genai.configure(api_key=api_key)

# Model Configuration
generation_config = {
    "temperature": 1,
    "top_p": 0.95,
    "top_k": 40,
    "max_output_tokens": 8192,
    "response_mime_type": "text/plain",
}

# Initialize the model
model = genai.GenerativeModel(
    model_name="gemini-2.0-flash-exp",
    generation_config=generation_config,
    system_instruction="Give a detailed summary of the provided YouTube video.",
)

# Start a chat session
chat_session = model.start_chat(history=[])

@app.route('/')
def home():
    return render_template("index.html")

# ✅ Function to extract video ID from URL
def extract_video_id(video_url):
    if "watch?v=" in video_url:
        return video_url.split("v=")[-1].split("&")[0]
    elif "youtu.be/" in video_url:
        return video_url.split("/")[-1].split("?")[0]
    return None

# ✅ Function to get YouTube transcript, fallback to Gemini AI if unavailable
def get_youtube_transcript(video_url):
    video_id = extract_video_id(video_url)
    if not video_id:
        return None, "Invalid YouTube URL format."

    try:
        # ✅ Try to fetch transcript
        transcript_list = YouTubeTranscriptApi.list_transcripts(video_id)
        transcript = transcript_list.find_transcript(['en']).fetch()
        transcript_text = " ".join([t["text"] for t in transcript])
        return transcript_text, None  # Success

    except TranscriptsDisabled:
        return None, "Transcripts are disabled for this video."
    except NoTranscriptFound:
        return None, "No transcripts were found for this video."
    except Exception as e:
        return None, f"Error fetching transcript: {str(e)}"

# ✅ Generate summary using Gemini AI (with or without transcript)
@app.route('/summarize', methods=['POST'])
def summarize_video():
    try:
        data = request.json
        video_url = data.get("video_url", "")

        if not video_url:
            return jsonify({"error": "YouTube video URL is required"}), 400

        # ✅ Get transcript (or fallback to Gemini AI)
        transcript, error = get_youtube_transcript(video_url)

        if error:
            # ✅ If transcript is missing, get video title and ask Gemini AI
            response = chat_session.send_message(
                f"The video at {video_url} does not have subtitles. "
                f"Based on the title, generate a summary as if you had watched it."
            )
        else:
            # ✅ If transcript exists, ask Gemini to summarize it
            response = chat_session.send_message(f"Summarize this video transcript:\n\n{transcript}")

        return jsonify({
            "video_url": video_url,
            "summary": response.text
        })
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# ✅ Run Flask App
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
