# ⚡ GUIA RÁPIDO DE INÍCIO

## 🚀 Inicie em 5 Minutos

### 1. Preparar Ambiente
```powershell
# Criar ambiente virtual
python -m venv .venv

# Ativar
.\.venv\Scripts\Activate.ps1

# Instalar dependências
pip install -r requirements.txt
```

### 2. Iniciar Aplicação
```powershell
python app_clinica.py
```

Você verá:
```
✓ Usuário 'luisaizza' criado como ADMINISTRADOR!
  - Usuário: luisaizza
  - Senha: 123
  - Perfil: ADMINISTRADOR

 * Running on http://127.0.0.1:5000
```

### 3. Acessar Sistema
- Abra navegador: `http://127.0.0.1:5000`
- Clique em "Login"
- Usuario: `luisaizza`
- Senha: `123`

---

## 📋 Primeiro Uso (Checklist)

- [ ] Login com usuário padrão
- [ ] Mudar senha do admin
- [ ] Criar usuário de secretária
- [ ] Criar usuário de esteta
- [ ] Cadastrar pacientes de teste
- [ ] Registrar atendimento de teste
- [ ] Testar busca de pacientes
- [ ] Testar upload de foto

---

## 👥 Criar Novos Usuários

### Passo 1: Login como Admin
- Use `luisaizza` / `123`

### Passo 2: Ir para Gerenciar Usuários
- Clique em "Usuários" na barra de navegação

### Passo 3: Criar Novo Usuário
- Clique em "+ Novo Usuário"
- Preencha:
  - Nome: `joao_secretaria`
  - Senha: senha forte
  - Perfil: **Secretaria**
- Clique em "Criar Conta"

### Perfis Disponíveis
- **Admin**: Controla tudo
- **Secretaria**: Agenda consultas
- **Esteta**: Atende e registra procedimentos

---

## 📝 Usar o Sistema

### Cadastrar Paciente
1. Clique em "+ Novo Paciente"
2. Preencha dados básicos
3. Clique em "Salvar Paciente"

### Registrar Atendimento
1. Acesse paciente
2. Preencha "Procedimentos" (ex: "Limpeza, Aplicação")
3. Adicione anotações
4. Carregue fotos (opcional)
5. Clique em "Salvar Atendimento"

### Buscar Paciente
1. Na página inicial
2. Digite nome na busca
3. Clique em "Buscar"

---

## ⚙️ Configurações Importantes

### Mudar Senha
1. Clique no menu do usuário (canto superior direito)
2. Clique em "Sair"
3. Faça login novamente com nova senha

### Pasta de Uploads
- Localização: `uploads_clinica/`
- Tamanho máximo: 5MB por arquivo
- Formatos: JPG, JPEG, PNG

### Banco de Dados
- Localização: `instance/clinica.db`
- Tipo: SQLite
- Fazer backup periodicamente!

---

## 🔑 Variáveis de Ambiente (Opcional)

Crie `.env` para configurações personalizadas:

```env
SECRET_KEY=sua-chave-aqui
FLASK_ENV=development
FLASK_DEBUG=True
```

---

## 📱 Compatibilidade

- ✅ Windows (PowerShell)
- ✅ Linux (Bash)
- ✅ macOS (Bash)
- ✅ Navegadores: Chrome, Firefox, Safari, Edge

---

## 🆘 Problemas Comuns

### Erro: "Porta 5000 em uso"
```powershell
# Usar outra porta
$env:FLASK_PORT="5001"
python app_clinica.py
```

### Erro: "Module not found"
```powershell
# Reinstalar dependências
pip install -r requirements.txt --force-reinstall
```

### Banco não foi criado
```powershell
# Remover e deixar recriar
Remove-Item -Path "instance\clinica.db" -ErrorAction SilentlyContinue
python app_clinica.py
```

---

## 📞 Precisa de Ajuda?

Consulte:
- 📖 `README.md` - Documentação completa
- 🚀 `DEPLOYMENT.md` - Guia de produção
- 📝 `MELHORIAS_APLICADAS.md` - O que foi feito
- 📋 `CHANGELOG.md` - Histórico de versões

---

## ✨ Próximas Ações Recomendadas

1. **Imediato**: Alterar senha do admin
2. **Hoje**: Criar usuários para sua equipe
3. **Esta semana**: Cadastrar pacientes
4. **Próximas**: Treinar usuários
5. **Mensal**: Fazer backups

---

**Bem-vindo ao Prontuário Clínico! 🎉**

Versão: 1.0.0  
Data: Novembro 2025
