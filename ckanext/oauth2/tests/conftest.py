# -*- coding: utf-8 -*-
"""Shared fixtures for the ckanext-oauth2 tests.

``OAuth2Helper.__init__`` reads each setting from the environment first and only
falls back to the CKAN config, so the ``CKAN_OAUTH2_*`` variables a deployment
puts in its ``.env`` silently win over the values these tests place in
``toolkit.config``. Run the suite inside a configured container without this and
most of ``test_oauth2.py`` fails against the real provider's settings rather than
the test ones -- ``test_minimum_conf`` in particular can never see a missing key.
"""

import os

import pytest


@pytest.fixture(autouse=True)
def isolate_oauth2_env(monkeypatch):
    """Hide the deployment's OAuth2 environment from every test."""
    for name in [key for key in os.environ if key.startswith('CKAN_OAUTH2_')]:
        monkeypatch.delenv(name, raising=False)
