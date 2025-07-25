from flask import Flask, request, jsonify, render_template
import requests
from textblob import TextBlob # For sentiment analysis (can be replaced by LLM for nuanced mood)
import base64 # For Spotify client credentials encoding
import json # For handling JSON schema in Gemini API

app = Flask(__name__)

# --- API Keys (Centralized in Backend for Security) ---
# NOTE: In a production environment, these should be loaded from environment variables
# or a secure configuration management system, not hardcoded.
LAST_FM_API_KEY = "fbd771e6c34f59fbccc03bfda4b8151f"
OPENWEATHER_API_KEY = "e11452321f1e40b6dc863a919c1a7fc5"
SPOTIFY_CLIENT_ID = "17f780418faa4cb6b35af94f8c7a51d7"
SPOTIFY_CLIENT_SECRET = "ba8f23b47320400b946ca6d8d0502be6"
GEMINI_API_KEY = "AIzaSyCrJo-67ESjilQSAkDh7iE5Y4uZqJbkhMU" # User's provided key

# --- API Endpoints ---
LAST_FM_API_URL = "http://ws.audioscrobbler.com/2.0/"
OPENWEATHER_API_URL = "https://api.openweathermap.org/data/2.5/weather"
SPOTIFY_TOKEN_URL = "https://accounts.spotify.com/api/token"
SPOTIFY_SEARCH_URL = "https://api.spotify.com/v1/search"
GEMINI_API_BASE_URL = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent"

# --- Global variable for Spotify Access Token ---
# In a real app, this should be managed with proper token refresh logic and storage
spotify_access_token = None

@app.route('/')
def home():
    """Renders the main chat interface."""
    return render_template('index.html')

@app.route("/ask-gemini", methods=["POST"])
def ask_gemini():
    """
    Handles general conversational queries using the Gemini API.
    Includes chat history for contextual responses and a persona for human-like interaction.
    """
    data = request.json
    user_message = data.get("message", "")
    chat_history = data.get("history", []) # Get chat history from frontend

    # Prepare chat history for Gemini API
    # Add a system instruction or persona for Gemini
    gemini_chat_history = [{
        "role": "user",
        "parts": [{"text": "You are a friendly, helpful, and empathetic AI assistant. Respond logically and emotionally like a human, providing concise and relevant information. If asked about music, suggest using the 'recommend' command. If asked about weather, suggest 'weather in [city]'."}]
    }]
    for msg in chat_history:
        gemini_chat_history.append({"role": msg["sender"], "parts": [{"text": msg["text"]}]})

    # Add current user message
    gemini_chat_history.append({"role": "user", "parts": [{"text": user_message}]})

    payload = {
        "contents": gemini_chat_history,
        "generationConfig": {
            "temperature": 0.7, # Adjust for creativity vs. focus
            "topP": 0.95,
            "topK": 40,
        }
    }
    headers = {
        "Content-Type": "application/json"
    }

    try:
        response = requests.post(
            f"{GEMINI_API_BASE_URL}?key={GEMINI_API_KEY}",
            json=payload,
            headers=headers,
            timeout=20 # Increased timeout for Gemini
        )
        response.raise_for_status() # Raise an exception for HTTP errors (4xx or 5xx)
        result = response.json()

        if result.get("candidates") and len(result["candidates"]) > 0 and \
           result["candidates"][0].get("content") and \
           result["candidates"][0]["content"].get("parts") and \
           len(result["candidates"][0]["content"]["parts"]) > 0:
            gemini_response = result["candidates"][0]["content"]["parts"][0]["text"]
            return jsonify({"response": gemini_response})
        else:
            return jsonify({"response": "Sorry, I couldn't generate a response."}), 500
    except requests.exceptions.RequestException as e:
        app.logger.error(f"Error connecting to Gemini API: {e}")
        return jsonify({"response": f"An error occurred while connecting to Gemini: {str(e)}"}), 500
    except json.JSONDecodeError:
        app.logger.error(f"Error decoding Gemini API response: {response.text}")
        return jsonify({"response": "An error occurred with the Gemini API response."}), 500


