#!/usr/bin/env python3
"""Script para testar o fluxo de login completo"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app_clinica import app, db, User
from flask import Flask

def test_login_flow():
    """Testa o fluxo completo de login"""
    
    app.config['TESTING'] = True
    app.config['WTF_CSRF_ENABLED'] = False
    
    with app.test_client() as client:
        print("=" * 60)
        print("TESTE DE FLUXO DE LOGIN")
        print("=" * 60)
        
        # 1. Acessar página de login
        print("\n1. Acessando página de login...")
        response = client.get('/login')
        print(f"   Status: {response.status_code}")
        
        # 2. Fazer login com credenciais corretas
        print("\n2. Testando login com luisaizza/123...")
        response = client.post('/login', data={
            'username': 'luisaizza',
            'password': '123'
        }, follow_redirects=True)
        print(f"   Status: {response.status_code}")
        print(f"   URL final: {response.request.path}")
        
        # 3. Acessar home e verificar se username está no HTML
        print("\n3. Verificando se username aparece na home...")
        response = client.get('/')
        html_content = response.get_data(as_text=True)
        
        if 'luisaizza' in html_content:
            print("   ✓ Username 'luisaizza' encontrado no HTML da página!")
        else:
            print("   ✗ Username 'luisaizza' NÃO encontrado no HTML!")
        
        if 'current_user.username' in html_content:
            print("   ⚠ Template ainda contém {{ current_user.username }} não renderizado")
        
        # Verificar se o dropdown está presente
        if 'userDropdown' in html_content or 'dropdown' in html_content:
            print("   ✓ Dropdown encontrado no HTML")
        else:
            print("   ✗ Dropdown NÃO encontrado no HTML")
        
        # 4. Verificar a sessão
        print("\n4. Verificando dados da sessão...")
        with client.session_transaction() as session:
            print(f"   Session data: {dict(session)}")
        
        print("\n" + "=" * 60)

if __name__ == '__main__':
    test_login_flow()
