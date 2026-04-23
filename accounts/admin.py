from django.contrib import admin
from .models import User, LawyerProfile, CaseQuery, ChatSession, ChatMessage


# ===============================
# 👤 USER ADMIN
# ===============================
@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ('username', 'email', 'role', 'email_verified', 'is_active', 'created_at')
    list_filter = ('role', 'email_verified', 'is_active')
    search_fields = ('username', 'email', 'cnic')
    readonly_fields = ('email_verification_token', 'reset_password_token')


# ===============================
# ⚖️ LAWYER PROFILE ADMIN
# ===============================
@admin.register(LawyerProfile)
class LawyerProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'license_number', 'location', 'years_experience', 'is_approved')  # ← is_approved yahan hai
    list_editable = ('is_approved',)  # ← Ab error nahi aayega
    list_filter = ('is_approved', 'location')
    search_fields = ('user__username', 'license_number', 'location')
    
    # Bulk actions
    actions = ['approve_lawyers', 'reject_lawyers']
    
    def approve_lawyers(self, request, queryset):
        updated = queryset.update(is_approved=True)
        self.message_user(request, f'✅ {updated} lawyer(s) approved successfully!')
    approve_lawyers.short_description = "✅ Approve selected lawyers"
    
    def reject_lawyers(self, request, queryset):
        updated = queryset.update(is_approved=False)
        self.message_user(request, f'❌ {updated} lawyer(s) rejected!')
    reject_lawyers.short_description = "❌ Reject selected lawyers"


# ===============================
# 📁 CASE QUERY ADMIN
# ===============================
@admin.register(CaseQuery)
class CaseQueryAdmin(admin.ModelAdmin):
    list_display = ('user', 'query_preview', 'created_at')
    search_fields = ('query_text', 'user__username')
    list_filter = ('created_at',)
    
    def query_preview(self, obj):
        return obj.query_text[:50] + '...' if len(obj.query_text) > 50 else obj.query_text
    query_preview.short_description = 'Query'


# ===============================
# 💬 CHAT SESSION ADMIN
# ===============================
@admin.register(ChatSession)
class ChatSessionAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'created_at')
    list_filter = ('created_at',)


# ===============================
# 💬 CHAT MESSAGE ADMIN
# ===============================
@admin.register(ChatMessage)
class ChatMessageAdmin(admin.ModelAdmin):
    list_display = ('session', 'role', 'content_preview', 'created_at')
    list_filter = ('role', 'created_at')
    search_fields = ('content',)
    
    def content_preview(self, obj):
        return obj.content[:40] + '...' if len(obj.content) > 40 else obj.content
    content_preview.short_description = 'Message'