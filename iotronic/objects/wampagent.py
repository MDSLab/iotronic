# coding=utf-8
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

from iotronic.common.i18n import _
from iotronic.db import api as db_api
from iotronic.objects import base


class WampAgent(base.IotronicObject):
    dbapi = db_api.get_instance()

    fields = {
        'id': int,
        'hostname': str,
        'wsurl': str,
        'online': bool,
        'ragent': bool,
    }

    @staticmethod
    def _from_db_object(wampagent, db_obj):
        """Converts a database entity to a formal object."""
        for field in wampagent.fields:
            wampagent[field] = db_obj[field]

        wampagent.obj_reset_changes()
        return wampagent

    @base.remotable_classmethod
    def get_by_hostname(cls, context, hostname):
        """Get a WampAgent record by its hostname.

        :param hostname: the hostname on which a WampAgent is running
        :returns: a :class:`WampAgent` object.
        """
        db_obj = cls.dbapi.get_wampagent(hostname)
        wampagent = WampAgent._from_db_object(cls(context), db_obj)
        return wampagent

    @base.remotable_classmethod
    def get_registration_agent(cls, context=None):
        """Get a Registration WampAgent

        :param hostname: the hostname on which a WampAgent is running
        :returns: a :class:`WampAgent` object.
        """
        db_obj = cls.dbapi.get_registration_wampagent()
        wampagent = WampAgent._from_db_object(cls(context), db_obj)
        return wampagent

    def save(self, context):
        """Save is not supported by WampAgent objects."""
        raise NotImplementedError(
            _('Cannot update a wampagent record directly.'))

    @base.remotable
    def refresh(self, context=None):
        """Loads and applies updates for this WampAgent.

        Loads a :class:`WampAgent` with the same uuid from the database and
        checks for updated attributes.

        :param context: Security context. NOTE: This should only
                        be used internally by the indirection_api.
                        Unfortunately, RPC requires context as the first
                        argument, even though we don't use it.
                        A context should be set when instantiating the
                        object, e.g.: WampAgent(context)
        """
        current = self.__class__.get_by_hostname(self._context,
                                                 hostname=self.hostname)
        for field in self.fields:
            if (hasattr(
                    self, base.get_attrname(field)) and
                    self[field] != current[field]):
                self[field] = current[field]

    @base.remotable
    def touch(self, context):
        """Touch this wampagent's DB record, marking it as up-to-date."""
        self.dbapi.touch_wampagent(self.hostname)

    @base.remotable_classmethod
    def list(cls, context, limit=None, marker=None, sort_key=None,
             sort_dir=None, filters=None):
        """Return a list of WampAgent objects.

        :param context: Security context.
        :param limit: maximum number of resources to return in a single result.
        :param marker: pagination marker for large data sets.
        :param sort_key: column to sort results by.
        :param sort_dir: direction to sort. "asc" or "desc".
        :param filters: Filters to apply.
        :returns: a list of :class:`WampAgent` object.

        """
        db_wampagents = cls.dbapi.get_wampagent_list(filters=filters,
                                                     limit=limit,
                                                     marker=marker,
                                                     sort_key=sort_key,
                                                     sort_dir=sort_dir)
        return [WampAgent._from_db_object(cls(context),
                                          obj) for obj in db_wampagents]
