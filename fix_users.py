#!/usr/bin/env python3
"""
Kullanıcı verilerindeki None değerlerini düzelt
"""
import os
import sys

# Add current directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import app, db
from models import User

def fix_user_data():
    """None olan kullanıcı verilerini düzelt"""
    with app.app_context():
        users = User.query.all()
        
        for user in users:
            updated = False
            
            if user.first_name is None:
                user.first_name = "Ad"
                updated = True
                print(f"Fixed first_name for user {user.username}")
            
            if user.last_name is None:
                user.last_name = "Soyad"
                updated = True
                print(f"Fixed last_name for user {user.username}")
            
            if updated:
                db.session.add(user)
        
        db.session.commit()
        print("Kullanıcı verileri düzeltildi!")

if __name__ == "__main__":
    fix_user_data()