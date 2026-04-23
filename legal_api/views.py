# from django.http import JsonResponse
# from django.views.decorators.csrf import csrf_exempt
# from django.views.decorators.http import require_http_methods
# from django.contrib.auth.decorators import login_required
# import json
# import traceback
# import os
# from django.conf import settings
# from django.utils import timezone

# from ai_engine.rag_engine import get_rag_engine
# from ai_engine.language_processor import detect_language
# from accounts.models import CaseQuery, ChatSession, ChatMessage

# @login_required
# @require_http_methods(["POST"])
# def analyze_query(request):
#     fir_image_path = None
#     try:
#         query = request.POST.get('query', '').strip()
#         fir_image = request.FILES.get('fir_image')
#         fir_text = ""
#         session_id = request.POST.get('session_id', '')

#         # Process FIR image if uploaded
#         if fir_image:
#             try:
#                 from ai_engine.ocr_processor import extract_text_from_image
#                 fir_text = extract_text_from_image(fir_image) or ""
#                 if fir_text:
#                     upload_dir = settings.MEDIA_ROOT / 'fir_images'
#                     upload_dir.mkdir(parents=True, exist_ok=True)
#                     fir_image_path = upload_dir / fir_image.name
#                     with open(fir_image_path, 'wb+') as f:
#                         for chunk in fir_image.chunks():
#                             f.write(chunk)
#             except Exception as e:
#                 print(f"OCR Error: {e}")

#         if not query and not fir_text:
#             return JsonResponse({'success': False, 'error': 'Query or FIR image required'}, status=400)

#         # 🔥 GET OR CREATE CHAT SESSION
#         if session_id:
#             try:
#                 chat_session = ChatSession.objects.get(id=session_id, user=request.user)
#             except ChatSession.DoesNotExist:
#                 chat_session = ChatSession.objects.create(user=request.user)
#                 session_id = chat_session.id
#         else:
#             chat_session = ChatSession.objects.create(user=request.user)
#             session_id = chat_session.id

#         # 🔥 SAVE USER MESSAGE
#         user_message = query if query else "FIR Image uploaded for analysis"
#         ChatMessage.objects.create(
#             session=chat_session,
#             role='user',
#             content=user_message
#         )

#         # 🔥 GET CHAT HISTORY (Last 10 messages)
#         chat_history = []
#         history_messages = ChatMessage.objects.filter(session=chat_session).order_by('-created_at')[:10]
#         for msg in reversed(history_messages):
#             chat_history.append({
#                 'role': msg.role,
#                 'content': msg.content
#             })

#         # 🔥 Use RAG Engine with chat history
#         rag = get_rag_engine()
#         response_text, lawyers, detected_lang = rag.search(
#             query=query or "FIR Analysis",
#             is_fir=bool(fir_text),
#             fir_text=fir_text,
#             top_k=5,
#             chat_history=chat_history  # ← Pass chat history
#         )

#         # 🔥 SAVE AI RESPONSE
#         ChatMessage.objects.create(
#             session=chat_session,
#             role='assistant',
#             content=response_text
#         )

#         # Format lawyers for frontend
#         formatted_lawyers = [{
#             'id': int(l.get('id', 0)),
#             'name': str(l.get('name', 'Lawyer')),
#             'specialty': str(l.get('specialty', 'General Practice')),
#             'location': str(l.get('location', 'Pakistan')),
#             'experience': str(l.get('experience', 'N/A'))
#         } for l in lawyers[:5]]

#         # Save to CaseQuery (legacy)
#         try:
#             CaseQuery.objects.create(
#                 user=request.user,
#                 query_text=query[:400] or "FIR Analysis",
#                 fir_extracted_text=fir_text[:1000] if fir_text else "",
#                 fir_image_path=str(fir_image_path) if fir_image_path else None,  # ← Add this
#                 ai_response=response_text[:2000]
#             )
#         except Exception as e:
#             print(f"DB Error: {e}")

#         # Auto delete FIR image
#         if fir_image_path and fir_image_path.exists():
#             try:
#                 fir_image_path.unlink()
#             except:
#                 pass

#         return JsonResponse({
#             'success': True,
#             'response_text': response_text,
#             'lawyers': formatted_lawyers,
#             'detected_language': detected_lang,
#             'session_id': session_id  # ← Return session ID to frontend
#         })

#     except Exception as e:
#         traceback.print_exc()
#         return JsonResponse({
#             'success': False,
#             'response_text': f'Error: {str(e)}',
#             'lawyers': []
#         }, status=500)

# @csrf_exempt
# @require_http_methods(["GET", "POST"])
# def test_analyze(request):
#     """Test endpoint to verify system status"""
#     try:
#         rag = get_rag_engine()
#         return JsonResponse({
#             'success': True,
#             'status': 'active',
#             'index_loaded': rag.is_loaded,
#             'chunks_count': rag.index.ntotal if rag.index else 0,
#             'groq_configured': bool(os.getenv('GROQ_API_KEY'))
#         })
#     except Exception as e:
#         return JsonResponse({
#             'success': False,
#             'error': str(e)
#         }, status=500)
    
