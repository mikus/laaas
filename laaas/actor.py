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

import asyncio

import functools
import inspect

from .message import ActorMessage, QueryMessage, stop_message


class AbstractActor(object):

    def __init__(self, context):
        self._context = context
        self._running = False
        self._completed = self._context.create_event()

    async def stop(self):
        self._running = False
        await self._before_stop()
        await self._completed.wait()

    async def tell(self, payload, sender=None, message_factory=ActorMessage):
        message = message_factory(payload, sender)
        await self._receive(message)

    async def ask(self, payload, sender=None):
        result = self._context.create_future()
        message_factory = functools.partial(QueryMessage, result)
        await self.tell(payload, sender, message_factory)
        return await result

    async def run(self):
        self._completed.clear()
        self._running = True
        await self._after_start()
        while self._running:
            await self._step()
        self._completed.set()

    async def _receive(self, message):
        raise NotImplementedError('Subclasses of AbstractActor must implement _receive()')

    async def _step(self):
        raise NotImplementedError('Subclasses of AbstractActor must implement _task()')

    async def _after_start(self): pass

    async def _before_stop(self): pass


class BaseActor(AbstractActor):

    def __init__(self, context, inbox_size=0):
        super().__init__(context)
        self._inbox = context.create_channel(inbox_size)
        self._handlers = {}
        for k, v in inspect.getmembers(self):
            if getattr(v, 'handler', False) is True:
                self.register_handler(v.type, v)

    def register_handler(self, message_cls, func):
        if not asyncio.iscoroutinefunction(func):
            raise ValueError('Handler {} should be a coroutine'.format(func))
        self._handlers[message_cls] = func

    async def _step(self):
        message = await self._inbox.get()
        handler = self._handlers.get(type(message.payload))
        if handler is None:
            for payload_type in self._handlers.keys():
                if isinstance(message.payload, payload_type):
                    handler = self._handlers[payload_type]
                    break
        if handler:
            result = None
            sig = inspect.signature(handler)
            if len(sig.parameters) == 1:
                result = await handler(message.payload)
            elif len(sig.parameters) == 2:
                result = await handler(message.payload, message.sender)
            try:
                if not message.result.cancelled():
                    message.result.set_result(result)
            except AttributeError:
                pass

    async def _receive(self, message):
        await self._inbox.put(message)

    async def _before_stop(self):
        await self._receive(stop_message)
