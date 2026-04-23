# from django.urls import path
# from . import views

# urlpatterns = [
#     path('analyze/', views.analyze_query, name='analyze_query'),
#     path('test-analyze/', views.test_analyze, name='test_analyze'),   # ← This line must be here
#     path('chat-history/', views.get_chat_history, name='chat_history'),
# ]

from django.urls import path
from . import views

urlpatterns = [
    path('analyze/', views.analyze_query, name='analyze_query'),
    path('analyze-stream/', views.analyze_query_stream, name='analyze_query_stream'),
    path('test-analyze/', views.test_analyze, name='test_analyze'),
    path('chat-history/', views.get_chat_history, name='chat_history'),
]