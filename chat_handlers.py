"""
Socket.IO Chat Handler'ları
Gerçek zamanlı chat işlevselliği
"""

from flask_socketio import emit, join_room, leave_room, disconnect
from flask_login import current_user
from flask import request
import json
from datetime import datetime

def register_chat_handlers(socketio, db):
    """Socket.IO event handler'larını kaydet"""
    
    @socketio.on('connect')
    def on_connect():
        """Kullanıcı bağlandığında"""
        if current_user.is_authenticated:
            print(f'User {current_user.username} connected')
            emit('status', {'msg': f'{current_user.username} has connected'})
        else:
            print('Anonymous user tried to connect')
            disconnect()

    @socketio.on('disconnect')
    def on_disconnect():
        """Kullanıcı ayrıldığında"""
        if current_user.is_authenticated:
            print(f'User {current_user.username} disconnected')

    @socketio.on('join_room')
    def on_join_room(data):
        """Kullanıcı odaya katıldığında"""
        if not current_user.is_authenticated:
            return
        
        room = data.get('room', 'general')
        join_room(room)
        print(f'User {current_user.username} joined room: {room}')
        emit('status', {
            'msg': f'{current_user.username} odaya katıldı',
            'room': room
        }, room=room)

    @socketio.on('leave_room')
    def on_leave_room(data):
        """Kullanıcı odadan ayrıldığında"""
        if not current_user.is_authenticated:
            return
        
        room = data.get('room', 'general')
        leave_room(room)
        print(f'User {current_user.username} left room: {room}')
        emit('status', {
            'msg': f'{current_user.username} odadan ayrıldı',
            'room': room
        }, room=room)

    @socketio.on('send_message')
    def handle_message(data):
        """Chat mesajı gönderildiğinde"""
        if not current_user.is_authenticated:
            return

        try:
            message_text = data.get('message', '').strip()
            room = data.get('room', 'general')
            project_id = data.get('project_id')

            if not message_text:
                emit('error', {'message': 'Mesaj boş olamaz'})
                return

            # Mesajı veritabanına kaydet
            from models import ChatMessage
            chat_message = ChatMessage(
                user_id=current_user.id,
                project_id=project_id,
                message=message_text,
                timestamp=datetime.utcnow()
            )
            
            db.session.add(chat_message)
            db.session.commit()

            # Mesaj verisini hazırla
            message_data = {
                'id': chat_message.id,
                'message': message_text,
                'username': current_user.username,
                'full_name': current_user.get_full_name(),
                'user_role': current_user.role,
                'timestamp': chat_message.timestamp.strftime('%H:%M'),
                'room': room,
                'project_id': project_id
            }

            # Odadaki herkese mesajı gönder
            emit('receive_message', message_data, room=room)
            print(f'Message from {current_user.username} in room {room}: {message_text}')

        except Exception as e:
            print(f'Error handling message: {str(e)}')
            emit('error', {'message': 'Mesaj gönderilirken hata oluştu'})

    @socketio.on('ai_chat')
    def handle_ai_chat(data):
        """AI chat mesajı işle"""
        if not current_user.is_authenticated:
            return

        try:
            message_text = data.get('message', '').strip()
            project_id = data.get('project_id')
            room = data.get('room', 'general')

            if not message_text:
                emit('error', {'message': 'Mesaj boş olamaz'})
                return

            # Kullanıcı mesajını kaydet ve gönder
            from models import ChatMessage
            user_message = ChatMessage(
                user_id=current_user.id,
                project_id=project_id,
                message=message_text,
                timestamp=datetime.utcnow()
            )
            
            db.session.add(user_message)
            db.session.commit()

            # Kullanıcı mesajını emit et
            user_message_data = {
                'id': user_message.id,
                'message': message_text,
                'username': current_user.username,
                'full_name': current_user.get_full_name(),
                'user_role': current_user.role,
                'timestamp': user_message.timestamp.strftime('%H:%M'),
                'room': room,
                'is_ai': False
            }
            emit('receive_message', user_message_data, room=room)

            # AI yanıtı için typing indicator göster
            emit('ai_typing', {'status': True}, room=room)

            try:
                # RAG sistemini kullanarak AI yanıtı al
                from rag_system import RAGSystem
                rag = RAGSystem()
                
                # Proje bağlamını al
                project_context = ""
                if project_id:
                    from models import Project
                    project = Project.query.get(project_id)
                    if project:
                        project_context = f"Proje: {project.title}\nAçıklama: {project.description}\nDurum: {project.get_status_display()}"

                # Kullanıcı rolüne göre AI yanıtı al
                ai_response = rag.get_ai_response(
                    question=message_text,
                    user_role=current_user.role,
                    project_context=project_context
                )

                # AI yanıtını kaydet
                ai_message = ChatMessage(
                    user_id=current_user.id,
                    project_id=project_id,
                    message=message_text,
                    response=ai_response,
                    timestamp=datetime.utcnow()
                )
                
                db.session.add(ai_message)
                db.session.commit()

                # AI yanıtını emit et
                ai_message_data = {
                    'id': ai_message.id,
                    'message': ai_response,
                    'username': 'AI Asistan',
                    'full_name': 'RAG AI Asistan',
                    'user_role': 'ai',
                    'timestamp': ai_message.timestamp.strftime('%H:%M'),
                    'room': room,
                    'is_ai': True
                }
                emit('receive_message', ai_message_data, room=room)

            except Exception as e:
                print(f'AI Chat Error: {str(e)}')
                # Hata durumunda basit yanıt ver
                error_response = "Üzgünüm, şu anda AI sisteminde bir sorun var. Lütfen daha sonra tekrar deneyin."
                
                ai_message_data = {
                    'id': 0,
                    'message': error_response,
                    'username': 'AI Asistan',
                    'full_name': 'RAG AI Asistan',
                    'user_role': 'ai',
                    'timestamp': datetime.now().strftime('%H:%M'),
                    'room': room,
                    'is_ai': True
                }
                emit('receive_message', ai_message_data, room=room)

            finally:
                # Typing indicator'ı kapat
                emit('ai_typing', {'status': False}, room=room)

        except Exception as e:
            print(f'Error in AI chat: {str(e)}')
            emit('error', {'message': 'AI chat hatası oluştu'})

    @socketio.on('typing')
    def handle_typing(data):
        """Kullanıcı yazıyor durumu"""
        if not current_user.is_authenticated:
            return

        room = data.get('room', 'general')
        is_typing = data.get('typing', False)
        
        emit('user_typing', {
            'username': current_user.username,
            'full_name': current_user.get_full_name(),
            'typing': is_typing
        }, room=room, include_self=False)

    @socketio.on('load_chat_history')
    def handle_load_chat_history(data):
        """Chat geçmişini yükle"""
        if not current_user.is_authenticated:
            return

        try:
            project_id = data.get('project_id')
            limit = data.get('limit', 50)

            from models import ChatMessage, User
            
            # Chat geçmişini al
            query = ChatMessage.query
            if project_id:
                query = query.filter_by(project_id=project_id)
            
            messages = query.order_by(ChatMessage.timestamp.desc()).limit(limit).all()
            messages.reverse()  # Kronolojik sıraya çevir

            # Mesajları formatla
            chat_history = []
            for msg in messages:
                # Kullanıcı mesajı
                user_msg = {
                    'id': msg.id,
                    'message': msg.message,
                    'username': msg.user.username,
                    'full_name': msg.user.get_full_name(),
                    'user_role': msg.user.role,
                    'timestamp': msg.timestamp.strftime('%H:%M'),
                    'is_ai': False
                }
                chat_history.append(user_msg)

                # AI yanıtı varsa ekle
                if msg.response:
                    ai_msg = {
                        'id': f'ai_{msg.id}',
                        'message': msg.response,
                        'username': 'AI Asistan',
                        'full_name': 'RAG AI Asistan',
                        'user_role': 'ai',
                        'timestamp': msg.timestamp.strftime('%H:%M'),
                        'is_ai': True
                    }
                    chat_history.append(ai_msg)

            emit('chat_history', {'messages': chat_history})

        except Exception as e:
            print(f'Error loading chat history: {str(e)}')
            emit('error', {'message': 'Chat geçmişi yüklenirken hata oluştu'})

    @socketio.on('ping')
    def handle_ping():
        """Bağlantı kontrolü"""
        emit('pong')

    print("Chat handlers başarıyla yüklendi!")

# Chat handler'ları kaydetme fonksiyonu
def init_chat_handlers(socketio, db):
    """Chat handler'larını başlat"""
    register_chat_handlers(socketio, db)
    return True