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
  
var WebSocketServer, bindSockets, http, net, url, wst_server_reverse;

WebSocketServer = require('websocket').server;
http = require('http');
url = require("url");
net = require("net");
bindSockets = require("./bindSockets_reverse");

var eventEmitter = require('events').EventEmitter;

var newWSTCP_DATA = new eventEmitter();

wst_server_reverse = function(dstHost, dstPort) {

  this.dstHost = dstHost;
  this.dstPort = dstPort;
  
  this.httpServer = http.createServer(function(request, response) {
    console.log((new Date()) + ' Received unhandled request for ' + request.url);
    response.writeHead(404);
    return response.end();
  });
      
  this.wsServerForControll = new WebSocketServer({
    httpServer: this.httpServer,
    autoAcceptConnections: false
    });
}

wst_server_reverse.prototype.start = function(port) {

  this.httpServer.listen(port, function() {
    return console.log((new Date()) + " Server is listening on port " + port);
  });
  
  this.wsServerForControll.on('request', (function(_this){
    return function(request){
      //One TCP Server for each client WS Request
      request.tcpServer = new net.createServer();

      var uri = url.parse(request.httpRequest.url, true);
      
      if (uri.query.dst != undefined){
        
        var remoteAddr = uri.query.dst;
        var hostComodo, portTcp;
        ref1 = remoteAddr.split(":"), hostComodo = ref1[0], portTcp = ref1[1];
     
        request.tcpServer.listen(portTcp);
        
        console.log("Created TCP server on port "+portTcp);
        
        request.wsConnectionForControll = request.accept('tunnel-protocol', request.origin);
        //DEBUG MESSAGE FOR TESTING
        console.log("WS Connectio for Control Created");

      }
      //REQUEST FOR WS SOCKET USED FOR DATA
      else{ 
        console.log("Request for Data WS Socket");
        newWSTCP_DATA.emit('created', request);
      }

      //Manage TCP Connection
      request.tcpServer.on('connection', (function(_this){
        
        return function(tcpConn){
          tcpConn.wsConnection;
          //Putting in pause the tcp connection waiting the new socket WS Socket for data
          tcpConn.pause();
        
          var idConnection = randomIntInc(1,1000);
          var msgForNewConnection = "NC:"+idConnection;
          
          request.wsConnectionForControll.sendUTF(msgForNewConnection);
  
          newWSTCP_DATA.on('created',(function(_this){
          return function(request){
            //DEBUG MESSAGE FOR TESTING
            //console.log(typeof(_this.wsConnection));            
            var uri = url.parse(request.httpRequest.url, true);
            //DEBUG MESSAGE FOR TESTING
            //console.log("TEEEEEEEEESTTTT::"+uri.query.id);
            if(idConnection == uri.query.id){
              //DEBUG MESSAGE FOR TESTING
              //console.log("TRUE")   
              //tcpConn.wsConnection = wsTCP;
              tcpConn.wsConnection = request.accept('tunnel-protocol', request.origin);
              bindSockets(tcpConn.wsConnection,tcpConn);
              //DEBUG MESSAGE FOR TESTING
              //console.log("Bind ws tcp");
              //Resuming of the tcp connection after WS Socket is just created
              tcpConn.resume();
              //DEBUG MESSAGE FOR TESTING
              //console.log("TCP RESUME");
              }
            }
          })(this));  
        }
      })(_this));

    }
  })(this));
};

function randomIntInc (low, high) {
    return Math.floor(Math.random() * (high - low + 1) + low);
}

module.exports = wst_server_reverse;