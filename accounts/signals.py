# """Signals to auto-refresh lawyer loader when profiles are approved or deleted"""
# from django.db.models.signals import post_save, post_delete
# from django.dispatch import receiver
# from .models import LawyerProfile
# from ai_engine.lawyer_loader import refresh_lawyer_loader

# @receiver(post_save, sender=LawyerProfile)
# def refresh_lawyer_loader_on_approval(sender, instance, created, **kwargs):
#     """Refresh lawyer list when a lawyer profile is approved"""
#     if instance.is_approved:
#         refresh_lawyer_loader()
#         print(f"✅ Lawyer loader refreshed - {instance.user.username} is now available for recommendations")

# @receiver(post_delete, sender=LawyerProfile)
# def refresh_lawyer_loader_on_delete(sender, instance, **kwargs):
#     """Refresh lawyer list when a lawyer profile is deleted"""
#     refresh_lawyer_loader()
#     print(f"🗑️ Lawyer profile deleted - {instance.user.username} removed from recommendations")

# """Signals to handle Lawyer Profile Delete + Refresh Recommendations"""
# from django.db.models.signals import post_save, post_delete
# from django.dispatch import receiver
# from .models import LawyerProfile, User
# from ai_engine.lawyer_loader import refresh_lawyer_loader

# # ==================== LAWYER PROFILE DELETE ====================
# @receiver(post_delete, sender=LawyerProfile)
# def handle_lawyer_profile_delete(sender, instance, **kwargs):
#     """Lawyer profile delete hone par uska User account bhi delete ho jaye"""
#     if instance.user:
#         try:
#             username = instance.user.username
#             instance.user.delete()          # This will delete User + all related data
#             print(f"🗑️ Lawyer profile + User account deleted: {username}")
#         except Exception as e:
#             print(f"❌ Error deleting user: {e}")

#     # Refresh lawyer list in recommendations
#     refresh_lawyer_loader()
#     print(f"✅ Recommendations updated - {instance.user.username if instance.user else 'Unknown'} removed")


# # ==================== LAWYER APPROVAL ====================
# @receiver(post_save, sender=LawyerProfile)
# def refresh_lawyer_loader_on_approval(sender, instance, created, **kwargs):
#     """Refresh lawyer list when a lawyer is approved by admin"""
#     if instance.is_approved:
#         refresh_lawyer_loader()
#         print(f"✅ Lawyer loader refreshed - {instance.user.username} is now approved")





"""Signals for Lawyer Profile + FIR Auto-Cleanup"""
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.conf import settings
from pathlib import Path
import time
from .models import LawyerProfile, CaseQuery
from ai_engine.lawyer_loader import refresh_lawyer_loader


# ==================== FIR IMAGE AUTO-DELETE ====================
@receiver(post_delete, sender=CaseQuery)
def auto_delete_fir_images(sender, instance, **kwargs):
    """Automatically delete FIR image when CaseQuery is deleted"""
    if hasattr(instance, 'fir_image_path') and instance.fir_image_path:
        try:
            image_path = Path(instance.fir_image_path)
            if image_path.exists():
                image_path.unlink()
                print(f"🗑️ FIR image auto-deleted: {image_path.name}")
        except Exception as e:
            print(f"⚠️ FIR cleanup error: {e}")


# ==================== OLD FIR IMAGES CLEANUP (HOURLY) ====================
def cleanup_old_fir_images():
    """Delete all FIR images older than 1 hour"""
    fir_dir = settings.MEDIA_ROOT / 'fir_images'
    if not fir_dir.exists():
        return
    
    cutoff = time.time() - 3600  # 1 hour old
    deleted = 0
    
    for filepath in fir_dir.iterdir():
        if filepath.is_file():
            try:
                if filepath.stat().st_mtime < cutoff:
                    filepath.unlink()
                    deleted += 1
            except Exception:
                pass
    
    if deleted > 0:
        print(f"🧹 Auto-cleaned {deleted} old FIR images")


# ==================== LAWYER PROFILE DELETE ====================
@receiver(post_delete, sender=LawyerProfile)
def handle_lawyer_profile_delete(sender, instance, **kwargs):
    """Lawyer profile delete hone par User account bhi delete ho"""
    if instance.user:
        try:
            username = instance.user.username
            instance.user.delete()
            print(f"🗑️ Lawyer + User deleted: {username}")
        except Exception as e:
            print(f"❌ Error: {e}")

    refresh_lawyer_loader()
    cleanup_old_fir_images()  # ← Cleanup old FIR images too
    print(f"✅ Recommendations updated")


# ==================== LAWYER APPROVAL ====================
@receiver(post_save, sender=LawyerProfile)
def refresh_on_approval(sender, instance, created, **kwargs):
    """Lawyer approved hone par recommendations refresh"""
    if instance.is_approved:
        refresh_lawyer_loader()
        print(f"✅ Lawyer approved: {instance.user.username}")
    
    # Cleanup old FIR images on any lawyer profile save (runs occasionally)
    cleanup_old_fir_images()