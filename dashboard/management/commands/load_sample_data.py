from django.core.management.base import BaseCommand
from django.utils import timezone
from decimal import Decimal
from datetime import date, timedelta
from dashboard.models import Cheque, OCRData, ChequeImage, ProcessingQueue, StatusHistory
from django.contrib.auth.models import User


class Command(BaseCommand):
    help = 'Load sample cheque data for testing'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('Loading sample data...'))
        
        # Create sample cheques
        cheques_data = [
            {
                'tracking_no': 'CHQ-10482',
                'cheque_no': '10482',
                'account_no': '1234567890',
                'bank_code': 'HBLC',
                'branch_code': '001',
                'amount': Decimal('1268.69'),
                'amount_in_words': 'ONE THOUSAND TWO HUNDRED SIXTY-EIGHT AND 69/100',
                'beneficiary_name': 'JANIE GOULD',
                'cheque_date': date(2026, 6, 9),
                'status': 'pending',
                'match_status': 'mismatch',
                'ocr_data': [
                    {'field_name': 'amount', 'field_value': '1268.69', 'confidence': 85.5},
                    {'field_name': 'date', 'field_value': '6/9/2026', 'confidence': 92.3},
                    {'field_name': 'beneficiary_name', 'field_value': 'JANIE GOULD', 'confidence': 78.2},
                    {'field_name': 'amount_in_words', 'field_value': 'THOUSAND NINE HUNDRED FIFTY AND 00/100', 'confidence': 65.8},
                ]
            },
            {
                'tracking_no': 'CHQ-10481',
                'cheque_no': '10481',
                'account_no': '0987654321',
                'bank_code': 'NIB',
                'branch_code': '002',
                'amount': Decimal('3950.00'),
                'amount_in_words': 'THREE THOUSAND NINE HUNDRED FIFTY AND 00/100',
                'beneficiary_name': 'AL-HABIB TRADERS',
                'cheque_date': date(2026, 6, 9),
                'status': 'approved',
                'match_status': 'match',
                'ocr_data': [
                    {'field_name': 'amount', 'field_value': '3950.00', 'confidence': 95.8},
                    {'field_name': 'date', 'field_value': '6/9/2026', 'confidence': 98.2},
                    {'field_name': 'beneficiary_name', 'field_value': 'AL-HABIB TRADERS', 'confidence': 93.5},
                    {'field_name': 'amount_in_words', 'field_value': 'THREE THOUSAND NINE HUNDRED FIFTY AND 00/100', 'confidence': 91.3},
                ]
            },
            {
                'tracking_no': 'CHQ-10480',
                'cheque_no': '10480',
                'account_no': '5555666677',
                'bank_code': 'ABL',
                'branch_code': '003',
                'amount': Decimal('5000.00'),
                'amount_in_words': 'FIVE THOUSAND AND 00/100',
                'beneficiary_name': 'BAY VIEW CONSTRUCTION',
                'cheque_date': date(2026, 6, 8),
                'status': 'rejected',
                'match_status': 'mismatch',
                'ocr_data': [
                    {'field_name': 'amount', 'field_value': '4000.00', 'confidence': 45.2},
                    {'field_name': 'date', 'field_value': '6/8/2026', 'confidence': 88.9},
                    {'field_name': 'beneficiary_name', 'field_value': 'BAY VIEW CONST', 'confidence': 72.1},
                ]
            },
            {
                'tracking_no': 'CHQ-10479',
                'cheque_no': '10479',
                'account_no': '1111222233',
                'bank_code': 'UBL',
                'branch_code': '004',
                'amount': Decimal('3000.00'),
                'amount_in_words': 'THREE THOUSAND AND 00/100',
                'beneficiary_name': 'AHSAN KHAN',
                'cheque_date': date(2025, 11, 4),
                'status': 'approved',
                'match_status': 'match',
                'ocr_data': [
                    {'field_name': 'amount', 'field_value': '3000.00', 'confidence': 94.5},
                    {'field_name': 'date', 'field_value': '11/4/2025', 'confidence': 97.1},
                    {'field_name': 'beneficiary_name', 'field_value': 'AHSAN KHAN', 'confidence': 91.8},
                ]
            },
            {
                'tracking_no': 'CHQ-10478',
                'cheque_no': '10478',
                'account_no': '9999888877',
                'bank_code': 'MCB',
                'branch_code': '005',
                'amount': Decimal('7500.50'),
                'amount_in_words': 'SEVEN THOUSAND FIVE HUNDRED AND 50/100',
                'beneficiary_name': 'NORTHLINE LOGISTICS',
                'cheque_date': date(2026, 6, 10),
                'status': 'rejected',
                'match_status': 'mismatch',
                'ocr_data': [
                    {'field_name': 'amount', 'field_value': '7500.50', 'confidence': 89.3},
                    {'field_name': 'date', 'field_value': '6/10/2026', 'confidence': 85.6},
                    {'field_name': 'beneficiary_name', 'field_value': 'NORTHLINE LOG', 'confidence': 68.4},
                ]
            },
        ]
        
        created_count = 0
        
        for cheque_data in cheques_data:
            ocr_items = cheque_data.pop('ocr_data', [])
            
            # Check if cheque already exists
            if Cheque.objects.filter(tracking_no=cheque_data['tracking_no']).exists():
                self.stdout.write(self.style.WARNING(f"Skipping: Cheque {cheque_data['tracking_no']} already exists, skipping..."))
                continue
            
            # Create cheque
            cheque = Cheque.objects.create(**cheque_data)
            created_count += 1
            
            # Create OCR data
            for ocr in ocr_items:
                OCRData.objects.create(
                    cheque=cheque,
                    field_name=ocr['field_name'],
                    field_value=ocr['field_value'],
                    confidence_score=Decimal(str(ocr['confidence']))
                )
            
            # Create processing queue item
            ProcessingQueue.objects.create(
                cheque=cheque,
                priority=50 - created_count * 10,  # Decreasing priority
                queue_status='pending' if cheque.status == 'pending' else 'completed',
                completed_at=timezone.now() if cheque.status != 'pending' else None,
            )
            
            # Create status history
            if cheque.status != 'pending':
                StatusHistory.objects.create(
                    cheque=cheque,
                    old_status='pending',
                    new_status=cheque.status,
                    remarks=f"Marked as {cheque.status} during sample data load"
                )
            
            self.stdout.write(self.style.SUCCESS(f"Created cheque: {cheque.tracking_no} ({cheque.beneficiary_name})"))
        
        # Summary
        self.stdout.write(self.style.SUCCESS(f'\nSuccessfully loaded {created_count} sample cheques!'))
        self.stdout.write(self.style.SUCCESS('You can now access them at: http://127.0.0.1:8000/dashboard/queue/'))
