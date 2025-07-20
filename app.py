from flask import Flask, request, jsonify, render_template
import requests
from textblob import TextBlob  # For sentiment analysis

app = Flask(__name__)

# API keys
LAST_FM_API_KEY = "fbd771e6c34f59fbccc03bfda4b8151f"
OPENWEATHER_API_KEY = "e11452321f1e40b6dc863a919c1a7fc5"
LAST_FM_API_URL = "http://ws.audioscrobbler.com/2.0/"
GEMINI_API_KEY = "AIzaSyCrJo-67ESjilQSAkDh7iE5Y4uZqJbkhMU"  # Replace with your API key


@app.route('/')
def home():
    return render_template('index.html')


# Function to handle general queries using Gemini API
def fetch_gemini_response(query):
    url = "https://api.gemini.ai/ask"  # Ensure this is correct
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {GEMINI_API_KEY}"
    }
    payload = {"query": query}

    try:
        response = requests.post(url, json=payload, headers=headers, timeout=10)
        if response.status_code == 200:
            return response.json().get("answer", "Sorry, I couldn't find an answer.")
        else:
            return f"Error: {response.status_code} - {response.text}"
    except requests.exceptions.RequestException as e:
        return f"An error occurred while connecting to Gemini: {str(e)}"


@app.route("/ask-gemini", methods=["POST"])
def ask_gemini():
    data = request.json
    user_message = data.get("message", "")

    gemini_response = fetch_gemini_response(user_message)
    return jsonify({"response": gemini_response})


@app.route("/get-recommendations", methods=["POST"])
def process_query():
    data = request.json
    user_message = data.get("message", "").lower()

    # Sentiment Analysis to determine mood
    analysis = TextBlob(user_message)
    sentiment = analysis.sentiment.polarity
    if sentiment > 0.5:
        mood = "happy"
    elif sentiment < -0.5:
        mood = "sad"
    elif sentiment > 0:
        mood = "relaxed"
    else:
        mood = "energetic"

    mood_to_tag = {
        "happy": "happy",
        "sad": "sad",
        "energetic": "rock",
        "relaxed": "chill"
    }
    tag = mood_to_tag.get(mood, "pop")

    # Fetch songs from Last.fm
    try:
        response = requests.get(LAST_FM_API_URL, params={
            "method": "tag.gettoptracks",
            "tag": tag,
            "api_key": LAST_FM_API_KEY,
            "format": "json"
        }, timeout=10)

        if response.status_code == 200:
            tracks = response.json()["tracks"]["track"]
            recommendations = [
                f"{track['name']} by {track['artist']['name']}" for track in tracks[:5]
            ]
            return jsonify({"recommendations": recommendations})
        else:
            return jsonify({"error": "Failed to fetch song recommendations."}), response.status_code
    except requests.exceptions.RequestException as e:
        return jsonify({"error": f"An error occurred: {str(e)}"}), 500


if __name__ == "__main__":
    app.run(debug=True)
