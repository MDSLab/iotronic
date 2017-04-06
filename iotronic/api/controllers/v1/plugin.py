#  Licensed under the Apache License, Version 2.0 (the "License"); you may
#  not use this file except in compliance with the License. You may obtain
#  a copy of the License at
#
#       http://www.apache.org/licenses/LICENSE-2.0
#
#  Unless required by applicable law or agreed to in writing, software
#  distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#  WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#  License for the specific language governing permissions and limitations
#  under the License.


from iotronic.api.controllers import base
from iotronic.api.controllers import link
from iotronic.api.controllers.v1 import collection
from iotronic.api.controllers.v1 import types
from iotronic.api.controllers.v1 import utils as api_utils
from iotronic.api import expose
from iotronic.common import exception
from iotronic.common import policy
from iotronic import objects

import pecan
from pecan import rest
import wsme
from wsme import types as wtypes

_DEFAULT_RETURN_FIELDS = ('name', 'uuid', 'owner', 'public', 'callable')


class Plugin(base.APIBase):
    """API representation of a plugin.

    """
    uuid = types.uuid
    name = wsme.wsattr(wtypes.text)
    code = wsme.wsattr(wtypes.text)
    public = types.boolean
    owner = types.uuid
    callable = types.boolean
    parameters = types.jsontype
    links = wsme.wsattr([link.Link], readonly=True)
    extra = types.jsontype

    def __init__(self, **kwargs):
        self.fields = []
        fields = list(objects.Plugin.fields)
        for k in fields:
            # Skip fields we do not expose.
            if not hasattr(self, k):
                continue
            self.fields.append(k)
            setattr(self, k, kwargs.get(k, wtypes.Unset))

    @staticmethod
    def _convert_with_links(plugin, url, fields=None):
        plugin_uuid = plugin.uuid
        if fields is not None:
            plugin.unset_fields_except(fields)

        plugin.links = [link.Link.make_link('self', url, 'plugins',
                                            plugin_uuid),
                        link.Link.make_link('bookmark', url, 'plugins',
                                            plugin_uuid, bookmark=True)
                        ]
        return plugin

    @classmethod
    def convert_with_links(cls, rpc_plugin, fields=None):
        plugin = Plugin(**rpc_plugin.as_dict())

        if fields is not None:
            api_utils.check_for_invalid_fields(fields, plugin.as_dict())

        return cls._convert_with_links(plugin, pecan.request.public_url,
                                       fields=fields)


class PluginCollection(collection.Collection):
    """API representation of a collection of plugins."""

    plugins = [Plugin]
    """A list containing plugins objects"""

    def __init__(self, **kwargs):
        self._type = 'plugins'

    @staticmethod
    def convert_with_links(plugins, limit, url=None, fields=None, **kwargs):
        collection = PluginCollection()
        collection.plugins = [Plugin.convert_with_links(n, fields=fields)
                              for n in plugins]
        collection.next = collection.get_next(limit, url=url, **kwargs)
        return collection


