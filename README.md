# 📋 Prontuário Clínico - Sistema de Gerenciamento

Um sistema profissional e seguro para gerenciamento de prontuários clínicos com controle de acesso por perfil de usuário.

## 🎯 Características Principais

### ✅ Funcionalidades
- ✓ Gerenciamento completo de pacientes
- ✓ Registro de atendimentos com fotos antes/depois
- ✓ Anamnese clínica detalhada
- ✓ Exame físico completo
- ✓ Agendamentos de consultas
- ✓ Sistema de permissões por perfil
- ✓ Upload seguro de imagens
- ✓ Busca avançada de pacientes

### 👥 Perfis de Usuário

#### 👨‍💼 **Administrador (ADM)**
- Acesso total ao sistema
- Gerenciar usuários (criar, editar, deletar)
- Visualizar todos os dados
- Gerar relatórios

#### 📅 **Secretaria**
- Agendar consultas
- Gerenciar agendamentos
- Visualizar lista de pacientes

#### 💄 **Esteta**
- Gerenciar pacientes (criar e editar)
- Registrar atendimentos
- Preencher anamnese e exame físico
- Visualizar próprios registros

## 🚀 Instalação

### Pré-requisitos
- Python 3.8 ou superior
- pip (gerenciador de pacotes Python)

### Passo a passo

1. **Clone ou baixe o projeto**
   ```bash
   cd Prontuário_Clinica
   ```

2. **Crie um ambiente virtual** (recomendado)
   ```bash
   python -m venv .venv
   # Windows
   .\.venv\Scripts\Activate.ps1
   # Linux/Mac
   source .venv/bin/activate
   ```

3. **Instale as dependências**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure as variáveis de ambiente** (opcional)
   ```bash
   # Copie o arquivo de exemplo
   copy .env.example .env
   
   # Edite .env com seus valores
   ```

5. **Inicie a aplicação**
   ```bash
   python app_clinica.py
   ```

6. **Acesse no navegador**
   ```
   http://127.0.0.1:5000
   ```

## 🔐 Primeiro Acesso

Na primeira execução, o sistema criará automaticamente:
- Banco de dados SQLite
- Usuário administrador padrão

**Credenciais iniciais:**
- Usuário: `luisaizza`
- Senha: `123`
- Perfil: **Administrador**

⚠️ **IMPORTANTE:** Altere a senha do administrador assim que fizer login!

## 📁 Estrutura do Projeto

```
Prontuário_Clinica/
├── app_clinica.py              # Aplicação principal
├── config.py                   # Configurações
├── requirements.txt            # Dependências
├── .env.example               # Exemplo de variáveis de ambiente
├── README.md                  # Este arquivo
│
├── Templates HTML/
│   ├── base_clinica.html      # Template base
│   ├── login_clinica.html     # Tela de login
│   ├── registro_clinica.html  # Tela de registro
│   ├── home_clinica.html      # Lista de pacientes
│   ├── novo_paciente.html     # Novo paciente
│   ├── editar_paciente.html   # Editar paciente
│   ├── ver_paciente.html      # Detalhes do paciente
│   ├── nova_anamnese.html     # Nova anamnese
│   ├── gerenciar_usuarios.html # Gerenciar usuários
│   └── ...
│
├── static/                    # Arquivos estáticos (logo, CSS, JS)
├── uploads_clinica/           # Fotos de pacientes (geradas)
├── instance/                  # Banco de dados (gerado)
└── migrations/                # Migrações de banco (Alembic)
```

## 🔧 Configuração Avançada

### Variáveis de Ambiente

Crie um arquivo `.env` na raiz do projeto:

```env
# Chave secreta (mude em produção!)
SECRET_KEY=sua-chave-super-segura-aqui

# Ambiente
FLASK_ENV=development
FLASK_DEBUG=True

# Setup inicial
SETUP_ENABLED=0
SETUP_USERNAME=admin
SETUP_PASSWORD=senha-forte
```

### Mudando a Senha Padrão

Edite a linha abaixo em `app_clinica.py`:
```python
new_user = User(
    username='luisaizza',
    password_hash=generate_password_hash('123'),  # ← Altere aqui
    perfil='admin'
)
```

### Banco de Dados

O sistema usa **SQLite** por padrão. Para usar outro banco:
1. Instale o driver apropriado (ex: `pip install psycopg2` para PostgreSQL)
2. Altere `SQLALCHEMY_DATABASE_URI` em `config.py`

## 🛡️ Segurança

### Implementações de Segurança

✅ **Autenticação:**
- Senhas com hash criptografado (Werkzeug)
- Cookies HTTP-only
- Sessão com timeout automático

✅ **Autorização:**
- Controle de acesso por perfil
- Decoradores de permissão
- Proteção em rotas sensíveis

✅ **Upload de Arquivos:**
- Validação de tipo de arquivo
- Limite de tamanho (5MB)
- Nomes de arquivo aleatórios

✅ **Dados:**
- Validações no lado do servidor
- Proteção contra SQL Injection (SQLAlchemy ORM)
- Auto-escape de templates Jinja2

## 📱 Uso da Aplicação

### Como Adicionar um Paciente

1. Faça login na aplicação
2. Clique em "+ Novo Paciente"
3. Preencha os dados básicos
4. Clique em "Salvar Paciente"

### Como Registrar um Atendimento

1. Acesse a página de detalhes do paciente
2. Preencha "Procedimentos Realizados" (separados por vírgula)
3. Adicione anotações
4. Carregue fotos "Antes" e "Depois" (opcional)
5. Clique em "Salvar Atendimento"

### Como Gerenciar Usuários (ADM)

1. Clique em "Usuários" na navegação
2. Clique em "+ Novo Usuário"
3. Preencha username, senha e escolha o perfil
4. Clique em "Criar Conta"

Para alterar perfil de usuário existente:
1. Vá em "Usuários"
2. Clique em "Alterar Perfil"
3. Selecione o novo perfil

## 🐛 Troubleshooting

### Erro: "Unable to open database file"
- Certifique-se de que a pasta `instance/` existe
- Verifique permissões de escrita no diretório

### Erro: "No such column"
- Apague o banco: `Remove-Item -Path "instance\clinica.db"`
- A aplicação recriará com a estrutura correta

### Login não funciona
- Verifique se o usuário foi criado
- Confira se a senha está correta
- Limpe cookies do navegador

## 📊 Relatórios e Dados

Os dados são armazenados no SQLite. Para análises:

```python
from app_clinica import db, Paciente
pacientes = Paciente.query.all()
for p in pacientes:
    print(f"{p.nome_completo}: {len(p.atendimentos)} atendimentos")
```

## 🔄 Backup

### Fazer backup do banco de dados:
```bash
# Windows
copy instance\clinica.db instance\clinica_backup_$(date /T).db

# Linux/Mac
cp instance/clinica.db instance/clinica_backup_$(date +%Y%m%d_%H%M%S).db
```

## 📝 Logs

Os logs da aplicação são salvos automaticamente. Para ativar logs mais detalhados:

```python
logger.setLevel(logging.DEBUG)
```

## 🤝 Suporte e Contribuições

Para reportar bugs ou sugerir melhorias, entre em contato ou abra uma issue.

## 📄 Licença

Este projeto é fornecido como está para uso interno da clínica.

---

**Versão:** 1.0.0  
**Última atualização:** Novembro 2025  
**Compatibilidade:** Python 3.8+
