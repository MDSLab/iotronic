# coding=utf-8

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

from iotronic.objects import base as objects_base

serializer = objects_base.IotronicObjectSerializer()


class Provisioner(object):
    def __init__(self, board=None):
        if not board:
            self.config = {"iotronic": {"extra": {}}}
        else:
            self.config = board.config
            if 'iotronic' not in self.config:
                self.config = {"iotronic": {"extra": {}}}
            if 'board' not in self.config['iotronic']:
                self.config['iotronic']['board'] = {}
            self.config['iotronic']['board'] = board.as_dict()
            self.config['iotronic']['board']['created_at'] = \
                board._attr_to_primitive('created_at')
            self.config['iotronic']['board']['updated_at'] = \
                board._attr_to_primitive('updated_at')

            try:
                del self.config['iotronic']['board']['config']
            except Exception:
                pass

    def get_config(self):
        return self.config

    def conf_registration_agent(self,
                                url="ws://<WAMP-SERVER>:<WAMP-PORT>/",
                                realm="s4t"):
        if 'wamp' not in self.config['iotronic']:
            self.config['iotronic']['wamp'] = {}
        if "registration-agent" not in self.config['iotronic']['wamp']:
            self.config['iotronic']['wamp']['registration-agent'] = {}
        if 'url' not in self.config['iotronic']['wamp']['registration-agent']:
            self.config['iotronic']['wamp']['registration-agent']['url'] = ""
        if 'realm' not in \
                self.config['iotronic']['wamp']['registration-agent']:
            self.config['iotronic']['wamp']['registration-agent']['realm'] = ""
        self.config['iotronic']['wamp']['registration-agent']['url'] = url
        self.config['iotronic']['wamp']['registration-agent']['realm'] = realm

    def conf_main_agent(self,
                        url="ws://<WAMP-SERVER>:<WAMP-PORT>/",
                        realm="s4t"):
        if 'wamp' not in self.config['iotronic']:
            self.config['iotronic']['wamp'] = {}
        if "main-agent" not in self.config['iotronic']['wamp']:
            self.config['iotronic']['wamp']['main-agent'] = {}
        if 'url' not in self.config['iotronic']['wamp']['main-agent']:
            self.config['iotronic']['wamp']['main-agent']['url'] = ""
        if 'realm' not in self.config['iotronic']['wamp']['main-agent']:
            self.config['iotronic']['wamp']['main-agent']['realm'] = ""
        self.config['iotronic']['wamp']['main-agent']['url'] = url
        self.config['iotronic']['wamp']['main-agent']['realm'] = realm

    def conf_clean(self):
        self.conf_registration_agent()
        if 'board' not in self.config['iotronic']:
            self.config['iotronic']['board'] = {}
        self.config['iotronic']['board']['token'] = "<REGISTRATION-TOKEN>"

    def conf_location(self, location):
        if "location" not in self.config['iotronic']['board']:
            self.config['iotronic']['board']['location'] = {}
        self.config['iotronic']['board']['location'] = location.get_geo()
