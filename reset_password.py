#!/usr/bin/env python3
"""Script para resetar a senha do usuario luisaizza"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app_clinica import app, db, User
from werkzeug.security import generate_password_hash

with app.app_context():
    # Encontrar ou criar o usuario luisaizza
    user = User.query.filter_by(username='luisaizza').first()
    
    if user:
        print(f"Encontrado usuario: {user.username} (ID: {user.id})")
        print(f"Perfil atual: {user.perfil}")
        
        # Resetar a senha
        user.password_hash = generate_password_hash('123')
        user.perfil = 'admin'  # Garantir que é admin
        db.session.commit()
        
        print(f"Senha resetada com sucesso!")
        print(f"Novas credenciais:")
        print(f"  Usuario: luisaizza")
        print(f"  Senha: 123")
        print(f"  Perfil: admin")
        
        # Testar
        from werkzeug.security import check_password_hash
        is_correct = check_password_hash(user.password_hash, '123')
        print(f"\nVerificacao: Senha correta? {is_correct}")
    else:
        print("Usuario nao encontrado! Criando...")
        admin_user = User(
            username='luisaizza',
            password_hash=generate_password_hash('123'),
            perfil='admin'
        )
        db.session.add(admin_user)
        db.session.commit()
        
        print("Usuario criado com sucesso!")
        print("  Usuario: luisaizza")
        print("  Senha: 123")
        print("  Perfil: admin")
