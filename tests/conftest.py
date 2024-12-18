import pytest


@pytest.fixture()
@pytest.fixture(scope='session')
def event_loop():
    import asyncio
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest.fixture()
async def client(aiohttp_client):
    from server import application
    return await aiohttp_client(application)
