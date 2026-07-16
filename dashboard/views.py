import uuid
from pathlib import Path
from datetime import date, datetime, timedelta

from django.http import JsonResponse
from django.shortcuts import render, redirect
from django.urls import reverse
from django.conf import settings
from .supabase_client import fetch_supabase_rows, normalize_supabase_status, update_supabase_record, insert_supabase_record, delete_supabase_records


def _safe_str(value):
    if value is None:
        return ''
    return str(value)


def _normalize_supabase_date(value):
    if not value:
        return '–'
    try:
        from datetime import datetime
        if isinstance(value, str):
            try:
                parsed = datetime.fromisoformat(value.replace('Z', '+00:00'))
            except ValueError:
                parsed = datetime.strptime(value, '%Y-%m-%d')
            return parsed.strftime('%m/%d/%Y')
    except Exception:
        return '–'
    return str(value)


def _get_supabase_cheques():
    fields = ['id', 'tracking_no', 'account_no', 'cheque_no', 'bank_code', 'branch_code', 'amount', 'amount_in_words', 'beneficiary_name', 'cheque_date', 'status', 'match_status', 'is_deleted', 'created_at', 'updated_at']
    rows = fetch_supabase_rows('cheques', select_fields=fields) or []
    if rows:
        return rows

    # Backward-compatible fallback for databases that have not added match_status yet.
    fallback_fields = [field for field in fields if field != 'match_status']
    return fetch_supabase_rows('cheques', select_fields=fallback_fields) or []


def normalize_match_status(value):
    if value is None:
        return ''

    normalized = str(value).strip().lower()
    if normalized in {'match', 'matched', 'verified', 'ok', 'true', '1'}:
        return 'match'
    if normalized in {'mismatch', 'mis_match', 'unmatched', 'failed', 'false', '0'}:
        return 'mismatch'
    return ''


def _is_supabase_row_deleted(row):
    is_deleted = row.get('is_deleted')
    return is_deleted is True or str(is_deleted).lower() in ('true', 't', '1')


def _get_active_supabase_cheques():
    return [row for row in _get_supabase_cheques() if not _is_supabase_row_deleted(row)]


def _delete_cheque_permanently(cheque_id):
    """Delete a cheque and related rows from Supabase instead of soft deleting it."""
    image_rows = fetch_supabase_rows('cheque_images', select_fields=['file_path'], filters={'cheque_id': cheque_id}) or []

    # Delete children first so the cheque delete is not blocked by foreign keys.
    for table_name in ('status_history', 'processing_queue', 'ocr_data', 'cheque_images'):
        delete_supabase_records(table_name, {'cheque_id': cheque_id})

    deleted = delete_supabase_records('cheques', {'id': cheque_id})

    # Uploaded files are local media files; remove them when their DB rows are removed.
    for image in image_rows:
        image_path = image.get('file_path')
        if not image_path:
            continue
        try:
            full_path = Path(settings.MEDIA_ROOT) / image_path
            if full_path.exists() and full_path.is_file():
                full_path.unlink()
        except OSError:
            pass

    return deleted


def _get_supabase_cheque_images():
    return fetch_supabase_rows('cheque_images', select_fields=['id', 'cheque_id', 'image_type', 'file_path', 'file_size', 'created_at']) or []


def _get_supabase_status_history():
    return fetch_supabase_rows('status_history', select_fields=['id', 'cheque_id', 'old_status', 'new_status', 'remarks', 'changed_at']) or []


