import base64
import os
from types import SimpleNamespace

from fastapi import FastAPI
from fastapi.testclient import TestClient

os.environ.setdefault('WEB_APP_USERNAME', 'testuser')
os.environ.setdefault('WEB_APP_PASSWORD', 'testpass')
os.environ.setdefault('AZURE_EXISTING_AGENT_ID', 'testagent:1')
os.environ.setdefault(
    'AZURE_EXISTING_AIPROJECT_RESOURCE_ID',
    '/subscriptions/11111111-1111-1111-1111-111111111111/resourceGroups/rg/providers/Microsoft.CognitiveServices/accounts/account/projects/project',
)

from src.api.routes import router


class DummyConversationItems:
    async def list(self, *args, **kwargs):
        class AsyncIterator:
            def __aiter__(self):
                return self

            async def __anext__(self):
                raise StopAsyncIteration

        return AsyncIterator()


class DummyConversations:
    def __init__(self):
        self.items = DummyConversationItems()

    async def retrieve(self, *args, **kwargs):
        return SimpleNamespace(id=kwargs.get('conversation_id', 'dummy-id'), metadata={})

    async def create(self, *args, **kwargs):
        return SimpleNamespace(id='dummy-id', metadata={})


class DummyOpenAI:
    def __init__(self):
        self.conversations = DummyConversations()

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        return False


def create_test_app():
    app = FastAPI()
    app.include_router(router)
    app.state.agent_version_details = SimpleNamespace(
        id='testagent:1',
        name='Test Agent',
        version='1',
        metadata={},
    )
    app.state.ai_project = SimpleNamespace(get_openai_client=lambda: DummyOpenAI())
    return app


def test_index_route_renders_html():
    client = TestClient(create_test_app())
    response = client.get('/')
    assert response.status_code == 200
    assert 'text/html' in response.headers['content-type']
    assert '<html' in response.text.lower()


def test_agent_route_blocks_without_auth():
    client = TestClient(create_test_app())
    response = client.get('/agent')
    assert response.status_code == 401


def test_agent_route_accepts_basic_auth():
    client = TestClient(create_test_app())
    token = base64.b64encode(b'testuser:testpass').decode('ascii')
    response = client.get('/agent', headers={'Authorization': f'Basic {token}'})
    assert response.status_code == 200
    assert response.json()['name'] == 'Test Agent'
    assert 'agentPlaygroundUrl' in response.json()
