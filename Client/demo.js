//The function below is called after we start the form
function startConnect() {
    // Below we generate a random clientID
    clientID = "clientID-" + parseInt(Math.random() * 100);

	//Below we get the hostname and the port number from the filled in form
    host = document.getElementById("host").value;
    port = document.getElementById("port").value;

	//Below we print the output
    document.getElementById("messages").innerHTML += '<span>Connecting to: ' + host + ' on port: ' + port + '</span><br/>';
    document.getElementById("messages").innerHTML += '<span>Using the following client value: ' + clientID + '</span><br/>';

	//Below is the starter for the Paho connection's client
    client = new Paho.MQTT.Client(host, Number(port), clientID);

	//Below we handle the callback
    client.onConnectionLost = onConnectionLost;
    client.onMessageArrived = onMessageArrived;

	//Below we connect to the client that goes to our onConnect function
    client.connect({ 
        onSuccess: onConnect,
    });
}

//Below we start once the client is connected
function onConnect() {
    
	//Below we start the MQTT Broker topic that is filled in the form
    topic = document.getElementById("topic").value;

	//Below we prints the output
    document.getElementById("messages").innerHTML += '<span>Subscribing to: ' + topic + '</span><br/>';

	//Below we subscribe to the topic in the filled in form
    client.subscribe(topic);
}

//Below is called once the client losses the connection and/or the user stops the connection
function onConnectionLost(responseObject) {
    document.getElementById("messages").innerHTML += '<span>Connection Stopped!!!</span><br/>';
    if (responseObject.errorCode !== 0) {
        document.getElementById("messages").innerHTML += '<span>Error here: ' + + responseObject.errorMessage + '</span><br/>';
    }
}

//Below we start when get a message
function onMessageArrived(message) {
    console.log("onMessageArrived: " + message.payloadString);
    document.getElementById("messages").innerHTML += '<span>Topic: ' + message.destinationName + '  | ' + message.payloadString + '</span><br/>';
}

//Below we start when the user clicks on the stop button
function startDisconnect() {
    client.disconnect();
    document.getElementById("messages").innerHTML += '<span>Disconnected</span><br/>';
}