class PluginsController(rest.RestController):
    """REST controller for Plugins."""

    invalid_sort_key_list = ['extra', 'location']

    _custom_actions = {
        'detail': ['GET'],
    }

    def _get_plugins_collection(self, marker, limit,
                                sort_key, sort_dir,
                                fields=None, with_public=False,
                                all_plugins=False):

        limit = api_utils.validate_limit(limit)
        sort_dir = api_utils.validate_sort_dir(sort_dir)

        marker_obj = None
        if marker:
            marker_obj = objects.Plugin.get_by_uuid(pecan.request.context,
                                                    marker)

        if sort_key in self.invalid_sort_key_list:
            raise exception.InvalidParameterValue(
                ("The sort_key value %(key)s is an invalid field for "
                 "sorting") % {'key': sort_key})

        filters = {}
        if all_plugins and not pecan.request.context.is_admin:
            msg = ("all_plugins parameter can only be used  "
                   "by the administrator.")
            raise wsme.exc.ClientSideError(msg,
                                           status_code=400)
        else:
            if not all_plugins:
                filters['owner'] = pecan.request.context.user_id
                if with_public:
                    filters['public'] = with_public

        plugins = objects.Plugin.list(pecan.request.context, limit, marker_obj,
                                      sort_key=sort_key, sort_dir=sort_dir,
                                      filters=filters)

        parameters = {'sort_key': sort_key, 'sort_dir': sort_dir}

        return PluginCollection.convert_with_links(plugins, limit,
                                                   fields=fields,
                                                   **parameters)

    @expose.expose(Plugin, types.uuid_or_name, types.listtype)
    def get_one(self, plugin_ident, fields=None):
        """Retrieve information about the given plugin.

        :param plugin_ident: UUID or logical name of a plugin.
        :param fields: Optional, a list with a specified set of fields
            of the resource to be returned.
        """

        rpc_plugin = api_utils.get_rpc_plugin(plugin_ident)
        if not rpc_plugin.public:
            cdict = pecan.request.context.to_policy_values()
            cdict['owner'] = rpc_plugin.owner
            policy.authorize('iot:plugin:get_one', cdict, cdict)

        return Plugin.convert_with_links(rpc_plugin, fields=fields)

    @expose.expose(PluginCollection, types.uuid, int, wtypes.text,
                   wtypes.text, types.listtype, types.boolean, types.boolean)
    def get_all(self, marker=None,
                limit=None, sort_key='id', sort_dir='asc',
                fields=None, with_public=False, all_plugins=False):
        """Retrieve a list of plugins.

        :param marker: pagination marker for large data sets.
        :param limit: maximum number of resources to return in a single result.
                      This value cannot be larger than the value of max_limit
                      in the [api] section of the ironic configuration, or only
                      max_limit resources will be returned.
        :param sort_key: column to sort results by. Default: id.
        :param sort_dir: direction to sort. "asc" or "desc". Default: asc.
        :param with_public: Optional boolean to get also public pluings.
        :param all_plugins: Optional boolean to get all the pluings.
                            Only for the admin
        :param fields: Optional, a list with a specified set of fields
                       of the resource to be returned.
        """
        cdict = pecan.request.context.to_policy_values()
        policy.authorize('iot:plugin:get', cdict, cdict)

        if fields is None:
            fields = _DEFAULT_RETURN_FIELDS
        return self._get_plugins_collection(marker,
                                            limit, sort_key, sort_dir,
                                            with_public=with_public,
                                            all_plugins=all_plugins,
                                            fields=fields)

    @expose.expose(Plugin, body=Plugin, status_code=201)
    def post(self, Plugin):
        """Create a new Plugin.

        :param Plugin: a Plugin within the request body.
        """
        context = pecan.request.context
        cdict = context.to_policy_values()
        policy.authorize('iot:plugin:create', cdict, cdict)

        if not Plugin.name:
            raise exception.MissingParameterValue(
                ("Name is not specified."))

        if Plugin.name:
            if not api_utils.is_valid_name(Plugin.name):
                msg = ("Cannot create plugin with invalid name %(name)s")
                raise wsme.exc.ClientSideError(msg % {'name': Plugin.name},
                                               status_code=400)

        new_Plugin = objects.Plugin(pecan.request.context,
                                    **Plugin.as_dict())

        new_Plugin.owner = cdict['user']
        new_Plugin = pecan.request.rpcapi.create_plugin(pecan.request.context,
                                                        new_Plugin)

        return Plugin.convert_with_links(new_Plugin)

    @expose.expose(None, types.uuid_or_name, status_code=204)
    def delete(self, plugin_ident):
        """Delete a plugin.

        :param plugin_ident: UUID or logical name of a plugin.
        """
        context = pecan.request.context
        cdict = context.to_policy_values()
        policy.authorize('iot:plugin:delete', cdict, cdict)

        rpc_plugin = api_utils.get_rpc_plugin(plugin_ident)
        pecan.request.rpcapi.destroy_plugin(pecan.request.context,
                                            rpc_plugin.uuid)

    @expose.expose(Plugin, types.uuid_or_name, body=Plugin, status_code=200)
    def patch(self, plugin_ident, val_Plugin):
        """Update a plugin.

        :param plugin_ident: UUID or logical name of a plugin.
        :param Plugin: values to be changed
        :return updated_plugin: updated_plugin
        """

        rpc_plugin = api_utils.get_rpc_plugin(plugin_ident)
        cdict = pecan.request.context.to_policy_values()
        cdict['owner'] = rpc_plugin.owner
        policy.authorize('iot:plugin:update', cdict, cdict)

        val_Plugin = val_Plugin.as_dict()
        for key in val_Plugin:
            try:
                rpc_plugin[key] = val_Plugin[key]
            except Exception:
                pass

        updated_plugin = pecan.request.rpcapi.update_plugin(
            pecan.request.context, rpc_plugin)
        return Plugin.convert_with_links(updated_plugin)

    @expose.expose(PluginCollection, types.uuid, int, wtypes.text,
                   wtypes.text, types.listtype, types.boolean, types.boolean)
    def detail(self, marker=None,
               limit=None, sort_key='id', sort_dir='asc',
               fields=None, with_public=False, all_plugins=False):
        """Retrieve a list of plugins.

        :param marker: pagination marker for large data sets.
        :param limit: maximum number of resources to return in a single result.
                      This value cannot be larger than the value of max_limit
                      in the [api] section of the ironic configuration, or only
                      max_limit resources will be returned.
        :param sort_key: column to sort results by. Default: id.
        :param sort_dir: direction to sort. "asc" or "desc". Default: asc.
        :param with_public: Optional boolean to get also public pluings.
        :param all_plugins: Optional boolean to get all the pluings.
                            Only for the admin
        :param fields: Optional, a list with a specified set of fields
                       of the resource to be returned.
        """

        cdict = pecan.request.context.to_policy_values()
        policy.authorize('iot:plugin:get', cdict, cdict)

        # /detail should only work against collections
        parent = pecan.request.path.split('/')[:-1][-1]
        if parent != "plugins":
            raise exception.HTTPNotFound()

        return self._get_plugins_collection(marker,
                                            limit, sort_key, sort_dir,
                                            with_public=with_public,
                                            all_plugins=all_plugins,
                                            fields=fields)
