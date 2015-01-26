/*
The MIT License (MIT)
Copyright (c) 2014 Andrea Rocco Lotronto
Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:
The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.
THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
*/

var autobahn = require('autobahn');
var boards = {};
var express = require('express');

var url_wamp_router = "ws://localhost:8080/ws";  //example of url wamp router

var connection = new autobahn.Connection({
	url: url_wamp_router,
	realm: "s4t"
});




connection.onopen = function (session, details) {

	var rest = express();

	rest.get('/', function (req, res){

		console.log('POST::::'+req.originalUrl);
		var board = req.query.board
		var command = req.query.command

		if(boards[board] != undefined){
			//invia comando sul topic
			console.log("corretto");
			//ricavo una porta random
			var port = randomIntInc(6000,7000);
			session.publish("board.command", [board, command, port]);
			res.send("Command: "+command+" opening on port: "+port);
		}
		else
			res.send("ERROR");	

	});

	rest.get('/list/', function (req, res){
		
		var board_list='';
		
		for (var i in boards){
   			board_list += boards[i];
   		}

   		res.send('List of the board: '+board_list);
	});

	rest.listen(6655);

	console.log("Connesso al router WAMP");
   // Publish, Subscribe, Call and Register

   var onBoardConnected = function (args){
   	//registrare le schede che si connettono
   	if(args[1]=='connection'){
   		boards[args[0]] = args[0];
   		console.log("Connessa scehda:"+args[0]+" stato scheda:"+args[1]);
   		//DEBUGGG
   		console.log("Schede::"+boards.length);
   		for (var i in boards){
   			console.log('Key: '+i+' value: '+boards[i]);
   		}

   	}
   	if(args[1]=='disconnect'){
   		delete boards[args[0]];
   		console.log("Disconnessa scehda:"+args[0]+" stato scheda:"+args[1]);

   		//DEBUGGG
   		console.log("Schede::"+boards.length);
   		for (var i in boards){
   			console.log('Key: '+i+' value: '+boards[i]);
   		}
   	}   
   }

   session.subscribe("board.connection", onBoardConnected);
   console.log("Inscritto al topic board.connection");
};

connection.onclose = function (reason, details) {
   // handle connection lost
}

connection.open();

//Creare una funzione per un numero random della porta
function randomIntInc (low, high) {
    return Math.floor(Math.random() * (high - low + 1) + low);
}