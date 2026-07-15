import uuid
from pathlib import Path

from django.shortcuts import render, get_object_or_404, redirect
from django.utils import timezone
from django.db.models import Q, Count, F, Avg, ExpressionWrapper, DurationField
from django.conf import settings
from .models import Cheque, OCRData, ProcessingQueue, ChequeImage, StatusHistory

def dashboard(request):
    """Render the main dashboard page with statistics"""
    total_queue = Cheque.objects.active().pending().count()
    total_approved = Cheque.objects.active().approved().count()
    total_rejected = Cheque.objects.active().rejected().count()
    total_cheques = Cheque.objects.active().count()
    total_processing = Cheque.objects.active().filter(status='processing').count()

    if total_cheques:
        approved_percent = round((total_approved / total_cheques) * 100)
        rejected_percent = round((total_rejected / total_cheques) * 100)
        pending_percent = max(0, 100 - approved_percent - rejected_percent)
    else:
        approved_percent = rejected_percent = pending_percent = 33

    context = {
        'total_queue': total_queue,
        'total_approved': total_approved,
        'total_rejected': total_rejected,
        'processing': total_processing,
        'total_cheques': total_cheques,
        'approved_percent': approved_percent,
        'rejected_percent': rejected_percent,
        'pending_percent': pending_percent,
    }
    return render(request, 'dashboard/dashboard.html', context)


def upload_cheque(request):
    """Upload a new cheque image and save it to the database."""
    selected_image_type = 'front'
    errors = []

    if request.method == 'POST':
        selected_image_type = request.POST.get('image_type', 'front')
        image_file = request.FILES.get('image_file')

        if not image_file:
            errors.append('Please select an image file to upload.')
        else:
            tracking_no = f"UPLOAD-{uuid.uuid4().hex[:10].upper()}"
            cheque = Cheque.objects.create(
                tracking_no=tracking_no,
                status='pending',
                match_status='pending',
            )

            media_root = Path(settings.MEDIA_ROOT)
            upload_dir = media_root / 'cheque_images'
            upload_dir.mkdir(parents=True, exist_ok=True)

            filename = f"{cheque.id.hex}_{selected_image_type}_{image_file.name}"
            file_path = upload_dir / filename
            with open(file_path, 'wb+') as dest:
                for chunk in image_file.chunks():
                    dest.write(chunk)

            ChequeImage.objects.create(
                cheque=cheque,
                image_type=selected_image_type,
                file_path=f"cheque_images/{filename}",
                file_size=image_file.size,
            )

            return redirect('queue')

    return render(request, 'dashboard/upload.html', {
        'selected_image_type': selected_image_type,
        'errors': errors,
    })


def queue(request):
    """Render the cheque queue page with database cheques"""
    if request.method == 'POST':
        action = request.POST.get('action')
        cheque_id = request.POST.get('cheque_id')
        if action == 'delete' and cheque_id:
            try:
                cheque_obj = Cheque.objects.get(id=cheque_id)
                cheque_obj.is_deleted = True
                cheque_obj.deleted_at = timezone.now()
                cheque_obj.save()
            except Cheque.DoesNotExist:
                pass
        return redirect('queue')

    status_filter = request.GET.get('status', 'all')
    search_query = request.GET.get('q', '').strip()
    
    # Get cheques from database
    cheques_qs = Cheque.objects.active().select_related('queue_item').prefetch_related('ocr_data', 'images')
    
    # Apply status filter
    if status_filter != 'all':
        cheques_qs = cheques_qs.filter(status=status_filter)

    # Apply search filter
    if search_query:
        cheques_qs = cheques_qs.filter(
            Q(tracking_no__icontains=search_query) |
            Q(beneficiary_name__icontains=search_query) |
            Q(cheque_no__icontains=search_query) |
            Q(account_no__icontains=search_query)
        )
    
    # Build cheque list with necessary data for template
    cheques = []
    for cheque in cheques_qs:
        # Get OCR data if available
        ocr_dict = {}
        for ocr in cheque.ocr_data.all():
            ocr_dict[ocr.field_name] = ocr.field_value
        
        cheque_data = {
            'id': str(cheque.id),
            'system_id': cheque.tracking_no,
            'amount': cheque.amount,
            'date': cheque.cheque_date.strftime('%m/%d/%Y') if cheque.cheque_date else '–',
            'beneficiary': cheque.beneficiary_name or '–',
            'match_status': cheque.match_status,
            'payee': cheque.beneficiary_name,
            'submitted_by': cheque.created_at.strftime('%b %d, %Y'),
            'avatar': get_initials(cheque.beneficiary_name) if cheque.beneficiary_name else 'CH',
            'status': cheque.status,
        }
        cheques.append(cheque_data)
    
    total_queue = Cheque.objects.active().pending().count()
    context = {
        'cheques': cheques,
        'status_filter': status_filter,
        'q': search_query,
        'total_queue': total_queue,
    }
    return render(request, 'dashboard/queue.html', context)

