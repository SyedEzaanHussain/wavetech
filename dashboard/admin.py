from django.contrib import admin
from django.utils.html import format_html
from .models import Cheque, ChequeImage, OCRData, ProcessingQueue, StatusHistory, AuditLog


@admin.register(Cheque)
class ChequeAdmin(admin.ModelAdmin):
    list_display = ('tracking_no', 'beneficiary_name', 'amount', 'status_badge', 'match_status_badge', 'cheque_date', 'created_at')
    list_filter = ('status', 'match_status', 'created_at', 'is_deleted')
    search_fields = ('tracking_no', 'beneficiary_name', 'cheque_no', 'account_no')
    readonly_fields = ('id', 'created_at', 'updated_at', 'version')
    
    fieldsets = (
        ('Identifiers', {
            'fields': ('id', 'tracking_no', 'cheque_no', 'account_no', 'bank_code', 'branch_code'),
        }),
        ('Financial Information', {
            'fields': ('amount', 'amount_in_words'),
        }),
        ('Cheque Details', {
            'fields': ('beneficiary_name', 'cheque_date'),
        }),
        ('Status', {
            'fields': ('status', 'match_status'),
        }),
        ('Audit', {
            'fields': ('version', 'created_at', 'updated_at'),
        }),
        ('Deletion', {
            'fields': ('is_deleted', 'deleted_at'),
            'classes': ('collapse',),
        }),
    )
    
    ordering = ('-created_at',)
    
    def status_badge(self, obj):
        colors = {
            'pending': '#FFC107',
            'approved': '#28A745',
            'rejected': '#DC3545',
            'processing': '#0DC3FF',
        }
        color = colors.get(obj.status, '#6C757D')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 5px 10px; border-radius: 5px;">{}</span>',
            color,
            obj.get_status_display()
        )
    status_badge.short_description = 'Status'
    
    def match_status_badge(self, obj):
        colors = {
            'match': '#28A745',
            'mismatch': '#FFC107',
            'pending': '#0DC3FF',
        }
        color = colors.get(obj.match_status, '#6C757D')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 5px 10px; border-radius: 5px;">{}</span>',
            color,
            obj.get_match_status_display()
        )
    match_status_badge.short_description = 'Match Status'


@admin.register(ChequeImage)
class ChequeImageAdmin(admin.ModelAdmin):
    list_display = ('cheque', 'image_type', 'file_size_display', 'created_at')
    list_filter = ('image_type', 'created_at')
    search_fields = ('cheque__tracking_no', 'file_path')
    readonly_fields = ('id', 'created_at')
    
    fieldsets = (
        ('Cheque', {
            'fields': ('cheque',),
        }),
        ('Image Details', {
            'fields': ('id', 'image_type', 'file_path', 'file_size'),
        }),
        ('Metadata', {
            'fields': ('created_at',),
        }),
    )
    
    def file_size_display(self, obj):
        size_kb = obj.file_size / 1024
        return f"{size_kb:.2f} KB"
    file_size_display.short_description = 'File Size'


@admin.register(OCRData)
class OCRDataAdmin(admin.ModelAdmin):
    list_display = ('cheque', 'field_name', 'confidence_display', 'field_value_short', 'created_at')
    list_filter = ('field_name', 'created_at')
    search_fields = ('cheque__tracking_no', 'field_value')
    readonly_fields = ('id', 'created_at')
    
    fieldsets = (
        ('Cheque', {
            'fields': ('cheque',),
        }),
        ('OCR Field Data', {
            'fields': ('id', 'field_name', 'field_value', 'confidence_score'),
        }),
        ('Metadata', {
            'fields': ('created_at',),
        }),
    )
    
    ordering = ('-created_at',)
    
    def confidence_display(self, obj):
        percentage = float(obj.confidence_score)
        if percentage >= 80:
            color = '#28A745'  # Green
        elif percentage >= 60:
            color = '#FFC107'  # Yellow
        else:
            color = '#DC3545'  # Red
        
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 8px; border-radius: 3px;">{:.1f}%</span>',
            color,
            percentage
        )
    confidence_display.short_description = 'Confidence'
    
    def field_value_short(self, obj):
        return obj.field_value[:50] + '...' if len(obj.field_value) > 50 else obj.field_value
    field_value_short.short_description = 'Value'


