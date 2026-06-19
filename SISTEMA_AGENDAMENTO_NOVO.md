# 🗓️ Sistema de Agendamento Refatorado

## Resumo das Melhorias

Implementamos um sistema completo de agendamento com calendário visual e gerenciamento de horários configurável pelo painel administrativo.

---

## ✅ Funcionalidades Implementadas

### 1. **Profissionais Pré-Cadastrados**

Dois profissionais foram criados automaticamente no primeiro acesso:

#### **SARAH** 👩‍⚕️
- **Usuário:** sarah
- **Senha:** 123
- **Especialidades:** Limpeza de pele, Estética facial, Depilação
- **Telefone:** (11) 98765-4321
- **Horários:**
  - Segunda a Sexta: 09:00 - 18:00
  - Sábado: 09:00 - 14:00
  - Intervalo: 30 minutos

#### **CIDINHA** 👩‍⚕️
- **Usuário:** cidinha
- **Senha:** 123
- **Especialidades:** Massagem estética, Drenagem linfática, Tratamentos corporais
- **Telefone:** (11) 99876-5432
- **Horários:**
  - Segunda a Sexta: 10:00 - 19:00
  - Sábado: 10:00 - 15:00
  - Intervalo: 30 minutos

---

### 2. **Agenda em Calendário** 📅

Nova página visual em formato de calendário mensal:

**Acessar em:** Menu → Agenda → **Calendário**

**Funcionalidades:**
- ✅ Visualizar todo o mês em um calendário
- ✅ Navegar entre meses (Anterior / Próximo)
- ✅ Filtrar por profissional
- ✅ Ver agendamentos coloridos por status:
  - 🟢 Verde: Agendado
  - 🟡 Amarelo: Confirmado
  - 🔵 Azul: Em andamento
  - ⚫ Cinza: Indisponível
- ✅ Clicar no dia para ver detalhes
- ✅ Clicar no agendamento para ver todos os dados

---

### 3. **Gerenciamento de Horários Configurável** ⚙️

Sistema completo para configurar disponibilidade de cada profissional **SEM ALTERAR O CÓDIGO**:

**Acessar em:** Menu → Admin → Gerenciar Profissionais → Botão "Horários"

**Funcionalidades:**
- ✅ Adicionar novos horários por dia da semana
- ✅ Configurar hora de início e fim
- ✅ Definir intervalo entre agendamentos (15, 30, 45 min ou 1 hora)
- ✅ Ativar/Desativar horários sem deletar
- ✅ Deletar horários antigos
- ✅ Ver resumo de horários ativos
- ✅ Visualizar informações do profissional

**Exemplo de Configuração:**
```
Segunda-feira: 09:00 - 12:00 (30 min)
Segunda-feira: 13:00 - 18:00 (30 min)
Terça-feira:   09:00 - 18:00 (45 min)
```

---

### 4. **Agendamento Melhorado** 📝

Sistema de agendamento com:
- ✅ Seleção de profissional
- ✅ Seleção de serviço
- ✅ Carregamento dinâmico de horários disponíveis
- ✅ Validação de conflitos
- ✅ Prevenção de agendamentos no passado
- ✅ Observações opcionais

**Fluxos de Uso:**

#### **Opção 1: Agendar para Paciente Existente**
```
1. Clique em "Novo Agendamento"
2. Selecione "Para Paciente Existente"
3. Procure o paciente na lista (com busca)
4. Clique no paciente
5. Preencha os dados do agendamento
6. Confirme
```

#### **Opção 2: Novo Paciente + Agendamento**
```
1. Clique em "Novo Agendamento"
2. Selecione "Criar Novo Paciente e Agendar"
3. Preencha os dados do paciente
4. Clique em "Salvar Paciente"
5. Você será redirecionado para o agendamento
6. Preencha os dados do serviço
7. Confirme
```

---

## 🔧 Como Usar

### Para Administrador:

