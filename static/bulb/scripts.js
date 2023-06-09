const API_URL = 'http://localhost:8080'
const MQTT_URL = 'mqtt://localhost:1883'

// MQTT
const client = mqtt.connect(MQTT_URL, { port: 1883 });

client.on('connect', () => {
  console.log('Connected to MQTT broker');
});

client.subscribe("#", (error) => {
	if (error) {
		console.error('Error subscribing to topic:', error);
	} else {
		console.log('Subscribed to topic:', topic);
	}
});

client.on('message', (topic, message) => {
  console.log(topic)
  console.log(message)
  /*
  isON = message == "on"
  lightStateElement.textContent = message.toUpperCase()
  faviconElement.href = isON ? "/static/icons/light-on.png" : "/static/icons/light-off.png"
  */
});

client.on('error', (error) => {
  console.error('Error connecting to MQTT broker:', error);
});

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