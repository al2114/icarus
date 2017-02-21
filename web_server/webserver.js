// Including dependencies
var http = require('http');
var mqtt = require('mqtt');
var jsonfile = require('jsonfile');


// Settings
var MQTT_HOST = "mqtt://192.168.0.10"
var SERVER_PORT = 8080
var P_FILE = "./data/profiles.json";

// Default environment state
var is_on = Boolean(false);
var curr_profile = "p_default";
var curr_data = {
	'name': "",
	'temp': 25.52232,
	'hum': 50
};
	
// Load in all profiles into var
var profiles = require("./data/profiles.json");


//-----------------------------------------------
//				- MQTT Handler -
//	This section handles all the server-device
//	services including receiving data and device
//	initialisation requests. 
//-----------------------------------------------

var client = mqtt.connect(MQTT_HOST);

// MQTT client connect
client.on('connect', function() {
	console.log("Web client connected!");

	// Topic 'icarus/status' listens to incoming sensor data
	// Topic 'icarus/alarm' listens for device intialisation 
	topic = ["esys/icarus/status","esys/icarus/alarm"];
	client.subscribe(topic);

	console.log("Web client subscribed to " + topic);
})

// MQTT message handler
client.on('message', function (topic, message) {

	console.log("Message: " + message.toString());
	msg = JSON.parse(message);

	if(topic === "esys/icarus/alarm" && msg.alarm === "request"){
		// Initalisation request
		mqtt_send_profile();
	}else if (topic === "esys/icarus/status"){
  	// message is Buffer 
  	if(is_on){
  		// Replace current data with new data
	  	curr_data = msg;
		}
	  console.log(curr_data);
	}
})

//-----------------------------------------------
//				- HTTP Handler -
//	This section handles all the requests from
//  the web control panel interface. Services
//  include sensor data polling, device power
//  toggle, requesting for profiles, updating
//  profiles, creating profiles etc.
//-----------------------------------------------


// Begin HTTP Server to respond to web requests 

http.createServer(function(request, response) {

	// Set CORS headers to allow for localhost connect (Needed by some browsers)
	response.setHeader('Access-Control-Allow-Origin', '*');
	response.setHeader('Access-Control-Request-Method', '*');
	response.setHeader('Access-Control-Allow-Methods', 'POST, GET');
	response.setHeader('Access-Control-Allow-Headers', '*');


	var reqdata = [];

	var body = "Hello from webserver!";
	console.log("\nIncoming " + request.method + " request:");
	console.log("\tUrl: " + request.url);

	// Handling HTTP requests
	request.on('data', function(chunk) {
	  reqdata.push(chunk);
	}).on('end', function() {
	  reqdata = Buffer.concat(reqdata).toString();

		console.log("\tData: " + reqdata);
	  // at this point, `data` has the entire request body stored in it as a string

	  // Depending on the HTTP url access, perform different services
		switch(request.url) {

			// The switch service either returns the power
			// of the machine if GET request, or toggles the
			// power of the machine and returns the state
			// if POST
			case('/switch'):
				if (request.method === 'GET') {
					console.log("Checking if machine is on");
					body = check_on();
				} else if (request.method === 'POST') {
					console.log("Toggled output");
					toggle_switch(reqdata);
					body = check_on();
				} else {
		    	response.statusCode = 404;
				}
				break;

			// The data service responds to client
			// with last heard sensor data, only
			// handles GET requests
			case('/data'):
				if (request.method === 'GET') {
					console.log("Getting new data");
					body = get_data(reqdata);
				} else {
		    	response.statusCode = 404;
				}
				break;

			// GET profile will respond with all profile information
			// to preload the profile interface on the web CP
			// POST profile will add a new profile to the bank
			// of current profiles
			case('/profile'):
				if (request.method === 'GET') {
					console.log("Retrieving all profiles");
					body = get_profiles();
				} else if (request.method === 'POST') {
					console.log("Adding profile");
					body = add_profile(reqdata);
				} else {
		    	response.statusCode = 404;
				}
				break;
			// set_profile is used for the web CP to modify
			// the loaded profile on the device, it takes in
			// the profile ID and sends the profile based on
			// settings stored on the server
			case('/set_profile'):
				if (request.method === 'POST') {
					body = set_profile(reqdata);
				}
				break;
			default:
		    response.statusCode = 404;
		}

		console.log(body)
  	response.end(body.toString());

	});
}).listen(SERVER_PORT);


// Returns the state of the device as a string of 1 or 0
function check_on() {
	var check = is_on?'1':'0';
	console.log(check);
	return check;
}

// Toggles the state, if set off, resets the data stored
function toggle_switch(state) {
	if(state === 'on') {
		console.log("Turning device on");
		is_on = Boolean(true);
	} else {
		console.log("Turning device off");
		is_on = Boolean(false);
		curr_data = {
			'name': "",
			'temp': 0,
			'hum': 0
		}
	}
	var msg = { 'power': is_on?1:0 }
  client.publish('esys/icarus/power', JSON.stringify(msg));
}

function get_data(req) {
	return JSON.stringify(curr_data);
}

function get_profiles() {
	return JSON.stringify(profiles);
}

// Adds profile data into list of profiles
// and backsup new profile list onto local file
function add_profile(profile_string) {

	var profile = JSON.parse(profile_string)	
	p = {
		'name': profile.name,
		'temp': parseFloat(profile.temp),
		'hum': parseFloat(profile.hum)
	};

	profiles[profile.pid] = p;

	console.log(profiles[profile.pid]);
	jsonfile.writeFile(P_FILE, profiles, function (err) {
  	console.error(err);
	})
	return 1;
}

// Sets the profile according to the profile ID
// and requests for the MQTT client to send
// the new settings to the device
function set_profile(p_string) {
	curr_profile = (JSON.parse(p_string)).profile
	mqtt_send_profile();
	return 1;
}

// Sends profile settings to device via MQTT
// based on curr_profile profile ID
function mqtt_send_profile() {
	key = curr_profile
		var params = 	{
			'plant': key,
			'temp': profiles[key].temp,
			'hum': profiles[key].hum
		}
	console.log(params)
  client.publish('esys/icarus/params', JSON.stringify(params));
}
