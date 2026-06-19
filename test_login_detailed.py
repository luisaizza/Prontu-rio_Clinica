#!/usr/bin/env python3
"""Script para testar o login com mais detalhes"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app_clinica import app, db, User
from flask import Flask
from werkzeug.security import check_password_hash

def test_detailed_login():
    """Testa o login com mais detalhes"""
    
    app.config['TESTING'] = True
    app.config['WTF_CSRF_ENABLED'] = False
    
    # Primeiro, verificar no app context se o usuário existe
    with app.app_context():
        print("=" * 70)
        print("TESTE DETALHADO DE LOGIN")
        print("=" * 70)
        
        # 1. Verificar usuário no banco
        print("\n1. Verificando usuário no banco de dados...")
        user = User.query.filter_by(username='luisaizza').first()
        if user:
            print(f"   ✓ Usuário 'luisaizza' encontrado")
            print(f"   - ID: {user.id}")
            print(f"   - Perfil: {user.perfil}")
            print(f"   - Hash de senha: {user.password_hash[:30]}...")
            
            # Testar senha
            is_password_correct = check_password_hash(user.password_hash, '123')
            print(f"   - Senha '123' correta: {is_password_correct}")
        else:
            print(f"   ✗ Usuário não encontrado!")
            return
    
    # Agora testar com client
    with app.test_client() as client:
        print("\n2. Testando login com test client...")
        
        # Fazer login
        response = client.post('/login', data={
            'username': 'luisaizza',
            'password': '123'
        }, follow_redirects=False)  # Não seguir redirect
        
        print(f"   Status do POST /login: {response.status_code}")
        print(f"   Redirect Location: {response.headers.get('Location', 'Nenhum')}")
        
        # Seguir o redirect manualmente
        if response.status_code == 302:
            location = response.headers.get('Location')
            print(f"\n   Seguindo redirect para: {location}")
            response = client.get(location)
            print(f"   Status da página redirecionada: {response.status_code}")
        
        # Verificar cookies
        print("\n3. Verificando cookies da sessão...")
        print(f"   Cookies: {response.headers.getlist('Set-Cookie')}")
        
        # Agora tentar acessar a página protegida
        print("\n4. Acessando página protegida (/) após login...")
        response = client.get('/')
        print(f"   Status: {response.status_code}")
        html = response.get_data(as_text=True)
        
        if 'luisaizza' in html:
            print(f"   ✓ Username 'luisaizza' encontrado no HTML!")
        else:
            print(f"   ✗ Username 'luisaizza' NÃO encontrado no HTML")
        
        if 'Por favor, faça login' in html:
            print(f"   ✗ Ainda mostra mensagem de login requerido")
        else:
            print(f"   ✓ Não mostra mensagem de login requerido")
        
        # Verificar com remember_me
        print("\n5. Testando login com follow_redirects=True...")
        response = client.post('/login', data={
            'username': 'luisaizza',
            'password': '123'
        }, follow_redirects=True)
        
        print(f"   Status final: {response.status_code}")
        print(f"   URL final: {response.request.path}")
        html = response.get_data(as_text=True)
        
        if 'luisaizza' in html:
            print(f"   ✓ Username 'luisaizza' encontrado no HTML!")
        else:
            print(f"   ✗ Username 'luisaizza' NÃO encontrado no HTML")
        
        print("\n" + "=" * 70)

if __name__ == '__main__':
    test_detailed_login()
