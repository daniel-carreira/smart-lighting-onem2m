axios.defaults.baseURL = 'http://localhost:8000/onem2m';
axios.defaults.headers.post['Content-Type'] = 'application/vnd.api+json';
axios.defaults.headers.post['Accept'] = 'application/vnd.api+json';

const url = 'ws://broker.emqx.io:8083/mqtt';
let currentIndex = 0;

//mqtt
const client = mqtt.connect(url);
client.on('connect', function () {
  console.log('Connected to broker');

  // Subscribe to a topic
  client.subscribe('test', function (err) {});
});

// Receive messages
client.on('message', function (topic, message) {
  console.log(message.toString());
});

//Array of smart bulbs
let smartBulbs = [
  { ip: "ip", name: "Smart Bulb 1" },
  { ip: "ip", name: "Smart Bulb 2" },
  { ip: "ip", name: "Smart Bulb 3" },
  { ip: "ip", name: "Smart Bulb 4" },
  { ip: "ip", name: "Smart Bulb 5" }
];


// Loop through the array and create the smart-bulb containers
const container = document.querySelector(".container-smart-switch");
smartBulbs.forEach((bulb, index) => {
  // Create the smart-bulb container
  const bulbContainer = document.createElement("div");
  bulbContainer.classList.add("container");

  // Add the "current" class to the first lightbulb
  if (index === currentIndex) {
    bulbContainer.classList.add("current");
  }

  // Create the smart-bulb label
  const bulbLabel = document.createElement("div");
  bulbLabel.textContent = bulb.name;
  bulbContainer.appendChild(bulbLabel);

  // Append the smart-bulb container to the container element
  container.appendChild(bulbContainer);
});


document.getElementById("toggle").addEventListener('click', toggle);
document.getElementById("next").addEventListener('click', next);


async function getData(url) {
	axios
		.get(url)
		.then(function (response) {
			// smartBulbs = response.data;
		})
		.catch(function (error) {
			console.log(error);
		});
}

function next() {
  let containers = document.querySelectorAll(".container");
  containers[currentIndex].classList.remove("current"); // Remove "current" class from previous container
  currentIndex = (currentIndex + 1) % smartBulbs.length; // Update the current index
  containers[currentIndex].classList.add("current"); // Add "current" class to the next container
}

async function toggle(data) {
  axios
    .post(url, data)
    .then(function (response) {
		if(response.data == "on"){
			containers[data.index].classList.add("on"); // Change state associated with lightbulb
		}else{
			containers[data.index].classList.remove("on"); // Change state associated with lightbulb
		}
	 })
    .catch(function (error) {
      console.log(error);
    });
}


// Define a CSS style rule for the "current" class
const style = document.createElement('style');
style.innerHTML = `
  .container.current {
    outline: 2px solid black;
  }
  .container.on {
    background-color: #fdfa72;
  }
`;
document.head.appendChild(style);