@admin.register(ProcessingQueue)
class ProcessingQueueAdmin(admin.ModelAdmin):
    list_display = ('cheque', 'priority', 'queue_status_badge', 'assigned_to', 'created_at')
    list_filter = ('queue_status', 'priority', 'created_at')
    search_fields = ('cheque__tracking_no', 'assigned_to__username')
    readonly_fields = ('id', 'created_at', 'picked_at', 'completed_at')
    
    fieldsets = (
        ('Cheque', {
            'fields': ('cheque',),
        }),
        ('Queue Status', {
            'fields': ('queue_status', 'priority'),
        }),
        ('Assignment', {
            'fields': ('assigned_to',),
        }),
        ('Timestamps', {
            'fields': ('created_at', 'picked_at', 'completed_at'),
        }),
    )
    
    ordering = ('-priority', 'created_at')
    
    def queue_status_badge(self, obj):
        colors = {
            'pending': '#0DC3FF',
            'picked': '#FFC107',
            'completed': '#28A745',
            'failed': '#DC3545',
        }
        color = colors.get(obj.queue_status, '#6C757D')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 5px 10px; border-radius: 5px;">{}</span>',
            color,
            obj.get_queue_status_display()
        )
    queue_status_badge.short_description = 'Status'


@admin.register(StatusHistory)
class StatusHistoryAdmin(admin.ModelAdmin):
    list_display = ('cheque', 'old_status_display', 'arrow', 'new_status_display', 'changed_by', 'changed_at')
    list_filter = ('new_status', 'changed_at')
    search_fields = ('cheque__tracking_no', 'changed_by__username')
    readonly_fields = ('id', 'changed_at')
    
    fieldsets = (
        ('Cheque', {
            'fields': ('cheque',),
        }),
        ('Status Change', {
            'fields': ('old_status', 'new_status'),
        }),
        ('Details', {
            'fields': ('changed_by', 'remarks'),
        }),
        ('Metadata', {
            'fields': ('id', 'changed_at'),
        }),
    )
    
    ordering = ('-changed_at',)
    
    def old_status_display(self, obj):
        if not obj.old_status:
            return '—'
        return obj.get_old_status_display()
    old_status_display.short_description = 'From'
    
    def arrow(self, obj):
        return format_html('→')
    arrow.short_description = ''
    
    def new_status_display(self, obj):
        return obj.get_new_status_display()
    new_status_display.short_description = 'To'


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = ('table_name', 'action_badge', 'performed_by', 'created_at')
    list_filter = ('table_name', 'action', 'created_at')
    search_fields = ('table_name', 'performed_by__username')
    readonly_fields = ('id', 'created_at', 'old_value', 'new_value', 'record_id')
    
    fieldsets = (
        ('Record', {
            'fields': ('id', 'table_name', 'record_id'),
        }),
        ('Action', {
            'fields': ('action', 'performed_by'),
        }),
        ('Changes', {
            'fields': ('old_value', 'new_value'),
        }),
        ('Metadata', {
            'fields': ('created_at',),
        }),
    )
    
    ordering = ('-created_at',)
    
    def action_badge(self, obj):
        colors = {
            'create': '#0DC3FF',
            'update': '#FFC107',
            'delete': '#DC3545',
            'approve': '#28A745',
            'reject': '#FF5733',
        }
        color = colors.get(obj.action, '#6C757D')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 5px 10px; border-radius: 5px;">{}</span>',
            color,
            obj.get_action_display()
        )
    action_badge.short_description = 'Action'
