from pecan import rest
from iotronic.api import expose
from wsme import types as wtypes
from iotronic import objects
from iotronic.api.controllers.v1 import types
from iotronic.api.controllers.v1 import collection
from iotronic.api.controllers.v1 import utils as api_utils
from iotronic.api.controllers import base
from oslo_utils import uuidutils
import wsme
import pecan
from pecan import rest


class Board(base.APIBase):
    """API representation of a board.
    """

    uuid = types.uuid
    code = wsme.wsattr(int)
    status = wsme.wsattr(wtypes.text)

    @staticmethod
    def _convert_with_links(board, url, expand=True, show_password=True):
        '''
        if not expand:
            except_list = ['instance_uuid', 'maintenance', 'power_state',
                           'provision_state', 'uuid', 'name']
            board.unset_fields_except(except_list)
        else:
            if not show_password:
                board.driver_info = ast.literal_eval(strutils.mask_password(
                                                    board.driver_info,
                                                    "******"))
            board.ports = [link.Link.make_link('self', url, 'boards',
                                              board.uuid + "/ports"),
                          link.Link.make_link('bookmark', url, 'boards',
                                              board.uuid + "/ports",
                                              bookmark=True)
                          ]

        board.chassis_id = wtypes.Unset
        '''
        '''
        board.links = [link.Link.make_link('self', url, 'boards',
                                          board.uuid),
                      link.Link.make_link('bookmark', url, 'boards',
                                          board.uuid, bookmark=True)
                      ]
        '''
        return board
    
    @classmethod
    def convert_with_links(cls, rpc_board, expand=True):
        board = Board(**rpc_board.as_dict())
        return cls._convert_with_links(board, pecan.request.host_url,
                                       expand,
                                       pecan.request.context.show_password)

    def __init__(self, **kwargs):
        self.fields = []
        fields = list(objects.Board.fields)
        for k in fields:
            # Skip fields we do not expose.
            if not hasattr(self, k):
                continue
            self.fields.append(k)
            setattr(self, k, kwargs.get(k, wtypes.Unset))
            
class BoardCollection(collection.Collection):
    """API representation of a collection of boards."""

    boards = [Board]
    """A list containing boards objects"""

    def __init__(self, **kwargs):
        self._type = 'boards'

    @staticmethod
    def convert_with_links(boards, limit, url=None, expand=False, **kwargs):
        collection = BoardCollection()
        collection.boards = [Board.convert_with_links(n, expand) for n in boards]
        collection.next = collection.get_next(limit, url=url, **kwargs)
        return collection
    
