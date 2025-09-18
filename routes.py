"""
Route yönetimi - Blueprint'ler
Ana sayfa, kimlik doğrulama, API ve admin route'ları
"""
from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, current_app
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import check_password_hash
from models import User, Project, Competition, ChatMessage, db
import json
from datetime import datetime

# Blueprint'leri tanımla
main_bp = Blueprint('main', __name__)
auth_bp = Blueprint('auth', __name__)
api_bp = Blueprint('api', __name__)
admin_bp = Blueprint('admin', __name__)

# Ana sayfa route'ları
@main_bp.route('/')
def index():
    """Ana sayfa"""
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))
    return render_template('index.html')

@main_bp.route('/dashboard')
@login_required
def dashboard():
    """Kullanıcı dashboard'u"""
    if current_user.is_student():
        # Öğrenci için projeler
        projects = Project.query.filter_by(owner_id=current_user.id).all()
        competitions = Competition.query.filter_by(is_active=True).all()
        return render_template('student_dashboard.html', projects=projects, competitions=competitions)
    elif current_user.is_advisor():
        # Danışman için danışmanlık yaptığı projeler
        advised_projects = Project.query.filter_by(advisor_id=current_user.id).all()
        return render_template('advisor_dashboard.html', projects=advised_projects)
    elif current_user.is_admin():
        # Admin için sistem özeti
        return redirect(url_for('admin.dashboard'))
    
    return render_template('dashboard.html')

@main_bp.route('/projects')
@login_required
def projects():
    """Proje listesi"""
    if current_user.is_student():
        user_projects = Project.query.filter_by(owner_id=current_user.id).all()
    elif current_user.is_advisor():
        user_projects = Project.query.filter_by(advisor_id=current_user.id).all()
    else:
        user_projects = Project.query.all()
    
    return render_template('projects.html', projects=user_projects)

@main_bp.route('/project/<int:project_id>')
@login_required
def project_detail(project_id):
    """Proje detayı"""
    project = db.session.get(Project, project_id)
    if not project:
        flash('Proje bulunamadı.', 'error')
        return redirect(url_for('main.projects'))
    
    # Erişim kontrolü
    if not (current_user.is_admin() or 
            project.owner_id == current_user.id or 
            project.advisor_id == current_user.id):
        flash('Bu projeye erişim yetkiniz yok.', 'error')
        return redirect(url_for('main.projects'))
    
    # İlgili projeler - aynı kategorideki diğer projeler
    related_projects = []
    if project.category:
        related_projects = Project.query.filter(
            Project.category == project.category,
            Project.id != project.id
        ).limit(5).all()
    
    return render_template('project_detail.html', 
                         project=project, 
                         related_projects=related_projects)

@main_bp.route('/chat')
@login_required
def chat():
    """AI Asistan chat sayfası"""
    return render_template('chat.html')

@main_bp.route('/profile')
@login_required
def profile():
    """Kullanıcı profili"""
    return render_template('profile.html', user=current_user)

