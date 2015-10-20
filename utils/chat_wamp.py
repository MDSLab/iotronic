from clientwamp import ClientWamp
from sys import stdin

c=ClientWamp('localhost','8181','s4t')
c.send('Hello!')
while True:
    userinput = stdin.readline()
    c.send(str(userinput))