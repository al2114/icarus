var http = require('http');
var mqtt = require('mqtt');
var jsonfile = require('jsonfile');

var p_file = "./data/profiles.json";
var profiles = require("./data/profiles.json");


// Environment state
var is_on = Boolean(false);
var curr_profile = "p_default";
var curr_data = {
	'name': "",
	'temp': 25.52232,
	'hum': 50
};
	
// Begin MQTT Client to handle device data

var client = mqtt.connect('mqtt://localhost');

client.on('connect', function() {
	console.log("Web client connected!");
	topic = ["esys/icarus/status","esys/icarus/alarm"];
	client.subscribe(topic);
	console.log("Web client subscribed to " + topic);
})


client.on('message', function (topic, message) {

	console.log("Message: " + message.toString());
	msg = JSON.parse(message);

	if(topic === "esys/icarus/alarm" && msg.alarm === "request"){
		mqtt_send_profile();
	}else if (topic === "esys/icarus/status"){
  	// message is Buffer 
  	if(is_on){
	  	curr_data = msg;
		}
	  console.log(curr_data);
	}
})

// Begin HTTP Server to respond to web requests 

http.createServer(function(request, response) {

	// Set CORS headers

	response.setHeader('Access-Control-Allow-Origin', '*');
	response.setHeader('Access-Control-Request-Method', '*');
	response.setHeader('Access-Control-Allow-Methods', 'POST, GET');
	response.setHeader('Access-Control-Allow-Headers', '*');


	var reqdata = [];

	var body = "Hello from webserver!";
	console.log("\nIncoming " + request.method + " request:");
	console.log("\tUrl: " + request.url);

	request.on('data', function(chunk) {
	  reqdata.push(chunk);
	}).on('end', function() {
	  reqdata = Buffer.concat(reqdata).toString();

		console.log("\tData: " + reqdata);
	  // at this point, `data` has the entire request body stored in it as a string

		switch(request.url) {
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
			case('/data'):
				if (request.method === 'GET') {
					console.log("Getting new data");
					body = get_data(reqdata);
				} else {
		    	response.statusCode = 404;
				}
				break;
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
}).listen(8080);

function check_on() {
	var check = is_on?'1':'0';
	console.log(check);
	return check;
}

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

function add_profile(profile_string) {

	var profile = JSON.parse(profile_string)	
	p = {
		'name': profile.name,
		'temp': parseFloat(profile.temp),
		'hum': parseFloat(profile.hum)
	};

	profiles[profile.pid] = p;

	console.log(profiles[profile.pid]);
	jsonfile.writeFile(p_file, profiles, function (err) {
  	console.error(err);
	})
	return 1;
}

function set_profile(p_string) {
	curr_profile = (JSON.parse(p_string)).profile
	mqtt_send_profile();
	return 1;
}

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
