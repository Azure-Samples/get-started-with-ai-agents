import os
import pytest


def pytest_configure(config):
    config.addinivalue_line(
        'markers',
        'integration: mark tests that require Azure environment variables and live Azure resources.'
    )


def pytest_collection_modifyitems(config, items):
    azure_endpoint = os.environ.get('AZURE_EXISTING_AIPROJECT_ENDPOINT', '')
    if not azure_endpoint:
        skip_integration = pytest.mark.skip(
            reason='Skipping Azure integration tests because AZURE_EXISTING_AIPROJECT_ENDPOINT is not set.'
        )
        for item in items:
            if 'integration' in item.keywords:
                item.add_marker(skip_integration)