@main_bp.route('/api/profile', methods=['PUT'])
@login_required
def update_profile():
    try:
        data = request.get_json()
        
        # Update user information
        if 'first_name' in data:
            current_user.first_name = data['first_name']
        if 'last_name' in data:
            current_user.last_name = data['last_name']
        if 'email' in data:
            # Check if email is already in use
            existing_user = db.session.query(User).filter_by(email=data['email']).first()
            if existing_user and existing_user.id != current_user.id:
                return jsonify({'success': False, 'message': 'Bu e-posta adresi başka bir kullanıcı tarafından kullanılıyor'}), 400
            current_user.email = data['email']
        
        db.session.commit()
        return jsonify({'success': True, 'message': 'Profil güncellendi'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500

@main_bp.route('/api/profile/password', methods=['PUT'])
@login_required
def update_password():
    try:
        data = request.get_json()
        
        # Verify current password
        if not current_user.check_password(data['current_password']):
            return jsonify({'success': False, 'message': 'Mevcut şifre yanlış'}), 400
        
        # Update password
        current_user.set_password(data['new_password'])
        db.session.commit()
        
        return jsonify({'success': True, 'message': 'Şifre güncellendi'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500

@main_bp.route('/api/profile/preferences', methods=['PUT'])
@login_required
def update_preferences():
    try:
        data = request.get_json()
        # For now, just return success
        # In a real application, you would save preferences to database
        return jsonify({'success': True, 'message': 'Tercihler kaydedildi'})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@main_bp.route('/api/profile/stats')
@login_required
def get_profile_stats():
    try:
        if current_user.is_student():
            # Student statistics
            total_projects = db.session.query(Project).filter_by(student_id=current_user.id).count()
            completed_projects = db.session.query(Project).filter_by(
                student_id=current_user.id, status='completed'
            ).count()
            in_progress_projects = db.session.query(Project).filter_by(
                student_id=current_user.id, status='in_progress'
            ).count()
            chat_messages = db.session.query(ChatMessage).filter_by(user_id=current_user.id).count()
            
            return jsonify({
                'total_projects': total_projects,
                'completed_projects': completed_projects,
                'in_progress_projects': in_progress_projects,
                'chat_messages': chat_messages
            })
        
        elif current_user.is_advisor():
            # Advisor statistics
            advised_projects = db.session.query(Project).filter_by(advisor_id=current_user.id).count()
            own_projects = db.session.query(Project).filter_by(created_by=current_user.id).count()
            students = db.session.query(Project.student_id).filter_by(advisor_id=current_user.id).distinct().count()
            feedbacks = db.session.query(Project).filter(
                Project.advisor_id == current_user.id,
                Project.feedback.isnot(None)
            ).count()
            
            return jsonify({
                'advised_projects': advised_projects,
                'own_projects': own_projects,
                'students': students,
                'feedbacks': feedbacks
            })
        
        else:
            return jsonify({})
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@main_bp.route('/api/profile/activity')
@login_required
def get_profile_activity():
    try:
        activities = []
        
        # Get recent projects
        recent_projects = db.session.query(Project).filter(
            (Project.student_id == current_user.id) | (Project.advisor_id == current_user.id)
        ).order_by(Project.updated_at.desc()).limit(5).all()
        
        for project in recent_projects:
            if project.student_id == current_user.id:
                activities.append({
                    'icon': 'project-diagram',
                    'title': f'Proje güncellendi: {project.title}',
                    'description': f'Durum: {project.get_status_display()}',
                    'time': project.updated_at.strftime('%d.%m.%Y')
                })
            elif project.advisor_id == current_user.id:
                activities.append({
                    'icon': 'chalkboard-teacher',
                    'title': f'Danışmanlık: {project.title}',
                    'description': f'Öğrenci projesi güncellendi',
                    'time': project.updated_at.strftime('%d.%m.%Y')
                })
        
        # Get recent chat messages
        recent_chats = db.session.query(ChatMessage).filter_by(
            user_id=current_user.id
        ).order_by(ChatMessage.timestamp.desc()).limit(3).all()
        
        for chat in recent_chats:
            activities.append({
                'icon': 'comments',
                'title': 'AI Asistan ile sohbet',
                'description': chat.message[:50] + '...' if len(chat.message) > 50 else chat.message,
                'time': chat.timestamp.strftime('%d.%m.%Y')
            })
        
        # Sort activities by time (most recent first)
        activities.sort(key=lambda x: x['time'], reverse=True)
        
        return jsonify(activities[:10])  # Return last 10 activities
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Proje API'leri
@main_bp.route('/api/projects', methods=['POST'])
@login_required
def create_project():
    """API: Yeni proje oluşturma"""
    try:
        data = request.get_json()
        
        # Validation
        if not data.get('title'):
            return jsonify({'success': False, 'message': 'Proje başlığı gereklidir'}), 400
        
        # Date parsing
        start_date = None
        deadline = None
        
        if data.get('start_date'):
            start_date = datetime.strptime(data['start_date'], '%Y-%m-%d').date()
        
        if data.get('deadline'):
            deadline = datetime.strptime(data['deadline'], '%Y-%m-%d').date()
        
        project = Project(
            title=data['title'],
            description=data.get('description', ''),
            category=data.get('category', ''),
            technologies=data.get('technologies', ''),
            github_url=data.get('github_url', ''),
            demo_url=data.get('demo_url', ''),
            start_date=start_date,
            deadline=deadline,
            owner_id=current_user.id,
            advisor_id=data.get('advisor_id'),
            competition_id=data.get('competition_id'),
            team_members=data.get('team_members', ''),
            status='planning'
        )
        
        db.session.add(project)
        db.session.commit()
        
        return jsonify({
            'success': True, 
            'message': 'Proje başarıyla oluşturuldu',
            'project_id': project.id
        })
    
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500

@main_bp.route('/api/projects/<int:project_id>', methods=['PUT'])
@login_required
def update_project(project_id):
    """API: Proje güncelleme"""
    try:
        project = db.session.get(Project, project_id)
        if not project:
            return jsonify({'success': False, 'message': 'Proje bulunamadı'}), 404
        
        # Check permissions
        if project.owner_id != current_user.id and project.advisor_id != current_user.id and not current_user.is_admin():
            return jsonify({'success': False, 'message': 'Yetkiniz yok'}), 403
        
        data = request.get_json()
        
        # Update fields
        if 'title' in data:
            project.title = data['title']
        if 'description' in data:
            project.description = data['description']
        if 'status' in data:
            project.status = data['status']
        if 'category' in data:
            project.category = data['category']
        if 'technologies' in data:
            project.technologies = data['technologies']
        if 'github_url' in data:
            project.github_url = data['github_url']
        if 'demo_url' in data:
            project.demo_url = data['demo_url']
        
        # Date fields
        if data.get('start_date'):
            project.start_date = datetime.strptime(data['start_date'], '%Y-%m-%d').date()
        if data.get('deadline'):
            project.deadline = datetime.strptime(data['deadline'], '%Y-%m-%d').date()
        
        project.updated_at = datetime.utcnow()
        db.session.commit()
        
        return jsonify({'success': True, 'message': 'Proje güncellendi'})
    
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500

@main_bp.route('/api/projects/<int:project_id>', methods=['DELETE'])
@login_required
def delete_project(project_id):
    """API: Proje silme"""
    try:
        project = db.session.get(Project, project_id)
        if not project:
            return jsonify({'success': False, 'message': 'Proje bulunamadı'}), 404
        
        # Check permissions
        if project.owner_id != current_user.id and not current_user.is_admin():
            return jsonify({'success': False, 'message': 'Yetkiniz yok'}), 403
        
        db.session.delete(project)
        db.session.commit()
        
        return jsonify({'success': True, 'message': 'Proje silindi'})
    
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500

# Kimlik doğrulama route'ları
@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    """Kullanıcı girişi"""
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))
    
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        remember = bool(request.form.get('remember'))
        
        user = User.query.filter_by(username=username).first()
        
        if user and user.check_password(password) and user.is_active:
            login_user(user, remember=remember)
            next_page = request.args.get('next')
            flash(f'Hoş geldiniz, {user.get_full_name()}!', 'success')
            return redirect(next_page) if next_page else redirect(url_for('main.dashboard'))
        else:
            flash('Geçersiz kullanıcı adı veya şifre.', 'error')
    
    return render_template('auth/login.html')

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    """Kullanıcı kaydı"""
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))
    
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        role = request.form.get('role', 'student')
        first_name = request.form.get('first_name')
        last_name = request.form.get('last_name')
        
        # Validation
        if password != confirm_password:
            flash('Şifreler eşleşmiyor.', 'error')
            return render_template('auth/register.html')
        
        if User.query.filter_by(username=username).first():
            flash('Bu kullanıcı adı zaten kullanılıyor.', 'error')
            return render_template('auth/register.html')
        
        if User.query.filter_by(email=email).first():
            flash('Bu e-posta adresi zaten kullanılıyor.', 'error')
            return render_template('auth/register.html')
        
        # Yeni kullanıcı oluştur
        user = User(
            username=username,
            email=email,
            role=role,
            first_name=first_name,
            last_name=last_name
        )
        user.set_password(password)
        
        db.session.add(user)
        db.session.commit()
        
        flash('Kayıt başarılı! Giriş yapabilirsiniz.', 'success')
        return redirect(url_for('auth.login'))
    
    return render_template('auth/register.html')

