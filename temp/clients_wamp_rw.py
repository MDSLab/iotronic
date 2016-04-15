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
from autobahn.twisted.wamp import ApplicationSessionFactory

from autobahn.twisted.websocket import WampWebSocketClientFactory

from autobahn.wamp.types import ComponentConfig

from twisted.internet.defer import inlineCallbacks
from twisted.internet import reactor, defer
from twisted.internet.endpoints import clientFromString
from twisted.python import log

import threading
import time
import sys
log.startLogging(sys.stdout)


##Global Variable for saving client writer session
sessio_writer=None


##    WAMP Application Class for Writer Client  ##
class AutobahnClientWriter(ApplicationSession):
	
	@inlineCallbacks
	def onJoin(self, details):
		
		global sessio_writer
		sessio_writer = self
		yield log.msg('Client Writer Connected')
######################################################

##    WAMP Application Class for Reader Client  ##
class AutobahnClientReader(ApplicationSession):

	@inlineCallbacks
	def onJoin(self, details):

		log.msg('Client Reader Connected')

		self.topic_reader = self.config.extra['topicReader']
		
		def onMessage(*args):
			#DEBUG Message
			log.msg('I receives',args)
			##New Class Parser for MSG
		
		try:			
			yield self.subscribe(onMessage, self.topic_reader) 
			print ("Subscribed to topic: "+self.topic_reader)

		except Exception as e:
			print("could not subscribe to topic:" +self.topic_reader)
######################################################

##          Principal class for inizialating and starting clients WAMP
class WampClient():

	def __init__(self, topicRead='board.connection'):#Sistemare
		
		self._topicRead = None
		self._debug = False
		self._debug_wamp = False
		self._debug_app = False
		
		self._factoryWriter = None
		self._factoryReader = None

		self._realm = None
		self._url = None
		
		self._extra = {'topicReader': topicRead}
		
	def connect(self, ip, port, realm):

		self._realm = realm
		self._url = 'ws://'+ip+':'+port+'/ws'
		self._reactor_thread = None

		self._session_factoryWriter = None
		self._session_factoryReader = None
	
		cfgReader = ComponentConfig(self._realm, self._extra)
		cfgWriter = ComponentConfig(self._realm, self._extra)
		
		self._session_factoryReader = ApplicationSessionFactory(cfgReader)
		self._session_factoryReader.session = AutobahnClientReader

		self._session_factoryWriter = ApplicationSessionFactory(cfgWriter)
		self._session_factoryWriter.session = AutobahnClientWriter


		self._factoryReader = WampWebSocketClientFactory(self._session_factoryReader, url = self._url, 
				#debug = self._debug, debug_wamp = self._debug_wamp
				)
		
		self._factoryWriter = WampWebSocketClientFactory(self._session_factoryWriter, url = self._url, 
				#debug = self._debug, debug_wamp = self._debug_wamp
				)

		self._reactor_thread = threading.Thread(target=reactor.run, args=(False,))
		self._reactor_thread.daemon = True
		
 		endpoint_descriptor = 'tcp:'+ip+':'+port

		self._clientReader = clientFromString(reactor, endpoint_descriptor)
		self._clientReader.connect(self._factoryReader)

		self._clientWriter = clientFromString(reactor, endpoint_descriptor)
		self._clientWriter.connect(self._factoryWriter)

 		self._reactor_thread.start()

 		return self
##################################################################################


##        Utility Class to wite on a specific topic  ##
def writeToTopic(topic, message):
	def p (x):
		print x
		
	global sessio_writer
	sessio_writer.publish(topic,message)
	print 'ooo'
	try:
		res = sessio_writer.call(u'stack4things.test',)
		print (format(res))
	except Exception as e:
		print(format(e))
#######################################################

#####Config paramiters####
ipWamp = '127.0.0.1'
portWamp ='8181'
realmWAMP = 's4t'
##Topic Scrittura; Msg
##########################	


if __name__ == '__main__':

	client = WampClient()
	test = client.connect(ipWamp, portWamp, realmWAMP)

	while True:
		time.sleep(2)
		writeToTopic('board.connection', 'MEEEEEEEEEEEEEE')
