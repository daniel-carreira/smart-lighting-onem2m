const API_URL = 'http://localhost:8080'
const WS_URL = 'ws://localhost:8081'

// H1 Element
const lightStateElement = document.getElementsByTagName("h1")[0]
const faviconElement = document.querySelector("link[rel='icon']")

// Axios config
axios.defaults.baseURL = API_URL
axios.defaults.headers.post['Accept'] = 'application/json'

// Get Current State
async function getState() {
	axios
		.get("state")
		.then(function (response) {
      isON = response.data["m2m:cin"]["con"]["state"] == "on"
			lightStateElement.textContent = response.data["m2m:cin"]["con"]["state"].toUpperCase()
      faviconElement.href = isON ? "/static/icons/light-on.png" : "/static/icons/light-off.png"
		})
		.catch(function (error) {
			console.log(error)
		})
}
getState()

// Web Sockets
const socket = new WebSocket(WS_URL);

// Connection established event
socket.addEventListener('open', () => {
  console.log('Connected to the WebSocket server');

  // Send a message to the server
  socket.send('Hello, server!');
});

// Message received event
socket.addEventListener('message', (event) => {
  const message = event.data;
  console.log(`Received message: ${message}`);
});

// Connection closed event
socket.addEventListener('close', () => {
  console.log('Connection closed');
});