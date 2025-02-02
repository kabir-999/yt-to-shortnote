import os
import google.generativeai as genai
from flask import Flask, request, jsonify, render_template
from dotenv import load_dotenv
from youtube_transcript_api import YouTubeTranscriptApi, TranscriptsDisabled, NoTranscriptFound

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
    system_instruction="Give short notes of the video title being provided.",
)

# Start a chat session
chat_session = model.start_chat(history=[])

@app.route('/')
def home():
    return render_template("index.html")

# ✅ Improved Transcript Fetching Function
def get_youtube_transcript(video_url, language="en"):
    try:
        # Extract video ID
        if "watch?v=" in video_url:
            video_id = video_url.split("v=")[-1].split("&")[0]
        elif "youtu.be/" in video_url:
            video_id = video_url.split("/")[-1].split("?")[0]
        else:
            return "Invalid YouTube URL format."

        # ✅ Get available transcript languages
        transcript_list = YouTubeTranscriptApi.list_transcripts(video_id)
        available_languages = [t.language_code for t in transcript_list]

        # ✅ Use requested language if available, otherwise pick the first available one
        selected_language = language if language in available_languages else available_languages[0]

        # ✅ Fetch transcript in the selected language
        transcript = transcript_list.find_transcript([selected_language]).fetch()
        transcript_text = " ".join([t["text"] for t in transcript])

        return transcript_text
    except TranscriptsDisabled:
        return "Transcripts are disabled for this video."
    except NoTranscriptFound:
        return "No transcripts were found for this video."
    except Exception as e:
        return f"Error fetching transcript: {str(e)}"

# ✅ Summarize transcript using Gemini AI
@app.route('/summarize', methods=['POST'])
def summarize_video():
    try:
        data = request.json
        video_url = data.get("video_url", "")
        language = data.get("language", "en")

        if not video_url:
            return jsonify({"error": "YouTube video URL is required"}), 400

        transcript = get_youtube_transcript(video_url, language)
        if "Error" in transcript or "No transcripts" in transcript:
            return jsonify({"error": transcript}), 500

        response = chat_session.send_message(f"Summarize this video transcript:\n\n{transcript}")
        return jsonify({"summary": response.text})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# ✅ Run Flask App
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
