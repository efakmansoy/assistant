#!/usr/bin/env python3
"""
Veritabanı şemasını güncelle
"""
import os
import sys

# Add current directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import app, db

def update_database():
    """Veritabanı şemasını güncelle"""
    with app.app_context():
        try:
            # Drop all tables and recreate
            db.drop_all()
            db.create_all()
            print("Veritabanı şeması güncellendi!")
            
            # Create admin user
            from models import User
            admin = User(
                username='admin',
                email='admin@example.com',
                first_name='Admin',
                last_name='User',
                role='admin'
            )
            admin.set_password('admin123')
            
            db.session.add(admin)
            db.session.commit()
            print("Admin kullanıcısı oluşturuldu!")
            
        except Exception as e:
            print(f"Hata: {e}")
            db.session.rollback()

if __name__ == "__main__":
    update_database()