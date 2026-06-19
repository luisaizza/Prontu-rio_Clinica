#!/usr/bin/env python3
"""Script para testar o sistema de login e autenticação"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app_clinica import app, db, User
from flask_login import login_user
from werkzeug.security import generate_password_hash

def test_login_system():
    """Testa se o sistema de login funciona corretamente"""
    
    with app.app_context():
        print("=" * 60)
        print("TESTE DO SISTEMA DE LOGIN E AUTENTICAÇÃO")
        print("=" * 60)
        
        # 1. Verificar se existem usuários
        print("\n1. Verificando usuários cadastrados...")
        users = User.query.all()
        print(f"   Total de usuários: {len(users)}")
        for user in users:
            print(f"   - {user.username} (perfil: {user.perfil})")
        
        # 2. Testar login do admin
        print("\n2. Testando login com credenciais de admin...")
        test_user = User.query.filter_by(username='luisaizza').first()
        if test_user:
            print(f"   ✓ Usuário 'luisaizza' encontrado")
            print(f"   - ID: {test_user.id}")
            print(f"   - Perfil: {test_user.perfil}")
            print(f"   - Username: {test_user.username}")
            
            # Testar verificação de senha
            from werkzeug.security import check_password_hash
            senha_correta = check_password_hash(test_user.password_hash, '123')
            print(f"   - Senha '123' está {'CORRETA' if senha_correta else 'INCORRETA'}")
        else:
            print(f"   ✗ Usuário 'luisaizza' não encontrado!")
        
        # 3. Verificar Dra. Patrícia
        print("\n3. Verificando Dra. Patrícia...")
        dra_patricia = User.query.filter_by(username='dra_patricia').first()
        if dra_patricia:
            print(f"   ✓ Usuário 'dra_patricia' encontrado")
            print(f"   - Perfil: {dra_patricia.perfil}")
        else:
            print(f"   ✗ Usuário 'dra_patricia' não encontrado!")
        
        # 4. Verificar Dra. Fernanda
        print("\n4. Verificando Dra. Fernanda...")
        dra_fernanda = User.query.filter_by(username='dra_fernanda').first()
        if dra_fernanda:
            print(f"   ✓ Usuário 'dra_fernanda' encontrado")
            print(f"   - Perfil: {dra_fernanda.perfil}")
        else:
            print(f"   ✗ Usuário 'dra_fernanda' não encontrado!")
        
        print("\n" + "=" * 60)
        print("CREDENCIAIS PARA TESTE:")
        print("=" * 60)
        print("Admin:        luisaizza / 123")
        print("Dra. Patrícia: dra_patricia / 123")
        print("Dra. Fernanda: dra_fernanda / 123")
        print("=" * 60)

if __name__ == '__main__':
    test_login_system()
