#!/usr/bin/env python3
"""
Script de teste para verificar problemas no agendamento e visualização de pacientes
"""
import requests
import json
from datetime import datetime, timedelta

# Configurações
BASE_URL = "http://127.0.0.1:5000"

def test_login():
    """Testa o login na aplicação"""
    print("🔐 Testando login...")

    # Primeiro, precisamos fazer login
    session = requests.Session()

    # Acessa a página de login para obter o CSRF token
    response = session.get(f"{BASE_URL}/login")
    if response.status_code != 200:
        print(f"❌ Erro ao acessar página de login: {response.status_code}")
        return None

    # Como estamos usando Flask-WTF, vamos tentar fazer login diretamente
    login_data = {
        'username': 'admin',
        'password': 'admin123'
    }

    response = session.post(f"{BASE_URL}/login", data=login_data, allow_redirects=True)

    if 'Fazer Login' in response.text:
        print("❌ Login falhou - ainda na página de login")
        return None

    print("✅ Login realizado com sucesso")
    return session

def test_criar_paciente(session):
    """Testa a criação de um paciente"""
    print("👤 Testando criação de paciente...")

    # Acessa a página de criação de paciente
    response = session.get(f"{BASE_URL}/novo-paciente")
    if response.status_code != 200:
        print(f"❌ Erro ao acessar página de novo paciente: {response.status_code}")
        return None

    # Dados do paciente
    paciente_data = {
        'nome_completo': 'João Silva Teste',
        'cpf': '12345678901',
        'data_nascimento': '1990-01-01',
        'telefone': '(11) 99999-9999',
        'email': 'joao.teste@email.com',
        'historico_medico': 'Paciente de teste'
    }

    response = session.post(f"{BASE_URL}/novo-paciente", data=paciente_data, allow_redirects=True)

    if response.status_code != 200:
        print(f"❌ Erro ao criar paciente: {response.status_code}")
        return None

    # Tenta encontrar o ID do paciente na URL de redirecionamento
    if 'pacientes/' in response.url:
        paciente_id = response.url.split('pacientes/')[-1].split('?')[0]
        print(f"✅ Paciente criado com ID: {paciente_id}")
        return int(paciente_id)

    print("❌ Não foi possível obter o ID do paciente criado")
    return None

def test_visualizar_paciente(session, paciente_id):
    """Testa a visualização do prontuário do paciente"""
    print(f"📋 Testando visualização do paciente ID {paciente_id}...")

    response = session.get(f"{BASE_URL}/pacientes/{paciente_id}")

    if response.status_code != 200:
        print(f"❌ Erro ao visualizar paciente: {response.status_code}")
        print(f"Resposta: {response.text[:500]}...")
        return False

    if 'João Silva Teste' in response.text:
        print("✅ Página do paciente carregada com sucesso")
        return True
    else:
        print("❌ Nome do paciente não encontrado na página")
        return False

def test_agendar_servico(session, paciente_id):
    """Testa o agendamento de um serviço"""
    print(f"📅 Testando agendamento para paciente ID {paciente_id}...")

    # Acessa a página de agendamento
    response = session.get(f"{BASE_URL}/agendar-servico/{paciente_id}")
    if response.status_code != 200:
        print(f"❌ Erro ao acessar página de agendamento: {response.status_code}")
        return False

    # Dados do agendamento
    data_futura = (datetime.now() + timedelta(days=1)).strftime('%Y-%m-%d')
    agendamento_data = {
        'profissional_id': '1',  # Assume que existe um profissional com ID 1
        'servico_id': '1',       # Assume que existe um serviço com ID 1
        'data_agendamento': data_futura,
        'hora_agendamento': '09:00',
        'observacoes': 'Agendamento de teste'
    }

    response = session.post(f"{BASE_URL}/agendar-servico/{paciente_id}", data=agendamento_data, allow_redirects=True)

    if response.status_code != 200:
        print(f"❌ Erro ao agendar serviço: {response.status_code}")
        print(f"Resposta: {response.text[:500]}...")
        return False

    if 'sucesso' in response.text.lower():
        print("✅ Agendamento realizado com sucesso")
        return True
    else:
        print("❌ Agendamento falhou")
        print(f"Resposta contém: {'danger' in response.text and 'flash' in response.text}")
        return False

def main():
    """Função principal do teste"""
    print("🚀 Iniciando testes da aplicação clínica...")
    print("=" * 50)

    # Testa login
    session = test_login()
    if not session:
        print("❌ Testes interrompidos - falha no login")
        return

    # Testa criação de paciente
    paciente_id = test_criar_paciente(session)
    if not paciente_id:
        print("❌ Testes interrompidos - falha na criação do paciente")
        return

    # Testa visualização do paciente
    if not test_visualizar_paciente(session, paciente_id):
        print("❌ Problema na visualização do paciente")

    # Testa agendamento
    if not test_agendar_servico(session, paciente_id):
        print("❌ Problema no agendamento")

    print("=" * 50)
    print("🏁 Testes concluídos")

if __name__ == "__main__":
    main()