import json
import os
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError
from urllib.parse import quote

from django.conf import settings


def get_supabase_config():
    return {
        'url': getattr(settings, 'SUPABASE_URL', os.getenv('SUPABASE_URL', '')).rstrip('/'),
        'anon_key': getattr(settings, 'SUPABASE_ANON_KEY', os.getenv('SUPABASE_ANON_KEY', '')),
        'service_role_key': getattr(settings, 'SUPABASE_SERVICE_ROLE_KEY', os.getenv('SUPABASE_SERVICE_ROLE_KEY', '')),
        'connection_string': getattr(settings, 'SUPABASE_CONNECTION_STRING', os.getenv('SUPABASE_CONNECTION_STRING', '')),
        'active_key': (
            getattr(settings, 'SUPABASE_SERVICE_ROLE_KEY', os.getenv('SUPABASE_SERVICE_ROLE_KEY', ''))
            or getattr(settings, 'SUPABASE_ANON_KEY', os.getenv('SUPABASE_ANON_KEY', ''))
        ),
    }


def fetch_supabase_rows(table_name, select_fields=None, filters=None):
    config = get_supabase_config()
    if not config['url'] or not config['anon_key']:
        return []

    select = ','.join(select_fields or ['*'])
    url = f"{config['url']}/rest/v1/{table_name}?select={select}"

    active_key = config.get('active_key') or config.get('anon_key') or config.get('service_role_key')
    headers = {
        'apikey': active_key,
        'Authorization': f"Bearer {active_key}",
        'Accept': 'application/json',
    }

    if filters:
        for field, value in filters.items():
            url += f"&{quote(str(field), safe='')}=eq.{quote(str(value), safe='')}"

    request = Request(url, headers=headers, method='GET')
    try:
        with urlopen(request, timeout=10) as response:
            payload = response.read().decode('utf-8')
            return json.loads(payload) if payload else []
    except (HTTPError, URLError, json.JSONDecodeError, ValueError):
        return []


def update_supabase_record(table_name, record_id, payload):
    config = get_supabase_config()
    if not config['url'] or not config.get('active_key'):
        return False

    url = f"{config['url']}/rest/v1/{table_name}?id=eq.{record_id}"
    headers = {
        'apikey': config.get('active_key'),
        'Authorization': f"Bearer {config.get('active_key')}",
        'Content-Type': 'application/json',
        'Accept': 'application/json',
        'Prefer': 'return=minimal',
    }
    request = Request(url, data=json.dumps(payload).encode('utf-8'), headers=headers, method='PATCH')
    try:
        with urlopen(request, timeout=10) as response:
            return response.status == 200 or response.status == 204
    except (HTTPError, URLError, json.JSONDecodeError, ValueError):
        return False


def insert_supabase_record(table_name, payload):
    config = get_supabase_config()
    if not config['url'] or not config.get('active_key'):
        return None

    url = f"{config['url']}/rest/v1/{table_name}"
    headers = {
        'apikey': config.get('active_key'),
        'Authorization': f"Bearer {config.get('active_key')}",
        'Content-Type': 'application/json',
        'Accept': 'application/json',
        'Prefer': 'return=representation',
    }
    request = Request(url, data=json.dumps(payload).encode('utf-8'), headers=headers, method='POST')
    try:
        with urlopen(request, timeout=10) as response:
            payload = response.read().decode('utf-8')
            return json.loads(payload)[0] if payload else None
    except (HTTPError, URLError, json.JSONDecodeError, ValueError):
        return None


def delete_supabase_records(table_name, filters):
    config = get_supabase_config()
    if not config['url'] or not config.get('active_key') or not filters:
        return False

    url = f"{config['url']}/rest/v1/{table_name}?"
    url += '&'.join(
        f"{quote(str(field), safe='')}=eq.{quote(str(value), safe='')}"
        for field, value in filters.items()
    )
    headers = {
        'apikey': config.get('active_key'),
        'Authorization': f"Bearer {config.get('active_key')}",
        'Accept': 'application/json',
        'Prefer': 'return=minimal',
    }
    request = Request(url, headers=headers, method='DELETE')
    try:
        with urlopen(request, timeout=10) as response:
            return response.status == 200 or response.status == 204
    except (HTTPError, URLError, json.JSONDecodeError, ValueError):
        return False


def normalize_supabase_status(value):
    if value is None:
        return 'pending'

    normalized = str(value).strip().lower()
    if normalized in {'pending', 'scanned', 'ocr_completed', 'in_review', 'processing', 'sent_to_bank'}:
        return 'pending'
    if normalized in {'approved', 'accepted', 'settled'}:
        return 'approved'
    if normalized in {'rejected', 'rescan'}:
        return 'rejected'
    return 'pending'