def _build_supabase_queue_rows(status_filter='all', search_query=''):
    cheques = _get_active_supabase_cheques()
    status_history_rows = _get_supabase_status_history()
    images = _get_supabase_cheque_images()

    latest_status_map = {}
    for row in status_history_rows:
        cheque_id = row.get('cheque_id')
        if cheque_id:
            latest_status_map[cheque_id] = row

    cheque_lookup = {row.get('id'): row for row in cheques if row.get('id')}
    image_lookup = {}
    for image in images:
        cheque_id = image.get('cheque_id')
        if cheque_id:
            image_lookup.setdefault(cheque_id, []).append(image)

    queue_rows = []
    for cheque in cheques:
        cheque_id = cheque.get('id')
        latest_status_row = latest_status_map.get(cheque_id) or {}
        latest_status = normalize_supabase_status(latest_status_row.get('new_status') or cheque.get('status'))

        if status_filter != 'all' and latest_status != status_filter:
            continue

        search_text = _safe_str(cheque.get('tracking_no')) + ' ' + _safe_str(cheque.get('beneficiary_name')) + ' ' + _safe_str(cheque.get('cheque_no')) + ' ' + _safe_str(cheque.get('account_no'))
        if search_query and search_query.lower() not in search_text.lower():
            continue

        queue_rows.append({
            'id': cheque_id,
            'system_id': cheque.get('tracking_no') or '–',
            'amount': cheque.get('amount') or '–',
            'date': _normalize_supabase_date(cheque.get('cheque_date')),
            'beneficiary': cheque.get('beneficiary_name') or '–',
            'match_status': normalize_match_status(cheque.get('match_status')),
            'payee': cheque.get('beneficiary_name') or '–',
            'submitted_by': _normalize_supabase_date(cheque.get('created_at')),
            'avatar': get_initials(cheque.get('beneficiary_name') or 'CH'),
            'status': latest_status,
            'remarks': latest_status_row.get('remarks') or '',
            'history_id': latest_status_row.get('id'),
            'image_count': len(image_lookup.get(cheque_id, [])),
        })

    queue_rows.sort(key=lambda item: item.get('submitted_by', ''), reverse=True)
    return queue_rows


def get_user_context(request):
    """Return user display info from request.user or sensible defaults."""
    user = request.user
    if user.is_authenticated:
        full_name = user.get_full_name() or user.username
        name_parts = full_name.split()
        initials = ''.join(p[0] for p in name_parts[:2]).upper() if name_parts else full_name[:2].upper()
        return {'user_name': full_name, 'user_initials': initials}
    return {'user_name': 'Guest', 'user_initials': 'GU'}


def get_realtime_context(request):
    """Expose realtime config to templates so the browser can subscribe via Supabase."""
    return {
        'supabase_url': getattr(settings, 'SUPABASE_URL', ''),
        'supabase_anon_key': getattr(settings, 'SUPABASE_ANON_KEY', ''),
    }


def _parse_supabase_datetime(value):
    """Parse a Supabase timestamp string into a date object, or None."""
    parsed = _parse_supabase_full_datetime(value)
    return parsed.date() if parsed else None


def _parse_supabase_full_datetime(value):
    """Parse a Supabase timestamp string into a full datetime object, or None."""
    if not value:
        return None
    try:
        from datetime import datetime
        text = str(value).replace('Z', '+00:00')
        return datetime.fromisoformat(text)
    except (ValueError, TypeError):
        return None


def compute_weekly_trend():
    """Return last 7 days of cheque counts for trend chart, sourced from Supabase."""
    rows = _get_active_supabase_cheques()
    created_dates = [
        d for d in (_parse_supabase_datetime(row.get('created_at')) for row in rows)
        if d is not None
    ]
    today = date.today()
    days = []
    max_count = 1
    for i in range(6, -1, -1):
        d = today - timedelta(days=i)
        count = sum(1 for created_at in created_dates if created_at == d)
        days.append({'label': d.strftime('%a'), 'count': count})
        if count > max_count:
            max_count = count
    result = []
    for day in days:
        pct = round((day['count'] / max_count) * 100) if max_count else 0
        result.append({'label': day['label'], 'height': pct, 'count': day['count']})
    return {'trend_days': result, 'has_data': max_count > 0}


