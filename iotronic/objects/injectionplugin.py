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

from iotronic.db import api as db_api
from iotronic.objects import base
from iotronic.objects import utils as obj_utils


class InjectionPlugin(base.IotronicObject):
    # Version 1.0: Initial version
    VERSION = '1.0'

    dbapi = db_api.get_instance()

    fields = {
        'id': int,
        'board_uuid': obj_utils.str_or_none,
        'plugin_uuid': obj_utils.str_or_none,
        'onboot': bool,
        'status': obj_utils.str_or_none,
    }

    @staticmethod
    def _from_db_object(injection_plugin, db_injection_plugin):
        """Converts a database entity to a formal object."""
        for field in injection_plugin.fields:
            injection_plugin[field] = db_injection_plugin[field]
        injection_plugin.obj_reset_changes()
        return injection_plugin

    @base.remotable_classmethod
    def get_by_id(cls, context, injection_plugin_id):
        """Find a injection_plugin based on its integer id and return a Board object.

        :param injection_plugin_id: the id of a injection_plugin.
        :returns: a :class:`injection_plugin` object.
        """
        db_inj_plugin = cls.dbapi.get_injection_plugin_by_id(
            injection_plugin_id)
        inj_plugin = InjectionPlugin._from_db_object(cls(context),
                                                     db_inj_plugin)
        return inj_plugin

    @base.remotable_classmethod
    def get_by_board_uuid(cls, context, board_uuid):
        """Find a injection_plugin based on uuid and return a Board object.

        :param board_uuid: the uuid of a injection_plugin.
        :returns: a :class:`injection_plugin` object.
        """
        db_inj_plugin = cls.dbapi.get_injection_plugin_by_board_uuid(
            board_uuid)
        inj_plugin = InjectionPlugin._from_db_object(cls(context),
                                                     db_inj_plugin)
        return inj_plugin

    @base.remotable_classmethod
    def get_by_plugin_uuid(cls, context, plugin_uuid):
        """Find a injection_plugin based on uuid and return a Board object.

        :param plugin_uuid: the uuid of a injection_plugin.
        :returns: a :class:`injection_plugin` object.
        """
        db_inj_plugin = cls.dbapi.get_injection_plugin_by_plugin_uuid(
            plugin_uuid)
        inj_plugin = InjectionPlugin._from_db_object(cls(context),
                                                     db_inj_plugin)
        return inj_plugin

    @base.remotable_classmethod
    def get(cls, context, board_uuid, plugin_uuid):
        """Find a injection_plugin based on uuid and return a Board object.

        :param board_uuid: the uuid of a injection_plugin.
        :returns: a :class:`injection_plugin` object.
        """
        db_inj_plugin = cls.dbapi.get_injection_plugin_by_uuids(board_uuid,
                                                                plugin_uuid)
        inj_plugin = InjectionPlugin._from_db_object(cls(context),
                                                     db_inj_plugin)
        return inj_plugin

    @base.remotable_classmethod
    def list(cls, context, board_uuid):
        """Return a list of InjectionPlugin objects.

        :param context: Security context.
        :param limit: maximum number of resources to return in a single result.
        :param marker: pagination marker for large data sets.
        :param sort_key: column to sort results by.
        :param sort_dir: direction to sort. "asc" or "desc".
        :param filters: Filters to apply.
        :returns: a list of :class:`InjectionPlugin` object.

        """
        db_injs = cls.dbapi.get_injection_plugin_list(board_uuid)
        return [InjectionPlugin._from_db_object(cls(context), obj)
                for obj in db_injs]

    @base.remotable
    def create(self, context=None):
        """Create a InjectionPlugin record in the DB.

        Column-wise updates will be made based on the result of
        self.what_changed(). If target_power_state is provided,
        it will be checked against the in-database copy of the
        injection_plugin before updates are made.

        :param context: Security context. NOTE: This should only
                        be used internally by the indirection_api.
                        Unfortunately, RPC requires context as the first
                        argument, even though we don't use it.
                        A context should be set when instantiating the
                        object, e.g.: InjectionPlugin(context)

        """
        values = self.obj_get_changes()
        db_injection_plugin = self.dbapi.create_injection_plugin(values)
        self._from_db_object(self, db_injection_plugin)

    @base.remotable
    def destroy(self, context=None):
        """Delete the InjectionPlugin from the DB.

        :param context: Security context. NOTE: This should only
                        be used internally by the indirection_api.
                        Unfortunately, RPC requires context as the first
                        argument, even though we don't use it.
                        A context should be set when instantiating the
                        object, e.g.: InjectionPlugin(context)
        """
        self.dbapi.destroy_injection_plugin(self.id)
        self.obj_reset_changes()

    @base.remotable
    def save(self, context=None):
        """Save updates to this InjectionPlugin.

        Column-wise updates will be made based on the result of
        self.what_changed(). If target_power_state is provided,
        it will be checked against the in-database copy of the
        injection_plugin before updates are made.

        :param context: Security context. NOTE: This should only
                        be used internally by the indirection_api.
                        Unfortunately, RPC requires context as the first
                        argument, even though we don't use it.
                        A context should be set when instantiating the
                        object, e.g.: InjectionPlugin(context)
        """
        updates = self.obj_get_changes()
        self.dbapi.update_injection_plugin(self.id, updates)
        self.obj_reset_changes()