# @login_required
# def get_chat_history(request):
#     """Get current session's chat history"""
#     try:
#         # Get latest session
#         latest_session = ChatSession.objects.filter(user=request.user).order_by('-created_at').first()
        
#         if latest_session:
#             messages = ChatMessage.objects.filter(session=latest_session).order_by('created_at')
#             history = [{'role': msg.role, 'content': msg.content} for msg in messages]
#             return JsonResponse({'success': True, 'messages': history, 'session_id': latest_session.id})
#         else:
#             return JsonResponse({'success': True, 'messages': [], 'session_id': None})
#     except Exception as e:
#         return JsonResponse({'success': False, 'error': str(e)})
    



from django.http import JsonResponse, StreamingHttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from django.conf import settings
import json
import traceback
import os

from ai_engine.rag_engine import get_rag_engine
from ai_engine.language_processor import detect_language
from accounts.models import CaseQuery, ChatSession, ChatMessage


@login_required
@require_http_methods(["POST"])
def analyze_query(request):
    """Non-streaming fallback - returns complete response"""
    fir_image_path = None
    try:
        query = request.POST.get('query', '').strip()
        fir_image = request.FILES.get('fir_image')
        fir_text = ""
        session_id = request.POST.get('session_id', '')

        if fir_image:
            try:
                from ai_engine.ocr_processor import extract_text_from_image
                fir_text = extract_text_from_image(fir_image) or ""
                if fir_text:
                    upload_dir = settings.MEDIA_ROOT / 'fir_images'
                    upload_dir.mkdir(parents=True, exist_ok=True)
                    fir_image_path = upload_dir / fir_image.name
                    with open(fir_image_path, 'wb+') as f:
                        for chunk in fir_image.chunks():
                            f.write(chunk)
            except Exception as e:
                print(f"OCR Error: {e}")

        if not query and not fir_text:
            return JsonResponse({'success': False, 'error': 'Query or FIR image required'}, status=400)

        # Get or create session
        if session_id:
            try:
                chat_session = ChatSession.objects.get(id=session_id, user=request.user)
            except ChatSession.DoesNotExist:
                chat_session = ChatSession.objects.create(user=request.user)
                session_id = chat_session.id
        else:
            chat_session = ChatSession.objects.create(user=request.user)
            session_id = chat_session.id

        user_message = query if query else "FIR uploaded for analysis"
        ChatMessage.objects.create(session=chat_session, role='user', content=user_message)

        chat_history = []
        history_messages = ChatMessage.objects.filter(session=chat_session).order_by('-created_at')[:10]
        for msg in reversed(history_messages):
            chat_history.append({'role': msg.role, 'content': msg.content})

        rag = get_rag_engine()
        messages, lawyers, detected_lang = rag.search(
            query=query or "FIR Analysis",
            is_fir=bool(fir_text),
            fir_text=fir_text,
            top_k=5,
            chat_history=chat_history
        )

        response = rag.client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=messages,
            temperature=0.3,
            max_tokens=1200,
        )
        response_text = response.choices[0].message.content

        # Format for Urdu
        if detected_lang == 'urdu':
            response_text = response_text.replace('1.', '١.')
            response_text = response_text.replace('2.', '٢.')
            response_text = response_text.replace('3.', '٣.')
            response_text = response_text.replace('4.', '٤.')
            response_text = response_text.replace('5.', '٥.')
            response_text = f'<div dir="rtl" style="text-align: right; unicode-bidi: embed;">{response_text}</div>'
        else:
            response_text = response_text.replace('*', '•')

        ChatMessage.objects.create(session=chat_session, role='assistant', content=response_text)

        formatted_lawyers = [{
            'id': int(l.get('id', 0)),
            'name': str(l.get('name', 'Lawyer')),
            'specialty': str(l.get('specialty', 'General Practice')),
            'location': str(l.get('location', 'Pakistan')),
            'experience': str(l.get('experience', 'N/A'))
        } for l in lawyers[:5]]

        try:
            CaseQuery.objects.create(
                user=request.user,
                query_text=query[:400] or "FIR Analysis",
                fir_extracted_text=fir_text[:1000] if fir_text else "",
                fir_image_path=str(fir_image_path) if fir_image_path else None,
                ai_response=response_text[:2000]
            )
        except Exception as e:
            print(f"DB Error: {e}")

        if fir_image_path and fir_image_path.exists():
            try:
                fir_image_path.unlink()
            except:
                pass

        return JsonResponse({
            'success': True,
            'response_text': response_text,
            'lawyers': formatted_lawyers,
            'detected_language': detected_lang,
            'session_id': session_id
        })

    except Exception as e:
        traceback.print_exc()
        return JsonResponse({'success': False, 'response_text': f'Error: {str(e)}', 'lawyers': []}, status=500)


