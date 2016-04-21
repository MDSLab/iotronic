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

import json


class WampResponse(object):

    def __init__(self):
        self.response = {}

    def getResponse(self):
        return json.dumps(self.response)

    def addSection(self, name, value=''):
        self.response[name] = value

    def addElement(self, position, value, section):
        if isinstance(self.response[section], list):
            self.response[section].append({"position": position,
                                           "value": value})
        elif isinstance(self.response[section], dict):
            self.response[section][position] = value

    def addConfig(self, action, position, value, section='config'):
        if isinstance(self.response[section], list):
            self.response[section].append({"action": action,
                                           "position": position,
                                           "value": value})

    def removeSection(self, name):
        self.response.pop(name, None)

    def clearSection(self, name):
        self.response[name] = ''

    def clearConfig(self):
        self.addSection('config', [])
        self.addConfig('clear', 'config', {"iotronic": {"registration-agent": {
            "url": "",
            "port": "",
            "realm": ""
        }},
            "log": {
            "logfile": "s4t-lightning-rod.log",
            "loglevel": "info"
        },
            "node": {
            "token": ""}
        })
