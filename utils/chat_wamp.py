from autobahn.twisted.wamp import ApplicationRunner
from autobahn.twisted.wamp import ApplicationSession
from twisted.internet.defer import inlineCallbacks
from autobahn.twisted.util import sleep
from twisted.internet.defer import inlineCallbacks
import multiprocessing
from Crypto.PublicKey.pubkey import pubkey
import time

msg_queue=None

class ClientWamp:
    
    class Publisher(ApplicationSession):
        
        def __init__(self, config=None):
            ApplicationSession.__init__(self, config)
            print("component created")
        
        @inlineCallbacks
        def onJoin(self, details):
            print("Publisher session ready")
            while True:
                if not msg_queue.empty():
                    msg=msg_queue.get()
                    self.publish(u'board.connection', msg)
                yield sleep(1)

    class Subscriber(ApplicationSession):
        @inlineCallbacks
        def onJoin(self, details):
            print("Subscriber session ready")
    
            def oncounter(count):
                print("event received: {0}", count)
    
            try:
                yield self.subscribe(oncounter, u'board.connection')
                print("subscribed to topic")
            except Exception as e:
                print("could not subscribe to topic: {0}".format(e))    
    
    
    def __init__(self,ip,port,realm):
        self.ip=unicode(ip)
        self.port=unicode(port)
        self.realm=unicode(realm)
        self._url = "ws://"+self.ip+":"+self.port+"/ws"
        runner = ApplicationRunner(url=unicode(self._url), realm=self.realm)
        global msg_queue
        msg_queue = multiprocessing.Queue()
        multi = multiprocessing.Process(target=runner.run, args=(self.Subscriber,))
        multi.start()
        mult2 = multiprocessing.Process(target=runner.run, args=(self.Publisher,))
        mult2.start()
        
    def send(self,msg):
        msg_queue.put(msg)
        

c=ClientWamp('localhost','8181','s4t')

from sys import stdin
c.send('Hello!')
while True:
    userinput = stdin.readline()
    c.send(str(userinput))