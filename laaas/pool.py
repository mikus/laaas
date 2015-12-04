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

import itertools

from .actor import AbstractActor


class ActorPool(AbstractActor):

    def __init__(self, router_type, actor_factory, actor_type, size, context, *args, **kwargs):
        super().__init__(context)
        kwargs.update({'context': context})
        self._actors = actor_factory(actor_type, size, *args, **kwargs)
        self._router = router_type(self._actors)

    async def _receive(self, message):
        await self._router.receive(message)

    async def stop(self):
        for actor in self._actors:
            await actor.stop()

    async def run(self):
        tasks = [actor.run() for actor in self._actors]
        await self._context.run_parallel(tasks)


class SimpleActorFactory:

    @staticmethod
    def create_actor(actor_type, *args, **kwargs):
        return actor_type(*args, **kwargs)

    @classmethod
    def create_actors(cls, actor_type, size, *args, **kwargs):
        return [cls.create_actor(actor_type, *args, **kwargs) for _ in range(size)]


class RoundRobinRouter:

    def __init__(self, actors):
        self._actors = actors
        self._iterator = itertools.cycle(self._actors)

    def receive(self, message):
        actor = next(self._iterator)
        return actor._receive(message)


class RoundRobinPool(ActorPool):

    def __init__(self, actor_type, size, context, *args, **kwargs):
        super().__init__(RoundRobinRouter, SimpleActorFactory.create_actors, actor_type, size, context, *args, **kwargs)
