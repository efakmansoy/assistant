"""
RAG Assistant - Ana Flask Uygulaması
Öğrenci ve danışmanlar için proje geliştirme platformu
"""
from flask import Flask
from flask_login import LoginManager
from flask_socketio import SocketIO
import os
from dotenv import load_dotenv

# .env dosyasını yükle
load_dotenv()

# Flask uygulamasını oluştur
app = Flask(__name__)

# Konfigürasyon
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev-secret-key-change-this')
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL', 'sqlite:///rag_assistant.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = os.getenv('UPLOAD_FOLDER', 'uploads')

# Modelleri import et ve db'yi başlat
from models import db
db.init_app(app)

# Uzantıları başlat
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'auth.login'
login_manager.login_message = 'Lütfen giriş yapın.'
socketio = SocketIO(app, cors_allowed_origins="*")

# Model ve route'ları import et
with app.app_context():
    from models import User, Project, Competition
    from routes import auth_bp, main_bp, api_bp, admin_bp

# Blueprint'leri kaydet
app.register_blueprint(auth_bp, url_prefix='/auth')
app.register_blueprint(main_bp)
app.register_blueprint(api_bp, url_prefix='/api')
app.register_blueprint(admin_bp, url_prefix='/admin')

@login_manager.user_loader
def load_user(user_id):
    from models import User
    return db.session.get(User, int(user_id))

# SocketIO event handlers
try:
    from chat_handlers import init_chat_handlers
    # Chat handler'ları başlat
    with app.app_context():
        init_chat_handlers(socketio, db)
    print("Chat handlers başarıyla yüklendi!")
except ImportError as e:
    print(f"Chat handlers yüklenemedi: {e}")
except Exception as e:
    print(f"Chat handlers başlatılırken hata: {e}")
    print("Chat handlers devre dışı bırakıldı")

if __name__ == '__main__':
    with app.app_context():
        # Veritabanı tablolarını oluştur
        db.create_all()
        
        # RAG sistemini başlat (geçici olarak devre dışı)
        # from rag_system import init_rag_system
        # init_rag_system()
        
        # Admin kullanıcısı oluştur (eğer yoksa)
        from models import User
        from werkzeug.security import generate_password_hash
        
        admin_user = User.query.filter_by(username='admin').first()
        if not admin_user:
            admin = User(
                username='admin',
                email='admin@example.com',
                password_hash=generate_password_hash('admin123'),
                role='admin'
            )
            db.session.add(admin)
            db.session.commit()
            print("Admin kullanıcısı oluşturuldu: admin/admin123")
    
    # Uygulamayı başlat
    socketio.run(app, debug=True, host='0.0.0.0', port=5000)