def cheque_detail(request, cheque_id):
    """Render the cheque detail page with OCR data from database"""
    # Get cheque from database
    try:
        cheque_obj = Cheque.objects.prefetch_related('ocr_data', 'images', 'status_history').get(id=cheque_id)
    except Cheque.DoesNotExist:
        # For development - return first cheque as fallback
        cheque_obj = Cheque.objects.prefetch_related('ocr_data', 'images', 'status_history').first()
    
    if request.method == 'POST' and cheque_obj:
        action = request.POST.get('action')
        if action in ('approve', 'reject', 'delete'):
            if action == 'delete':
                cheque_obj.is_deleted = True
                cheque_obj.deleted_at = timezone.now()
                new_status = 'deleted'
            else:
                old_status = cheque_obj.status
                cheque_obj.status = 'approved' if action == 'approve' else 'rejected'
                cheque_obj.match_status = 'match' if action == 'approve' else 'mismatch'
                new_status = cheque_obj.status
            cheque_obj.save()

            # Log status changes for approved/rejected
            if action in ('approve', 'reject'):
                StatusHistory.objects.create(
                    cheque=cheque_obj,
                    old_status=old_status,
                    new_status=new_status,
                )

            if action == 'delete':
                return redirect('queue')
            return redirect(f"{request.path}?status={new_status}")

    if not cheque_obj:
        # Fallback to sample data if no cheques in DB
        context = {
            'cheque': {
                'id': 'sample',
                'system_id': 'CHQ-10482',
                'amount': 1268.69,
                'date': '6/9/2026',
                'beneficiary': 'JANIE GOULD',
                'amount_in_words': 'THOUSAND NINE HUNDRED FIFTY AND 00/100',
                'amount_status': 'mismatch',
                'date_status': 'match',
                'beneficiary_status': 'mismatch',
                'amount_words_status': 'mismatch',
            },
            'total_queue': Cheque.objects.active().pending().count(),
        }
        return render(request, 'dashboard/cheque-detail.html', context)
    
    # Build OCR data dictionary for matching
    ocr_dict = {}
    for ocr in cheque_obj.ocr_data.all():
        ocr_dict[ocr.field_name] = {
            'value': ocr.field_value,
            'confidence': float(ocr.confidence_score)
        }
    
    # Determine field match statuses based on OCR confidence or actual matches
    def get_field_status(field_name, db_value):
        if field_name in ocr_dict:
            confidence = ocr_dict[field_name]['confidence']
            ocr_value = ocr_dict[field_name]['value']
            
            # Match if OCR value equals DB value and confidence > 80
            if str(ocr_value).strip() == str(db_value).strip() and confidence > 80:
                return 'match'
            return 'mismatch'
        return 'pending'
    
    front_image_url = None
    back_image_url = None
    front_uv_image_url = None
    back_uv_image_url = None
    for image in cheque_obj.images.all():
        url = settings.MEDIA_URL + image.file_path
        if image.image_type == 'front':
            front_image_url = url
        elif image.image_type == 'back':
            back_image_url = url
        elif image.image_type == 'front_uv':
            front_uv_image_url = url
        elif image.image_type == 'back_uv':
            back_uv_image_url = url

    cheque_data = {
        'id': str(cheque_obj.id),
        'system_id': cheque_obj.tracking_no,
        'amount': cheque_obj.amount,
        'date': cheque_obj.cheque_date.strftime('%m/%d/%Y') if cheque_obj.cheque_date else '–',
        'beneficiary': cheque_obj.beneficiary_name or '–',
        'amount_in_words': cheque_obj.amount_in_words or '–',
        
        # Status indicators for each field
        'amount_status': get_field_status('amount', cheque_obj.amount),
        'date_status': get_field_status('date', cheque_obj.cheque_date),
        'beneficiary_status': get_field_status('beneficiary_name', cheque_obj.beneficiary_name),
        'amount_words_status': get_field_status('amount_in_words', cheque_obj.amount_in_words),
        
        # Images
        'front_image_url': front_image_url,
        'back_image_url': back_image_url,
        'front_uv_image_url': front_uv_image_url,
        'back_uv_image_url': back_uv_image_url,
        
        # Status history
        'status_history': cheque_obj.status_history.all().values('old_status', 'new_status', 'changed_at', 'remarks'),
    }
    
    context = {
        'cheque': cheque_data,
        'total_queue': Cheque.objects.active().pending().count(),
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
