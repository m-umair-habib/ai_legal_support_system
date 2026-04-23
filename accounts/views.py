from django.shortcuts import render, redirect
from django.contrib.auth import login, authenticate, logout
from django.contrib import messages
from django.core.mail import send_mail
from django.conf import settings
from django.urls import reverse
from django.utils import timezone
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import uuid
import re
import os
import time
from datetime import timedelta

from .models import User, LawyerProfile, ChatSession, ChatMessage
from ai_engine.lawyer_loader import get_lawyer_loader

# ==================== AUTO CLEAN FIR IMAGES ====================
def clean_old_fir_images():
    media_dir = os.path.join(settings.MEDIA_ROOT, 'fir_images')
    if not os.path.exists(media_dir):
        return
    cutoff = time.time() - 3600
    for filename in os.listdir(media_dir):
        filepath = os.path.join(media_dir, filename)
        if os.path.isfile(filepath) and os.path.getmtime(filepath) < cutoff:
            try:
                os.remove(filepath)
                print(f"🗑️ Auto-deleted old FIR image: {filename}")
            except Exception as e:
                print(f"❌ Error deleting {filename}: {e}")

# ==================== MAIN PAGE & LOGOUT ====================
def index(request):
    return render(request, 'index.html', {'user': request.user})

def user_logout(request):
    logout(request)
    messages.info(request, 'You have been logged out')
    return redirect('index')

# ==================== AUTHENTICATION VIEWS ====================
def signup_login(request):
    if request.user.is_authenticated:
        return redirect('index')
   
    if request.method == 'POST':
        if 'login' in request.POST:
            return handle_login(request)
        elif 'signup' in request.POST:
            return handle_signup(request)
   
    return render(request, 'signup_login.html')

def handle_login(request):
    email = request.POST.get('email')
    password = request.POST.get('password')
   
    if not email or not password:
        messages.error(request, 'Please enter both email and password')
        return render(request, 'signup_login.html')
   
    try:
        user = User.objects.get(email=email)
       
        if not user.email_verified:
            messages.error(request, 'Please verify your email first.')
            return render(request, 'signup_login.html')
       
        if not user.is_active:
            messages.error(request, 'Your account is not active. Please verify your email.')
            return render(request, 'signup_login.html')
       
        user = authenticate(request, username=user.username, password=password)
        if user is not None:
            login(request, user)
            messages.success(request, f'Welcome back, {user.username}!')
            return redirect('index')
        else:
            messages.error(request, 'Invalid password')
    except User.DoesNotExist:
        messages.error(request, 'User not found')
   
    return render(request, 'signup_login.html')

def validate_strong_password(password):
    errors = []
    if len(password) < 8:
        errors.append('Password must be at least 8 characters long')
    if not re.search(r'[A-Z]', password):
        errors.append('Password must contain at least one uppercase letter')
    if not re.search(r'[a-z]', password):
        errors.append('Password must contain at least one lowercase letter')
    if not re.search(r'\d', password):
        errors.append('Password must contain at least one number')
    if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
        errors.append('Password must contain at least one special character')
    return errors

def handle_signup(request):
    full_name = request.POST.get('full_name', '').strip()
    username = request.POST.get('username', '').strip()
    cnic = request.POST.get('cnic', '').strip()
    email = request.POST.get('email', '').strip()
    contact = request.POST.get('contact', '').strip()
    password = request.POST.get('password', '')
    role = request.POST.get('role', 'client')
   
    errors = []
    if not full_name: errors.append('Full name is required')
    if not username: errors.append('Username is required')
    if not cnic: errors.append('CNIC is required')
    if not email: errors.append('Email is required')
    if not contact: errors.append('Contact number is required')
   
    password_errors = validate_strong_password(password)
    errors.extend(password_errors)
   
    if cnic and not re.match(r'^\d{5}-\d{7}-\d$', cnic):
        errors.append('CNIC must be in format: 00000-0000000-0')
   
    if contact and not re.match(r'^03\d{9}$', contact):
        errors.append('Contact number must be in format: 03XXXXXXXXX')
   
    if errors:
        for error in errors:
            messages.error(request, error)
        return render(request, 'signup_login.html')
   
    if User.objects.filter(email=email).exists():
        messages.error(request, 'Email already registered')
        return render(request, 'signup_login.html')
    if User.objects.filter(username=username).exists():
        messages.error(request, 'Username already taken')
        return render(request, 'signup_login.html')
    if User.objects.filter(cnic=cnic).exists():
        messages.error(request, 'CNIC already registered')
        return render(request, 'signup_login.html')
   
    name_parts = full_name.split(' ', 1)
    first_name = name_parts[0]
    last_name = name_parts[1] if len(name_parts) > 1 else ''
   
    user = User.objects.create_user(
        username=username,
        email=email,
        password=password,
        first_name=first_name,
        last_name=last_name,
        cnic=cnic,
        contact_number=contact,
        role=role,
        email_verified=False,
        is_active=False
    )
   
    if role == 'lawyer':
        exp_map = {'1-5 Years': 1, '5-10 Years': 2, '10+ Years': 3}
        license_number = request.POST.get('license_number', '').strip()
        location = request.POST.get('location', '').strip()
        years_exp = request.POST.get('years_experience', '1-5 Years')
        languages = request.POST.get('languages', '').strip()
        specialty = request.POST.get('speciality', '').strip()
       
        lawyer_errors = []
        if not license_number: lawyer_errors.append('License number is required')
        if not location: lawyer_errors.append('Location is required')
        if not languages: lawyer_errors.append('Languages are required')
        if not specialty: lawyer_errors.append('Speciality is required')
       
        if lawyer_errors:
            user.delete()
            for error in lawyer_errors:
                messages.error(request, error)
            return render(request, 'signup_login.html')
       
        LawyerProfile.objects.create(
            user=user,
            license_number=license_number,
            location=location,
            years_experience=exp_map.get(years_exp, 1),
            languages=languages,
            case_specialty=specialty,
            online_availability=request.POST.get('online_availability') == 'on',
            is_approved=False,
            # profile_complete=True
        )
        messages.success(request, 'Lawyer account created! Please verify your email.')
    else:
        messages.success(request, 'Client account created! Please verify your email to login.')
   
    verification_link = request.build_absolute_uri(
        reverse('verify_email', args=[str(user.email_verification_token)])
    )
   
    try:
        send_mail(
            subject='Verify Your Email - AdalatAI',
            message=f"""
Hello {username},
Thank you for registering with AdalatAI. Please click the link below to verify your email address:
{verification_link}
This link will expire in 24 hours.
If you didn't create an account with us, please ignore this email.
Best regards,
AdalatAI Team
""",
            from_email=settings.EMAIL_HOST_USER,
            recipient_list=[email],
            fail_silently=False,
        )
        messages.success(request, f'Verification email sent to {email}. Please check your inbox.')
    except Exception as e:
        print(f"Email error: {e}")
        messages.warning(request, 'Account created but verification email could not be sent.')
   
    return redirect('signup_login')

