const chatMessages = document.getElementById("chat-messages");
const userInput = document.getElementById("user-input");

// Spotify API Credentials
const spotifyClientId = "17f780418faa4cb6b35af94f8c7a51d7"; // Replace with your Spotify Client ID
const spotifyClientSecret = "ba8f23b47320400b946ca6d8d0502be6"; // Replace with your Spotify Client Secret
let spotifyAccessToken = null;

// Add welcome message when the page loads
window.onload = () => {
  addMessage(
    "Hello! I'm your AI assistant. How can I help you today?",
    "bot-message"
  );
};


// Fetch response for general questions using Gemini API
async function fetchGeminiResponse(query) {
  const apiUrl = "http://127.0.0.1:5000/ask-gemini"; // Update URL if needed

  try {
    const response = await fetch(apiUrl, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ message: query }),
    });

    if (!response.ok) {
      throw new Error("Error fetching Gemini API response.");
    }

    const data = await response.json();
    addMessage(data.response, "bot-message");
  } catch (error) {
    console.error("Error fetching Gemini response:", error);
    addMessage("Sorry, I couldn't process your question. Please try again later.", "bot-message");
  }
}




// Handle Enter key press
function handleKeyPress(event) {
  if (event.key === "Enter" && !event.shiftKey) {
    event.preventDefault();
    sendMessage();
  }
}

// Send message
function sendMessage() {
  const message = userInput.value.trim();
  if (!message) return;

  // Display user message
  addMessage(message, "user-message");

  // Clear input and adjust height
  userInput.value = "";

  // Show typing indicator
  showTypingIndicator();

  // Simulate bot response after a delay
  setTimeout(() => {
    removeTypingIndicator();
    processAndRespond(message);
  }, 1500);
}

// Add message to the chat
// Add message to the chat
function addMessage(text, className) {
  const messageDiv = document.createElement("div");
  messageDiv.className = `message ${className}`;

  // Use innerHTML for bot messages to support links
  if (className === "bot-message") {
    messageDiv.innerHTML = text;
  } else {
    messageDiv.textContent = text;
  }

  chatMessages.appendChild(messageDiv);
  scrollToBottom();
}

// Show typing indicator
function showTypingIndicator() {
  const indicator = document.createElement("div");
  indicator.className = "typing-indicator";
  indicator.innerHTML = "<span></span><span></span><span></span>";
  indicator.id = "typing-indicator";
  chatMessages.appendChild(indicator);
  scrollToBottom();
}

// Remove typing indicator
function removeTypingIndicator() {
  const indicator = document.getElementById("typing-indicator");
  if (indicator) {
    indicator.remove();
  }
}

// Scroll chat to the bottom
function scrollToBottom() {
  chatMessages.scrollTop = chatMessages.scrollHeight;
}

// Fetch Spotify Access Token
async function fetchSpotifyAccessToken() {
  const url = "https://accounts.spotify.com/api/token";
  const body = "grant_type=client_credentials";
  const headers = {
    "Content-Type": "application/x-www-form-urlencoded",
    Authorization: `Basic ${btoa(spotifyClientId + ":" + spotifyClientSecret)}`,
  };

  try {
    const response = await fetch(url, {
      method: "POST",
      headers,
      body,
    });
    const data = await response.json();
    spotifyAccessToken = data.access_token;
  } catch (error) {
    console.error("Error fetching Spotify access token:", error);
    addMessage(
      "Sorry, I couldn't connect to Spotify. Please try again later.",
      "bot-message"
    );
  }
}