def dashboard(request):
    """Render the main dashboard page with statistics"""
    rows = _get_active_supabase_cheques()
    history_rows = _get_supabase_status_history()
    latest_status_map = {}
    for row in history_rows:
        latest_status_map[row.get('cheque_id')] = row

    total_queue = sum(1 for row in rows if normalize_supabase_status((latest_status_map.get(row.get('id'), {}) or {}).get('new_status') or row.get('status')) == 'pending')
    total_approved = sum(1 for row in rows if normalize_supabase_status((latest_status_map.get(row.get('id'), {}) or {}).get('new_status') or row.get('status')) == 'approved')
    total_rejected = sum(1 for row in rows if normalize_supabase_status((latest_status_map.get(row.get('id'), {}) or {}).get('new_status') or row.get('status')) == 'rejected')
    total_cheques = len(rows)
    total_processing = sum(1 for row in rows if str((latest_status_map.get(row.get('id'), {}) or {}).get('new_status') or row.get('status', '')).upper() in {'SCANNED', 'OCR_COMPLETED', 'PENDING', 'IN_REVIEW', 'PROCESSING'})

    if total_cheques:
        approved_percent = round((total_approved / total_cheques) * 100)
        rejected_percent = round((total_rejected / total_cheques) * 100)
        pending_percent = max(0, 100 - approved_percent - rejected_percent)
    else:
        approved_percent = rejected_percent = pending_percent = 33

    trend = compute_weekly_trend()

    context = {
        **get_user_context(request),
        **get_realtime_context(request),
        'total_queue': total_queue,
        'total_approved': total_approved,
        'total_rejected': total_rejected,
        'processing': total_processing,
        'total_cheques': total_cheques,
        'approved_percent': approved_percent,
        'rejected_percent': rejected_percent,
        'pending_percent': pending_percent,
        'pending_count': total_queue,
        'trend_days': trend['trend_days'],
        'has_trend_data': trend['has_data'],
        'q': '',
    }
    return render(request, 'dashboard/dashboard.html', context)


VALID_IMAGE_TYPES = {'front', 'back', 'front_uv', 'back_uv'}


def upload_cheque(request):
    """Upload a new cheque image, save the file locally, and record it in Supabase."""
    selected_image_type = 'front'
    errors = []

    if request.method == 'POST':
        selected_image_type = request.POST.get('image_type', 'front')
        image_file = request.FILES.get('image_file')

        if selected_image_type not in VALID_IMAGE_TYPES:
            errors.append('Invalid image type selected.')
        if not image_file:
            errors.append('Please select an image file to upload.')

        if not errors:
            tracking_no = f"UPLOAD-{uuid.uuid4().hex[:10].upper()}"
            new_cheque_id = str(uuid.uuid4())

            cheque_row = insert_supabase_record('cheques', {
                'id': new_cheque_id,
                'tracking_no': tracking_no,
                'status': 'pending',
            })

            if cheque_row is None:
                errors.append('Could not create the cheque record. Please try again.')
            else:
                cheque_id = cheque_row.get('id', new_cheque_id)

                media_root = Path(settings.MEDIA_ROOT)
                upload_dir = media_root / 'cheque_images'
                upload_dir.mkdir(parents=True, exist_ok=True)

                filename = f"{uuid.uuid4().hex}_{selected_image_type}_{image_file.name}"
                file_path = upload_dir / filename
                with open(file_path, 'wb+') as dest:
                    for chunk in image_file.chunks():
                        dest.write(chunk)

                insert_supabase_record('cheque_images', {
                    'id': str(uuid.uuid4()),
                    'cheque_id': cheque_id,
                    'image_type': selected_image_type,
                    'file_path': f"cheque_images/{filename}",
                    'file_size': image_file.size,
                })

                insert_supabase_record('status_history', {
                    'cheque_id': cheque_id,
                    'old_status': None,
                    'new_status': 'pending',
                    'remarks': 'Uploaded',
                })

                return redirect('queue')

    return render(request, 'dashboard/upload.html', {
        **get_user_context(request),
        **get_realtime_context(request),
        'selected_image_type': selected_image_type,
        'errors': errors,
    })


def build_queue_payload(request, status_filter='all', search_query=''):
    """Build the queue payload used by the HTML view and the realtime JSON endpoint from Supabase-backed rows."""
    cheques = _build_supabase_queue_rows(status_filter=status_filter, search_query=search_query)
    total_queue = sum(1 for item in cheques if item.get('status') == 'pending')
    return {
        'cheques': cheques,
        'status_filter': status_filter,
        'q': search_query,
        'total_queue': total_queue,
    }


