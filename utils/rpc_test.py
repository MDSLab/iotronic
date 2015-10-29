from autobahn.twisted.wamp import ApplicationSession
from twisted.internet.defer import inlineCallbacks
from autobahn.twisted.wamp import ApplicationRunner


class RPCCaller(ApplicationSession):
    @inlineCallbacks
    def onJoin(self, details):
        print("session ready")
        try:
            res = yield self.call(u'stack4things.conductor.rpc.test',)
            print("call result: {}".format(res))
        except Exception as e:
            print("call error: {0}".format(e))

runner = ApplicationRunner(url=u"ws://localhost:8181/ws", realm=u"s4t")
runner.run(RPCCaller)


