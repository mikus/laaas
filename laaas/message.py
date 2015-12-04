# Copyright 2015 Mikołaj Olszewski
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.


class Message:

    def __init__(self, payload=None):
        self.payload = payload


class ActorMessage(Message):

    def __init__(self, payload=None, sender=None):
        super().__init__(payload)
        self.sender = sender


class QueryMessage(ActorMessage):

    def __init__(self, future, payload=None, sender=None):
        super().__init__(payload, sender)
        self.result = future


class SystemMessage(Message):

    def __init__(self, payload=None):
        super().__init__(payload)


class StopMessage(SystemMessage): pass


stop_message = StopMessage()
