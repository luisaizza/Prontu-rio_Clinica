#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Script de diagnostico completo do sistema"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app_clinica import app, db, User, ProfissionalEstetico, ServicoEstetico, Paciente, Atendimento, Anamnese, ExameFisico, AgendamentoServico, HorarioAtendimento

def diagnostico():
    with app.app_context():
        print("=" * 70)
        print("DIAGNOSTICO COMPLETO DO SISTEMA")
        print("=" * 70)
        
        print("\n1. VERIFICANDO DATABASE")
        print("-" * 70)
        
        try:
            usuarios = User.query.count()
            profissionais = ProfissionalEstetico.query.count()
            servicos = ServicoEstetico.query.count()
            pacientes = Paciente.query.count()
            atendimentos = Atendimento.query.count()
            agendamentos = AgendamentoServico.query.count()
            
            print(f"   Usuarios: {usuarios}")
            print(f"   Profissionais Esteticos: {profissionais}")
            print(f"   Servicos Esteticos: {servicos}")
            print(f"   Pacientes: {pacientes}")
            print(f"   Atendimentos: {atendimentos}")
            print(f"   Agendamentos: {agendamentos}")
        except Exception as e:
            print(f"   ERRO ao contar registros: {str(e)}")
        
        print("\n2. VERIFICANDO CREDENCIAIS")
        print("-" * 70)
        
        try:
            admin = User.query.filter_by(username='luisaizza').first()
            if admin:
                print(f"   Admin (luisaizza): ENCONTRADO")
                print(f"     - ID: {admin.id}")
                print(f"     - Perfil: {admin.perfil}")
                
                from werkzeug.security import check_password_hash
                senha_ok = check_password_hash(admin.password_hash, '123')
                print(f"     - Senha '123' funciona: {'SIM' if senha_ok else 'NAO'}")
            else:
                print(f"   Admin (luisaizza): NAO ENCONTRADO")
            
            dra_p = User.query.filter_by(username='dra_patricia').first()
            print(f"   Dra Patricia: {'ENCONTRADA' if dra_p else 'NAO ENCONTRADA'}")
            
            dra_f = User.query.filter_by(username='dra_fernanda').first()
            print(f"   Dra Fernanda: {'ENCONTRADA' if dra_f else 'NAO ENCONTRADA'}")
            
        except Exception as e:
            print(f"   ERRO ao verificar usuarios: {str(e)}")
        
        print("\n3. VERIFICANDO SERVICOS")
        print("-" * 70)
        
        try:
            servicos_list = ServicoEstetico.query.all()
            print(f"   Total de servicos: {len(servicos_list)}")
            print(f"\n   Primeiros 5 servicos:")
            for i, s in enumerate(servicos_list[:5], 1):
                print(f"   {i}. {s.nome_servico} - R$ {s.preco:.2f}")
            
            if len(servicos_list) > 5:
                print(f"   ... e mais {len(servicos_list) - 5} servicos")
        except Exception as e:
            print(f"   ERRO ao listar servicos: {str(e)}")
        
        print("\n4. VERIFICANDO HORARIOS")
        print("-" * 70)
        
        try:
            horarios = HorarioAtendimento.query.all()
            print(f"   Total de horarios: {len(horarios)}")
            
            if dra_p:
                horarios_p = HorarioAtendimento.query.filter_by(profissional_id=ProfissionalEstetico.query.filter_by(usuario_id=dra_p.id).first().id if ProfissionalEstetico.query.filter_by(usuario_id=dra_p.id).first() else None).all()
                print(f"   Horarios de Dra Patricia: {len(horarios_p)}")
            
            if dra_f:
                horarios_f = HorarioAtendimento.query.filter_by(profissional_id=ProfissionalEstetico.query.filter_by(usuario_id=dra_f.id).first().id if ProfissionalEstetico.query.filter_by(usuario_id=dra_f.id).first() else None).all()
                print(f"   Horarios de Dra Fernanda: {len(horarios_f)}")
        except Exception as e:
            print(f"   ERRO ao verificar horarios: {str(e)}")
        
        print("\n5. VERIFICANDO ROTAS")
        print("-" * 70)
        
        try:
            rotas = [str(rule) for rule in app.url_map.iter_rules()]
            print(f"   Total de rotas: {len(rotas)}")
            print(f"\n   Rotas principais:")
            main_routes = ['/login', '/home', '/', '/agendar-servico', '/agenda-calendario', '/gerenciar-horarios']
            for route in main_routes:
                found = any(route in r for r in rotas)
                status = 'OK' if found else 'FALTANDO'
                print(f"     {route}: {status}")
        except Exception as e:
            print(f"   ERRO ao verificar rotas: {str(e)}")
        
        print("\n6. VERIFICANDO TEMPLATES")
        print("-" * 70)
        
        try:
            templates_path = os.path.join(os.path.dirname(__file__), 'Templates HTML')
            if os.path.exists(templates_path):
                templates = os.listdir(templates_path)
                print(f"   Templates encontrados: {len(templates)}")
                critical_templates = ['base_clinica.html', 'login_clinica.html', 'home_clinica.html', 'agendar_servico.html']
                for tmpl in critical_templates:
                    found = tmpl in templates
                    status = 'OK' if found else 'FALTANDO'
                    print(f"     {tmpl}: {status}")
            else:
                print(f"   Pasta templates nao encontrada!")
        except Exception as e:
            print(f"   ERRO ao verificar templates: {str(e)}")
        
        print("\n" + "=" * 70)
        print("DIAGNOSTICO CONCLUIDO")
        print("=" * 70)

if __name__ == '__main__':
    diagnostico()
