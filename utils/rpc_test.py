from twisted.internet.defer import inlineCallbacks
from autobahn.twisted.wamp import ApplicationSession, ApplicationRunner
import multiprocessing
from twisted.internet import reactor
from oslo_log import log
from oslo_config import cfg
from multiprocessing import Process, Pipe


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

class RPCWampManager(ApplicationSession):
    
    def __init__(self, config=None):
        ApplicationSession.__init__(self, config)
        LOG.info("RPC wamp manager created")
        global q_rpc
        self.pipe=q_rpc
    
    @inlineCallbacks
    def onJoin(self, details):
        LOG.info('RPC Wamp Session ready')
        print self._session
        while True:
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
        self.runner.run(RPCWampManager, start_reactor=False)
        
        
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
        x=self.parent_conn.recv()
        return x
        #q_rpc.put(rpc)

r=RPC_Wamp_Client()
res=r.rpc_call(u'stack4things.test')
print res,'qqqqqqqqqqqqqqqqqqqqqq'
import time
time.sleep(3)
res=r.rpc_call(u'stack4things.test')
print res