**1. Configurar Horários:**
```
1. Acesse: Menu → Admin → Gerenciar Profissionais
2. Clique no botão "Horários" de um profissional
3. Preencha o formulário à esquerda:
   - Dia da semana
   - Hora de início
   - Hora de término
   - Intervalo entre agendamentos
4. Clique em "Adicionar Horário"
5. Para modificar, use os botões de ações (👁️ ativador, 🗑️ deletar)
```

**2. Visualizar Agenda:**
```
1. Acesse: Menu → Agenda → Calendário
2. Navegue entre meses
3. Filtre por profissional (opcional)
4. Clique em um dia para ver detalhes
5. Clique em um agendamento para ver informações completas
```

### Para Secretária/Esteticista:

**1. Agendar Serviço:**
```
1. Na página inicial (Pacientes), clique em "Novo Agendamento"
2. Escolha entre paciente existente ou novo
3. Complete o formulário com:
   - Profissional
   - Serviço
   - Data
   - Horário (será carregado automaticamente conforme disponibilidade)
4. Salve o agendamento
```

**2. Visualizar Minha Agenda:**
```
1. Acesse: Menu → Agenda → Minha Agenda
2. Veja todos os seus agendamentos
3. Clique para ver detalhes ou gerenciar status
```

**3. Ver Agenda Geral:**
```
1. Acesse: Menu → Agenda → Calendário
2. Veja todo o calendário do mês
3. Use o filtro para ver apenas seus agendamentos
```

---

## 📊 Estrutura do Banco de Dados

### Tabelas Utilizadas:

#### `profissional_estetico`
```sql
- id (PK)
- usuario_id (FK) → User
- especialidades (texto)
- telefone_contato
- disponibilidade_status (disponível|indisponível|de_ferias)
- data_inicio_ferias
- data_fim_ferias
```

#### `horario_atendimento`
```sql
- id (PK)
- profissional_id (FK) → ProfissionalEstetico
- dia_semana (0=Seg, 1=Ter, ..., 6=Dom)
- hora_inicio (TIME)
- hora_fim (TIME)
- intervalo_minutos
- ativo (boolean)
```

#### `agendamento_servico`
```sql
- id (PK)
- paciente_id (FK) → Paciente
- profissional_id (FK) → ProfissionalEstetico
- servico_id (FK) → ServicoEstetico
- data_agendamento (DATETIME)
- observacoes
- status (agendado|confirmado|em_andamento|finalizado|cancelado)
```

---

## 🚀 Novas Rotas Criadas

| Rota | Método | Descrição |
|------|--------|-----------|
| `/agenda-calendario` | GET | Exibe calendário visual |
| `/admin/horarios-profissional/<id>` | GET/POST | Gerencia horários de um profissional |

---

## 💡 Próximas Melhorias Sugeridas

- [ ] Importação de horários em lote (Excel/CSV)
- [ ] Feriados/Datas especiais
- [ ] Notificações de agendamento (SMS/Email)
- [ ] Relatórios de ocupação
- [ ] Configuração de tempo de intervalo entre agendamentos por serviço
- [ ] Bloqueio de datas para férias
- [ ] Sistema de reagendamento automático

---

## 🔐 Permissões

- **Admin:** Acesso total (configurar horários, ver agenda global)
- **Secretária:** Agendar, ver agenda, filtrar por profissional
- **Esteticista:** Ver própria agenda, ver dados de agendamentos

---

## 📝 Notas Importantes

1. **Horários são configuráveis:** Todos os horários podem ser alterados no painel sem mexer no código
2. **Intervalos automáticos:** O sistema calcula automaticamente os horários disponíveis baseado no intervalo configurado
3. **Validação de conflitos:** Não permite agendar dois serviços no mesmo horário para um profissional
4. **Prevenção de passado:** Não permite agendar para datas/horas já passadas
5. **Dados persistem:** Todas as configurações são salvas no banco de dados SQLite

---

**Sistema desenvolvido e testado em 1