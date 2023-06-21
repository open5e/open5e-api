"""Pytest configuration module."""
import pytest

from api.models import Document


@pytest.fixture
def document():
    data = {
        "id": 1,
        "slug": "o5e",
        "title": "Open5e OGL",
        "desc": "Open5e Original Content",
        "license": "Open Gaming License",
        "author": "Ean Moody and Open Source Contributors from github.com/open5e-api",
        "organization": "Open5e",
        "version": "1.0",
        "url": "open5e.com",
        "copyright": "Open5e.com Copyright 2019.",
        "created_at": "2023-05-17 14:25:56.586864",
        "license_url": "http://open5e.com/legal",
    }
    _document = Document.objects.create(**data)
    return _document
