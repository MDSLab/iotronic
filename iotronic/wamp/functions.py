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

from iotronic.common import exception
from iotronic import objects
from iotronic.wamp.wampresponse import WampResponse
from oslo_log import log

LOG = log.getLogger(__name__)


def leave_function(session_id):
    LOG.debug('A node with %s disconnectd', session_id)
    try:
        old_session = objects.SessionWP({}).get_by_session_id({}, session_id)
        old_session.valid = False
        old_session.save()
        LOG.debug('Session %s deleted', session_id)
    except Exception:
        LOG.debug('session %s not found', session_id)


def echo(text):
    LOG.debug(text)
    return text


def registration(code_node, session_num):
    LOG.debug('Receved registration from %s with session %s',
              code_node, session_num)
    try:
        node = objects.Node.get_by_code({}, code_node)
    except Exception:
        return exception.NodeNotFound(node=code_node)
    try:
        old_session = objects.SessionWP(
            {}).get_session_by_node_uuid(node.uuid, valid=True)
        old_session.valid = False
        old_session.save()
    except Exception:
        LOG.debug('valid session for %s Not found', node.uuid)

    session = objects.SessionWP({})
    session.node_id = node.id
    session.node_uuid = node.uuid
    session.session_id = session_num
    session.create()
    session.save()

    r = WampResponse()

    r.addSection('config', [])
    r.addConfig('add', 'config:node:uuid', node.uuid, 'config')
    r.addConfig('add', 'config:iotronic:command-agent',
                {"url": "ws://cmd-iotronic", "port": "8181",
                 "realm": "s4t"}, 'config')

    return r.getResponse()


def registration_uuid(uuid, session_num):
    LOG.debug('Receved registration from %s with session %s',
              uuid, session_num)
    try:
        node = objects.Node.get_by_uuid({}, uuid)
    except Exception:
        return exception.NodeNotFound(node=uuid)
    try:
        old_session = objects.SessionWP(
            {}).get_session_by_node_uuid(node.uuid, valid=True)
        old_session.valid = False
        old_session.save()
    except Exception:
        LOG.debug('valid session for %s not found', node.uuid)

    session = objects.SessionWP({})
    session.node_id = node.id
    session.node_uuid = node.uuid
    session.session_id = session_num
    session.create()
    session.save()
    r = WampResponse()
    r.addSection('result', 0)
    return r.getResponse()