@app.route("/get-spotify-token", methods=["POST"])
def get_spotify_token():
    """Fetches a Spotify access token using client credentials flow."""
    global spotify_access_token
    auth_string = f"{SPOTIFY_CLIENT_ID}:{SPOTIFY_CLIENT_SECRET}"
    encoded_auth_string = base64.b64encode(auth_string.encode("utf-8")).decode("utf-8")

    headers = {
        "Authorization": f"Basic {encoded_auth_string}",
        "Content-Type": "application/x-www-form-urlencoded"
    }
    body = {"grant_type": "client_credentials"}

    try:
        response = requests.post(SPOTIFY_TOKEN_URL, headers=headers, data=body, timeout=10)
        response.raise_for_status()
        token_info = response.json()
        spotify_access_token = token_info.get("access_token")
        if spotify_access_token:
            return jsonify({"access_token": spotify_access_token})
        else:
            return jsonify({"error": "Failed to get Spotify access token."}), 500
    except requests.exceptions.RequestException as e:
        app.logger.error(f"Error fetching Spotify token: {e}")
        return jsonify({"error": f"An error occurred fetching Spotify token: {str(e)}"}), 500

@app.route("/get-spotify-recommendations", methods=["POST"])
def get_spotify_recommendations():
    """
    Fetches song recommendations from Spotify based on a query.
    Requires a valid Spotify access token.
    """
    global spotify_access_token
    data = request.json
    query = data.get("query", "")

    if not spotify_access_token:
        # Try to get a new token if it's missing
        token_response = get_spotify_token()
        if token_response.status_code != 200:
            return token_response # Return the error response from get_spotify_token

    headers = {
        "Authorization": f"Bearer {spotify_access_token}"
    }
    params = {
        "q": query,
        "type": "track",
        "limit": 10
    }

    try:
        response = requests.get(SPOTIFY_SEARCH_URL, headers=headers, params=params, timeout=10)
        response.raise_for_status()
        tracks_data = response.json()
        tracks = tracks_data.get("tracks", {}).get("items", [])

        if tracks:
            recommendations = []
            for track in tracks:
                song_name = track.get("name", "Unknown Song")
                artist_name = track.get("artists", [{}])[0].get("name", "Unknown Artist")
                song_url = track.get("external_urls", {}).get("spotify", "#")
                recommendations.append({
                    "name": song_name,
                    "artist": artist_name,
                    "url": song_url
                })
            return jsonify({"recommendations": recommendations})
        else:
            return jsonify({"recommendations": []}) # Return empty list if no tracks found
    except requests.exceptions.RequestException as e:
        app.logger.error(f"Error fetching Spotify recommendations: {e}")
        return jsonify({"error": f"An error occurred fetching Spotify recommendations: {str(e)}"}), 500

@app.route("/get-weather", methods=["POST"])
def get_weather():
    """Fetches weather information from OpenWeatherMap."""
    data = request.json
    city = data.get("city", "")

    if not city:
        return jsonify({"error": "City name is required."}), 400

    params = {
        "q": city,
        "units": "metric", # For Celsius
        "appid": OPENWEATHER_API_KEY
    }

    try:
        response = requests.get(OPENWEATHER_API_URL, params=params, timeout=10)
        response.raise_for_status()
        weather_data = response.json()

        description = weather_data["weather"][0]["description"]
        temp = weather_data["main"]["temp"]
        humidity = weather_data["main"]["humidity"]

        weather_info = {
            "city": city,
            "description": description,
            "temperature": temp,
            "humidity": humidity
        }
        return jsonify(weather_info)
    except requests.exceptions.RequestException as e:
        app.logger.error(f"Error fetching weather: {e}")
        return jsonify({"error": f"Could not fetch weather for {city}. Please check the city name."}), 500

if __name__ == "__main__":
    app.run(debug=True, port=5000)

