const API_URL = 'http://localhost:8080'
const WS_URL = 'ws://localhost:8080'

const lookingElement = document.getElementsByTagName("h1")[0]
const containerElement = document.getElementsByClassName("container-switch")[0]
const actionButtonsElement = document.getElementsByClassName("fixed-buttons")[0]

// Axios config
axios.defaults.baseURL = API_URL
//axios.defaults.headers.post['Content-Type'] = 'application/json';
axios.defaults.headers.post['Accept'] = 'application/json'

// Socket IO
var socket = io(WS_URL);
socket.on('connect', () => {
  console.log("[WS]: Connection established")
});

socket.on('state', (message) => {
  updateBulb(message.ip, message.state)
  console.log("Toggle action completed")
})

socket.on('target', (message) => {
  targetBulb(message.ip)
  console.log("Next action completed")
})

socket.on('add', (message) => {
  createBulb(message)
  updateUI()
})

socket.on('remove', (message) => {
  removeBulb(message.ip)
  updateUI()
})


let currentIndex = 0;
let smartBulbs = [];

function createBulb(bulb) {
  smartBulbs.push(bulb)

  isON = bulb.state == "on"

  // Create Lightbulb Div
  const bulbContainer = document.createElement("div")
  bulbContainer.classList.add("container-lightbulb")

  // Add the "current" class
  if (bulb.current) {
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
      let bulbs = response.data

      updateUI()

      bulbs.forEach((bulb, index) => {
        createBulb(bulb)
        currentIndex = bulb.current ? index : currentIndex
      })
		})
		.catch(error => {
			console.log(error)
		})
}
getBulb()

async function toggle() {
  axios
		.post("toggle")
		.then(function (response) {
			console.log("Toggle action requested")
		})
		.catch(function (error) {
			console.log(error)
		})
}

function targetBulb(ip) {
  ip = response.data.ip;
  const index = smartBulbs.findIndex(item => item.ip === ip);

  currentIndex = index;
  const containers = document.querySelectorAll(".container-lightbulb");
  containers.forEach(container => {
    container.classList.remove("current");
  });

  containers[currentIndex].classList.add("current");
}

async function next() {
  axios
		.post("next")
		.then(function (response) {
			console.log("Next action requested")
		})
		.catch(function (error) {
			console.log(error)
		})
}

function removeBulb(ip) {
  const index = smartBulbs.findIndex(item => item.ip === ip);
  const containers = document.querySelectorAll(".container-lightbulb");
  containers[index].remove()
}


document.getElementById("toggle").addEventListener('click', toggle);
document.getElementById("next").addEventListener('click', next);