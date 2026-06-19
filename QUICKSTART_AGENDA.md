# 🚀 Quick Start - Agenda Estética (5 Minutos)

## 1️⃣ Iniciar a Aplicação

```bash
cd "c:\Users\32250\Documents\Prontuário_Clinica"
python app_clinica.py
```

Acesse: **http://localhost:5000**

---

## 2️⃣ Login

```
Usuário: luisaizza
Senha: 123
```

> ⚠️ **IMPORTANTE:** Altere esta senha após o primeiro login!

---

## 3️⃣ Setup em 3 Cliques (Admin)

### ✅ Criar um Serviço (30 segundos)

```
Menu: Admin → Gerenciar Serviços → Novo Serviço
```

Preencha:
- **Nome:** Limpeza de Pele
- **Duração:** 60 (minutos)
- **Preço:** 150.00

Clique: **Criar Serviço**

---

### ✅ Configurar Horários do Profissional (1 minuto)

```
Menu: Admin → Gerenciar Profissionais
```

Selecione um profissional → Clique **Horários**

Adicione:
- **Dia:** Segunda-feira
- **Início:** 08:00
- **Fim:** 18:00
- **Intervalo:** 30 minutos

Clique: **Salvar Horário**

Repita para outros dias (Ter, Qua, Qui, Sex)

---

### ✅ Agendar Primeiro Cliente (2 minutos)

```
Menu: Agenda → Pacientes → Ver Paciente → Agendar Serviço
```

**OU**

```
Menu: Agenda → [botão azul "Novo Agendamento"]
```

Selecione:
1. **Serviço:** Limpeza de Pele
2. **Profissional:** (nome do profissional)
3. **Data:** Hoje ou amanhã
4. **Hora:** Aparece automaticamente

Clique: **Confirmar Agendamento**

✅ **Pronto! Seu primeiro agendamento está criado!**

---

## 4️⃣ Próximas Ações

### 👤 Ver Agenda Completa
```
Menu: Agenda
```
- Lista todos os agendamentos dos próximos 30 dias
- Mostra status de cada um
- Permite confirmar/cancelar

### 📅 Minha Agenda Pessoal
```
Menu: Minha Agenda
```
- Seu próprio histórico
- Filtrar por status
- Ver detalhes de cada agendamento

### ⚙️ Gerenciar Mais Serviços
```
Menu: Admin → Gerenciar Serviços
```
- Adicione mais 4-5 serviços comuns
- Ex: Microdermoabrasão, Massagem, Drenagem Linfática

---

## 🎯 Fluxo Completo em Uma Sessão

```
1. Login como admin (luisaizza/123)
   ↓
2. Criar 3 serviços
   ↓
3. Ir para listar profissionais
   ↓
4. Clique em "Horários" para cada profissional
   ↓
5. Configure seg-sex (8-18, intervalo 30 min)
   ↓
6. Vá para pacientes e selecione um
   ↓
7. Clique "Agendar Serviço"
   ↓
8. Selecione serviço, profissional, data/hora
   ↓
9. Confirme
   ↓
10. Vá para Menu: Agenda e veja seu agendamento
```

---

## 💡 Dicas Rápidas

### Carregar Horários Dinamicamente
Ao selecionar profissional e data em "Agendar Serviço", os horários livres aparecem automaticamente:

```
1. Seleciona Profissional ✓
2. Seleciona Data ✓
3. Campo "Hora" habilita-se automaticamente
4. Mostra apenas horários livres
```

### Validações Automáticas
❌ Não permite:
- Data/hora no passado
- Dois agendamentos no mesmo horário
- Agendar quando profissional está de férias

✅ Sempre mostra:
- Preço do serviço
- Duração do procedimento
- Nome do profissional
- Data/hora confirmadas antes de salvar

---

## 📱 Navegação Rápida

| Menu | Atalho | Para Quem |
|------|--------|----------|
| **Agenda** | `Menu: Agenda` | Secretária |
| **Minha Agenda** | `Menu: Minha Agenda` | Profissional |
| **Agendar** | Paciente → Botão Azul | Secretária |
| **Admin > Serviços** | `Menu: Admin → Serviços` | Admin |
| **Admin > Profissionais** | `Menu: Admin → Profissionais` | Admin |
| **Admin > Horários** | `Profissional → Horários` | Admin |

---

## ⚡ Atalhos de Teclado

| Tecla | Ação |
|-------|------|
| `Tab` | Navegar entre campos |
| `Enter` | Submeter formulário |
| `Esc` | Fechar modal |
| `Ctrl+L` | Logout (depois de confirmar) |

---

## 🎓 Exemplo de Agendamento Real

**Cenário:** Maria (secretária) agenda cliente Ana para limpeza com profissional Fernanda

### Passo 1: Acessar Agendamento
```
Menu → Agenda → Pacientes
```

### Passo 2: Selecionar Cliente
Clique em "Ana Silva" → Botão "Agendar Serviço"

### Passo 3: Preencher Formulário
```
Serviço:      Limpeza de Pele
Profissional: Fernanda
Data:         15/11/2025
Hora:         14:00 (aparece automaticamente)
Observações:  Pele sensível
```

### Passo 4: Confirmar
Clique botão azul "Confirmar Agendamento"

### Resultado
✅ Agendamento criado!  
Status: **AGENDADO** (azul)  
Data: 15/11/2025 às 14:00

### Dia do Agendamento
Volta para Menu: Agenda
- Encontra o agendamento de Ana
- Clica botão "Confirmar" ✅
- Status muda para: **CONFIRMADO** (verde)
- Quando Ana chega, clica "Iniciar" ▶️
- Status: **EM ANDAMENTO** (amarelo)
- Após 60 min, clica "Finalizar" ✅
- Status: **FINALIZADO** (verde escuro)

---

## 🔍 Verificação Rápida

Após 5 minutos, você deve conseguir:

- ✅ Login com sucesso
- ✅ Ver menu "Admin" com sub-menus
- ✅ Criar um novo serviço
- ✅ Configurar horários de profissional
- ✅ Selecionar um cliente e agendá-lo
- ✅ Ver o agendamento na Agenda
- ✅ Confirmar o agendamento
- ✅ Iniciar e finalizar o atendimento

Se tudo isso funcionar, seu sistema está **pronto para uso!**

---

## ⚠️ Se Algo Der Errado

### Erro: "Nenhum horário disponível"
```
Solução: Configure horários em Admin → Profissionais → Horários
```

### Erro: "Profissional não encontrado"
```
Solução: Verifique se profissional existe em Admin → Profissionais
```

### Horários não carregam dinamicamente
```
Solução: Recarregue a página (F5) e tente novamente
```

### Banco de dados vazio
```
Solução: Delete "instance/clinica.db" e reinicie a app
(vai recriar do zero com admin default)
```

---

## 📚 Documentação Completa

Para mais detalhes, consulte:
- **GUIA_AGENDA.md** - Documentação completa
- **AGENDA_RESUMO.md** - Resumo técnico
- **README.md** - Visão geral do projeto

---

**Tempo estimado: 5 minutos ⏱️**

🎉 **Divirta-se com sua nova agenda profissional!**

