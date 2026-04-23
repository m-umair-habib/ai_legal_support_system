from django.urls import path
from . import views
from . import profile_views

urlpatterns = [
    path('', views.index, name='index'),
    path('signup-login/', views.signup_login, name='signup_login'),
    path('logout/', views.user_logout, name='logout'),
    path('verify-email/<str:token>/', views.verify_email, name='verify_email'),
    path('resend-verification/', views.resend_verification, name='resend_verification'),
    path('forgot-password/', views.forgot_password, name='forgot_password'),
    path('reset-password/<str:token>/', views.reset_password, name='reset_password'),
    path('lawyer/<int:lawyer_id>/', views.lawyer_profile, name='lawyer_profile'),
    path('profile/', profile_views.profile_view, name='profile_view'),
    path('profile/edit/', profile_views.edit_profile, name='edit_profile'),
    path('profile/change-password/', profile_views.change_password, name='change_password'),
    path('profile/delete-request/', profile_views.request_account_deletion, name='request_account_deletion'),
    path('profile/delete-confirm/<str:token>/', profile_views.confirm_account_deletion, name='confirm_account_deletion'),
    path('profile/cancel-deletion/', profile_views.cancel_deletion, name='cancel_deletion'),
]