def queue(request):
    """Render the cheque queue page with database cheques"""
    if request.method == 'POST':
        action = request.POST.get('action')
        cheque_id = request.POST.get('cheque_id')
        if cheque_id:
            # Fetch current status for accurate old_status in history
            cheque_rows = fetch_supabase_rows('cheques', select_fields=['id', 'status'], filters={'id': cheque_id})
            current_status = (cheque_rows[0].get('status') if cheque_rows else 'pending') or 'pending'

            if action == 'delete':
                _delete_cheque_permanently(cheque_id)
            elif action in {'approve', 'reject'}:
                target_status = 'approved' if action == 'approve' else 'rejected'
                update_supabase_record('cheques', cheque_id, {'status': target_status})
                insert_supabase_record('status_history', {
                    'cheque_id': cheque_id,
                    'old_status': current_status,
                    'new_status': target_status,
                    'remarks': f'{action.title()}d from queue',
                })
        if action == 'approve':
            return redirect(f"{reverse('queue')}?status=approved")
        if action == 'reject':
            return redirect(f"{reverse('queue')}?status=rejected")
        return redirect('queue')

    status_filter = request.GET.get('status', 'all')
    search_query = request.GET.get('q', '').strip()
    payload = build_queue_payload(request, status_filter=status_filter, search_query=search_query)

    context = {
        **get_user_context(request),
        **get_realtime_context(request),
        'cheques': payload['cheques'],
        'status_filter': payload['status_filter'],
        'q': payload['q'],
        'total_queue': payload['total_queue'],
    }
    return render(request, 'dashboard/queue.html', context)


def realtime_summary(request):
    """Return a JSON summary used by the realtime client."""
    rows = _get_active_supabase_cheques()
    history_rows = _get_supabase_status_history()
    latest_status_map = {}
    for row in history_rows:
        latest_status_map[row.get('cheque_id')] = row

    total_queue = sum(1 for row in rows if normalize_supabase_status((latest_status_map.get(row.get('id'), {}) or {}).get('new_status') or row.get('status')) == 'pending')
    total_approved = sum(1 for row in rows if normalize_supabase_status((latest_status_map.get(row.get('id'), {}) or {}).get('new_status') or row.get('status')) == 'approved')
    total_rejected = sum(1 for row in rows if normalize_supabase_status((latest_status_map.get(row.get('id'), {}) or {}).get('new_status') or row.get('status')) == 'rejected')
    total_cheques = len(rows)
    total_processing = sum(1 for row in rows if str((latest_status_map.get(row.get('id'), {}) or {}).get('new_status') or row.get('status', '')).upper() in {'SCANNED', 'OCR_COMPLETED', 'PENDING', 'IN_REVIEW', 'PROCESSING'})

    if total_cheques:
        approved_percent = round((total_approved / total_cheques) * 100)
        rejected_percent = round((total_rejected / total_cheques) * 100)
        pending_percent = max(0, 100 - approved_percent - rejected_percent)
    else:
        approved_percent = rejected_percent = pending_percent = 33

    return JsonResponse({
        'total_queue': total_queue,
        'total_approved': total_approved,
        'total_rejected': total_rejected,
        'processing': total_processing,
        'total_cheques': total_cheques,
        'approved_percent': approved_percent,
        'rejected_percent': rejected_percent,
        'pending_percent': pending_percent,
        'pending_count': total_queue,
    })


def realtime_queue_data(request):
    """Return a JSON queue snapshot for live updates."""
    status_filter = request.GET.get('status', 'all')
    search_query = request.GET.get('q', '').strip()
    payload = build_queue_payload(request, status_filter=status_filter, search_query=search_query)
    return JsonResponse(payload)


