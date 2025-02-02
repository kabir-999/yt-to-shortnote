import os
import google.generativeai as genai
from flask import Flask, request, jsonify, render_template
from dotenv import load_dotenv
import requests
from bs4 import BeautifulSoup

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
    system_instruction="Provide a detailed summary based on the video title, as if you've watched the video.",
)

# Start a chat session
chat_session = model.start_chat(history=[])

@app.route('/')
def home():
    return render_template("index.html")

# ✅ Web Scraping to Search YouTube Without API Key
def search_youtube_video(title):
    search_query = title.replace(" ", "+")
    url = f"https://www.youtube.com/results?search_query={search_query}"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }
    
    response = requests.get(url, headers=headers)
    if response.status_code != 200:
        return None, None

    soup = BeautifulSoup(response.text, "html.parser")

    for link in soup.find_all("a", href=True):
        if "/watch?v=" in link["href"]:
            video_id = link["href"].split("=")[-1]
            video_title = link.text.strip() if link.text else title
            return video_id, video_title

    return None, None

# ✅ Generate a summary using Gemini AI
@app.route('/summarize', methods=['POST'])
def summarize_video():
    try:
        data = request.json
        video_title = data.get("video_title", "")

        if not video_title:
            return jsonify({"error": "YouTube video title is required"}), 400

        # Search for video using web scraping
        video_id, actual_title = search_youtube_video(video_title)
        if not video_id:
            return jsonify({"error": "No YouTube video found for this title."}), 404

        # Request Gemini AI to generate the summary (correct video title)
        response = chat_session.send_message(
            f"Provide a detailed summary based on the video titled '{actual_title}', as if you've watched it."
        )

        # Return the summary and video details
        return jsonify({
            "video_title": actual_title,
            "video_id": video_id,
            "video_url": f"https://www.youtube.com/watch?v={video_id}",
            "summary": response.text
        })
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# ✅ Run Flask App
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
