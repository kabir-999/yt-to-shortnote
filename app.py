import os
import google.generativeai as genai
from flask import Flask, request, jsonify, render_template
from dotenv import load_dotenv

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

# ✅ Generate a summary using Gemini AI based on the video title
@app.route('/summarize', methods=['POST'])
def summarize_video():
    try:
        data = request.json
        video_title = data.get("video_title", "")

        if not video_title:
            return jsonify({"error": "YouTube video title is required"}), 400

        # Request Gemini AI to generate the summary based on the video title alone
        response = chat_session.send_message(
            f"Provide a detailed summary based on the video titled '{video_title}', as if you've watched it."
        )

        return jsonify({
            "video_title": video_title,
            "summary": response.text
        })
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# ✅ Run Flask App
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
