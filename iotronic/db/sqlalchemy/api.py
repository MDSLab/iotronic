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

"""SQLAlchemy storage backend."""

from oslo_config import cfg
from oslo_db import exception as db_exc
from oslo_db.sqlalchemy import session as db_session
from oslo_db.sqlalchemy import utils as db_utils
from oslo_utils import strutils
from oslo_utils import timeutils
from oslo_utils import uuidutils
from sqlalchemy import or_
from sqlalchemy.orm.exc import NoResultFound

from iotronic.common import exception
from iotronic.common.i18n import _
from iotronic.common import states
from iotronic.db import api
from iotronic.db.sqlalchemy import models

CONF = cfg.CONF
CONF.import_opt('heartbeat_timeout',
                'iotronic.conductor.manager',
                group='conductor')

_FACADE = None


def _create_facade_lazily():
    global _FACADE
    if _FACADE is None:
        _FACADE = db_session.EngineFacade.from_config(CONF)
    return _FACADE


def get_engine():
    facade = _create_facade_lazily()
    return facade.get_engine()


def get_session(**kwargs):
    facade = _create_facade_lazily()
    return facade.get_session(**kwargs)


def get_backend():
    """The backend is this module itself."""
    return Connection()


def model_query(model, *args, **kwargs):
    """Query helper for simpler session usage.

    :param session: if present, the session to use
    """

    session = kwargs.get('session') or get_session()
    query = session.query(model, *args)
    return query


def add_identity_filter(query, value):
    """Adds an identity filter to a query.

    Filters results by ID, if supplied value is a valid integer.
    Otherwise attempts to filter results by UUID.

    :param query: Initial query to add filter to.
    :param value: Value for filtering results by.
    :return: Modified query.
    """
    if strutils.is_int_like(value):
        return query.filter_by(id=value)
    elif uuidutils.is_uuid_like(value):
        return query.filter_by(uuid=value)
    else:
        raise exception.InvalidIdentity(identity=value)


def _paginate_query(model, limit=None, marker=None, sort_key=None,
                    sort_dir=None, query=None):
    if not query:
        query = model_query(model)
    sort_keys = ['id']
    if sort_key and sort_key not in sort_keys:
        sort_keys.insert(0, sort_key)
    try:
        query = db_utils.paginate_query(query, model, limit, sort_keys,
                                        marker=marker, sort_dir=sort_dir)
    except db_exc.InvalidSortKey:
        raise exception.InvalidParameterValue(
            _('The sort_key value "%(key)s" is an invalid field for sorting')
            % {'key': sort_key})

    return query.all()


