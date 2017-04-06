# coding=utf-8
#
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.

from oslo_utils import strutils
from oslo_utils import uuidutils

from iotronic.common import exception
from iotronic.common import states
from iotronic.db import api as db_api
from iotronic.objects import base
from iotronic.objects import utils as obj_utils


class Board(base.IotronicObject):
    # Version 1.0: Initial version
    VERSION = '1.0'

    dbapi = db_api.get_instance()

    fields = {
        'id': int,
        'uuid': obj_utils.str_or_none,
        'code': obj_utils.str_or_none,
        'status': obj_utils.str_or_none,
        'name': obj_utils.str_or_none,
        'type': obj_utils.str_or_none,
        'agent': obj_utils.str_or_none,
        'owner': obj_utils.str_or_none,
        'project': obj_utils.str_or_none,
        'mobile': bool,
        'config': obj_utils.dict_or_none,
        'extra': obj_utils.dict_or_none,
    }

    def check_if_online(self):
        if self.status != states.ONLINE:
            raise exception.BoardNotConnected(board=self.uuid)

    def is_online(self):
        if self.status == states.ONLINE:
            return True
        return False

    @staticmethod
    def _from_db_object(board, db_board):
        """Converts a database entity to a formal object."""
        for field in board.fields:
            board[field] = db_board[field]
        board.obj_reset_changes()
        return board

    @base.remotable_classmethod
    def get(cls, context, board_id):
        """Find a board based on its id or uuid and return a Board object.

        :param board_id: the id *or* uuid of a board.
        :returns: a :class:`Board` object.
        """
        if strutils.is_int_like(board_id):
            return cls.get_by_id(context, board_id)
        elif uuidutils.is_uuid_like(board_id):
            return cls.get_by_uuid(context, board_id)
        else:
            raise exception.InvalidIdentity(identity=board_id)

    @base.remotable_classmethod
    def get_by_id(cls, context, board_id):
        """Find a board based on its integer id and return a Board object.

        :param board_id: the id of a board.
        :returns: a :class:`Board` object.
        """
        db_board = cls.dbapi.get_board_by_id(board_id)
        board = Board._from_db_object(cls(context), db_board)
        return board

    @base.remotable_classmethod
    def get_by_uuid(cls, context, uuid):
        """Find a board based on uuid and return a Board object.

        :param uuid: the uuid of a board.
        :returns: a :class:`Board` object.
        """
        db_board = cls.dbapi.get_board_by_uuid(uuid)
        board = Board._from_db_object(cls(context), db_board)
        return board

    @base.remotable_classmethod
    def get_by_code(cls, context, code):
        """Find a board based on name and return a Board object.

        :param name: the logical name of a board.
        :returns: a :class:`Board` object.
        """
        db_board = cls.dbapi.get_board_by_code(code)
        board = Board._from_db_object(cls(context), db_board)
        return board

    @base.remotable_classmethod
    def get_by_name(cls, context, name):
        """Find a board based on name and return a Board object.

        :param name: the logical name of a board.
        :returns: a :class:`Board` object.
        """
        db_board = cls.dbapi.get_board_by_name(name)
        board = Board._from_db_object(cls(context), db_board)
        return board

    @base.remotable_classmethod
    def list(cls, context, limit=None, marker=None, sort_key=None,
             sort_dir=None, filters=None):
        """Return a list of Board objects.

        :param context: Security context.
        :param limit: maximum number of resources to return in a single result.
        :param marker: pagination marker for large data sets.
        :param sort_key: column to sort results by.
        :param sort_dir: direction to sort. "asc" or "desc".
        :param filters: Filters to apply.
        :returns: a list of :class:`Board` object.

        """
        db_boards = cls.dbapi.get_board_list(filters=filters, limit=limit,
                                             marker=marker, sort_key=sort_key,
                                             sort_dir=sort_dir)
        return [Board._from_db_object(cls(context), obj) for obj in db_boards]

    @base.remotable_classmethod
    def reserve(cls, context, tag, board_id):
        """Get and reserve a board.

        To prevent other ManagerServices from manipulating the given
        Board while a Task is performed, mark it reserved by this host.

        :param context: Security context.
        :param tag: A string uniquely identifying the reservation holder.
        :param board_id: A board id or uuid.
        :raises: BoardNotFound if the board is not found.
        :returns: a :class:`Board` object.

        """
        db_board = cls.dbapi.reserve_board(tag, board_id)
        board = Board._from_db_object(cls(context), db_board)
        return board

    @base.remotable_classmethod
    def release(cls, context, tag, board_id):
        """Release the reservation on a board.

        :param context: Security context.
        :param tag: A string uniquely identifying the reservation holder.
        :param board_id: A board id or uuid.
        :raises: BoardNotFound if the board is not found.

        """
        cls.dbapi.release_board(tag, board_id)

    @base.remotable
    def create(self, context=None):
        """Create a Board record in the DB.

        Column-wise updates will be made based on the result of
        self.what_changed(). If target_power_state is provided,
        it will be checked against the in-database copy of the
        board before updates are made.

        :param context: Security context. NOTE: This should only
                        be used internally by the indirection_api.
                        Unfortunately, RPC requires context as the first
                        argument, even though we don't use it.
                        A context should be set when instantiating the
                        object, e.g.: Board(context)

        """
        values = self.obj_get_changes()
        db_board = self.dbapi.create_board(values)
        self._from_db_object(self, db_board)

    @base.remotable
    def destroy(self, context=None):
        """Delete the Board from the DB.

        :param context: Security context. NOTE: This should only
                        be used internally by the indirection_api.
                        Unfortunately, RPC requires context as the first
                        argument, even though we don't use it.
                        A context should be set when instantiating the
                        object, e.g.: Board(context)
        """
        self.dbapi.destroy_board(self.uuid)
        self.obj_reset_changes()

    @base.remotable
    def save(self, context=None):
        """Save updates to this Board.

        Column-wise updates will be made based on the result of
        self.what_changed(). If target_power_state is provided,
        it will be checked against the in-database copy of the
        board before updates are made.

        :param context: Security context. NOTE: This should only
                        be used internally by the indirection_api.
                        Unfortunately, RPC requires context as the first
                        argument, even though we don't use it.
                        A context should be set when instantiating the
                        object, e.g.: Board(context)
        """
        updates = self.obj_get_changes()
        self.dbapi.update_board(self.uuid, updates)
        self.obj_reset_changes()

    @base.remotable
    def refresh(self, context=None):
        """Refresh the object by re-fetching from the DB.

        :param context: Security context. NOTE: This should only
                        be used internally by the indirection_api.
                        Unfortunately, RPC requires context as the first
                        argument, even though we don't use it.
                        A context should be set when instantiating the
                        object, e.g.: Board(context)
        """
        current = self.__class__.get_by_uuid(self._context, self.uuid)
        for field in self.fields:
            if (hasattr(
                    self, base.get_attrname(field))
                    and self[field] != current[field]):
                self[field] = current[field]