@login_required
@require_http_methods(["POST"])
def analyze_query_stream(request):
    """Streaming endpoint - token by token response"""
    try:
        query = request.POST.get('query', '').strip()
        fir_image = request.FILES.get('fir_image')
        fir_text = ""
        session_id = request.POST.get('session_id', '')

        if fir_image:
            try:
                from ai_engine.ocr_processor import extract_text_from_image
                fir_text = extract_text_from_image(fir_image) or ""
            except Exception as e:
                print(f"OCR Error: {e}")

        if not query and not fir_text:
            return JsonResponse({'success': False, 'error': 'Query or FIR image required'}, status=400)

        # Get or create session
        if session_id:
            try:
                chat_session = ChatSession.objects.get(id=session_id, user=request.user)
            except ChatSession.DoesNotExist:
                chat_session = ChatSession.objects.create(user=request.user)
                session_id = chat_session.id
        else:
            chat_session = ChatSession.objects.create(user=request.user)
            session_id = chat_session.id

        user_message = query if query else "FIR uploaded for analysis"
        ChatMessage.objects.create(session=chat_session, role='user', content=user_message)

        chat_history = []
        history_messages = ChatMessage.objects.filter(session=chat_session).order_by('-created_at')[:10]
        for msg in reversed(history_messages):
            chat_history.append({'role': msg.role, 'content': msg.content})

        rag = get_rag_engine()
        messages, lawyers, detected_lang = rag.search(
            query=query or "FIR Analysis",
            is_fir=bool(fir_text),
            fir_text=fir_text,
            top_k=5,
            chat_history=chat_history
        )

        def stream_generator():
            full_response = ""
            try:
                stream = rag.client.chat.completions.create(
                    model="llama-3.3-70b-versatile",
                    messages=messages,
                    temperature=0.3,
                    max_tokens=1200,
                    stream=True
                )
                
                # Send session_id first
                yield f"data: {json.dumps({'type': 'session', 'session_id': session_id})}\n\n"
                
                # Send lawyers
                formatted_lawyers = [{
                    'id': int(l.get('id', 0)),
                    'name': str(l.get('name', 'Lawyer')),
                    'specialty': str(l.get('specialty', 'General Practice')),
                    'location': str(l.get('location', 'Pakistan')),
                    'experience': str(l.get('experience', 'N/A'))
                } for l in lawyers[:5]]
                yield f"data: {json.dumps({'type': 'lawyers', 'lawyers': formatted_lawyers})}\n\n"
                
                # Send language
                yield f"data: {json.dumps({'type': 'language', 'lang': detected_lang})}\n\n"
                
                # Stream tokens
                for chunk in stream:
                    if chunk.choices[0].delta.content:
                        token = chunk.choices[0].delta.content
                        full_response += token
                        
                        # Format token for Urdu
                        if detected_lang == 'urdu':
                            token = token.replace('1.', '١.')
                            token = token.replace('2.', '٢.')
                            token = token.replace('3.', '٣.')
                            token = token.replace('4.', '٤.')
                            token = token.replace('5.', '٥.')
                            token = token.replace('6.', '٦.')
                            token = token.replace('7.', '٧.')
                            token = token.replace('8.', '٨.')
                            token = token.replace('9.', '٩.')
                        
                        yield f"data: {json.dumps({'type': 'token', 'content': token})}\n\n"
                
                # Send final formatted response
                if detected_lang == 'urdu':
                    final_response = f'<div dir="rtl" style="text-align: right; unicode-bidi: embed;">{full_response}</div>'
                else:
                    final_response = full_response.replace('*', '•')
                
                # Save to database
                ChatMessage.objects.create(session=chat_session, role='assistant', content=final_response)
                
                yield f"data: {json.dumps({'type': 'done', 'full_response': final_response})}\n\n"
                
            except Exception as e:
                yield f"data: {json.dumps({'type': 'error', 'error': str(e)})}\n\n"

        response = StreamingHttpResponse(
            stream_generator(),
            content_type='text/event-stream'
        )
        response['Cache-Control'] = 'no-cache'
        response['X-Accel-Buffering'] = 'no'
        return response

    except Exception as e:
        traceback.print_exc()
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


@csrf_exempt
@require_http_methods(["GET"])
def test_analyze(request):
    try:
        rag = get_rag_engine()
        return JsonResponse({
            'success': True,
            'status': 'active',
            'index_loaded': rag.is_loaded,
            'chunks_count': rag.index.ntotal if rag.index else 0,
            'groq_configured': bool(os.getenv('GROQ_API_KEY'))
        })
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


@login_required
def get_chat_history(request):
    try:
        latest_session = ChatSession.objects.filter(user=request.user).order_by('-created_at').first()
        if latest_session:
            messages = ChatMessage.objects.filter(session=latest_session).order_by('created_at')
            history = [{'role': msg.role, 'content': msg.content} for msg in messages]
            return JsonResponse({'success': True, 'messages': history, 'session_id': latest_session.id})
        else:
            return JsonResponse({'success': True, 'messages': [], 'session_id': None})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})