from django.db import models
from django.contrib.auth.models import AbstractUser
from django.core.validators import RegexValidator
import uuid


class User(AbstractUser):
    ROLE_CHOICES = [
        ('client', 'Client'),
        ('lawyer', 'Lawyer'),
    ]

    cnic = models.CharField(
        max_length=15,
        unique=True,
        validators=[
            RegexValidator(
                regex=r'^\d{5}-\d{7}-\d$',
                message='CNIC must be in format: 00000-0000000-0'
            )
        ]
    )

    contact_number = models.CharField(
        max_length=15,
        validators=[
            RegexValidator(
                regex=r'^03\d{9}$',
                message='Contact number must be in format: 03XXXXXXXXX'
            )
        ]
    )

    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default='client')
    is_verified = models.BooleanField(default=False)

    email_verified = models.BooleanField(default=False)
    email_verification_token = models.UUIDField(default=uuid.uuid4, unique=True)

    reset_password_token = models.UUIDField(blank=True, null=True)
    reset_password_expires = models.DateTimeField(blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.username


# ===============================
# ⚖️ LAWYER PROFILE
# ===============================
class LawyerProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='lawyer_profile')
    # user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='lawyer_profile')
    license_number = models.CharField(max_length=50, unique=True)
    location = models.CharField(max_length=100)
    years_experience = models.IntegerField()
    languages = models.CharField(max_length=200)
    case_specialty = models.TextField()
    is_approved = models.BooleanField(default=False)
    online_availability = models.BooleanField(default=True)

    def __str__(self):
        return self.user.username


# ===============================
# 💬 CHAT MEMORY (NEW)
# ===============================
class ChatSession(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)


class ChatMessage(models.Model):
    session = models.ForeignKey(ChatSession, on_delete=models.CASCADE, related_name='messages')
    role = models.CharField(max_length=10)  # user / assistant
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)


# ===============================
# 📁 OLD QUERY STORAGE (KEEP)
# ===============================
class CaseQuery(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    query_text = models.TextField()
    fir_extracted_text = models.TextField(blank=True, null=True)
    fir_image_path = models.CharField(max_length=500, blank=True, null=True)  # ← Add this field
    ai_response = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    
    def delete(self, *args, **kwargs):
        """Delete FIR image when query is deleted"""
        if self.fir_image_path:
            from pathlib import Path
            try:
                image_path = Path(self.fir_image_path)
                if image_path.exists():
                    image_path.unlink()
            except Exception:
                pass
        super().delete(*args, **kwargs)