// Fetch Song Recommendations from Spotify
async function fetchSpotifyRecommendations(query) {
  if (!spotifyAccessToken) {
    await fetchSpotifyAccessToken();
  }

  const searchUrl = `https://api.spotify.com/v1/search?q=${encodeURIComponent(
    query
  )}&type=track&limit=10`;

  const headers = {
    Authorization: `Bearer ${spotifyAccessToken}`,
  };

  try {
    const response = await fetch(searchUrl, { headers });
    if (!response.ok) {
      throw new Error("Error fetching song recommendations.");
    }

    const data = await response.json();
    const tracks = data.tracks.items;

    if (tracks.length > 0) {
      // Build recommendations with song names and links
      let recommendations = "Here are some song recommendations:<br>";
      tracks.forEach((track, index) => {
        const songName = track.name;
        const songUrl = track.external_urls.spotify; // Spotify play link
        recommendations += `${
          index + 1
        }. <a href="${songUrl}" target="_blank">${songName}</a><br>`;
      });

      addMessage(recommendations, "bot-message");
    } else {
      addMessage("No songs found for your query.", "bot-message");
    }
  } catch (error) {
    console.error("Error fetching song recommendations:", error);
    addMessage(
      "Sorry, I couldn't fetch song recommendations. Please try again later.",
      "bot-message"
    );
  }
}

// Fetch Weather Information

async function fetchWeather(city) {
  const apiKey = 'e11452321f1e40b6dc863a919c1a7fc5'; // Replace with your OpenWeatherMap API key
  const apiUrl = `https://api.openweathermap.org/data/2.5/weather?q=${city}&units=metric&appid=${apiKey}`;

  try {
      const response = await fetch(apiUrl);
      if (!response.ok) {
          throw new Error("City not found");
      }
      const data = await response.json();

      const weather = `The current weather in ${city} is ${data.weather[0].description} with a temperature of ${data.main.temp}°C and humidity of ${data.main.humidity}%.`;
      addMessage(weather, 'bot-message');
  } catch (error) {
      addMessage("Sorry, I couldn't fetch the weather for the specified location. Please try again.", 'bot-message');
  }
}



// Process and Respond
function processAndRespond(userMessage) {
  const message = userMessage.toLowerCase().trim();
  let response;

  if (message.includes("hello") || message.includes("hi")) {
    response = "Hello! How can I assist you today?";
    addMessage(response, "bot-message");
  } else if (message.includes("weather")) {
    const cityMatch = userMessage.match(/weather in (.+)/i);
    const city = cityMatch ? cityMatch[1] : null;
    if (city) {
      fetchWeather(city);
    } else {
      response = "Please specify a city, e.g., 'weather in London'.";
      addMessage(response, "bot-message");
    }
  } else if (message.includes("recommend")) {
    const queryMatch = userMessage.match(/recommend (.+)/i);
    const query = queryMatch ? queryMatch[1] : null;
    if (query) {
      fetchSpotifyRecommendations(query);
    } else {
      response = "Please specify what you want recommendations for.";
      addMessage(response, "bot-message");
    }
  } else if (
    message.includes("happy") ||
    message.includes("sad") ||
    message.includes("party") ||
    message.includes("chill") ||
    message.includes("relaxed")
  ) {
    // Enhanced mood-based search queries
    let moodQuery = "";

    if (message.includes("happy")) {
      moodQuery = "happy pop"; // Example: happy pop music
    } else if (message.includes("sad")) {
      moodQuery = "sad acoustic"; // Example: sad acoustic music
    } else if (message.includes("party")) {
      moodQuery = "party dance"; // Example: party dance music
    } else if (message.includes("chill")) {
      moodQuery = "chill ambient"; // Example: chill ambient music
    } else if (message.includes("relaxed")) {
      moodQuery = "relaxed jazz"; // Example: relaxed jazz music
    }

    // Fetch Spotify recommendations with mood-based queries
    fetchSpotifyRecommendations(`${moodQuery} songs`);
  } else if (message.includes("help")) {
    response =
      "I can help with: \n- Weather information\n- Song recommendations\n- Mood-based playlists\n- General questions\nWhat do you need help with?";
    addMessage(response, "bot-message");
  } else if (message.includes("bye") || message.includes("goodbye")) {
    response = "Goodbye! Have a great day!";
    addMessage(response, "bot-message");
  } else {
    fetchGeminiResponse(userMessage);
  }
}