@auth_bp.route('/logout')
@login_required
def logout():
    """Kullanıcı çıkışı"""
    logout_user()
    flash('Başarıyla çıkış yaptınız.', 'success')
    return redirect(url_for('main.index'))

# API route'ları
@api_bp.route('/projects', methods=['GET', 'POST'])
@login_required
def api_projects():
    """Proje API'si"""
    if request.method == 'GET':
        if current_user.is_student():
            projects = Project.query.filter_by(owner_id=current_user.id).all()
        elif current_user.is_advisor():
            projects = Project.query.filter_by(advisor_id=current_user.id).all()
        else:
            projects = Project.query.all()
        
        return jsonify([{
            'id': p.id,
            'title': p.title,
            'description': p.description,
            'status': p.status,
            'progress': p.get_progress_percentage()
        } for p in projects])
    
    elif request.method == 'POST':
        data = request.get_json()
        
        project = Project(
            title=data['title'],
            description=data.get('description'),
            category=data.get('category'),
            owner_id=current_user.id,
            competition_id=data.get('competition_id')
        )
        
        db.session.add(project)
        db.session.commit()
        
        return jsonify({'message': 'Proje oluşturuldu', 'project_id': project.id}), 201

@api_bp.route('/competitions')
@login_required
def api_competitions():
    """Yarışma listesi API'si"""
    competitions = Competition.query.filter_by(is_active=True).all()
    return jsonify([{
        'id': c.id,
        'name': c.name,
        'description': c.description,
        'deadline': c.registration_deadline.isoformat() if c.registration_deadline else None
    } for c in competitions])

