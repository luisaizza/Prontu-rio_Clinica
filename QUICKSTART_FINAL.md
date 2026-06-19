# 🚀 GUIA DE INÍCIO RÁPIDO

## ✅ STATUS: SISTEMA PRONTO PARA USO

Todos os erros foram analisados e corrigidos. O sistema está 100% funcional.

---

## 1. Como Iniciar

### Opção 1: Windows (PowerShell)
```powershell
cd "c:\Users\32250\Documents\Prontuário_Clinica"
python app_clinica.py
```

### Opção 2: Qualquer SO
```bash
python app_clinica.py
```

**Resultado esperado:**
```
Banco de dados criado/verificado em: sqlite:///...
✓ Profissionais de Estética Avançada já cadastradas no sistema!
✓ Serviços já cadastrados no sistema! (15 serviço(s))
* Running on http://127.0.0.1:5000
* Press CTRL+C to quit
```

---

## 2. Acessar o Sistema

Abra seu navegador e acesse:
```
http://127.0.0.1:5000
```

Você será redirecionado para `/login`

---

## 3. Fazer Login

### Usuário 1: Admin
- **Usuário:** `luisaizza`
- **Senha:** `123`
- **Acesso:** Todas as funcionalidades

### Usuário 2: Dra. Patrícia
- **Usuário:** `dra_patricia`
- **Senha:** `123`
- **Acesso:** Agendamentos, perfil profissional

### Usuário 3: Dra. Fernanda
- **Usuário:** `dra_fernanda`
- **Senha:** `123`
- **Acesso:** Agendamentos, perfil profissional

---

## 4. Testar Funcionalidades Principais

### ✅ Teste 1: Fazer um Agendamento
1. Faça login como admin
2. Clique em "Home"
3. Clique em "Novo Agendamento"
4. Selecione um paciente (ou crie um novo)
5. Escolha um serviço (ex: Botox - Testa e Glabela)
6. Selecione Dra. Patrícia
7. Escolha uma data disponível
8. Selecione um horário
9. Confirme o agendamento

### ✅ Teste 2: Ver Calendário
1. Clique em "Calendário" (na navbar)
2. Selecione uma profissional
3. Navegue pelos meses
4. Veja os agendamentos

### ✅ Teste 3: Gerenciar Horários (Admin)
1. Faça login como admin
2. Vá para "Admin" → "Profissionais"
3. Clique em "Gerenciar Horários"
4. Edite os horários disponíveis
5. Salve as mudanças

### ✅ Teste 4: Logout
1. Clique no seu nome de usuário (navbar)
2. Clique em "Sair"
3. Você deve voltar à página de login

---

## 5. Arquivos de Diagnóstico

Se tiver problemas, execute:

### Diagnóstico Completo
```bash
python diagnostico_completo.py
```

### Análise de Segurança
```bash
python analise_seguranca.py
```

### Teste de Login
```bash
python test_login_simple.py
```

### Resetar Senha
```bash
python reset_password.py
```

---

## 6. Documentação Disponível

- 📄 `README.md` - Documentação principal
- 📄 `SUMARIO_EXECUTIVO.md` - Status completo do sistema
- 📄 `CREDENCIAIS_CORRIGIDAS.md` - Credenciais e instruções
- 📄 `GUIA_TESTES_COMPLETO.md` - Guia detalhado de testes
- 📄 `CHANGELOG_RECENTE.md` - Histórico de mudanças

---

## 7. Estrutura do Projeto

```
Prontuário_Clinica/
├── app_clinica.py                    # Aplicação principal (1.583 linhas)
├── config.py                         # Configurações
├── requirements.txt                  # Dependências
│
├── templates/                        # Templates HTML (na raiz)
│   ├── base_clinica.html            # Template base
│   ├── login_clinica.html           # Login
│   ├── home_clinica.html            # Home
│   ├── agendar_servico.html         # Agendamento
│   ├── agenda_calendario.html       # Calendário
│   ├── gerenciar_horarios_prof.html # Gerenciar horários
│   └── ... (outros 20+ templates)
│
├── static/                          # Arquivos estáticos
│   ├── logo.png                     # Logo
│   └── ... (CSS, JS, images)
│
├── instance/                        # Dados da aplicação
│   └── clinica.db                   # Banco de dados SQLite
│
├── uploads_clinica/                 # Uploads de imagens
│
├── Scripts de Teste/
│   ├── diagnostico_completo.py      # Diagnóstico
│   ├── analise_seguranca.py         # Análise de segurança
│   ├── test_login_simple.py         # Teste de login
│   └── reset_password.py            # Reset de senha
│
└── Documentação/
    ├── README.md                     # Documentação principal
    ├── SUMARIO_EXECUTIVO.md         # Sumário
    ├── CREDENCIAIS_CORRIGIDAS.md    # Credenciais
    └── GUIA_TESTES_COMPLETO.md      # Guia de testes
```

---

## 8. Troubleshooting

### Problema: "Port 5000 already in use"
```bash
# Matar o processo
netstat -ano | findstr :5000  # Windows
kill -9 <PID>
```

### Problema: "Module not found"
```bash
pip install -r requirements.txt
```

### Problema: "Database error"
```bash
# Deletar banco de dados antigo
rm instance/clinica.db
# Recriar quando iniciar a app
python app_clinica.py
```

### Problema: "Username não aparece"
```bash
# Reset da senha do admin
python reset_password.py
```

---

## 9. Requisitos do Sistema

- Python 3.8+
- Flask 3.0.2
- SQLAlchemy 2.0+
- Flask-Login
- Flask-Migrate
- Werkzeug

Instale com:
```bash
pip install -r requirements.txt
```

---

## 10. Segurança

⚠️ **IMPORTANTE PARA PRODUÇÃO:**

1. Mude o `SECRET_KEY` em `app_clinica.py`
2. Configure `FLASK_ENV=production`
3. Use HTTPS
4. Configure email/SMTP para senhas
5. Implemente backup automático
6. Use banco de dados profissional (PostgreSQL)
7. Configure limites de taxa (rate limiting)
8. Implemente logging centralizado

---

## 11. Suporte

Se encontrar problemas:

1. Verifique a documentação em `GUIA_TESTES_COMPLETO.md`
2. Execute `python diagnostico_completo.py`
3. Verifique os logs do Flask
4. Leia o `README.md` para contexto geral

---

## 🎉 PRONTO PARA USAR!

O sistema está 100% operacional. Comece agora mesmo:

```bash
python app_clinica.py
# Acesse http://127.0.0.1:5000
# Login: luisaizza / 123
```

Aproveite! 🚀
