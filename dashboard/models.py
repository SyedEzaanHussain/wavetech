import uuid
from django.db import models
from django.contrib.auth.models import User
from django.contrib.postgres.fields import ArrayField
from django.core.validators import MinValueValidator, MaxValueValidator


class ChequeQuerySet(models.QuerySet):
    """Custom QuerySet for Cheque model"""
    def active(self):
        return self.filter(is_deleted=False)
    
    def pending(self):
        return self.filter(status='pending')
    
    def approved(self):
        return self.filter(status='approved')
    
    def rejected(self):
        return self.filter(status='rejected')


class ChequeManager(models.Manager):
    """Custom Manager for Cheque model"""
    def get_queryset(self):
        return ChequeQuerySet(self.model, using=self._db)
    
    def active(self):
        return self.get_queryset().active()
    
    def pending(self):
        return self.get_queryset().pending()
    
    def approved(self):
        return self.get_queryset().approved()
    
    def rejected(self):
        return self.get_queryset().rejected()


class Cheque(models.Model):
    """Main Cheque model - represents a single cheque document"""
    
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('processing', 'Processing'),
    ]
    
    MATCH_STATUS_CHOICES = [
        ('match', 'Match'),
        ('mismatch', 'Mismatch'),
        ('pending', 'Pending'),
    ]
    
    # Primary key
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    # Identifiers
    tracking_no = models.CharField(max_length=100, unique=True, db_index=True)
    cheque_no = models.CharField(max_length=50, blank=True, null=True)
    account_no = models.CharField(max_length=50, blank=True, null=True)
    bank_code = models.CharField(max_length=20, blank=True, null=True)
    branch_code = models.CharField(max_length=20, blank=True, null=True)
    
    # Financial Details
    amount = models.DecimalField(max_digits=15, decimal_places=2, blank=True, null=True, validators=[MinValueValidator(0)])
    amount_in_words = models.TextField(blank=True, null=True)
    
    # Cheque Information
    beneficiary_name = models.CharField(max_length=255, blank=True, null=True)
    cheque_date = models.DateField(blank=True, null=True)
    
    # Status tracking
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending', db_index=True)
    match_status = models.CharField(max_length=20, choices=MATCH_STATUS_CHOICES, default='pending', db_index=True)
    
    # Soft delete
    is_deleted = models.BooleanField(default=False)
    deleted_at = models.DateTimeField(null=True, blank=True)
    
    # Version control
    version = models.IntegerField(default=1)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    # Manager
    objects = ChequeManager()
    
    class Meta:
        ordering = ['-created_at']
        db_table = 'cheques'
        indexes = [
            models.Index(fields=['tracking_no']),
            models.Index(fields=['status']),
            models.Index(fields=['created_at']),
            models.Index(fields=['match_status']),
        ]
    
    def __str__(self):
        return f"CHQ-{self.tracking_no} ({self.beneficiary_name})"


class ChequeImage(models.Model):
    """Stores cheque images (front, back, UV, etc.)"""
    
    IMAGE_TYPE_CHOICES = [
        ('front', 'Front'),
        ('back', 'Back'),
        ('front_uv', 'Front UV'),
        ('back_uv', 'Back UV'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    cheque = models.ForeignKey(Cheque, on_delete=models.CASCADE, related_name='images')
    
    image_type = models.CharField(max_length=20, choices=IMAGE_TYPE_CHOICES)
    file_path = models.TextField()
    file_size = models.IntegerField(validators=[MinValueValidator(0)])
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'cheque_images'
        unique_together = ('cheque', 'image_type')
        indexes = [
            models.Index(fields=['cheque', 'image_type']),
        ]
    
    def __str__(self):
        return f"{self.cheque.tracking_no} - {self.get_image_type_display()}"


class OCRData(models.Model):
    """Stores OCR extracted data from cheques"""
    
    FIELD_TYPES = [
        ('amount', 'Amount'),
        ('date', 'Date'),
        ('beneficiary_name', 'Beneficiary Name'),
        ('account_number', 'Account Number'),
        ('cheque_number', 'Cheque Number'),
        ('bank_code', 'Bank Code'),
        ('branch_code', 'Branch Code'),
        ('amount_in_words', 'Amount In Words'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    cheque = models.ForeignKey(Cheque, on_delete=models.CASCADE, related_name='ocr_data')
    
    field_name = models.CharField(max_length=100, choices=FIELD_TYPES)
    field_value = models.TextField()
    confidence_score = models.DecimalField(max_digits=5, decimal_places=2, validators=[MinValueValidator(0), MaxValueValidator(100)])
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'ocr_data'
        unique_together = ('cheque', 'field_name')
        ordering = ['field_name']
        indexes = [
            models.Index(fields=['cheque', 'field_name']),
        ]
    
    def __str__(self):
        return f"{self.cheque.tracking_no} - {self.get_field_name_display()}"


class ProcessingQueue(models.Model):
    """Tracks cheques in the processing queue"""
    
    QUEUE_STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('picked', 'Picked'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    cheque = models.OneToOneField(Cheque, on_delete=models.CASCADE, related_name='queue_item')
    
    priority = models.SmallIntegerField(default=0, validators=[MinValueValidator(0), MaxValueValidator(100)])
    assigned_to = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='assigned_queues')
    
    queue_status = models.CharField(max_length=20, choices=QUEUE_STATUS_CHOICES, default='pending', db_index=True)
    
    picked_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'processing_queue'
        ordering = ['-priority', 'created_at']
        indexes = [
            models.Index(fields=['queue_status', 'priority']),
            models.Index(fields=['assigned_to']),
        ]
    
    def __str__(self):
        return f"Queue: {self.cheque.tracking_no} - {self.get_queue_status_display()}"


class StatusHistory(models.Model):
    """Tracks status changes and audit trail for cheques"""
    
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('processing', 'Processing'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    cheque = models.ForeignKey(Cheque, on_delete=models.CASCADE, related_name='status_history')
    
    old_status = models.CharField(max_length=20, choices=STATUS_CHOICES, null=True, blank=True)
    new_status = models.CharField(max_length=20, choices=STATUS_CHOICES)
    
    changed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='status_changes')
    remarks = models.TextField(blank=True, null=True)
    
    changed_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'status_history'
        ordering = ['-changed_at']
        indexes = [
            models.Index(fields=['cheque', '-changed_at']),
        ]
    
    def __str__(self):
        return f"{self.cheque.tracking_no}: {self.old_status} → {self.new_status}"


class AuditLog(models.Model):
    """Comprehensive audit logging for all changes"""
    
    ACTION_CHOICES = [
        ('create', 'Create'),
        ('update', 'Update'),
        ('delete', 'Delete'),
        ('approve', 'Approve'),
        ('reject', 'Reject'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    table_name = models.CharField(max_length=100, db_index=True)
    record_id = models.UUIDField(db_index=True)
    
    action = models.CharField(max_length=20, choices=ACTION_CHOICES)
    performed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='audit_logs')
    
    old_value = models.JSONField(null=True, blank=True)
    new_value = models.JSONField(null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'audit_log'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['table_name', 'record_id']),
            models.Index(fields=['performed_by', '-created_at']),
        ]
    
    def __str__(self):
        return f"{self.table_name}: {self.action.upper()} by {self.performed_by}"
