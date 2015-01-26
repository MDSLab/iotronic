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

var WebSocketClient = require('websocket').client;
var net = require("net");

var bindSockets = require("./bindSockets_reverse");

wst_client_reverse = function() {
  this.wsClientForControll = new WebSocketClient();
}

wst_client_reverse.prototype.start = function(portTunnel, wsHostUrl, remoteAddr) {
  //Getting paramiter
  var url = require("url");
  var urlWsHostObj = url.parse(wsHostUrl);
  var _ref1 = remoteAddr.split(":"), remoteHost = _ref1[0], remotePort = _ref1[1];
  url = "" + wsHostUrl + "/?dst=" + urlWsHostObj.hostname+":"+portTunnel;
  //Connection to Controll WS Server
  this.wsClientForControll.connect(url, 'tunnel-protocol');
  
  this.wsClientForControll.on('connect', (function(_this){
    return function(wsConnectionForControll) {
      //console.log('wsClientForControll for  Controll connected');
      wsConnectionForControll.on('message', function(message) {
        //Only utf8 message used in Controll WS Socket
        //DEBUG MESSAGE FOR TESTING
        //console.log("Message for new TCP Connectio on WS Server");
          
        var parsing = message.utf8Data.split(":");

        //Managing new TCP connection on WS Server
        if (parsing[0] === 'NC'){

          //Identification of ID connection
          var idConnection = parsing[1];
  
          this.wsClientData = new WebSocketClient();
          this.wsClientData.connect(wsHostUrl+"/?id="+idConnection, 'tunnel-protocol');
          //DEBUG MESSAGE FOR TESTING
          //console.log("Call WS-Server for connect id::"+parsing[1]);

          //Management of new WS Client for every TCP connection on WS Server
          this.wsClientData.on('connect', (function(_this){
            return function(wsConnectionForData){
            //Waiting of WS Socket with WS Server
              wsConnectionForData.socket.pause();
              //DEBUG MESSAGE FOR TESTING
              //console.log("WS PAUSE");
              //console.log("Connected wsClientData to WS-Server for id "+parsing[1]+" on localport::"+wsConnectionForData.socket.localPort);
              console.log("Start PIPE wsConnectionForData TCP client to :"+remoteHost+":"+remotePort);
                
              tcpConnection(wsConnectionForData,remoteHost,remotePort);     
            }
          })(this));
        }
      });
    }
  })(this));
  
  //Management of WS Connection failed
  this.wsClientForControll.on('connectFailed', function(error) {
    console.log('WS connect error: ' + error.toString());
  });

};

function tcpConnection(wsConn,host,port){
  var tcpConn = net.connect({port: port,host: host},function(){
    });

  tcpConn.on("connect",function(){
    //DEBUG MESSAGE FOR TESTING
    //console.log((new Date()) + "CONNECTED TCP---->REMOTE");
    bindSockets(wsConn,tcpConn);
    //Resume of the WS Socket after the connection to WS Server
    wsConn.socket.resume();
    //DEBUG MESSAGE FOR TESTING
    //console.log("RESUME WS");
  });
}

module.exports = wst_client_reverse;