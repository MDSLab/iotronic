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
(function() {
  var WebSocketClient, bindSockets, net, wst_client;

  WebSocketClient = require('websocket').client;

  net = require("net");

  bindSockets = require("./bindSockets");

  module.exports = wst_client = (function() {
    function wst_client() {
      this.tcpServer = net.createServer();
    }

    wst_client.prototype.start = function(localPort, wsHostUrl, remoteAddr) {
      this.tcpServer.listen(localPort);
      return this.tcpServer.on("connection", (function(_this) {
        return function(tcpConn) {
          var url, wsClient;
          console.log("Connection detected");
          wsClient = new WebSocketClient();
          wsClient.on('connectFailed', function(error) {
            console.log('WS connect error: ' + error.toString());
            return tcpConn.destroy();
          });
          wsClient.on('connect', function(wsConn) {
            console.log('WebSocket connected, binding tunnel');
            return bindSockets(wsConn, tcpConn);
          });
          if (remoteAddr) {
            url = "" + wsHostUrl + "/?dst=" + remoteAddr;
          } else {
            url = "" + wsHostUrl;
          }
          return wsClient.connect(url, 'tunnel-protocol');
        };
      })(this));
    };

    return wst_client;

  })();

}).call(this);