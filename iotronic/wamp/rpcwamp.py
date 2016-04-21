#  Licensed under the Apache License, Version 2.0 (the "License"); you may
#  not use this file except in compliance with the License. You may obtain
#  a copy of the License at
#
#       http://www.apache.org/licenses/LICENSE-2.0
#
#  Unless required by applicable law or agreed to in writing, software
#  distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#  WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#  License for the specific language governing permissions and limitations
#  under the License.

import multiprocessing

from autobahn.twisted.wamp import ApplicationRunner
from autobahn.twisted.wamp import ApplicationSession
from twisted.internet.defer import inlineCallbacks

from oslo_config import cfg
from oslo_log import log
from twisted.internet import reactor


from multiprocessing import Pipe


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


class RPCWampServerManager(ApplicationSession):

    def __init__(self, config=None):
        ApplicationSession.__init__(self, config)
        LOG.info("RPC wamp manager created")

    '''
    #unused methods
    def onConnect(self):
        print("transport connected")
        self.join(self.config.realm)

    def onChallenge(self, challenge):
        print("authentication challenge received")

    def onLeave(self, details):
        print("session left")
        import os, signal
        os.kill(multi.pid, signal.SIGKILL)

    def onDisconnect(self):
        print("transport disconnected")
    '''

    @inlineCallbacks
    def onJoin(self, details):
        LOG.info('RPC Wamp Session ready')
        import iotronic.wamp.functions as fun
        self.subscribe(fun.leave_function, 'wamp.session.on_leave')

        try:
            yield self.register(fun.echo,
                                u'stack4things.echo')
            yield self.register(fun.registration,
                                u'stack4things.register')
            yield self.register(fun.registration_uuid,
                                u'stack4things.register_uuid')

            LOG.info("Procedures registered")
        except Exception as e:
            LOG.error("could not register procedure: {0}".format(e))


class RPCWampServer(object):

    def __init__(self, ip, port, realm):
        self.ip = unicode(ip)
        self.port = unicode(port)
        self.realm = unicode(realm)
        self._url = "ws://" + self.ip + ":" + self.port + "/ws"
        self.runner = ApplicationRunner(
            url=unicode(self._url),
            realm=self.realm,
            # debug = True, debug_wamp = True, debug_app = True
        )
        self.runner.run(RPCWampServerManager, start_reactor=False)


class RPCWampManagerClient(ApplicationSession):
    """An application component calling the different backend procedures.

    """

    @inlineCallbacks
    def onJoin(self, details):
        LOG.debug("session attached")
        rpc = self.config.extra['rpc']
        args = self.config.extra['args']
        self.pipe_out = self.config.extra['pipe']
        res = {'response': '', 'error': ''}
        try:
            res['response'] = yield self.call(rpc, args)
            res['error'] = 0
        except Exception as e:
            LOG.error(e)
            res['response'] = e
            res['error'] = 1
        self.pipe_out.send(res)
        self.leave()

    def onDisconnect(self):
        pass
        #reactor.stop()


class RPCWampClient(object):

    def __init__(self, ip, port, realm, rpc, args, b_a_ext):
        self.ip = unicode(ip)
        self.port = unicode(port)
        self.realm = unicode(realm)
        self._url = "ws://" + self.ip + ":" + self.port + "/ws"

        self.runner = ApplicationRunner(
            url=unicode(self._url),
            realm=self.realm,
            extra={'rpc': rpc, 'args': args, 'pipe': b_a_ext},
            # debug = False, debug_wamp = False, debug_app = False
        )
        self.runner.run(RPCWampManagerClient, start_reactor=False)


class RPC_Wamp(object):

    def __init__(self):
        self.ip = unicode(CONF.wamp.wamp_ip)
        self.port = unicode(CONF.wamp.wamp_port)
        self.realm = unicode(CONF.wamp.wamp_realm)
        self.server = RPCWampServer(self.ip, self.port, self.realm)
        self.b_a_int, self.b_a_ext = Pipe()
        server_process = multiprocessing.Process(target=reactor.run, args=())
        server_process.start()

    def rpc_call(self, rpc, *args):
        res = ''
        RPCWampClient(
            self.ip, self.port, self.realm, rpc, args, self.b_a_ext)
        client_process = multiprocessing.Process(target=reactor.run, args=())
        client_process.start()

        while True:
            if self.b_a_int.poll():
                res = self.b_a_int.recv()
                client_process.join()
                break
        if res['error'] == 0:
            return res['response']
        else:
            return {'result': 1}
