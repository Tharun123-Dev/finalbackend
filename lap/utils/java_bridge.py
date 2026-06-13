from __future__ import annotations

import json
import urllib.error
import urllib.parse
import urllib.request

from django.conf import settings


def _post_json(path: str, payload: dict, timeout: float = 2.5) -> dict:
    base_url = getattr(settings, 'JAVA_AUTH_BASE_URL', '').rstrip('/')
    if not base_url:
        return {}

    data = json.dumps(payload).encode('utf-8')
    request = urllib.request.Request(
        f'{base_url}/{path.lstrip("/")}',
        data=data,
        headers={
            'Accept': 'application/json',
            'Content-Type': 'application/json',
        },
        method='POST',
    )

    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            body = response.read().decode('utf-8')
    except (urllib.error.URLError, TimeoutError, ValueError):
        return {}

    try:
        parsed = json.loads(body or '{}')
    except json.JSONDecodeError:
        return {}
    return parsed if isinstance(parsed, dict) else {}


def _request_json(base_url: str, path: str, token: str = '', timeout: float = 2.5):
    base_url = (base_url or '').rstrip('/')
    if not base_url:
        return None

    headers = {'Accept': 'application/json'}
    if token:
        headers['Authorization'] = f'Bearer {token}'

    request = urllib.request.Request(
        f'{base_url}/{path.lstrip("/")}',
        headers=headers,
        method='GET',
    )

    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            body = response.read().decode('utf-8')
    except (urllib.error.URLError, TimeoutError, ValueError):
        return None

    try:
        return json.loads(body or '{}')
    except json.JSONDecodeError:
        return None


def _get_json(path: str, token: str, timeout: float = 2.5) -> dict:
    base_url = getattr(settings, 'JAVA_AUTH_BASE_URL', '').rstrip('/')
    if not base_url or not token:
        return {}

    parsed = _request_json(base_url, path, token, timeout)
    return parsed if isinstance(parsed, dict) else {}


def _java_api_base_url() -> str:
    explicit = getattr(settings, 'JAVA_API_BASE_URL', '').rstrip('/')
    if explicit:
        return explicit
    auth_base = getattr(settings, 'JAVA_AUTH_BASE_URL', '').rstrip('/')
    if auth_base.endswith('/api/auth'):
        return auth_base[:-len('/api/auth')]
    if auth_base.endswith('/auth'):
        return auth_base[:-len('/auth')]
    return auth_base


def validate_token(token: str) -> dict:
    if not token:
        return {}
    data = _post_json('validate-token', {'token': token})
    return data if data.get('valid') is True else {}


def current_user(token: str) -> dict:
    return _get_json('me', token)


def list_users(token: str):
    if not token:
        return []

    base_url = _java_api_base_url()
    candidates = getattr(settings, 'JAVA_USERS_PATHS', None) or [
        'api/users',
        'api/auth/users',
        'users',
        'api/user',
    ]

    users = []
    seen = set()
    requested_paths = set()

    def add_user(item):
        if not isinstance(item, dict):
            return
        key = (
            item.get('id')
            or item.get('userId')
            or item.get('user_id')
            or item.get('email')
            or item.get('username')
        )
        key = str(key or '').strip().lower()
        if not key or key in seen:
            return
        seen.add(key)
        users.append(item)

    def extract_list(payload):
        if isinstance(payload, list):
            return payload
        if not isinstance(payload, dict):
            return []
        for key in ('users', 'data', 'content', 'items', 'results'):
            value = payload.get(key)
            if isinstance(value, list):
                return value
            if isinstance(value, dict):
                nested = value.get('content') or value.get('items') or value.get('results')
                if isinstance(nested, list):
                    return nested
        return []

    def page_info(payload):
        if not isinstance(payload, dict):
            return {}

        page_source = payload
        for key in ('data', 'page', 'pagination'):
            value = payload.get(key)
            if isinstance(value, dict):
                page_source = {**page_source, **value}

        total_pages = (
            page_source.get('totalPages')
            or page_source.get('total_pages')
            or page_source.get('pages')
        )
        current_page = (
            page_source.get('number')
            if page_source.get('number') is not None
            else page_source.get('page')
        )
        last = page_source.get('last')
        return {
            'total_pages': int(total_pages) if str(total_pages or '').isdigit() else None,
            'current_page': int(current_page) if str(current_page or '').isdigit() else None,
            'last': last if isinstance(last, bool) else None,
        }

    def with_params(path, **params):
        clean_params = {key: value for key, value in params.items() if value is not None}
        separator = '&' if '?' in path else '?'
        return f'{path}{separator}{urllib.parse.urlencode(clean_params)}'

    def request_path(path):
        if path in requested_paths:
            return None
        requested_paths.add(path)
        return _request_json(base_url, path, token, timeout=4)

    for path in candidates:
        payload = request_path(path)
        for item in extract_list(payload):
            add_user(item)

        for size_key in ('size', 'limit', 'pageSize'):
            payload = request_path(with_params(path, **{size_key: 1000}))
            for item in extract_list(payload):
                add_user(item)

        for page_key, first_page in (('page', 0), ('page', 1)):
            for page in range(first_page, first_page + 20):
                payload = request_path(with_params(path, **{page_key: page, 'size': 100}))
                page_items = extract_list(payload)
                if not page_items:
                    break
                for item in page_items:
                    add_user(item)

                info = page_info(payload)
                total_pages = info.get('total_pages')
                current_page = info.get('current_page')
                if info.get('last') is True:
                    break
                if total_pages is not None and current_page is not None and current_page + 1 >= total_pages:
                    break
    return users


def check_permission(token: str, permission: str) -> bool:
    if not token or not permission:
        return False
    data = _post_json('check-permission', {
        'token': token,
        'permission': permission,
    })
    return data.get('valid') is True and data.get('allowed') is True
