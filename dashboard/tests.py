from unittest.mock import patch

from django.test import TestCase
from django.urls import reverse

from dashboard.supabase_client import fetch_supabase_rows, normalize_supabase_status
from dashboard.views import build_queue_payload


class RealtimeApiTests(TestCase):
    def test_realtime_summary_endpoint_returns_payload(self):
        response = self.client.get(reverse('realtime_summary'))

        self.assertEqual(response.status_code, 200)
        self.assertTrue(response['Content-Type'].startswith('application/json'))

        payload = response.json()
        self.assertIn('total_queue', payload)
        self.assertIn('total_approved', payload)
        self.assertIn('total_rejected', payload)


class SupabaseClientTests(TestCase):
    @patch('dashboard.views.fetch_supabase_rows')
    def test_cheque_detail_view_uses_supabase_rows(self, mock_fetch):
        cheque_id = '2a96cef1-3763-42bb-9136-6157a774d848'
        mock_fetch.side_effect = [
            [{
                'id': cheque_id,
                'tracking_no': 'TRK-999',
                'amount': '100.00',
                'cheque_date': '2026-07-16',
                'beneficiary_name': 'Jane Doe',
                'amount_in_words': 'One hundred',
                'status': 'SCANNED',
                'created_at': '2026-07-16T00:00:00Z',
            }],
            [],
            [{
                'id': 'hist-1',
                'cheque_id': cheque_id,
                'old_status': 'SCANNED',
                'new_status': 'PENDING',
                'remarks': 'Queued',
                'changed_at': '2026-07-16T00:00:00Z',
            }],
            [{
                'id': cheque_id,
                'tracking_no': 'TRK-999',
                'amount': '100.00',
                'cheque_date': '2026-07-16',
                'beneficiary_name': 'Jane Doe',
                'amount_in_words': 'One hundred',
                'status': 'SCANNED',
                'created_at': '2026-07-16T00:00:00Z',
            }],
            [{
                'id': 'hist-1',
                'cheque_id': cheque_id,
                'old_status': 'SCANNED',
                'new_status': 'PENDING',
                'remarks': 'Queued',
                'changed_at': '2026-07-16T00:00:00Z',
            }],
            [],
        ]

        response = self.client.get(reverse('cheque_detail', kwargs={'cheque_id': cheque_id}))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'TRK-999')

    def test_normalize_supabase_status_maps_to_dashboard_statuses(self):
        self.assertEqual(normalize_supabase_status('PENDING'), 'pending')
        self.assertEqual(normalize_supabase_status('ACCEPTED'), 'approved')
        self.assertEqual(normalize_supabase_status('REJECTED'), 'rejected')
        self.assertEqual(normalize_supabase_status('approved'), 'approved')
        self.assertEqual(normalize_supabase_status('rejected'), 'rejected')
        self.assertEqual(normalize_supabase_status('processing'), 'pending')

    @patch('dashboard.supabase_client.urlopen')
    def test_fetch_supabase_rows_returns_json_payload(self, mock_urlopen):
        class DummyResponse:
            def __enter__(self):
                return self

            def __exit__(self, exc_type, exc, tb):
                return False

            def read(self):
                return b'[{"id": "123"}]'

        mock_urlopen.return_value = DummyResponse()
        rows = fetch_supabase_rows('cheques', ['id'])

        self.assertEqual(rows, [{'id': '123'}])

    @patch('dashboard.views.fetch_supabase_rows')
    def test_build_queue_payload_uses_supabase_status_history(self, mock_fetch):
        mock_fetch.side_effect = [
            [{
                'id': 'cheque-1',
                'tracking_no': 'TRK-100',
                'amount': '100.00',
                'cheque_date': '2024-01-01',
                'beneficiary_name': 'Ava',
                'status': 'SCANNED',
                'created_at': '2024-01-01T00:00:00Z',
            }],
            [{
                'id': 'history-1',
                'cheque_id': 'cheque-1',
                'old_status': 'SCANNED',
                'new_status': 'PENDING',
                'remarks': 'Waiting review',
                'changed_at': '2024-01-02T00:00:00Z',
            }],
            [],
        ]

        payload = build_queue_payload(None, status_filter='all', search_query='')

        self.assertEqual(payload['total_queue'], 1)
        self.assertEqual(len(payload['cheques']), 1)
        self.assertEqual(payload['cheques'][0]['status'], 'pending')
        self.assertEqual(payload['cheques'][0]['system_id'], 'TRK-100')
