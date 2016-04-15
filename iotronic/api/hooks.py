# -*- encoding: utf-8 -*-
#
# Copyright © 2012 New Dream Network, LLC (DreamHost)
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

from oslo_config import cfg
from pecan import hooks
from webob import exc

from iotronic.common import context
from iotronic.common import policy


from iotronic.conductor import rpcapi


class ConfigHook(hooks.PecanHook):
    """Attach the config object to the request so controllers can get to it."""

    def before(self, state):
        state.request.cfg = cfg.CONF


class DBHook(hooks.PecanHook):
    """Attach the dbapi object to the request so controllers can get to it."""

    def before(self, state):

        # state.request.dbapi = dbapi.get_instance()
        pass


class ContextHook(hooks.PecanHook):
    """Configures a request context and attaches it to the request.

    The following HTTP request headers are used:

    X-User-Id or X-User:
        Used for context.user_id.

    X-Tenant-Id or X-Tenant:
        Used for context.tenant.

    X-Auth-Token:
        Used for context.auth_token.

    X-Roles:
        Used for setting context.is_admin flag to either True or False.
        The flag is set to True, if X-Roles contains either an administrator
        or admin substring. Otherwise it is set to False.

    """

    def __init__(self, public_api_routes):
        self.public_api_routes = public_api_routes
        super(ContextHook, self).__init__()

    def before(self, state):
        headers = state.request.headers

        # Do not pass any token with context for noauth mode
        auth_token = (None if cfg.CONF.auth_strategy == 'noauth' else
                      headers.get('X-Auth-Token'))

        creds = {
            'user': headers.get('X-User') or headers.get('X-User-Id'),
            'tenant': headers.get('X-Tenant') or headers.get('X-Tenant-Id'),
            'domain_id': headers.get('X-User-Domain-Id'),
            'domain_name': headers.get('X-User-Domain-Name'),
            'auth_token': auth_token,
            'roles': headers.get('X-Roles', '').split(','),
        }

        # NOTE(adam_g): We also check the previous 'admin' rule to ensure
        # compat with default juno policy.json.  This double check may be
        # removed in L.
        is_admin = (policy.enforce('admin_api', creds, creds) or
                    policy.enforce('admin', creds, creds))
        is_public_api = state.request.environ.get('is_public_api', False)
        show_password = policy.enforce('show_password', creds, creds)

        state.request.context = context.RequestContext(
            is_admin=is_admin,
            is_public_api=is_public_api,
            show_password=show_password,
            **creds)


class RPCHook(hooks.PecanHook):
    """Attach the rpcapi object to the request so controllers can get to it."""

    def before(self, state):
        state.request.rpcapi = rpcapi.ConductorAPI()


class TrustedCallHook(hooks.PecanHook):
    """Verify that the user has admin rights.

    Checks whether the API call is performed against a public
    resource or the user has admin privileges in the appropriate
    tenant, domain or other administrative unit.

    """

    def before(self, state):
        ctx = state.request.context
        if ctx.is_public_api:
            return
        policy.enforce('admin_api', ctx.to_dict(), ctx.to_dict(),
                       do_raise=True, exc=exc.HTTPForbidden)


class NoExceptionTracebackHook(hooks.PecanHook):
    """Workaround rpc.common: deserialize_remote_exception.

    deserialize_remote_exception builds rpc exception traceback into error
    message which is then sent to the client. Such behavior is a security
    concern so this hook is aimed to cut-off traceback from the error message.

    """
    # NOTE(max_lobur): 'after' hook used instead of 'on_error' because
    # 'on_error' never fired for wsme+pecan pair. wsme @wsexpose decorator
    # catches and handles all the errors, so 'on_error' dedicated for unhandled
    # exceptions never fired.

    def after(self, state):
        # Omit empty body. Some errors may not have body at this level yet.
        if not state.response.body:
            return

        # Do nothing if there is no error.
        if 200 <= state.response.status_int < 400:
            return

        json_body = state.response.json
        # Do not remove traceback when server in debug mode (except 'Server'
        # errors when 'debuginfo' will be used for traces).
        if cfg.CONF.debug and json_body.get('faultcode') != 'Server':
            return

        faultstring = json_body.get('faultstring')
        traceback_marker = 'Traceback (most recent call last):'
        if faultstring and traceback_marker in faultstring:
            # Cut-off traceback.
            faultstring = faultstring.split(traceback_marker, 1)[0]
            # Remove trailing newlines and spaces if any.
            json_body['faultstring'] = faultstring.rstrip()
            # Replace the whole json. Cannot change original one beacause it's
            # generated on the fly.
            state.response.json = json_body
