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


var portTunnel , argv, client, host, localport, optimist, port, server, wsHost, wst, _, _ref, _ref1;

var _ = require("under_score");

optimist = require('optimist').usage("\nRun websocket tunnel and reverse tunnel such server or client.\nTo run websocket tunnel server: wstt.js -s 8080\nTo run websocket tunnel client: wstt.js -t localport:host:port ws://wshost:wsport\nNow connecting to localhost:localport is same as connecting to host:port on wshost\nIf websocket server is behind ssl proxy, then use \"wss://host:port\" in client mode\nFor security, you can \"lock\" the tunnel destination on server side, for eample:\nwstunnel -s 8080 -t host:port\nServer will tunnel incomming websocket connection to host:port only, so client can just run\n wstunnel -t localport ws://wshost:port\nIf client run:\n  wstunnel -t localpost:otherhost:otherport ws://wshost:port\n  * otherhost:otherport is ignored, tunnel destination is still \"host:port\" as specified on server.\n").string("s").string("t").alias('t', "tunnel").describe('s', 'run as server, specify listen port').describe('tunnel', 'run as tunnel client, specify localport:host:port');


  argv = optimist.argv;

  if (_.size(argv) === 2) {
    return console.log(optimist.help());
  }

  if (argv.s && !argv.r) {
    wst = require("../lib/wst");
    if (argv.t) {
      _ref = argv.t.split(":"), host = _ref[0], port = _ref[1];
      server = new wst.server(host, port);
    } 
    else {
      server = new wst.server;
    }
    server.start(argv.s);
  }else if (argv.t) {
    require("../lib/https_override");
    wst = require("../lib/wst");
    client = new wst.client;
    wsHost = _.last(argv._);
    _ref1 = argv.t.split(":"), localport = _ref1[0], host = _ref1[1], port = _ref1[2];
    if (host && port) {
      client.start(localport, wsHost, "" + host + ":" + port);
    } else {
      client.start(localport, wsHost);
    }
  }else if (argv.r) {
    if (argv.s){
      require("../lib/https_override");
      wst = require("../lib/wst");
      server = new wst.server_reverse;
      server.start(argv.s);
    }
    else{
      require("../lib/https_override");
      wst = require("../lib/wst");
      client = new wst.client_reverse;
      wsHost = _.last(argv._);
      var test = argv.r.split(":");
      _ref1 = argv.r.split(":"), portTunnel = _ref1[0], host = _ref1[1], port =_ref1[2];
      client.start(portTunnel, wsHost, "" + host + ":" + port);
      
    } 
  } else {
    return console.log(optimist.help());
  }