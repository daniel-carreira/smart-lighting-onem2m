const API_URL = 'http://localhost:8080'
const WS_URL = 'ws://localhost:8080'

// Socket IO
var socket = io(WS_URL);
socket.on('connect', () => {
  console.log("Connection established")
});

socket.on('state', (message) => {
  isON = message == "on"
  lightStateElement.textContent = message.toUpperCase()
  faviconElement.href = isON ? "/static/icons/light-on.png" : "/static/icons/light-off.png"
})

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
			isON = response.data["state"] == "on"
			lightStateElement.textContent = response.data["state"].toUpperCase()
			faviconElement.href = isON ? "/static/icons/light-on.png" : "/static/icons/light-off.png"
		})
		.catch(function (error) {
			console.log(error)
		})
}
getState()