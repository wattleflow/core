# --------------------------------------------
# Requirements:
# pip install pytest
# --------------------------------------------
import pytest
import asyncio

def test_istate_requires_handle():
    from wattleflow.core.behavioral import IState
    # subclass that does not implement handle remains abstract => cannot instantiate
    class BadState(IState):
        pass
    with pytest.raises(TypeError):
        BadState()

def test_itemplate_calls_hooks_and_finalise():
    from wattleflow.core.behavioral import ITemplate
    calls = []
    class MyTemplate(ITemplate):
        def initialise(self):
            calls.append("initialise")
        def before_task(self):
            calls.append("before")
        def perform_task(self):
            calls.append("perform")
        def after_task(self):
            calls.append("after")
        def finalise(self):
            calls.append("finalise")

    t = MyTemplate()
    t.process()
    assert calls == ["initialise", "before", "perform", "after", "finalise"]

def test_iasynciterator_create_and_iterate():
    from wattleflow.core.behavioral import IAsyncIterator
    class MyAsyncIterator(IAsyncIterator[int]):
        def create_iterator(self):
            async def gen():
                for i in range(3):
                    yield i
            return gen()

    async def collect():
        it = MyAsyncIterator()
        res = []
        async for x in it:
            res.append(x)
        return res

    result = asyncio.run(collect())
    assert result == [0, 1, 2]