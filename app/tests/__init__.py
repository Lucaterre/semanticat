# -*- coding: UTF-8 -*-

import pytest
try:
    from collections.abc import Callable  # noqa
except ImportError:
    from collections import Callable  # noqa


from app.config import create_app


@pytest.fixture
def client():
    app = create_app(config="test", erase_recreate=True)
    with app.test_client() as client:
        # populate with test data here ?
        yield client


