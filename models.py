"""
Veritabanı Modelleri
User, Project, Competition tablolarını tanımlar
"""
from flask_login import UserMixin
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from flask_sqlalchemy import SQLAlchemy

# db instance'ı burada tanımlanacak
db = SQLAlchemy()

class User(UserMixin, db.Model):
    """Kullanıcı modeli - öğrenci, danışman, admin rolleri"""
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(20), nullable=False, default='student')  # student, advisor, admin
    first_name = db.Column(db.String(50))
    last_name = db.Column(db.String(50))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_active = db.Column(db.Boolean, default=True)
    
    # İlişkiler
    owned_projects = db.relationship('Project', foreign_keys='Project.owner_id', backref='owner', lazy=True)
    advised_projects = db.relationship('Project', foreign_keys='Project.advisor_id', backref='advisor', lazy=True)
    
    def set_password(self, password):
        """Şifreyi hash'leyerek kaydet"""
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        """Şifreyi kontrol et"""
        return check_password_hash(self.password_hash, password)
    
    def get_full_name(self):
        """Tam adı döndür"""
        if self.first_name and self.last_name:
            return f"{self.first_name} {self.last_name}"
        return self.username
    
    def get_role_display(self):
        """Rol adını Türkçe olarak döndür"""
        role_map = {
            'admin': 'Admin',
            'advisor': 'Danışman',
            'student': 'Öğrenci'
        }
        return role_map.get(self.role, self.role.title())
    
    def is_admin(self):
        return self.role == 'admin'
    
    def is_advisor(self):
        return self.role == 'advisor'
    
    def is_student(self):
        return self.role == 'student'
    
    def __repr__(self):
        return f'<User {self.username}>'

class Competition(db.Model):
    """Yarışma modeli"""
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    start_date = db.Column(db.Date)
    end_date = db.Column(db.Date)
    registration_deadline = db.Column(db.Date)
    submission_deadline = db.Column(db.Date)
    requirements = db.Column(db.Text)  # JSON formatında gereksinimler
    prizes = db.Column(db.Text)  # Ödül bilgileri
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    created_by = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    
    # İlişkiler
    projects = db.relationship('Project', backref='competition', lazy=True)
    
    def __repr__(self):
        return f'<Competition {self.name}>'

class Project(db.Model):
    """Proje modeli"""
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    status = db.Column(db.String(20), default='planning')  # planning, development, testing, completed
    category = db.Column(db.String(50))  # web, mobile, ai, iot, etc.
    technologies = db.Column(db.Text)  # JSON formatında teknoloji listesi
    github_url = db.Column(db.String(255))
    demo_url = db.Column(db.String(255))
    documentation_path = db.Column(db.String(255))  # Yüklenen dokümantasyon dosyası
    
    # Tarih bilgileri
    start_date = db.Column(db.Date)
    deadline = db.Column(db.Date)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # İlişkiler
    owner_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    advisor_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    competition_id = db.Column(db.Integer, db.ForeignKey('competition.id'))
    
    # Proje ekibi (many-to-many için ayrı tablo gerekebilir)
    team_members = db.Column(db.Text)  # JSON formatında ekip üyeleri
    
    def get_status_display(self):
        """Durum görüntü adı"""
        status_map = {
            'planning': 'Planlama',
            'development': 'Geliştirme',
            'testing': 'Test',
            'completed': 'Tamamlandı'
        }
        return status_map.get(self.status, self.status)
    
    def get_progress_percentage(self):
        """İlerleme yüzdesi (basit hesaplama)"""
        status_progress = {
            'planning': 25,
            'development': 50,
            'testing': 75,
            'completed': 100
        }
        return status_progress.get(self.status, 0)
    
    def __repr__(self):
        return f'<Project {self.title}>'

class ChatMessage(db.Model):
    """Chat mesajları için model"""
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    project_id = db.Column(db.Integer, db.ForeignKey('project.id'))
    message = db.Column(db.Text, nullable=False)
    response = db.Column(db.Text)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    
    # İlişkiler
    user = db.relationship('User', backref='chat_messages')
    project = db.relationship('Project', backref='chat_messages')
    
    def __repr__(self):
        return f'<ChatMessage {self.id}>'