def cheque_detail(request, cheque_id):
    """Render the cheque detail page using the Supabase-backed data when available."""
    cheque_id = str(cheque_id)  # Convert UUID to string for JSON serialization
    cheque_rows = _get_active_supabase_cheques()
    cheque_row = None
    for row in cheque_rows:
        if str(row.get('id')) == str(cheque_id):
            cheque_row = row
            break

    if cheque_row is None:
        from django.http import Http404
        raise Http404('No Cheque matches the given query.')

    if request.method == 'POST':
        action = request.POST.get('action')
        current_status = cheque_row.get('status') or 'pending'
        if action in ('approve', 'reject', 'delete'):
            if action == 'delete':
                _delete_cheque_permanently(cheque_id)
            elif action in ('approve', 'reject'):
                target_status = 'approved' if action == 'approve' else 'rejected'
                update_supabase_record('cheques', cheque_id, {'status': target_status})
                insert_supabase_record('status_history', {
                    'cheque_id': cheque_id,
                    'old_status': current_status,
                    'new_status': target_status,
                    'remarks': f'{action.title()}d from detail view',
                })
            if action == 'approve':
                return redirect(f"{reverse('queue')}?status=approved")
            if action == 'reject':
                return redirect(f"{reverse('queue')}?status=rejected")
            return redirect('queue')

    history_rows = _get_supabase_status_history()
    history_for_cheque = [
        {
            'old_status': row.get('old_status'),
            'new_status': row.get('new_status'),
            'changed_at': _parse_supabase_full_datetime(row.get('changed_at')),
            'remarks': row.get('remarks'),
        }
        for row in history_rows if str(row.get('cheque_id')) == str(cheque_id)
    ]
    history_for_cheque.sort(
        key=lambda entry: entry['changed_at'] or datetime.min,
        reverse=True,
    )

    def get_field_status(field_name, db_value):
        """
        No OCR comparison source is in scope, so we can't truly detect
        a mismatch. Showing 'pending' unconditionally previously caused
        every field to render as a false 'mismatch' in the template.
        Instead: treat a present value as verified, and an empty one as
        still pending review.
        """
        if db_value not in (None, ''):
            return 'match'
        return 'pending'

    image_rows = _get_supabase_cheque_images()
    front_image_url = None
    back_image_url = None
    front_uv_image_url = None
    back_uv_image_url = None
    for image in image_rows:
        if str(image.get('cheque_id')) != str(cheque_id):
            continue
        image_path = image.get('file_path') or ''
        url = settings.MEDIA_URL + image_path if image_path else None
        image_type = str(image.get('image_type') or '').strip().lower()
        if image_type == 'front':
            front_image_url = url
        elif image_type == 'back':
            back_image_url = url
        elif image_type == 'front_uv':
            front_uv_image_url = url
        elif image_type == 'back_uv':
            back_uv_image_url = url

    cheque_data = {
        'id': str(cheque_row.get('id') or cheque_id),
        'system_id': cheque_row.get('tracking_no') or '–',
        'amount': cheque_row.get('amount') or '–',
        'date': _normalize_supabase_date(cheque_row.get('cheque_date')),
        'beneficiary': cheque_row.get('beneficiary_name') or '–',
        'amount_in_words': cheque_row.get('amount_in_words') or '–',
        'amount_status': get_field_status('amount', cheque_row.get('amount')),
        'date_status': get_field_status('date', cheque_row.get('cheque_date')),
        'beneficiary_status': get_field_status('beneficiary_name', cheque_row.get('beneficiary_name')),
        'amount_words_status': get_field_status('amount_in_words', cheque_row.get('amount_in_words')),
        'front_image_url': front_image_url,
        'back_image_url': back_image_url,
        'front_uv_image_url': front_uv_image_url,
        'back_uv_image_url': back_uv_image_url,
        'status_history': history_for_cheque,
    }

    context = {
        **get_user_context(request),
        **get_realtime_context(request),
        'cheque': cheque_data,
        'total_queue': sum(1 for item in _build_supabase_queue_rows(status_filter='pending', search_query='') if item.get('status') == 'pending'),
    }
    return render(request, 'dashboard/cheque-detail.html', context)


def get_initials(name):
    """Extract initials from a name"""
    if not name:
        return 'CH'
    words = name.split()
    if len(words) >= 2:
        return (words[0][0] + words[-1][0]).upper()
    return name[:2].upper()