class Connection(api.Connection):
    """SqlAlchemy connection."""

    def __init__(self):
        pass

    def _add_location_filter_by_board(self, query, value):
        if strutils.is_int_like(value):
            return query.filter_by(board_id=value)
        else:
            query = query.join(models.Board,
                               models.Location.board_id == models.Board.id)
            return query.filter(models.Board.uuid == value)

    def _add_boards_filters(self, query, filters):
        if filters is None:
            filters = []

        if 'project_id' in filters:
            query = query.filter(models.Board.project == filters['project_id'])
        if 'status' in filters:
            query = query.filter(models.Board.status == filters['status'])

        return query

    def _add_plugins_filters(self, query, filters):
        if filters is None:
            filters = []

        if 'owner' in filters:
            if 'public' in filters and filters['public']:
                query = query.filter(
                    or_(
                        models.Plugin.owner == filters['owner'],
                        models.Plugin.public == 1)
                )
            else:
                query = query.filter(models.Plugin.owner == filters['owner'])

        return query

    def _add_wampagents_filters(self, query, filters):
        if filters is None:
            filters = []

        if 'online' in filters:
            if filters['online']:
                query = query.filter(models.WampAgent.online == 1)
            else:
                query = query.filter(models.WampAgent.online == 0)

        if 'no_ragent' in filters:
            if filters['no_ragent']:
                query = query.filter(models.WampAgent.ragent == 0)
            else:
                query = query.filter(models.WampAgent.ragent == 1)

        return query

    def _do_update_board(self, board_id, values):
        session = get_session()
        with session.begin():
            query = model_query(models.Board, session=session)
            query = add_identity_filter(query, board_id)
            try:
                ref = query.with_lockmode('update').one()
            except NoResultFound:
                raise exception.BoardNotFound(board=board_id)

            ref.update(values)
        return ref

    def _do_update_plugin(self, plugin_id, values):
        session = get_session()
        with session.begin():
            query = model_query(models.Plugin, session=session)
            query = add_identity_filter(query, plugin_id)
            try:
                ref = query.with_lockmode('update').one()
            except NoResultFound:
                raise exception.PluginNotFound(plugin=plugin_id)

            ref.update(values)
        return ref

    def _do_update_injection_plugin(self, injection_plugin_id, values):
        session = get_session()
        with session.begin():
            query = model_query(models.InjectionPlugin, session=session)
            query = add_identity_filter(query, injection_plugin_id)
            try:
                ref = query.with_lockmode('update').one()
            except NoResultFound:
                raise exception.InjectionPluginNotFound(
                    injection_plugin=injection_plugin_id)

            ref.update(values)
        return ref

    # BOARD api

    def get_boardinfo_list(self, columns=None, filters=None, limit=None,
                           marker=None, sort_key=None, sort_dir=None):
        # list-ify columns default values because it is bad form
        # to include a mutable list in function definitions.
        if columns is None:
            columns = [models.Board.id]
        else:
            columns = [getattr(models.Board, c) for c in columns]

        query = model_query(*columns, base_model=models.Board)
        query = self._add_boards_filters(query, filters)
        return _paginate_query(models.Board, limit, marker,
                               sort_key, sort_dir, query)

    def get_board_list(self, filters=None, limit=None, marker=None,
                       sort_key=None, sort_dir=None):
        query = model_query(models.Board)
        query = self._add_boards_filters(query, filters)
        return _paginate_query(models.Board, limit, marker,
                               sort_key, sort_dir, query)

    def create_board(self, values):
        # ensure defaults are present for new boards
        if 'uuid' not in values:
            values['uuid'] = uuidutils.generate_uuid()
        if 'status' not in values:
            values['status'] = states.REGISTERED

        board = models.Board()
        board.update(values)
        try:
            board.save()
        except db_exc.DBDuplicateEntry as exc:
            if 'code' in exc.columns:
                raise exception.DuplicateCode(code=values['code'])
            raise exception.BoardAlreadyExists(uuid=values['uuid'])
        return board

    def get_board_by_id(self, board_id):
        query = model_query(models.Board).filter_by(id=board_id)
        try:
            return query.one()
        except NoResultFound:
            raise exception.BoardNotFound(board=board_id)

    def get_board_id_by_uuid(self, board_uuid):
        query = model_query(models.Board.id).filter_by(uuid=board_uuid)
        try:
            return query.one()
        except NoResultFound:
            raise exception.BoardNotFound(board=board_uuid)

    def get_board_by_uuid(self, board_uuid):
        query = model_query(models.Board).filter_by(uuid=board_uuid)
        try:
            return query.one()
        except NoResultFound:
            raise exception.BoardNotFound(board=board_uuid)

    def get_board_by_name(self, board_name):
        query = model_query(models.Board).filter_by(name=board_name)
        try:
            return query.one()
        except NoResultFound:
            raise exception.BoardNotFound(board=board_name)

    def get_board_by_code(self, board_code):
        query = model_query(models.Board).filter_by(code=board_code)
        try:
            return query.one()
        except NoResultFound:
            raise exception.BoardNotFound(board=board_code)

    def destroy_board(self, board_id):

        session = get_session()
        with session.begin():
            query = model_query(models.Board, session=session)
            query = add_identity_filter(query, board_id)
            try:
                board_ref = query.one()
            except NoResultFound:
                raise exception.BoardNotFound(board=board_id)

            # Get board ID, if an UUID was supplied. The ID is
            # required for deleting all ports, attached to the board.
            if uuidutils.is_uuid_like(board_id):
                board_id = board_ref['id']

            location_query = model_query(models.Location, session=session)
            location_query = self._add_location_filter_by_board(
                location_query, board_id)
            location_query.delete()

            query.delete()

    def update_board(self, board_id, values):
        # NOTE(dtantsur): this can lead to very strange errors
        if 'uuid' in values:
            msg = _("Cannot overwrite UUID for an existing Board.")
            raise exception.InvalidParameterValue(err=msg)

        try:
            return self._do_update_board(board_id, values)
        except db_exc.DBDuplicateEntry as e:
            if 'name' in e.columns:
                raise exception.DuplicateName(name=values['name'])
            elif 'uuid' in e.columns:
                raise exception.BoardAlreadyExists(uuid=values['uuid'])
            else:
                raise e

    # CONDUCTOR api

    def register_conductor(self, values, update_existing=False):
        session = get_session()
        with session.begin():
            query = (model_query(models.Conductor, session=session)
                     .filter_by(hostname=values['hostname']))
            try:
                ref = query.one()
                if ref.online is True and not update_existing:
                    raise exception.ConductorAlreadyRegistered(
                        conductor=values['hostname'])
            except NoResultFound:
                ref = models.Conductor()
            ref.update(values)
            # always set online and updated_at fields when registering
            # a conductor, especially when updating an existing one
            ref.update({'updated_at': timeutils.utcnow(),
                        'online': True})
            ref.save(session)
        return ref

    def get_conductor(self, hostname):
        try:
            return (model_query(models.Conductor)
                    .filter_by(hostname=hostname, online=True)
                    .one())
        except NoResultFound:
            raise exception.ConductorNotFound(conductor=hostname)

    def unregister_conductor(self, hostname):
        session = get_session()
        with session.begin():
            query = (model_query(models.Conductor, session=session)
                     .filter_by(hostname=hostname, online=True))
            count = query.update({'online': False})
            if count == 0:
                raise exception.ConductorNotFound(conductor=hostname)

    def touch_conductor(self, hostname):
        session = get_session()
        with session.begin():
            query = (model_query(models.Conductor, session=session)
                     .filter_by(hostname=hostname))
            # since we're not changing any other field, manually set updated_at
            # and since we're heartbeating, make sure that online=True
            count = query.update({'updated_at': timeutils.utcnow(),
                                  'online': True})
            if count == 0:
                raise exception.ConductorNotFound(conductor=hostname)

    # LOCATION api

    def create_location(self, values):
        location = models.Location()
        location.update(values)
        location.save()
        return location

    def update_location(self, location_id, values):
        # NOTE(dtantsur): this can lead to very strange errors
        session = get_session()
        try:
            with session.begin():
                query = model_query(models.Location, session=session)
                query = add_identity_filter(query, location_id)
                ref = query.one()
                ref.update(values)
        except NoResultFound:
            raise exception.LocationNotFound(location=location_id)
        return ref

    def destroy_location(self, location_id):
        session = get_session()
        with session.begin():
            query = model_query(models.Location, session=session)
            query = add_identity_filter(query, location_id)
            count = query.delete()
            if count == 0:
                raise exception.LocationNotFound(location=location_id)

    def get_locations_by_board_id(self, board_id, limit=None, marker=None,
                                  sort_key=None, sort_dir=None):
        query = model_query(models.Location)
        query = query.filter_by(board_id=board_id)
        return _paginate_query(models.Location, limit, marker,
                               sort_key, sort_dir, query)

    # SESSION api

    def create_session(self, values):
        session = models.SessionWP()
        session.update(values)
        session.save()
        return session

    def update_session(self, ses_id, values):
        # NOTE(dtantsur): this can lead to very strange errors
        session = get_session()
        try:
            with session.begin():
                query = model_query(models.SessionWP, session=session)
                query = add_identity_filter(query, ses_id)
                ref = query.one()
                ref.update(values)
        except NoResultFound:
            raise exception.SessionWPNotFound(ses=ses_id)
        return ref

    def get_session_by_board_uuid(self, board_uuid, valid):
        query = model_query(
            models.SessionWP).filter_by(
            board_uuid=board_uuid).filter_by(
            valid=valid)
        try:
            return query.one()
        except NoResultFound:
            raise exception.BoardNotConnected(board=board_uuid)

    def get_session_by_id(self, session_id):
        query = model_query(models.SessionWP).filter_by(session_id=session_id)
        try:
            return query.one()
        except NoResultFound:
            return None

    def get_valid_wpsessions_list(self):
        query = model_query(models.SessionWP).filter_by(valid=1)
        return query.all()

    # WAMPAGENT api

    def register_wampagent(self, values, update_existing=False):
        session = get_session()
        with session.begin():
            query = (model_query(models.WampAgent, session=session)
                     .filter_by(hostname=values['hostname']))
            try:
                ref = query.one()
                if ref.online is True and not update_existing:
                    raise exception.WampAgentAlreadyRegistered(
                        wampagent=values['hostname'])
            except NoResultFound:
                ref = models.WampAgent()
            ref.update(values)
            # always set online and updated_at fields when registering
            # a wampagent, especially when updating an existing one
            ref.update({'updated_at': timeutils.utcnow(),
                        'online': True})
            ref.save(session)
        return ref

    def get_wampagent(self, hostname):
        try:
            return (model_query(models.WampAgent)
                    .filter_by(hostname=hostname, online=True)
                    .one())
        except NoResultFound:
            raise exception.WampAgentNotFound(wampagent=hostname)

    def get_registration_wampagent(self):
        try:
            return (model_query(models.WampAgent)
                    .filter_by(ragent=True, online=True)
                    .one())
        except NoResultFound:
            raise exception.WampRegistrationAgentNotFound()

    def unregister_wampagent(self, hostname):
        session = get_session()
        with session.begin():
            query = (model_query(models.WampAgent, session=session)
                     .filter_by(hostname=hostname, online=True))
            count = query.update({'online': False})
            if count == 0:
                raise exception.WampAgentNotFound(wampagent=hostname)

    def touch_wampagent(self, hostname):
        session = get_session()
        with session.begin():
            query = (model_query(models.WampAgent, session=session)
                     .filter_by(hostname=hostname))
            # since we're not changing any other field, manually set updated_at
            # and since we're heartbeating, make sure that online=True
            count = query.update({'updated_at': timeutils.utcnow(),
                                  'online': True})
            if count == 0:
                raise exception.WampAgentNotFound(wampagent=hostname)

    def get_wampagent_list(self, filters=None, limit=None, marker=None,
                           sort_key=None, sort_dir=None):
        query = model_query(models.WampAgent)
        query = self._add_wampagents_filters(query, filters)
        return _paginate_query(models.WampAgent, limit, marker,
                               sort_key, sort_dir, query)

    # PLUGIN api

    def get_plugin_by_id(self, plugin_id):
        query = model_query(models.Plugin).filter_by(id=plugin_id)
        try:
            return query.one()
        except NoResultFound:
            raise exception.PluginNotFound(plugin=plugin_id)

    def get_plugin_by_uuid(self, plugin_uuid):
        query = model_query(models.Plugin).filter_by(uuid=plugin_uuid)
        try:
            return query.one()
        except NoResultFound:
            raise exception.PluginNotFound(plugin=plugin_uuid)

    def get_plugin_by_name(self, plugin_name):
        query = model_query(models.Plugin).filter_by(name=plugin_name)
        try:
            return query.one()
        except NoResultFound:
            raise exception.PluginNotFound(plugin=plugin_name)

    def destroy_plugin(self, plugin_id):

        session = get_session()
        with session.begin():
            query = model_query(models.Plugin, session=session)
            query = add_identity_filter(query, plugin_id)
            try:
                plugin_ref = query.one()
            except NoResultFound:
                raise exception.PluginNotFound(plugin=plugin_id)

            # Get plugin ID, if an UUID was supplied. The ID is
            # required for deleting all ports, attached to the plugin.
            if uuidutils.is_uuid_like(plugin_id):
                plugin_id = plugin_ref['id']

            query.delete()

    def update_plugin(self, plugin_id, values):
        # NOTE(dtantsur): this can lead to very strange errors
        if 'uuid' in values:
            msg = _("Cannot overwrite UUID for an existing Plugin.")
            raise exception.InvalidParameterValue(err=msg)

        try:
            return self._do_update_plugin(plugin_id, values)
        except db_exc.DBDuplicateEntry as e:
            if 'name' in e.columns:
                raise exception.DuplicateName(name=values['name'])
            elif 'uuid' in e.columns:
                raise exception.PluginAlreadyExists(uuid=values['uuid'])
            else:
                raise e

    def create_plugin(self, values):
        # ensure defaults are present for new plugins
        if 'uuid' not in values:
            values['uuid'] = uuidutils.generate_uuid()
        plugin = models.Plugin()
        plugin.update(values)
        try:
            plugin.save()
        except db_exc.DBDuplicateEntry:
            raise exception.PluginAlreadyExists(uuid=values['uuid'])
        return plugin

    def get_plugin_list(self, filters=None, limit=None, marker=None,
                        sort_key=None, sort_dir=None):
        query = model_query(models.Plugin)
        query = self._add_plugins_filters(query, filters)
        return _paginate_query(models.Plugin, limit, marker,
                               sort_key, sort_dir, query)

    # INJECTION PLUGIN api

    def get_injection_plugin_by_board_uuid(self, board_uuid):
        query = model_query(
            models.InjectionPlugin).filter_by(
            board_uuid=board_uuid)
        try:
            return query.one()
        except NoResultFound:
            raise exception.InjectionPluginNotFound()

    def create_injection_plugin(self, values):
        # ensure defaults are present for new plugins
        if 'uuid' not in values:
            values['uuid'] = uuidutils.generate_uuid()
        inj_plug = models.InjectionPlugin()
        inj_plug.update(values)
        try:
            inj_plug.save()
        except db_exc.DBDuplicateEntry:
            raise exception.PluginAlreadyExists(uuid=values['uuid'])
        return inj_plug

    def update_injection_plugin(self, plugin_injection_id, values):

        if 'uuid' in values:
            msg = _("Cannot overwrite UUID for an existing Plugin.")
            raise exception.InvalidParameterValue(err=msg)
        try:
            return self._do_update_injection_plugin(
                plugin_injection_id, values)

        except db_exc.DBDuplicateEntry as e:
            if 'name' in e.columns:
                raise exception.DuplicateName(name=values['name'])
            elif 'uuid' in e.columns:
                raise exception.PluginAlreadyExists(uuid=values['uuid'])
            else:
                raise e

    def get_injection_plugin_by_uuids(self, board_uuid, plugin_uuid):
        query = model_query(
            models.InjectionPlugin).filter_by(
            board_uuid=board_uuid).filter_by(
            plugin_uuid=plugin_uuid)
        try:
            return query.one()
        except NoResultFound:
            raise exception.InjectionPluginNotFound()

    def destroy_injection_plugin(self, injection_plugin_id):

        session = get_session()
        with session.begin():
            query = model_query(models.InjectionPlugin, session=session)
            query = add_identity_filter(query, injection_plugin_id)
            try:
                query.delete()

            except NoResultFound:
                raise exception.InjectionPluginNotFound()

    def get_injection_plugin_list(self, board_uuid):
        query = model_query(
            models.InjectionPlugin).filter_by(
            board_uuid=board_uuid)
        return query.all()
