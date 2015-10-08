
wampAddress = 'ws://172.17.3.139:8181/ws'
wampRealm = 's4t'

#from threading import Thread

from autobahn.twisted.wamp import ApplicationRunner
from autobahn.twisted.wamp import ApplicationSession
from twisted.internet.defer import inlineCallbacks

#import per test
from twisted.internet.defer import DeferredQueue
from twisted.internet import threads

#Classe autobahn per ka gestione della comunicazione con i dispositivi remoti
class AutobahnMRS(ApplicationSession):
	@inlineCallbacks
	def onJoin(self, details):
		print("Sessio attached [Connect to WAMP Router] Sub")

		def onMessage(*args):
			print args

		try:
			yield self.subscribe(onMessage, 'test')
			print ("Subscribed to topic: test")

		except Exception as e:
			print("Exception:" +e)


#Classe autobahn per la gestione della comunicazione interna
class AutobahnIM(ApplicationSession):

	@inlineCallbacks
	def onJoin(self, details):
		print("Sessio attached [Connect to WAMP Router] Pub")

		try:
			yield self.publish('test','YOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOO')
			print ("Publish to topic: test")

		except Exception as e:
			print("Exception:" +e)



#Classe per la gestione della comunicazioni con i dispositivi remoti
class ManageRemoteSystem:
	def __init__(self):
		self.runner = ApplicationRunner(url= wampAddress, realm = wampRealm)

	def start(self):
		self.runner.run(AutobahnMRS, start_reactor=False);


#Classe per la gestione della comunicazione interna al ManageRemoteSystem
class InternalMessages:
	def __init__(self):
		self.runner = ApplicationRunner(url= wampAddress, realm = wampRealm)

	def start(self):
		self.runner.run(AutobahnIM, start_reactor=False);

#Classe principale per il servizio iotronic
#class S4tServer:

def something():
	count = 0
	while True:
		print('something:', count)
		yield sleep(1)
		count+=1

if __name__ == '__main__':
	
	#import multiprocessing

	server = ManageRemoteSystem()
	#sendMessage = InternalMessages()
	server.start()
	#sendMessage.start()
	
	from twisted.internet import reactor
	reactor.run()
	#thread1 = Thread(target = reactor.run())
	#thread2 = Thread(target = something())

	#thread2.start()
	#thread1.start()
	
	#thread1.daemon = True
	#thread2.daemon = True

	#thread2.join()
	#thread1.join()

