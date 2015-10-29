from twisted.internet.defer import inlineCallbacks
from autobahn.twisted.wamp import ApplicationSession, ApplicationRunner
import multiprocessing
from twisted.internet import reactor

class RPCWampManager(ApplicationSession):
    
    def __init__(self, config=None):
        ApplicationSession.__init__(self, config)
        print("component created")

    def onConnect(self):
        print("transport connected")
        self.join(self.config.realm)

    def onChallenge(self, challenge):
        print("authentication challenge received")

    #def onLeave(self, details):
    #    print("session left")
    #    import os, signal
    #    os.kill(multi.pid, signal.SIGKILL)

    def onDisconnect(self):
        print("transport disconnected")
    
    @inlineCallbacks
    def onJoin(self, details):
        print("session ready")

        def add2(x, y):
            return x + y
        
        def test():
            return u'hello!'
        
        def registration(board,session):
            return u'registred board'

        try:
            yield self.register(test, u'stack4things.conductor.rpc.test')
            yield self.register(registration, u'stack4things.conductor.rpc.registration')
            print("procedure registered")
        except Exception as e:
            print("could not register procedure: {0}".format(e))
            
class RPCWampServer:
    def __init__(self,ip,port,realm):
        self.ip=unicode(ip)
        self.port=unicode(port)
        self.realm=unicode(realm)
        self._url = "ws://"+self.ip+":"+self.port+"/ws"
        self.runner = ApplicationRunner(url=unicode(self._url), realm=self.realm,
                                        #debug=True, debug_wamp=True, debug_app=True
                                        )

    def start(self):
        # Pass start_reactor=False to all runner.run() calls
        self.runner.run(RPCWampManager, start_reactor=False)
        
        
class RPC_Wamp_Server:    
    
    def __init__(self,ip,port,realm):
        server = RPCWampServer(ip,port,realm)
        server.start()
        multi = multiprocessing.Process(target=reactor.run, name='reactor',args=())
        multi.start()
        

