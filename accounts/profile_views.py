# ai_legal_support_system/accounts/profile_views.py

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.auth import update_session_auth_hash
from django.core.validators import ValidationError
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.utils import timezone
from datetime import timedelta
import re
import uuid  # ← ADD THIS IMPORT

from .models import User, LawyerProfile


@login_required
def profile_view(request):
    """Display user profile"""
    user = request.user
    lawyer_profile = None
    editable_fields = []
    readonly_fields = []
    
    if user.role == 'lawyer' and hasattr(user, 'lawyer_profile'):
        lawyer_profile = user.lawyer_profile
        # Lawyers can edit these
        editable_fields = ['first_name', 'last_name', 'contact_number']
        # These are read-only for lawyers
        readonly_fields = ['license_number', 'languages', 'case_specialty', 'location', 'years_experience']
    
    context = {
        'user': user,
        'lawyer_profile': lawyer_profile,
        'editable_fields': editable_fields,
        'readonly_fields': readonly_fields,
    }
    return render(request, 'accounts/profile.html', context)


@login_required
def edit_profile(request):
    """Edit user profile with role-based restrictions"""
    user = request.user
    
    if request.method == 'POST':
        # Get form data
        first_name = request.POST.get('first_name', '').strip()
        last_name = request.POST.get('last_name', '').strip()
        username = request.POST.get('username', '').strip()
        contact_number = request.POST.get('contact_number', '').strip()
        
        errors = []
        
        # Validate username uniqueness
        if username != user.username and User.objects.filter(username=username).exists():
            errors.append('Username already taken')
        
        # Validate contact number
        if contact_number and not re.match(r'^03\d{9}$', contact_number):
            errors.append('Contact number must be in format: 03XXXXXXXXX')
        
        if errors:
            for error in errors:
                messages.error(request, error)
            return redirect('edit_profile')
        
        # Update user fields
        user.first_name = first_name
        user.last_name = last_name
        user.username = username
        user.contact_number = contact_number
        user.save()
        
        messages.success(request, 'Profile updated successfully!')
        return redirect('profile_view')
    
    context = {
        'user': user,
        'lawyer_profile': user.lawyer_profile if user.role == 'lawyer' else None,
    }
    return render(request, 'accounts/edit_profile.html', context)


@login_required
def change_password(request):
    """Change user password"""
    if request.method == 'POST':
        current_password = request.POST.get('current_password')
        new_password = request.POST.get('new_password')
        confirm_password = request.POST.get('confirm_password')
        
        # Verify current password
        if not request.user.check_password(current_password):
            messages.error(request, 'Current password is incorrect.')
            return redirect('change_password')
        
        # Check new password match
        if new_password != confirm_password:
            messages.error(request, 'New passwords do not match.')
            return redirect('change_password')
        
        # Validate strong password
        from .views import validate_strong_password
        password_errors = validate_strong_password(new_password)
        
        if password_errors:
            for error in password_errors:
                messages.error(request, error)
            return redirect('change_password')
        
        # Change password
        request.user.set_password(new_password)
        request.user.save()
        update_session_auth_hash(request, request.user)  # Keep user logged in
        
        messages.success(request, 'Password changed successfully!')
        return redirect('profile_view')
    
    return render(request, 'accounts/change_password.html')


@login_required
@require_http_methods(['POST'])
def request_account_deletion(request):
    """Request account deletion - sends confirmation email"""
    user = request.user
    
    # Generate deletion token
    deletion_token = str(uuid.uuid4())  # Now uuid is defined
    user.reset_password_token = deletion_token  # Reusing this field for deletion
    user.reset_password_expires = timezone.now() + timedelta(hours=1)
    user.save()
    
    # Send confirmation email
    from django.core.mail import send_mail
    from django.conf import settings
    from django.urls import reverse
    
    deletion_link = request.build_absolute_uri(
        reverse('confirm_account_deletion', args=[deletion_token])
    )
    
    try:
        send_mail(
            subject='Account Deletion Request - AdalatAI',
            message=f"""
Hello {user.username},

We received a request to delete your AdalatAI account.

⚠️ **WARNING: This action is permanent and cannot be undone.**
- All your queries and chat history will be permanently deleted.
- Your lawyer profile (if any) will be removed.
- You will lose access to all saved data.

If you want to proceed, click the link below within 1 hour:

{deletion_link}

If you did NOT request this, please ignore this email and your account will remain active.

Best regards,
AdalatAI Team
""",
            from_email=settings.EMAIL_HOST_USER,
            recipient_list=[user.email],
            fail_silently=False,
        )
        messages.success(request, 'A confirmation email has been sent to your email address. Click the link to permanently delete your account.')
    except Exception as e:
        messages.error(request, 'Could not send confirmation email. Please try again later.')
    
    return redirect('profile_view')


@login_required
def confirm_account_deletion(request, token):
    """Confirm and execute account deletion"""
    user = get_object_or_404(User, reset_password_token=token, reset_password_expires__gt=timezone.now())
    
    if request.method == 'POST':
        confirmation = request.POST.get('confirmation')
        
        if confirmation == 'DELETE MY ACCOUNT':
            # Store user info for goodbye message
            username = user.username
            email = user.email
            
            # Delete the user (cascade will delete lawyer profile, case queries, etc.)
            user.delete()
            
            # Logout user
            from django.contrib.auth import logout
            logout(request)
            
            messages.success(request, f'Account {username} has been permanently deleted. We\'re sad to see you go!')
            return redirect('index')
        else:
            messages.error(request, 'Please type "DELETE MY ACCOUNT" to confirm deletion.')
            return redirect('confirm_account_deletion', token=token)
    
    context = {'user': user, 'token': token}
    return render(request, 'accounts/confirm_deletion.html', context)


@login_required
@require_http_methods(['POST'])
def cancel_deletion(request):
    """Cancel pending account deletion request"""
    user = request.user
    user.reset_password_token = None
    user.reset_password_expires = None
    user.save()
    
    messages.success(request, 'Account deletion request cancelled.')
    return redirect('profile_view')