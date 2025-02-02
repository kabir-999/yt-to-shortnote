import os
import google.generativeai as genai
from flask import Flask, request, jsonify, render_template
from dotenv import load_dotenv
from youtube_transcript_api import YouTubeTranscriptApi

# Load environment variables
load_dotenv()

# Initialize Flask app with correct template and static folder paths
app = Flask(_name_, template_folder="templates", static_folder="static")

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
    system_instruction="Give short notes of the video link being provided.",
)

# Start a chat session
chat_session = model.start_chat(history=[])

# ✅ Corrected Route to Serve index.html
@app.route('/')
def home():
    return render_template("index.html")  # ✅ Corrected: No need to mention templates/

# ✅ Extract transcript from YouTube video
def get_youtube_transcript(video_url):
    try:
        if "watch?v=" in video_url:
            video_id = video_url.split("v=")[-1].split("&")[0]  # Handle extra params
        elif "youtu.be/" in video_url:
            video_id = video_url.split("/")[-1].split("?")[0]
        else:
            return "Invalid YouTube URL format."

        # Fetch transcript
        transcript_list = YouTubeTranscriptApi.get_transcript(video_id)

        # Convert transcript into a single text string
        transcript_text = " ".join([t["text"] for t in transcript_list])

        return transcript_text
    except Exception as e:
        return f"Error fetching transcript: {str(e)}"

# ✅ Summarize transcript using Gemini AI
@app.route('/summarize', methods=['POST'])
def summarize_video():
    try:
        data = request.json
        video_url = data.get("video_url", "")

        if not video_url:
            return jsonify({"error": "YouTube video URL is required"}), 400

        transcript = get_youtube_transcript(video_url)
        if "Error" in transcript:
            return jsonify({"error": transcript}), 500

        response = chat_session.send_message(f"Summarize this video transcript:\n\n{transcript}")
        return jsonify({"summary": response.text})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# ✅ Chat API
@app.route('/chat', methods=['POST'])
def chat():
    try:
        data = request.json
        user_input = data.get("message", "")

        if not user_input:
            return jsonify({"error": "Message is required"}), 400

        response = chat_session.send_message(user_input)

        return jsonify({"response": response.text})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# ✅ Run Flask App
if _name_ == "_main_":
    app.run(host="0.0.0.0", port=5000, debug=True)
