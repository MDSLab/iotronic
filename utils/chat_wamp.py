from iotronic.wamp.clientwamp import ClientWamp
from sys import stdin
import inspect

c=ClientWamp('localhost','8181','s4t')
c.send('board.connection','Hello from the chat wamp!')
print 'USING',inspect.getfile(c.__class__)
while True:
    userinput = stdin.readline()
    c.send('board.connection',str(userinput))