class BoardsController(rest.RestController):

    invalid_sort_key_list = ['properties']

    def _get_boards_collection(self, chassis_uuid, instance_uuid, associated,
                              maintenance, marker, limit, sort_key, sort_dir,
                              expand=False, resource_url=None):
        '''
        if self.from_chassis and not chassis_uuid:
            raise exception.MissingParameterValue(
                _("Chassis id not specified."))
        '''
        limit = api_utils.validate_limit(limit)
        sort_dir = api_utils.validate_sort_dir(sort_dir)

        marker_obj = None
        if marker:
            marker_obj = objects.Board.get_by_uuid(pecan.request.context,
                                                  marker)

        if sort_key in self.invalid_sort_key_list:
            raise exception.InvalidParameterValue(
                _("The sort_key value %(key)s is an invalid field for "
                  "sorting") % {'key': sort_key})

        if instance_uuid:
            boards = self._get_boards_by_instance(instance_uuid)
        else:
            filters = {}
            if chassis_uuid:
                filters['chassis_uuid'] = chassis_uuid
            if associated is not None:
                filters['associated'] = associated
            if maintenance is not None:
                filters['maintenance'] = maintenance

            boards = objects.Board.list(pecan.request.context, limit, marker_obj,
                                      sort_key=sort_key, sort_dir=sort_dir,
                                      filters=filters)
            
        parameters = {'sort_key': sort_key, 'sort_dir': sort_dir}
        if associated:
            parameters['associated'] = associated
        if maintenance:
            parameters['maintenance'] = maintenance
        return BoardCollection.convert_with_links(boards, limit,
                                                 url=resource_url,
                                                 expand=expand,
                                                 **parameters)
    
    @expose.expose(BoardCollection, types.uuid, types.uuid, types.boolean,
                   types.boolean, types.uuid, int, wtypes.text, wtypes.text)
    def get_all(self, chassis_uuid=None, instance_uuid=None, associated=None,
                maintenance=None, marker=None, limit=None, sort_key='id',
                sort_dir='asc'):
        """Retrieve a list of boards.

        :param chassis_uuid: Optional UUID of a chassis, to get only boards for
                           that chassis.
        :param instance_uuid: Optional UUID of an instance, to find the board
                              associated with that instance.
        :param associated: Optional boolean whether to return a list of
                           associated or unassociated boards. May be combined
                           with other parameters.
        :param maintenance: Optional boolean value that indicates whether
                            to get boards in maintenance mode ("True"), or not
                            in maintenance mode ("False").
        :param marker: pagination marker for large data sets.
        :param limit: maximum number of resources to return in a single result.
        :param sort_key: column to sort results by. Default: id.
        :param sort_dir: direction to sort. "asc" or "desc". Default: asc.
        """
        return self._get_boards_collection(chassis_uuid, instance_uuid,
                                          associated, maintenance, marker,
                                          limit, sort_key, sort_dir)

    
    
    @expose.expose(Board,types.uuid_or_name)    
    def get(self,board_ident):
        """Retrieve information about the given board.

        :param node_ident: UUID or logical name of a board.
        """
        rpc_board = api_utils.get_rpc_board(board_ident)
        board = Board(**rpc_board.as_dict())
        return board
    
    @expose.expose(None, types.uuid_or_name, status_code=204)
    def delete(self, board_ident):
        """Delete a board.

        :param board_ident: UUID or logical name of a board.
        """
        rpc_board = api_utils.get_rpc_board(board_ident)

        try:
            topic = pecan.request.rpcapi.get_topic_for(rpc_board)
        except exception.NoValidHost as e:
            e.code = 400
            raise e

        pecan.request.rpcapi.destroy_board(pecan.request.context,
                                          rpc_board.uuid, topic)
        
    #@expose.expose(Board, body=Board, status_code=201)
    #def post(self, Board):
    @expose.expose(Board, status_code=201)
    def post(self):
        """Create a new Board.

        :param Board: a Board within the request body.
        """
        '''
        if not Board.uuid:
            Board.uuid = uuidutils.generate_uuid()

        try:
            pecan.request.rpcapi.get_topic_for(Board)
        except exception.NoValidHost as e:
            e.code = 400
            raise e

        if Board.name:
            if not api_utils.allow_Board_logical_names():
                raise exception.NotAcceptable()
            if not api_utils.is_valid_Board_name(Board.name):
                msg = _("Cannot create Board with invalid name %(name)s")
                raise wsme.exc.ClientSideError(msg % {'name': Board.name},
                                               status_code=400)
        '''
        #new_Board = objects.Board(pecan.request.context,
        #                        **Board.as_dict())
        
        #new_Board = objects.Board(pecan.request.context,
        #                        **Board.as_dict())
        #rpc_board = api_utils.get_rpc_board('a9a86ab8-ad45-455e-86c3-d8f7d892ec9d')
        
        """{'status': u'1', 'uuid': u'a9a86ab8-ad45-455e-86c3-d8f7d892ec9d', 
        'created_at': datetime.datetime(2015, 1, 30, 16, 56, tzinfo=<iso8601.iso8601.Utc object at 0x7f5b81e0dd90>), 
        'updated_at': None, 
        'reservation': None, 'id': 106, 'name': u'provaaaa'}
        """

        uuid = uuidutils.generate_uuid()
        b={'status': 'DISCONNECTED', 'uuid': uuid, 'code':'11223344'}
        board = Board(**b)
        
        new_Board = objects.Board(pecan.request.context,
                                **board.as_dict())
        new_Board.create()
        #pecan.response.location = link.build_url('Boards', new_Board.uuid)
        return Board.convert_with_links(new_Board)

