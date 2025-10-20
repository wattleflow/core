# WattleFlow core (excerpt)
- Date: 2025-10-21

## Examples — behavioral interfaces

Template method example:

```python
from wattleflow.core.behavioral import ITemplate

class MyTemplate(ITemplate):
    def initialise(self):
        print("initialise")
    def before_task(self):
        print("before task (hook)")
    def perform_task(self):
        print("perform task")
    def after_task(self):
        print("after task (hook)")
    def finalise(self):
        print("finalise")

MyTemplate().process()
Async iterator example (IAsyncIterator.create_iterator returns an AsyncIterator):

import asyncio
from wattleflow.core.behavioral import IAsyncIterator

class MyAsyncIterator(IAsyncIterator[int]):
    def create_iterator(self):
        async def gen():
            for i in range(3):
                yield i
        return gen()

async def main():
    it = MyAsyncIterator()
    async for item in it:
        print(item)

asyncio.run(main())
