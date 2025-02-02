import os
import google.generativeai as genai
from flask import Flask, request, jsonify, render_template
from dotenv import load_dotenv
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

# YouTube API Key (Required)
YOUTUBE_API_KEY = os.getenv("YOUTUBE_API_KEY")
if not YOUTUBE_API_KEY:
    raise ValueError("YOUTUBE_API_KEY is missing in environment variables.")

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
    system_instruction="Give a detailed summary of the provided YouTube video title.",
)

# Start a chat session
chat_session = model.start_chat(history=[])

@app.route('/')
def home():
    return render_template("index.html")

# ✅ Function to search for a YouTube video by title
def search_youtube_video(title):
    search_url = "https://www.googleapis.com/youtube/v3/search"
    params = {
        "part": "snippet",
        "q": title,
        "type": "video",
        "key": YOUTUBE_API_KEY,
        "maxResults": 1  # Fetch only the top result
    }
    
    response = requests.get(search_url, params=params)
    data = response.json()

    if "items" in data and len(data["items"]) > 0:
        video_id = data["items"][0]["id"]["videoId"]
        video_title = data["items"][0]["snippet"]["title"]
        return video_id, video_title
    else:
        return None, None

# ✅ Generate a summary using Gemini AI
@app.route('/summarize', methods=['POST'])
def summarize_video():
    try:
        data = request.json
        video_title = data.get("video_title", "")

        if not video_title:
            return jsonify({"error": "YouTube video title is required"}), 400

        # Search for video
        video_id, actual_title = search_youtube_video(video_title)
        if not video_id:
            return jsonify({"error": "No YouTube video found for this title."}), 404

        # Request Gemini AI to generate the summary
        response = chat_session.send_message(
            f"Provide a detailed summary of a YouTube video titled '{actual_title}'. Assume you have watched the video."
        )

        return jsonify({
            "video_title": actual_title,
            "video_id": video_id,
            "summary": response.text
        })
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# ✅ Run Flask App
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