@api_bp.route('/projects/<int:project_id>/upload-document', methods=['POST'])
@login_required
def upload_project_document(project_id):
    """Proje dökümanı yükleme"""
    project = db.session.get(Project, project_id)
    if not project:
        return jsonify({'error': 'Proje bulunamadı'}), 404
    
    # Erişim kontrolü
    if not (current_user.is_admin() or 
            project.owner_id == current_user.id or 
            project.advisor_id == current_user.id):
        return jsonify({'error': 'Bu projeye erişim yetkiniz yok.'}), 403
    
    if 'document' not in request.files:
        return jsonify({'error': 'Dosya seçilmedi'}), 400
    
    file = request.files['document']
    if file.filename == '':
        return jsonify({'error': 'Dosya seçilmedi'}), 400
    
    if file and file.filename.lower().endswith('.pdf'):
        # Dosya adını güvenli hale getir
        import os
        import uuid
        from werkzeug.utils import secure_filename
        
        filename = secure_filename(file.filename)
        unique_filename = f"{uuid.uuid4()}_{filename}"
        
        # Uploads klasörünü oluştur
        upload_folder = os.path.join(current_app.root_path, 'uploads')
        os.makedirs(upload_folder, exist_ok=True)
        
        file_path = os.path.join(upload_folder, unique_filename)
        file.save(file_path)
        
        # Veritabanını güncelle
        project.documentation_path = unique_filename
        db.session.commit()
        
        # RAG sistemine dökümanı ekle (eğer varsa)
        try:
            from rag_system import RAGSystem
            rag = RAGSystem()
            rag.add_document(file_path, project_id)
        except Exception as e:
            print(f"RAG sistemi döküman ekleme hatası: {e}")
        
        return jsonify({'message': 'Döküman başarıyla yüklendi'}), 200
    
    return jsonify({'error': 'Sadece PDF dosyaları kabul edilir'}), 400

@api_bp.route('/projects/<int:project_id>/status', methods=['PUT'])
@login_required
def update_project_status(project_id):
    """Proje durumu güncelleme"""
    project = db.session.get(Project, project_id)
    if not project:
        return jsonify({'error': 'Proje bulunamadı'}), 404
    
    # Erişim kontrolü
    if not (current_user.is_admin() or 
            project.owner_id == current_user.id or 
            project.advisor_id == current_user.id):
        return jsonify({'error': 'Bu projeye erişim yetkiniz yok.'}), 403
    
    data = request.get_json()
    new_status = data.get('status')
    
    if new_status not in ['planning', 'development', 'testing', 'completed']:
        return jsonify({'error': 'Geçersiz durum'}), 400
    
    project.status = new_status
    db.session.commit()
    
    return jsonify({'message': 'Proje durumu güncellendi'}), 200

@api_bp.route('/projects/feedback', methods=['POST'])
@login_required
def project_feedback():
    """Proje geri bildirimi"""
    if not current_user.is_advisor():
        return jsonify({'error': 'Bu işlemi sadece danışmanlar yapabilir'}), 403
    
    data = request.get_json()
    project_id = data.get('project_id')
    feedback = data.get('feedback')
    rating = data.get('rating')
    
    project = db.session.get(Project, project_id)
    if not project:
        return jsonify({'error': 'Proje bulunamadı'}), 404
    
    # Danışman kontrolü
    if project.advisor_id != current_user.id:
        return jsonify({'error': 'Bu projenin danışmanı değilsiniz'}), 403
    
    # Geri bildirim kaydetme (şimdilik basit)
    # TODO: Ayrı bir Feedback modeli oluşturulabilir
    
    return jsonify({'message': 'Geri bildirim kaydedildi'}), 200

