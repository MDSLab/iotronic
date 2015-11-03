from iotronic import objects
from oslo_utils import uuidutils
import pecan
from oslo_log import log

LOG = log.getLogger(__name__)

def test():
    LOG.debug('hellooooooooo')
    return u'hello!'

def registration(code,session_num):
    
    
    board = objects.Board.get_by_code({}, code)
    if not board:
        new_Board = objects.Board({})
        new_Board.uuid=uuidutils.generate_uuid()
        new_Board.code=str(code)
        new_Board.status='CONNECTED'
        
        new_Board.create()
        response='NO BOARD FOUND, inserted new board: '+str(code)
        return unicode(response)
    
    board.status='CONNECTED'
    board.save()    
    
    response='Board '+ code +' connected'
    return unicode(response)