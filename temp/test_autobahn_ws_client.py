from autobahn.twisted.websocket import WebSocketClientProtocol
from autobahn.twisted.websocket import WebSocketClientFactory
from autobahn.twisted.websocket import connectWS

from twisted.internet import reactor

from twisted.python import log
import sys
log.startLogging(sys.stdout)
import threading
import Queue

# ----- twisted ----------
class _WebSocketClientProtocol(WebSocketClientProtocol):
    def __init__(self, factory):
        self.factory = factory

    def onOpen(self):
        #log.debug("Client connected")
        self.factory.protocol_instance = self
        self.factory.base_client._connected_event.set()

class _WebSocketClientFactory(WebSocketClientFactory):
    def __init__(self, *args, **kwargs):
        WebSocketClientFactory.__init__(self, *args, **kwargs)
        self.protocol_instance = None
        self.base_client = None

    def buildProtocol(self, addr):
        return _WebSocketClientProtocol(self)
# ------ end twisted -------

class BaseWBClient(object):

    def __init__(self, websocket_settings):
        #self.settings = websocket_settings
        # instance to be set by the own factory
        self.factory = None
        # this event will be triggered on onOpen()
        self._connected_event = threading.Event()
        # queue to hold not yet dispatched messages
        self._send_queue = Queue.Queue()
        self._reactor_thread = None

    def connect(self):
        
        self.factory = _WebSocketClientFactory(
                                "ws://172.17.4.26:8181",
                                debug=True)
        self.factory.base_client = self
        
        c = connectWS(self.factory)
        
        self._reactor_thread = threading.Thread(target=reactor.run,
                                               args=(False,))
        self._reactor_thread.daemon = True
        self._reactor_thread.start()

    def send_message(self, body):
        if not self._check_connection():
            return
        log.msg("Queing send")
        self._send_queue.put(body)
        reactor.callFromThread(self._dispatch)

    def _check_connection(self):
        if not self._connected_event.wait(timeout=10):
            log.err("Unable to connect to server")
            self.close()
            return False
        return True

    def _dispatch(self):
        log.msg("Dispatching")
        while True:
            try:
                body = self._send_queue.get(block=False)
            except Queue.Empty:
                break
            self.factory.protocol_instance.sendMessage(body)

    def close(self):
        reactor.callFromThread(reactor.stop)

import time
def Ppippo(coda):
        while True:
            coda.send_message('YOOOOOOOO')
            time.sleep(5)

if __name__ == '__main__':
    
    ws_setting = {'host':'172.17.4.126', 'port':8181}

    client = BaseWBClient(ws_setting)

    t1 = threading.Thread(client.connect())
    t11 = threading.Thread(Ppippo(client))
    t11.start()
    t1.start()

    #client.connect()
    client.send_message('pippo')

    
    