def verify_email(request, token):
    try:
        user = User.objects.get(email_verification_token=token, email_verified=False)
        user.email_verified = True
        user.is_active = True
        user.save()
        messages.success(request, 'Email verified successfully! You can now login.')
    except User.DoesNotExist:
        messages.error(request, 'Invalid or expired verification link.')
    return redirect('signup_login')

def resend_verification(request):
    if request.method == 'POST':
        email = request.POST.get('email')
        try:
            user = User.objects.get(email=email, email_verified=False)
            verification_link = request.build_absolute_uri(
                reverse('verify_email', args=[str(user.email_verification_token)])
            )
            send_mail(
                subject='Resend Verification - AdalatAI',
                message=f"Click the link to verify: {verification_link}",
                from_email=settings.EMAIL_HOST_USER,
                recipient_list=[email],
                fail_silently=False,
            )
            messages.success(request, f'Verification email sent to {email}')
        except User.DoesNotExist:
            messages.error(request, 'Email not found or already verified')
    return redirect('signup_login')

def forgot_password(request):
    if request.method == 'POST':
        email = request.POST.get('email')
        try:
            user = User.objects.get(email=email)
            reset_token = uuid.uuid4()
            user.reset_password_token = reset_token
            user.reset_password_expires = timezone.now() + timedelta(hours=24)
            user.save()
           
            reset_link = request.build_absolute_uri(
                reverse('reset_password', args=[str(reset_token)])
            )
           
            send_mail(
                subject='Reset Your Password - AdalatAI',
                message=f"""
Hello {user.username},
You requested to reset your password. Click the link below:
{reset_link}
This link will expire in 24 hours.
If you didn't request this, please ignore this email.
Best regards,
AdalatAI Team
""",
                from_email=settings.EMAIL_HOST_USER,
                recipient_list=[email],
                fail_silently=False,
            )
            messages.success(request, 'Password reset link sent to your email.')
        except User.DoesNotExist:
            messages.error(request, 'No account found with this email.')
    return render(request, 'forgot_password.html')

def reset_password(request, token):
    try:
        user = User.objects.get(
            reset_password_token=token,
            reset_password_expires__gt=timezone.now()
        )
    except User.DoesNotExist:
        messages.error(request, 'Invalid or expired reset link.')
        return redirect('signup_login')
   
    if request.method == 'POST':
        password = request.POST.get('password')
        confirm_password = request.POST.get('confirm_password')
       
        if password != confirm_password:
            messages.error(request, 'Passwords do not match.')
            return render(request, 'reset_password.html', {'token': token})
       
        password_errors = validate_strong_password(password)
        if password_errors:
            for error in password_errors:
                messages.error(request, error)
            return render(request, 'reset_password.html', {'token': token})
       
        user.set_password(password)
        user.reset_password_token = None
        user.reset_password_expires = None
        user.save()
       
        messages.success(request, 'Password reset successfully! Please login.')
        return redirect('signup_login')
   
    return render(request, 'reset_password.html', {'token': token})

# ==================== LAWYER PROFILE VIEW ====================
def lawyer_profile(request, lawyer_id):
    loader = get_lawyer_loader()
    lawyer_data = loader.get_lawyer_by_id(lawyer_id)
    
    if not lawyer_data:
        messages.error(request, 'Lawyer not found or profile is not available.')
        return redirect('index')
    
    show_contact = request.user.is_authenticated
    
    # === WhatsApp ready link with pre-filled message ===
    whatsapp_number = lawyer_data.get('phone', '').strip()
    if whatsapp_number and whatsapp_number.startswith('03'):
        # Convert 03XX to 923XX for wa.me
        whatsapp_number = '92' + whatsapp_number[1:]
    
    whatsapp_message = (
        "Assalamualaikum!%0A"
        "Main aap se *AdalatAI Legal Support System* ke through contact kar raha hoon.%0A%0A"
        "Mera case AI system ne analyze kiya hai aur aapko recommend kiya gaya hai.%0A"
        "Kya aap mujhe guide kar sakte hain?"
    )
    
    context = {
        'lawyer': lawyer_data,
        'show_contact': show_contact,
        'whatsapp_link': f"https://wa.me/{whatsapp_number}?text={whatsapp_message}" if whatsapp_number else None,
    }
    
    return render(request, 'lawyer_profile.html', context)
