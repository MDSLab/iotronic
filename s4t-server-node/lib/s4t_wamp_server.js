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
var express = require('express');


s4t_wamp_server = function(){


}

s4t_wamp_server.prototype.start = function(restPort){


   var boards = {};
   var getIP = require('./getIP.js');
   var IPLocal = getIP('eth0', 'IPv4');

   var url_wamp_router = "ws://ip:port/ws";  //example of url wamp router

   var connection = new autobahn.Connection({
      url: url_wamp_router,
      realm: "s4t"
   });

   var topic_command = 'board.command'
   var topic_connection = 'board.connection'

   connection.onopen = function (session, details) {


   	var rest = express();

      rest.get('/', function (req, res){
         res.send('API: <br> http://'+IPLocal+':'+restPort+'/list   for board list');
      });

   	rest.get('/command/', function (req, res){

         //DEBUG Message
   		console.log('POST::::'+req.originalUrl);
   		var board = req.query.board
   		var command = req.query.command

   		if(boards[board] != undefined){
   			//DEBUG Message
            //
   			console.log("ID exsist");
   			//random port for reverse service
   			var port = randomIntInc(6000,7000);
   			session.publish(topic_command, [board, command, port]);
   			if(command == 'ssh'){
               res.send("ssh -p "+port+" root@"+IPLocal);   
            }
            if(command == 'ideino'){
               res.send("http://"+IPLocal+":"+port);
            }
            
   		}
   		else
   			res.send("Error: malformed REST ");	

   	});

   	rest.get('/list/', function (req, res){
   		
   		var board_list='';
   		
   		for (var i in boards){
      			board_list += boards[i];
               command_list = "ssh"
      		}

      		res.send('List of the board: '+board_list+'<br>'+'use URL: '+IPLocal+":"+'6655'+"/commad/?board=board_name&command=ssh|ideino");
   	});

   	rest.listen(restPort);
      console.log("Server REST started on: http://"+IPLocal+":"+restPort);

   	console.log("Connected to router WAMP");
      // Publish, Subscribe, Call and Register

      var onBoardConnected = function (args){
      	//registrare le schede che si connettono
      	if(args[1]=='connection'){
      		boards[args[0]] = args[0];
      		//DEBUGGG Message
            console.log("Board connected:"+args[0]+" board state:"+args[1]);
      		//DEBUGGG Message
      		console.log("List of board::"+boards.length);
      		for (var i in boards){
      			console.log('Key: '+i+' value: '+boards[i]);
      		}

      	}
      	if(args[1]=='disconnect'){
      		delete boards[args[0]];
      		//DEBUGGG
            console.log("Board disconnected:"+args[0]+" board state:"+args[1]);
      		//DEBUGGG
      		console.log("List of the board::"+boards.length);
      		for (var i in boards){
      			console.log('Key: '+i+' value: '+boards[i]);
      		}
      	}   
      }

      session.subscribe(topic_connection, onBoardConnected);
      console.log("Subsscribe to topic: "+topic_connection);
   };

   connection.onclose = function (reason, details) {
      // handle connection lost
   }

   connection.open();

}

//function for pseudo random number
function randomIntInc (low, high) {
    return Math.floor(Math.random() * (high - low + 1) + low);
}

module.exports = s4t_wamp_server;