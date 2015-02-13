#########################################################################################
##
## The MIT License (MIT)
##
## Copyright (c) 2014 Andrea Rocco Lotronto
##
## Permission is hereby granted, free of charge, to any person obtaining a copy
## of this software and associated documentation files (the "Software"), to deal
## in the Software without restriction, including without limitation the rights
## to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
## copies of the Software, and to permit persons to whom the Software is
## furnished to do so, subject to the following conditions:
##
## The above copyright notice and this permission notice shall be included in all
## copies or substantial portions of the Software.
##
## THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
## IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
## FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
## AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
## LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
## OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
## SOFTWARE.
########################################################################################

from autobahn.twisted.wamp import ApplicationSession
from autobahn.twisted.wamp import ApplicationRunner
from twisted.internet.defer import inlineCallbacks

urlWampRouter = "ws://172.17.3.139:8181/ws"
realmWampRouter = "s4t"

class S4TWampServer(ApplicationSession):

	@inlineCallbacks
	def onJoin(self, details):
		self.connectedBoard = {}
		self.topic_connection = self.config.extra['topic_connection']
		self.topic_command = self.config.extra['topic_command']
		
		print("Sessio attached [Connect to WAMP Router]")

		def onMessage(*args):
			#DEBUG Message
			print args
			
			if args[1] == 'connection':
				print(args[0]+ " connessa")
				self.connectedBoard[args[0]] = args[0]
				print self.connectedBoard
				
			if args[1] == 'disconnect':
				print(args[0]+ " disconnessa")
				del self.connectedBoard[args[0]]
				print self.connectedBoard

		try:			
			yield self.subscribe(onMessage, self.topic_connection) #threads.deferToThread(self.subscribe(onMessage, self.topic_connection))
			print ("Subscribed to topic: "+self.topic_connection)

		except Exception as e:
			print("could not subscribe to topic:" +self.topic_connection)

		#def pubB(msg=''):
		yield self.publish(self.topic_connection,'pippo')#threads.deferToThread(self.publish(self.topic_connection,'pippo'))

class s4_wamp_server:
	def __init__(self, t_connection, t_command):
		self.topic_connection = t_connection
		self.topic_command = t_command
				
	def start(self):		
		self.runner = ApplicationRunner(url = urlWampRouter, realm = realmWampRouter, extra={'topic_connection':self.topic_connection, 'topic_command':self.topic_command})	
		self.runner.run(S4TWampServer)

if __name__ == '__main__':

	server = s4_wamp_server('board.connection', 'board.command')
	server.start()