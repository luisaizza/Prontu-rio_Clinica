#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Script para testar o login simplificado"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app_clinica import app, db, User
from werkzeug.security import check_password_hash

def test_login_simple():
    """Testa o login de forma simplificada"""
    
    app.config['TESTING'] = True
    app.config['WTF_CSRF_ENABLED'] = False
    
    with app.app_context():
        print("TEST - Checking user in database...")
        user = User.query.filter_by(username='luisaizza').first()
        if user:
            print(f"PASS - User 'luisaizza' found")
            print(f"  ID: {user.id}")
            print(f"  Perfil: {user.perfil}")
            
            is_correct = check_password_hash(user.password_hash, '123')
            print(f"  Senha '123' correta: {is_correct}")
        else:
            print(f"FAIL - User not found!")
            return
    
    with app.test_client() as client:
        print("\nTEST - Testing login with username/password...")
        
        response = client.post('/login', data={
            'username': 'luisaizza',
            'password': '123'
        }, follow_redirects=True)
        
        print(f"Status: {response.status_code}")
        print(f"URL final: {response.request.path}")
        
        html = response.get_data(as_text=True)
        if 'luisaizza' in html:
            print("PASS - Username found in HTML!")
        else:
            print("FAIL - Username NOT found in HTML!")
            
            # Verificar se mostra login requerido
            if 'Por favor, faca login' in html or 'login' in html.lower():
                print("INFO - Still showing login page")

if __name__ == '__main__':
    test_login_simple()