# Admin route'ları
@admin_bp.route('/')
@admin_bp.route('/dashboard')
@login_required
def dashboard():
    """Admin dashboard"""
    if not current_user.is_admin():
        flash('Bu sayfaya erişim yetkiniz yok.', 'error')
        return redirect(url_for('main.dashboard'))
    
    # İstatistikler
    users = User.query.all()
    projects = Project.query.all()
    competitions = Competition.query.all()
    
    stats = {
        'total_users': len(users),
        'total_projects': len(projects),
        'total_competitions': len(competitions),
        'total_messages': 0  # TODO: ChatMessage sayısı eklenecek
    }
    
    return render_template('admin_dashboard.html', 
                         stats=stats, 
                         users=users, 
                         projects=projects, 
                         competitions=competitions)

@admin_bp.route('/users')
@login_required
def users():
    """Kullanıcı yönetimi"""
    if not current_user.is_admin():
        flash('Bu sayfaya erişim yetkiniz yok.', 'error')
        return redirect(url_for('main.dashboard'))
    
    users = User.query.all()
    return render_template('admin/users.html', users=users)

@admin_bp.route('/competitions')
@login_required
def competitions():
    """Yarışma yönetimi"""
    if not current_user.is_admin():
        flash('Bu sayfaya erişim yetkiniz yok.', 'error')
        return redirect(url_for('main.dashboard'))
    
    competitions = Competition.query.all()
    return render_template('admin/competitions.html', competitions=competitions)

@admin_bp.route('/competitions', methods=['POST'])
@login_required
def add_competition_api():
    """API: Yarışma ekleme"""
    if not current_user.is_admin():
        return jsonify({'success': False, 'message': 'Yetkiniz yok'}), 403
    
    try:
        data = request.get_json()
        print(f"Received data: {data}")  # Debug log
        
        # Date parsing
        registration_deadline = None
        submission_deadline = None
        
        if data.get('registration_deadline'):
            registration_deadline = datetime.strptime(data['registration_deadline'], '%Y-%m-%d').date()
        
        if data.get('submission_deadline'):
            submission_deadline = datetime.strptime(data['submission_deadline'], '%Y-%m-%d').date()
        
        competition = Competition(
            name=data['name'],
            description=data.get('description', ''),
            registration_deadline=registration_deadline,
            submission_deadline=submission_deadline,
            is_active=data.get('is_active', True),
            created_by=current_user.id
        )
        
        print(f"Creating competition: {competition.name}")  # Debug log
        
        db.session.add(competition)
        db.session.commit()
        
        print("Competition created successfully!")  # Debug log
        
        return jsonify({'success': True, 'message': 'Yarışma başarıyla eklendi'})
    
    except Exception as e:
        print(f"Error creating competition: {e}")  # Debug log
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500

@admin_bp.route('/users', methods=['POST'])
@login_required
def add_user_api():
    """API: Kullanıcı ekleme"""
    if not current_user.is_admin():
        return jsonify({'success': False, 'message': 'Yetkiniz yok'}), 403
    
    try:
        data = request.get_json()
        
        # Check if username or email already exists
        if User.query.filter_by(username=data['username']).first():
            return jsonify({'success': False, 'message': 'Bu kullanıcı adı zaten kullanılıyor'}), 400
        
        if User.query.filter_by(email=data['email']).first():
            return jsonify({'success': False, 'message': 'Bu e-posta adresi zaten kullanılıyor'}), 400
        
        user = User(
            username=data['username'],
            email=data['email'],
            first_name=data['first_name'],
            last_name=data['last_name'],
            role=data['role']
        )
        user.set_password(data['password'])
        
        db.session.add(user)
        db.session.commit()
        
        return jsonify({'success': True, 'message': 'Kullanıcı başarıyla eklendi'})
    
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500

@admin_bp.route('/competitions/add', methods=['GET', 'POST'])
@login_required
def add_competition():
    """Yarışma ekleme"""
    if not current_user.is_admin():
        flash('Bu sayfaya erişim yetkiniz yok.', 'error')
        return redirect(url_for('main.dashboard'))
    
    if request.method == 'POST':
        data = request.form
        
        competition = Competition(
            name=data['name'],
            description=data['description'],
            start_date=datetime.strptime(data['start_date'], '%Y-%m-%d').date() if data.get('start_date') else None,
            end_date=datetime.strptime(data['end_date'], '%Y-%m-%d').date() if data.get('end_date') else None,
            registration_deadline=datetime.strptime(data['registration_deadline'], '%Y-%m-%d').date() if data.get('registration_deadline') else None,
            requirements=data.get('requirements'),
            prizes=data.get('prizes'),
            created_by=current_user.id
        )
        
        db.session.add(competition)
        db.session.commit()
        
        flash('Yarışma başarıyla eklendi.', 'success')
        return redirect(url_for('admin.competitions'))
    
    return render_template('admin/add_competition.html')