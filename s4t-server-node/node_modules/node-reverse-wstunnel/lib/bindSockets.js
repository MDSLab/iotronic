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
  var bindSockets;

  module.exports = bindSockets = function(wsconn, tcpconn) {
    wsconn.__paused = false;
    wsconn.on('message', function(message) {
      if (message.type === 'utf8') {
        return console.log('Error, Not supposed to received message ');
      } else if (message.type === 'binary') {
        if (false === tcpconn.write(message.binaryData)) {
          wsconn.socket.pause();
          wsconn.__paused = true;
          return "";
        } else {
          if (true === wsconn.__paused) {
            wsconn.socket.resume();
            return wsconn.__paused = false;
          }
        }
      }
    });
    tcpconn.on("drain", function() {
      wsconn.socket.resume();
      return wsconn.__paused = false;
    });
    wsconn.on("overflow", function() {
      return tcpconn.pause();
    });
    wsconn.socket.on("drain", function() {
      return tcpconn.resume();
    });
    tcpconn.on("data", function(buffer) {
      return wsconn.sendBytes(buffer);
    });
    wsconn.on("error", function(err) {
      return console.log((new Date()) + 'ws Error ' + err);
    });
    tcpconn.on("error", function(err) {
      return console.log((new Date()) + 'tcp Error ' + err);
    });
    wsconn.on('close', function(reasonCode, description) {
      console.log((new Date()) + 'ws Peer ' + wsconn.remoteAddress + ' disconnected for: '+description);
      return tcpconn.destroy();
    });
    return tcpconn.on("close", function() {
      console.log((new Date()) + 'tunnel disconnected.');
      return wsconn.close();
    });
  };

}).call(this);
