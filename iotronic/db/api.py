# -*- encoding: utf-8 -*-
#
# Copyright 2013 Hewlett-Packard Development Company, L.P.
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.
"""
Base classes for storage engines
"""

import abc

from oslo_config import cfg
from oslo_db import api as db_api
import six

_BACKEND_MAPPING = {'sqlalchemy': 'iotronic.db.sqlalchemy.api'}
IMPL = db_api.DBAPI.from_config(cfg.CONF,
                                backend_mapping=_BACKEND_MAPPING,
                                lazy=True)


def get_instance():
    """Return a DB API instance."""
    return IMPL


@six.add_metaclass(abc.ABCMeta)
class Connection(object):
    """Base class for storage system connections."""

    @abc.abstractmethod
    def __init__(self):
        """Constructor."""

    @abc.abstractmethod
    def get_boardinfo_list(self, columns=None, filters=None, limit=None,
                           marker=None, sort_key=None, sort_dir=None):
        """Get specific columns for matching boards.

        Return a list of the specified columns for all boards that match the
        specified filters.

        :param columns: List of column names to return.
                        Defaults to 'id' column when columns == None.
        :param filters: Filters to apply. Defaults to None.

                        :associated: True | False
                        :reserved: True | False
                        :maintenance: True | False
                        :provision_state: provision state of board
                        :provisioned_before:
                            boards with provision_updated_at field before this
                            interval in seconds
        :param limit: Maximum number of boards to return.
        :param marker: the last item of the previous page; we return the next
                       result set.
        :param sort_key: Attribute by which results should be sorted.
        :param sort_dir: direction in which results should be sorted.
                         (asc, desc)
        :returns: A list of tuples of the specified columns.
        """

    @abc.abstractmethod
    def get_board_list(self, filters=None, limit=None, marker=None,
                       sort_key=None, sort_dir=None):
        """Return a list of boards.

        :param filters: Filters to apply. Defaults to None.

                        :associated: True | False
                        :reserved: True | False
                        :maintenance: True | False
                        :provision_state: provision state of board
                        :provisioned_before:
                            boards with provision_updated_at field before this
                            interval in seconds
        :param limit: Maximum number of boards to return.
        :param marker: the last item of the previous page; we return the next
                       result set.
        :param sort_key: Attribute by which results should be sorted.
        :param sort_dir: direction in which results should be sorted.
                         (asc, desc)
        """

    @abc.abstractmethod
    def create_board(self, values):
        """Create a new board.

        :param values: A dict containing several items used to identify
                       and track the board, and several dicts which are passed
                       into the Drivers when managing this board. For example:

                       ::

                        {
                         'uuid': uuidutils.generate_uuid(),
                         'instance_uuid': None,
                         'power_state': states.POWER_OFF,
                         'provision_state': states.AVAILABLE,
                         'properties': { ... },
                         'extra': { ... },
                        }
        :returns: A board.
        """

    @abc.abstractmethod
    def get_board_by_id(self, board_id):
        """Return a board.

        :param board_id: The id of a board.
        :returns: A board.
        """

    @abc.abstractmethod
    def get_board_by_uuid(self, board_uuid):
        """Return a board.

        :param board_uuid: The uuid of a board.
        :returns: A board.
        """

    @abc.abstractmethod
    def get_board_id_by_uuid(self, board_uuid):
        """Return a board id.

        :param board_uuid: The uuid of a board.
        # :returns: A board.id.
        """

    @abc.abstractmethod
    def get_board_by_name(self, board_name):
        """Return a board.

        :param board_name: The logical name of a board.
        :returns: A board.
        """

    @abc.abstractmethod
    def get_board_by_code(self, instance):
        """Return a board.

        :param instance: The instance code or uuid to search for.
        :returns: A board.
        """

    @abc.abstractmethod
    def destroy_board(self, board_id):
        """Destroy a board and all associated interfaces.

        :param board_id: The id or uuid of a board.
        """

    @abc.abstractmethod
    def update_board(self, board_id, values):
        """Update properties of a board.

        :param board_id: The id or uuid of a board.
        :param values: Dict of values to update.
        :returns: A board.
        :raises: BoardAssociated
        :raises: BoardNotFound
        """

    @abc.abstractmethod
    def get_conductor(self, hostname):
        """Retrieve a conductor's service record from the database.

        :param hostname: The hostname of the conductor service.
        :returns: A conductor.
        :raises: ConductorNotFound
        """

    @abc.abstractmethod
    def unregister_conductor(self, hostname):
        """Remove this conductor from the service registry immediately.

        :param hostname: The hostname of this conductor service.
        :raises: ConductorNotFound
        """

    @abc.abstractmethod
    def touch_conductor(self, hostname):
        """Mark a conductor as active by updating its 'updated_at' property.

        :param hostname: The hostname of this conductor service.
        :raises: ConductorNotFound
        """

    @abc.abstractmethod
    def create_session(self, values):
        """Create a new location.

        :param values: session_id.
        """

    @abc.abstractmethod
    def update_session(self, session_id, values):
        """Update properties of an session.

        :param session_id: The id of a session.
        :param values: Dict of values to update.
        :returns: A session.
        """

    @abc.abstractmethod
    def get_session_by_board_uuid(self, board_uuid, valid):
        """Return a Wamp session of a Board

        :param board_uuid: Filters to apply. Defaults to None.
        :param valid: is valid
        :returns: A session.
        """

    @abc.abstractmethod
    def get_session_by_id(self, session_id):
        """Return a Wamp session

        :param session_id: The id of a session.
         :returns: A session.
        """

    @abc.abstractmethod
    def create_location(self, values):
        """Create a new location.

        :param values: Dict of values.
        """

    @abc.abstractmethod
    def update_location(self, location_id, values):
        """Update properties of an location.

        :param location_id: The id of a location.
        :param values: Dict of values to update.
        :returns: A location.
        """

    @abc.abstractmethod
    def destroy_location(self, location_id):
        """Destroy an location.

        :param location_id: The id or MAC of a location.
        """

    @abc.abstractmethod
    def get_locations_by_board_id(self, board_id, limit=None, marker=None,
                                  sort_key=None, sort_dir=None):
        """List all the locations for a given board.

        :param board_id: The integer board ID.
        :param limit: Maximum number of locations to return.
        :param marker: the last item of the previous page; we return the next
                       result set.
        :param sort_key: Attribute by which results should be sorted
        :param sort_dir: direction in which results should be sorted
                         (asc, desc)
        :returns: A list of locations.
        """

    @abc.abstractmethod
    def get_valid_wpsessions_list(self):
        """Return a list of wpsession."""

    @abc.abstractmethod
    def get_wampagent(self, hostname):
        """Retrieve a wampagent's service record from the database.

        :param hostname: The hostname of the wampagent service.
        :returns: A wampagent.
        :raises: WampAgentNotFound
        """

    @abc.abstractmethod
    def get_registration_wampagent(self):
        """Retrieve the registration wampagent record from the database.

        :returns: A wampagent.
        :raises: WampAgentNotFound
        """

    @abc.abstractmethod
    def unregister_wampagent(self, hostname):
        """Remove this wampagent from the service registry immediately.

        :param hostname: The hostname of this wampagent service.
        :raises: WampAgentNotFound
        """

    @abc.abstractmethod
    def touch_wampagent(self, hostname):
        """Mark a wampagent as active by updating its 'updated_at' property.

        :param hostname: The hostname of this wampagent service.
        :raises: WampAgentNotFound
        """

    @abc.abstractmethod
    def get_wampagent_list(self, filters=None, limit=None, marker=None,
                           sort_key=None, sort_dir=None):
        """Return a list of wampagents.

        :param filters: Filters to apply. Defaults to None.
        :param limit: Maximum number of wampagents to return.
        :param marker: the last item of the previous page; we return the next
                       result set.
        :param sort_key: Attribute by which results should be sorted.
        :param sort_dir: direction in which results should be sorted.
                         (asc, desc)
        """

    @abc.abstractmethod
    def get_plugin_by_id(self, plugin_id):
        """Return a plugin.

        :param plugin_id: The id of a plugin.
        :returns: A plugin.
        """

    @abc.abstractmethod
    def get_plugin_by_uuid(self, plugin_uuid):
        """Return a plugin.

        :param plugin_uuid: The uuid of a plugin.
        :returns: A plugin.
        """

    @abc.abstractmethod
    def get_plugin_by_name(self, plugin_name):
        """Return a plugin.

        :param plugin_name: The logical name of a plugin.
        :returns: A plugin.
        """

    @abc.abstractmethod
    def create_plugin(self, values):
        """Create a new plugin.

        :param values: A dict containing several items used to identify
                       and track the plugin
        :returns: A plugin.
        """

    @abc.abstractmethod
    def destroy_plugin(self, plugin_id):
        """Destroy a plugin and all associated interfaces.

        :param plugin_id: The id or uuid of a plugin.
        """

    @abc.abstractmethod
    def update_plugin(self, plugin_id, values):
        """Update properties of a plugin.

        :param plugin_id: The id or uuid of a plugin.
        :param values: Dict of values to update.
        :returns: A plugin.
        :raises: PluginAssociated
        :raises: PluginNotFound
        """

    @abc.abstractmethod
    def get_injection_plugin_by_board_uuid(self, board_uuid):
        """get an injection of a plugin using a board_uuid

        :param board_uuid: The id or uuid of a board.
        :returns: An injection_plugin.

        """

    @abc.abstractmethod
    def get_injection_plugin_by_uuids(self, board_uuid, plugin_uuid):
        """get an injection of a plugin using a board_uuid and plugin_uuid

        :param board_uuid: The id or uuid of a board.
        :param plugin_uuid: The id or uuid of a plugin.
        :returns: An injection_plugin.

        """

    @abc.abstractmethod
    def create_injection_plugin(self, values):
        """Create a new injection_plugin.

        :param values: A dict containing several items used to identify
                       and track the plugin
        :returns: An injection plugin.
        """

    @abc.abstractmethod
    def destroy_injection_plugin(self, injection_plugin_id):
        """Destroy an injection plugin and all associated interfaces.

        :param injection_plugin_id: The id or uuid of a plugin.
        """

    @abc.abstractmethod
    def update_injection_plugin(self, plugin_injection_id, values):
        """Update properties of a plugin.

        :param plugin_id: The id or uuid of a plugin.
        :param values: Dict of values to update.
        :returns: A plugin.
        :raises: PluginAssociated
        :raises: PluginNotFound
        """

    @abc.abstractmethod
    def get_injection_plugin_list(self, board_uuid):
        """Return a list of injection_plugins.

        :param board_uuid: The id or uuid of a plugin.
        :returns: A list of InjectionPlugins on the board.

        """
