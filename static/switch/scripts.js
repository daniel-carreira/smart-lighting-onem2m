const API_URL = 'http://localhost:8080'
const MQTT_URL = 'mqtt://localhost:1883'

const lookingElement = document.getElementsByTagName("h1")[0]
const containerElement = document.getElementsByClassName("container-switch")[0]
const actionButtonsElement = document.getElementsByClassName("fixed-buttons")[0]

// Axios config
axios.defaults.baseURL = API_URL
axios.defaults.headers.post['Content-Type'] = 'application/json';
axios.defaults.headers.post['Accept'] = 'application/json'

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

let currentIndex = 0;
let smartBulbs = [];

function createBulb(bulb, index) {
  isON = bulb.state == "on"

  // Create Lightbulb Div
  const bulbContainer = document.createElement("div")
  bulbContainer.classList.add("container-lightbulb")

  // Add the "current" class
  if (bulb.current) {
    currentIndex = index
    bulbContainer.classList.add("current")
  }

  // Create the smart-bulb label
  const bulbLabel = document.createElement("h2")
  bulbLabel.textContent = bulb.ip
  bulbContainer.appendChild(bulbLabel)

  // Create the smart-bulb image
  const bulbImg = document.createElement("img")
  bulbImg.src = isON ? "/static/icons/light-on.png" : "/static/icons/light-off.png"
  bulbContainer.appendChild(bulbImg)

  // Append the smart-bulb container to the container element
  containerElement.appendChild(bulbContainer)
}

function updateUI() {
  if (smartBulbs.length > 0) {
    lookingElement.style.display = "none"
    actionButtonsElement.style.display = "inline"
  }
  else {
    lookingElement.style.display = "inline"
    actionButtonsElement.style.display = "none"
  }
}

function updateBulb(ip, state) {
  index = 0
  smartBulbs.forEach((item, idx) => {
    if (item.ip == ip) {
      index = idx
      return
    }
  })
  let containers = document.querySelectorAll(".container-lightbulb");
  to_update = containers[index]

  imgElem = to_update.getElementsByTagName("img")[0]
  isON = state == "on"
  imgElem.src = isON ? "/static/icons/light-on.png" : "/static/icons/light-off.png"
}

// Get Current Bulbs
async function getBulb() {
	return axios
		.get("bulbs")
		.then(function (response) {
      smartBulbs = response.data

      updateUI()

      smartBulbs.forEach((bulb, index) => {
        socket.on(bulb.ip, (message) => {
          console.log(`Room "${bulb.ip}": ${message}`)
          updateBulb(bulb.ip, message)
        })
        createBulb(bulb, index)
      })
		})
		.catch(error => {
			console.log(error)
		})
}
getBulb()

async function toggle() {
  ip = smartBulbs[currentIndex].ip

  return axios.post("toggle", {"state": ip})
    .then(response => {
      isON = response.data.state == "on"

      imgs = document.querySelectorAll(".container-lightbulb img");
      imgs[currentIndex].src = isON ? "/static/icons/light-on.png" : "/static/icons/light-off.png"
    })
    .catch(error => {
			console.log(error)
		})
}

function next() {
  return axios.post("next")
    .then(response => {
      ip = response.data.state
      index = smartBulbs.find( item => item.ip == ip)

      currentIndex = index
      let containers = document.querySelectorAll(".container-lightbulb");
      containers.forEach( container => {
        container.classList.remove("current");
      })

      containers[currentIndex].classList.add("current");
    })
    .catch(error => {
      console.log(error)
    })
}

document.getElementById("toggle").addEventListener('click', toggle);
document.getElementById("next").addEventListener('click', next);