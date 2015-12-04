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


class ActorSystem:

    def __init__(self, loop=None):
        self._loop = loop or asyncio.get_event_loop()
        self._actors = set()
        self._context = ActorSystemContext(self)

    def create(self, actor_type, *args, **kwargs):
        kwargs.update({'context': self._context})
        actor = actor_type(*args, **kwargs)
        self._start_actor(actor)
        return actor

    def _start_actor(self, actor):
        task = self._loop.create_task(actor.run())
        self._actors.add((actor, task))

    async def shutdown(self):
        await asyncio.wait([actor[0].stop() for actor in self._actors], loop=self._loop)

    async def await_termination(self, timeout):
        await asyncio.wait([actor[1] for actor in self._actors], timeout=timeout, loop=self._loop)
        await self.shutdown()

    def run(self, fn, debug=False):
        self._loop.set_debug(debug)
        self._loop.run_until_complete(fn(self))
        #self._loop.run_forever()


class ActorSystemContext:

    def __init__(self, system):
        self._system = system
        self._loop = self._system._loop

    def create(self, actor_type, *args, **kwargs):
        return self._system.create(actor_type, *args, **kwargs)

    def shutdown(self):
        self._loop.create_task(self._system.shutdown())

    def create_event(self):
        return asyncio.Event(loop=self._loop)

    def create_future(self):
        return asyncio.Future(loop=self._loop)

    def create_channel(self, max_size):
        return asyncio.Queue(maxsize=max_size, loop=self._loop)

    def run_in_executor(self, fn, *args):
        return self._loop.run_in_executor(None, fn, *args)

    def run_parallel(self, fs, timeout=None):
        tasks = [self._loop.create_task(fn) for fn in fs]
        return asyncio.wait(tasks, timeout=timeout, loop=self._loop)
