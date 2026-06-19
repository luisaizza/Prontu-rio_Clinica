# 🏥 Prontuário Clínico - Agenda Estética v2.0

Sistema completo de gerenciamento de clínica com **agenda visual em calendário** e **horários configuráveis pelo painel administrativo**.

---

## 🚀 Início Rápido

### 1. **Instalar Dependências**

```bash
pip install -r requirements.txt
```

### 2. **Iniciar a Aplicação**

```bash
python app_clinica.py
```

Você verá:
```
✓ Banco de dados criado/verificado
✓ Profissionais já cadastradas no sistema!
✓ Running on http://127.0.0.1:5000
```

### 3. **Acessar o Sistema**

Abra no navegador: **http://127.0.0.1:5000**

---

## 👥 Credenciais Padrão

| Usuário | Senha | Perfil | Acesso |
|---------|-------|--------|--------|
| **luisaizza** | 123 | 🔐 ADMIN | Total |
| **sarah** | 123 | 👩‍⚕️ ESTETICISTA | Agendar, Ver Agenda |
| **cidinha** | 123 | 👩‍⚕️ ESTETICISTA | Agendar, Ver Agenda |

---

## ✨ Principais Funcionalidades

### 📅 Agenda em Calendário
- Visualização mensal completa
- Navegação entre meses
- Filtro por profissional
- Status visual com cores
- Clique no dia para ver detalhes

### ⚙️ Configurar Horários (SEM CÓDIGO!)
- Menu → Admin → Gerenciar Profissionais
- Clique em "Horários"
- Adicione novo horário por dia da semana
- Defina início, fim e intervalo
- Ative/Desative quando necessário

### 📝 Agendamento Flexível
- Agendar para pacientes existentes
- Criar novo paciente + agendar (em um fluxo)
- Validações automáticas
- Horários carregados dinamicamente

---

## 📖 Documentação Completa

| Arquivo | Descrição |
|---------|-----------|
| [SISTEMA_AGENDAMENTO_NOVO.md](SISTEMA_AGENDAMENTO_NOVO.md) | Documentação técnica completa |
| [GUIA_TESTES_AGENDAMENTO.md](GUIA_TESTES_AGENDAMENTO.md) | 10 testes passo-a-passo |
| [RESUMO_EXECUTIVO.md](RESUMO_EXECUTIVO.md) | Visão geral executiva |

---

## 🎯 Fluxo Típico

### Para Agendar um Serviço:

```
1. Home (Pacientes Cadastrados)
   ↓
2. Clique "Novo Agendamento"
   ↓
3. Escolha:
   • Para Paciente Existente → Busque o paciente
   • Criar Novo Paciente e Agendar → Preencha dados
   ↓
4. Complete o agendamento:
   • Selecione profissional (SARAH ou CIDINHA)
   • Selecione serviço
   • Escolha data (calendário)
   • Sistema carrega horários disponíveis
   ↓
5. Confirme
   ✓ Agendamento criado!
```

### Para Configurar Disponibilidade:

```
1. Admin → Menu Admin
   ↓
2. Gerenciar Profissionais
   ↓
3. Clique "Horários" de um profissional
   ↓
4. Preencha formulário:
   • Dia da semana
   • Hora de início
   • Hora de término
   • Intervalo (15, 30, 45 min ou 1h)
   ↓
5. Clique "Adicionar Horário"
   ✓ Configurado e pronto para usar!
```

---

## 📊 Estrutura do Projeto

```
Prontuário_Clinica/
├── app_clinica.py                 # Aplicação principal
├── requirements.txt               # Dependências
├── base_clinica.html              # Template base (navbar, footer)
├── home_clinica.html              # Lista de pacientes
├── agenda_calendario.html         # Novo: Calendário visual
├── agendar_servico.html           # Formulário de agendamento
├── gerenciar_horarios_prof.html   # Novo: Gerenciar horários
├── novo_paciente.html             # Cadastro de pacientes
├── instance/
│   └── clinica.db                 # Banco de dados SQLite
├── uploads_clinica/               # Arquivos de upload
├── static/                        # CSS, JS, imagens
└── [Documentação]
    ├── SISTEMA_AGENDAMENTO_NOVO.md
    ├── GUIA_TESTES_AGENDAMENTO.md
    ├── RESUMO_EXECUTIVO.md
    └── ... (outros arquivos)
```

---

## 🔧 Tecnologias Utilizadas

- **Backend:** Flask 3.0.2
- **Banco de Dados:** SQLite
- **ORM:** SQLAlchemy 2.0+
- **Autenticação:** Flask-Login
- **Frontend:** Bootstrap 5.3
- **JavaScript:** Vanilla JS + AJAX

---

## 🎨 Recursos Visuais

### Calendário
- Navegação mensal
- Agendamentos coloridos por status
- Filtro por profissional
- Clique para ver detalhes

### Gerenciador de Horários
- Interface intuitiva em dois painéis
- Adicionar/Editar/Deletar horários
- Ativar/Desativar sem deletar
- Resumo de horários ativos

### Agendamento
- Formulário dinâmico
- Carregamento de horários em tempo real
- Validações automáticas
- Observações opcionais

---

## ⚡ Recursos Implementados

- ✅ Dois profissionais pré-cadastrados (SARAH e CIDINHA)
- ✅ Horários configuráveis pelo painel admin
- ✅ Agenda visual em calendário
- ✅ Agendamento automático após criar novo paciente
- ✅ Validações de conflitos e datas
- ✅ Carregamento dinâmico de horários
- ✅ Sistema de filtros
- ✅ Responsivo (desktop, tablet, mobile)

---

## 🐛 Resolução de Problemas

### Erro: "Banco de dados não encontrado"
```bash
# Apague o banco antigo e reinicie
del instance/clinica.db
python app_clinica.py
```

### Erro: "Porta 5000 já está em uso"
```bash
# Mude a porta no final de app_clinica.py
app.run(debug=True, port=5001)
```

### Calendário não aparece
```
1. Abra F12 (Developer Tools)
2. Vá para Console
3. Procure por erros de JavaScript
4. Recarregue a página (Ctrl+F5)
```

---

## 📞 Contato & Suporte

Para dúvidas, sugestões ou problemas:

1. Consulte a [documentação completa](SISTEMA_AGENDAMENTO_NOVO.md)
2. Veja os [testes de exemplo](GUIA_TESTES_AGENDAMENTO.md)
3. Revise o [resumo executivo](RESUMO_EXECUTIVO.md)

---

## 📝 Notas Importantes

⚠️ **Segurança:** Este é um ambiente de desenvolvimento. Para produção:
- Altere o `SECRET_KEY` em `app_clinica.py`
- Use um banco de dados mais robusto (PostgreSQL)
- Configure HTTPS
- Use um servidor WSGI (Gunicorn, uWSGI)

---

## 🎓 Próximas Melhorias

- [ ] Notificações por email/SMS
- [ ] Relatórios de ocupação
- [ ] Integração com pagamento
- [ ] App mobile
- [ ] Dark mode
- [ ] Backup automático

---

**Versão:** 2.0  
**Data:** 10 de Novembro de 2025  
**Status:** ✅ Pronto para usar!

---

### 🚀 Pronto? Comece por:

1. Faça login com `luisaizza / 123`
2. Vá para Admin → Gerenciar Profissionais
3. Configure os horários conforme necessário
4. Faça seu primeiro agendamento!

**Boa sorte!** 🎉
