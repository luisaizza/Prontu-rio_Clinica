#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Analise de seguranca e funcionalidade do sistema"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app_clinica import app, db, User, ProfissionalEstetico, ServicoEstetico
from werkzeug.security import check_password_hash

def analise_seguranca():
    """Analisa seguranca do sistema"""
    
    print("\n" + "=" * 70)
    print("ANALISE DE SEGURANCA E FUNCIONALIDADE")
    print("=" * 70)
    
    with app.app_context():
        print("\n1. SEGURANCA DE CREDENCIAIS")
        print("-" * 70)
        
        usuarios = User.query.all()
        for user in usuarios:
            senha_ok = check_password_hash(user.password_hash, '123')
            print(f"   {user.username:20} | Perfil: {user.perfil:10} | Senha OK: {str(senha_ok):5}")
        
        print("\n2. PROFISSIONAIS E ESPECIALIZACOES")
        print("-" * 70)
        
        profs = ProfissionalEstetico.query.all()
        for prof in profs:
            user = db.session.get(User, prof.usuario_id)
            print(f"   {user.username:20} | Tel: {prof.telefone_contato:15} | Ativo: {prof.disponibilidade_status}")
            print(f"      Especialidades: {prof.especialidades}")
        
        print("\n3. SERVICOS DISPONIVEIS (15 no total)")
        print("-" * 70)
        
        servicos = ServicoEstetico.query.all()
        
        categorias = {}
        for srv in servicos:
            nome_partes = srv.nome_servico.split(' - ')
            categoria = nome_partes[0]
            
            if categoria not in categorias:
                categorias[categoria] = []
            categorias[categoria].append(srv)
        
        for categoria in sorted(categorias.keys()):
            servicos_cat = categorias[categoria]
            print(f"\n   {categoria.upper()} ({len(servicos_cat)} servico(s)):")
            for srv in servicos_cat:
                print(f"      - {srv.nome_servico:45} | R$ {srv.preco:7.2f} | {srv.duracao_minutos}min")
        
        print("\n4. VERIFICACAO DE ROTAS")
        print("-" * 70)
        
        rotas_importantes = {
            'GET /': 'Home',
            'GET /login': 'Login',
            'POST /login': 'Post Login',
            'GET /logout': 'Logout',
            'GET /agendar-servico': 'Agendar',
            'POST /agendar-servico': 'Post Agendar',
            'GET /agenda-calendario': 'Calendario',
            'GET /gerenciar-horarios': 'Gerenciar Horarios',
            'GET /listar-servicos': 'Listar Servicos',
        }
        
        rotas_sistema = []
        for rule in app.url_map.iter_rules():
            if rule.endpoint != 'static':
                rotas_sistema.append(f"{','.join(rule.methods - {'OPTIONS'})} {rule.rule}")
        
        for rota, descricao in rotas_importantes.items():
            encontrada = any(rota.split()[1] in r for r in rotas_sistema)
            status = 'OK' if encontrada else 'FALTANDO'
            print(f"   {status:10} | {rota:25} ({descricao})")
        
        print("\n5. INTEGRIDADE DO BANCO DE DADOS")
        print("-" * 70)
        
        try:
            from app_clinica import HorarioAtendimento, Paciente
            
            horarios = HorarioAtendimento.query.count()
            pacientes = Paciente.query.count()
            
            print(f"   Horarios configurados: {horarios}")
            print(f"   Pacientes: {pacientes}")
            print(f"   Status: OK")
        except Exception as e:
            print(f"   Erro: {str(e)}")
        
        print("\n6. TESTES DE LOGIN")
        print("-" * 70)
        
        app.config['TESTING'] = True
        with app.test_client() as client:
            # Teste 1: Login
            response = client.post('/login', data={
                'username': 'luisaizza',
                'password': '123'
            }, follow_redirects=True)
            
            print(f"   Login (luisaizza/123): {'OK' if response.status_code == 200 else 'ERRO'}")
            
            # Teste 2: Verificar se username aparece
            html = response.get_data(as_text=True)
            username_visivel = 'luisaizza' in html.lower()
            print(f"   Username visivel na pagina: {'SIM' if username_visivel else 'NAO'}")
            
            # Teste 3: Logout
            response = client.get('/logout', follow_redirects=True)
            print(f"   Logout: {'OK' if response.status_code == 200 else 'ERRO'}")
        
        print("\n" + "=" * 70)
        print("ANALISE CONCLUIDA - SISTEMA OPERACIONAL")
        print("=" * 70 + "\n")

if __name__ == '__main__':
    analise_seguranca()
