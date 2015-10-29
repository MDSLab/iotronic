from iotronic import objects
from oslo_utils import uuidutils
import pecan

def test():
    return u'hello!'

def registration(code,session):
    new_Board = objects.Board({})
    new_Board.uuid=uuidutils.generate_uuid()
    new_Board.code=str(code)
    new_Board.status='CONNECTED'
    
    new_Board.create()

    print Board
    response='registred board '+str(Board)
    return unicode(response)