from twisted.internet.defer import inlineCallbacks
from autobahn.twisted.wamp import ApplicationSession, ApplicationRunner
import multiprocessing
from twisted.internet import reactor
from oslo_log import log
from oslo_config import cfg
from multiprocessing import Process, Pipe
import time

LOG = log.getLogger(__name__)

wamp_opts = [
    cfg.StrOpt('wamp_ip',
               default='127.0.0.1',
               help=('URL of wamp broker')),
    cfg.IntOpt('wamp_port',
               default=8181,
               help='port wamp broker'),
    cfg.StrOpt('wamp_realm',
               default='s4t',
               help=('realm broker')),
]
CONF = cfg.CONF
CONF.register_opts(wamp_opts, 'wamp')

q_rpc=None

class RPCWampClientManager(ApplicationSession):
    
    def __init__(self, config=None):
        ApplicationSession.__init__(self, config)
        LOG.info("RPC wamp manager created")
        global q_rpc
        self.pipe=q_rpc
    
    @inlineCallbacks
    def onJoin(self, details):
        LOG.info('RPC Wamp Session ready')
        while True:
            time.sleep(.01)
            if self.pipe.poll():
                rpc=self.pipe.recv()
                try:
                    res = yield self.call(rpc,)
                    self.pipe.send(format(res))
                except Exception as e:
                    print(format(e))

        
            
class RPCWampClient:
    def __init__(self,ip,port,realm):
        self.ip=unicode(ip)
        self.port=unicode(port)
        self.realm=unicode(realm)
        self._url = "ws://"+self.ip+":"+self.port+"/ws"
        self.runner = ApplicationRunner(url=unicode(self._url), realm=self.realm,
                                        #debug=True, debug_wamp=True, debug_app=True
                                        )
    def start(self):
        self.runner.run(RPCWampClientManager, start_reactor=False)
        
        
class RPC_Wamp_Client:    
    
    def __init__(self):
        self.ip=unicode(CONF.wamp.wamp_ip)
        self.port=unicode(CONF.wamp.wamp_port)
        self.realm=unicode(CONF.wamp.wamp_realm)
        client = RPCWampClient(self.ip,self.port,self.realm)
        client.start()
        global q_rpc
        #q_rpc = multiprocessing.Queue()
        self.parent_conn, q_rpc = Pipe()
        multi = multiprocessing.Process(target=reactor.run,args=())
        multi.start()
        
    def rpc_call(self,rpc):
        self.parent_conn.send(rpc)
        x=''
        while True:
            time.sleep(.01)
            if self.parent_conn.poll():
                x= self.parent_conn.recv()
                break
        return x


'''
from autobahn.twisted.wamp import ApplicationSession
from twisted.internet.defer import inlineCallbacks
from autobahn.twisted.wamp import ApplicationRunner


class RPCCaller(ApplicationSession):
    @inlineCallbacks
    def onJoin(self, details):
        print("session ready")
        print details
        try:
            #stack4things.iotronic.conductor.function
            res = yield self.call(u'stack4things.test',)
            print("call result: {}".format(res))
        except Exception as e:
            print("call error: {0}".format(e))
        
        exit()

runner = ApplicationRunner(url=u"ws://localhost:8181/ws", realm=u"s4t",details='0000')
runner.run(RPCCaller)
'''