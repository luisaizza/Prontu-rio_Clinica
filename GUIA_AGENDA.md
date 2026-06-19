# 📅 Sistema de Agenda Estética - Guia Completo

## 🎯 Visão Geral

O novo sistema de agenda profissional foi desenvolvido para gerenciar de forma dinâmica e eficiente todos os agendamentos do centro de estética. Com funcionalidades avançadas, permite:

- ✅ Agendamento automático de serviços estéticos
- ✅ Gerenciamento de profissionais e horários
- ✅ Controle de disponibilidade
- ✅ Rastreamento de status de atendimento
- ✅ Visualização em tempo real da agenda

---

## 🏗️ Arquitetura do Sistema

### Modelos de Dados

#### 1. **ServicoEstetico**
Define os serviços oferecidos pelo centro estético.

```python
- nome_servico: string (único)
- descricao: texto
- duracao_minutos: inteiro (default: 60)
- preco: float
- ativo: booleano (true/false)
- data_criacao: datetime
```

**Exemplo de Serviços:**
- Limpeza de Pele (60 min, R$ 150)
- Microdermoabrasão (45 min, R$ 200)
- Drenagem Linfática (90 min, R$ 180)
- Hidratação Profunda (60 min, R$ 120)

---

#### 2. **ProfissionalEstetico**
Vincula um usuário do sistema como profissional com suas especialidades.

```python
- usuario_id: FK para User
- especialidades: string (ex: "Limpeza, Microdermoabrasão")
- telefone_contato: string
- disponibilidade_status: enum [disponível, indisponível, de_ferias]
- data_inicio_ferias: date
- data_fim_ferias: date
```

**Exemplo:**
```
Usuário: Maria Silva
Especialidades: Limpeza de Pele, Microdermoabrasão, Massagem
Telefone: (21) 98765-4321
Status: Disponível
```

---

#### 3. **HorarioAtendimento**
Define os horários disponíveis de cada profissional por dia da semana.

```python
- profissional_id: FK para ProfissionalEstetico
- dia_semana: inteiro (0=Seg, 1=Ter, ..., 6=Dom)
- hora_inicio: time (ex: 08:00)
- hora_fim: time (ex: 18:00)
- intervalo_minutos: inteiro (default: 30)
- ativo: booleano
```

**Exemplo:**
```
Profissional: Maria Silva
Segunda-feira: 08:00 - 18:00 (intervalo: 30 min)
Terça-feira: 08:00 - 18:00 (intervalo: 30 min)
Quarta-feira: OFF
Quinta-feira: 10:00 - 16:00 (intervalo: 45 min)
Sexta-feira: 08:00 - 18:00 (intervalo: 30 min)
Sábado: 09:00 - 14:00 (intervalo: 45 min)
Domingo: OFF
```

---

#### 4. **AgendamentoServico**
Registra cada agendamento realizado.

```python
- paciente_id: FK para Paciente
- profissional_id: FK para ProfissionalEstetico
- servico_id: FK para ServicoEstetico
- data_agendamento: datetime (data + hora exata)
- status: enum [agendado, confirmado, em_andamento, finalizado, cancelado, no_show]
- observacoes: texto
- avaliacao: inteiro (1-5)
- comentario_cliente: texto
- data_criacao: datetime
```

**Fluxo de Status:**
```
agendado → confirmado → em_andamento → finalizado
                     ↓
                   cancelado / no_show
```

---

## 🚀 Como Usar

### 1️⃣ SETUP INICIAL (Admin)

#### Passo 1: Criar Serviços
```
Menu: Admin → Gerenciar Serviços → Novo Serviço
```

Preenchimento obrigatório:
- Nome do Serviço (único)
- Duração em minutos
- Preço

**Exemplo:**
- Nome: Limpeza Profunda de Pele
- Duração: 60 minutos
- Preço: R$ 150.00

#### Passo 2: Criar Profissionais
```
Menu: Admin → Gerenciar Profissionais
```

Associar usuários como profissionais:
1. Usuário deve existir no sistema (Secretaria ou Esteta)
2. Adicionar especialidades
3. Definir telefone de contato

#### Passo 3: Configurar Horários
```
Menu: Admin → Gerenciar Profissionais → [Prof] → Horários
```

Para cada profissional:
1. Dia da semana
2. Hora de início (ex: 08:00)
3. Hora de término (ex: 18:00)
4. Intervalo entre agendamentos (15, 30, 45, 60, 90 min)

**Cálculo de Capacidade:**
- Horário: 08:00 - 18:00 (10 horas)
- Intervalo: 30 minutos
- **Capacidade: 20 agendamentos/dia**

---

### 2️⃣ AGENDAMENTO (Secretária ou Esteta)

#### Agendar um Cliente
```
Menu: Agenda → Pacientes → Ver Paciente → Agendar Serviço
```

**OU**

```
Menu: Agenda → [botão "Novo Agendamento"]
```

Passo a passo:
1. **Selecione o Paciente** (já deve estar cadastrado)
2. **Escolha o Serviço** (ex: Limpeza de Pele)
3. **Selecione o Profissional** (disponível)
4. **Escolha a Data** (a partir de hoje)
5. **Selecione a Hora** (carrega automaticamente horários disponíveis)
6. **Adicione Observações** (opcional)
7. **Confirme**

**Validações Automáticas:**
- ✅ Não permite agendar no passado
- ✅ Detecta conflitos de horário
- ✅ Verifica disponibilidade do profissional
- ✅ Respeita intervalo entre agendamentos

---

### 3️⃣ GERENCIAMENTO DA AGENDA (Secretária)

#### Visualizar Agenda Completa
```
Menu: Agenda
```

Funcionalidades:
- 📋 Lista de agendamentos próximos 30 dias
- 🔍 Filtrar por status e profissional
- ✅ Confirmar agendamento
- 🚫 Cancelar agendamento
- 👁️ Ver detalhes do paciente

#### Minha Agenda (Profissional)
```
Menu: Minha Agenda
```

Visualizações:
- Todos os agendamentos
- Abas por status (Agendado, Confirmado, Em Andamento, Finalizado)
- Estatísticas resumidas
- Opções de cancelamento

---

### 4️⃣ CICLO DE VIDA DE UM AGENDAMENTO

```
┌──────────────────────────────────────────────────────────────────┐
│                    CICLO DE VIDA COMPLETO                        │
└──────────────────────────────────────────────────────────────────┘

1. AGENDADO
   ↓ (Cliente marca presença)
2. CONFIRMADO
   ↓ (Na hora, profissional inicia)
3. EM_ANDAMENTO
   ↓ (Após conclusão do procedimento)
4. FINALIZADO
   ↓ (Opcional: cliente deixa avaliação)
5. AVALIADO

Cenário Alternativo:
   AGENDADO → CANCELADO (por cliente ou profissional)
   AGENDADO → NO_SHOW (cliente não compareceu)
```

**Ações Disponíveis por Status:**

| Status | Ações Disponíveis |
|--------|------------------|
| **Agendado** | Confirmar, Cancelar, Ver Paciente |
| **Confirmado** | Iniciar Atendimento, Cancelar, Ver Paciente |
| **Em Andamento** | Finalizar, Ver Paciente |
| **Finalizado** | Ver Paciente, Deixar Avaliação |
| **Cancelado** | Ver Paciente |

---

## 📊 Exemplos Práticos

### Exemplo 1: Agendamento Completo

**Cenário:** Maria (secretária) precisa agendar a cliente Ana Silva para limpeza de pele com a profissional Fernanda

**Passos:**
1. Menu: Agenda → Agendar Serviço
2. Cliente: Ana Silva
3. Serviço: Limpeza de Pele (60 min, R$ 150)
4. Profissional: Fernanda
5. Data: 15/11/2025
6. Hora: 14:00 (sistema valida que é horário disponível)
7. Observações: "Pele sensível, usar produtos hipoalergênicos"
8. Confirmar

**Resultado:** Agendamento criado em status "agendado"

---

### Exemplo 2: Confirmação de Agendamento

**Cenário:** Ana Silva confirmou presença. Hora de iniciar o atendimento.

**Passos:**
1. Menu: Agenda
2. Encontrar agendamento de Ana Silva - 15/11/2025 14:00
3. Status: Agendado → Clicar no ícone ✅ (Confirmar)
4. Status muda para: Confirmado
5. Quando Ana chegar, clique no ✅ (Iniciar Atendimento)
6. Status muda para: Em Andamento
7. Após 60 min, clique no ✅ (Finalizar)
8. Status muda para: Finalizado

---

### Exemplo 3: Configuração de Horários

**Cenário:** Fernanda trabalha segunda a sexta, com almoço de 12h-13h

**Configuração:**
```
Segunda-feira:
- Hora início: 08:00
- Hora fim: 12:00 (até almoço)
- Intervalo: 30 min
→ Capacidade: 8 agendamentos

Segunda-feira (tarde):
- Seria necessário criar entrada adicional ou ajustar horários
```

**Alternativa Melhor:**
```
Segunda-feira:
- Hora início: 08:00
- Hora fim: 18:00 (full day)
- Intervalo: 60 min (deixa tempo para almoço/café)
→ Capacidade: 10 agendamentos/dia
```

---

## ⚙️ Configurações Avançadas

### Férias e Indisponibilidade

**Para marcar profissional de férias:**
1. Ir a: Admin → Gerenciar Profissionais
2. Clicar no profissional
3. Mudar Status: "Disponível" → "De Férias"
4. Indicar datas início/fim

**Efeito:** Sistema não permite agendar nesse período

---

### Intervalo Entre Agendamentos

**Recomendações:**
- 15-30 min: Para procedimentos rápidos (microdermoabrasão relâmpago)
- 30-45 min: Padrão (limpeza, hidratação)
- 60 min: Para procedimentos mais longos ou com deslocamento
- 90 min+: Para tratamentos intensivos (drenagem completa)

**Impacto no Calendário:**
```
Intervalo 30 min → 20 slots/dia (8h-18h)
Intervalo 60 min → 10 slots/dia (8h-18h)
Intervalo 90 min → 7 slots/dia (8h-18h)
```

---

## 🔐 Permissões e Perfis

### Por Perfil de Usuário

| Funcionalidade | Admin | Secretaria | Esteta |
|---|---|---|---|
| Ver Agenda | ✅ | ✅ | ✅ |
| Agendar Serviço | ✅ | ✅ | ✅ |
| Confirmar Agendamento | ✅ | ✅ | ❌ |
| Iniciar/Finalizar Atendimento | ✅ | ✅ | ✅ |
| Cancelar Agendamento | ✅ | ✅ | ❌ |
| Gerenciar Serviços | ✅ | ❌ | ❌ |
| Gerenciar Profissionais | ✅ | ❌ | ❌ |
| Configurar Horários | ✅ | ❌ | ❌ |
| Gerenciar Usuários | ✅ | ❌ | ❌ |

---

## 🎨 Interface Visual

### Cores de Status

- 🔵 **Agendado** (Azul): Aguardando confirmação
- 🟢 **Confirmado** (Verde): Cliente confirmou presença
- 🟡 **Em Andamento** (Amarelo): Procedimento em execução
- 🟢 **Finalizado** (Verde escuro): Atendimento concluído
- 🔴 **Cancelado** (Vermelho): Agendamento cancelado

### Componentes da Interface

1. **Tabela de Agenda:** Cards responsivos com informações completas
2. **Filtros Rápidos:** Status, Profissional, Data
3. **Modais de Confirmação:** Para ações críticas (cancelamento)
4. **Loading States:** Indicadores de carregamento de horários
5. **Paginação:** 10-15 registros por página

---

## 🐛 Troubleshooting

### Problema: "Nenhum horário disponível"

**Causas Possíveis:**
1. Profissional não tem horários configurados
   - Solução: Admin → Gerenciar Profissionais → Horários
2. Profissional está de férias
   - Solução: Alterar status em Gerenciar Profissionais
3. Data escolhida cai num dia "off"
   - Solução: Escolher outro dia ou adicionar horário

### Problema: "Este horário já está agendado"

**Causa:** Sistema detectou conflito (mesmo profissional, mesma hora)

**Solução:**
1. Escolher outro horário disponível
2. Ou escolher outro profissional
3. Ou escolher outra data

### Problema: Horários não aparecem na seleção

**Causas:**
1. Formulário incompleto (falta data ou profissional)
2. AJAX não carregou (verificar console do navegador)
3. Profissional sem horários no dia da semana escolhido

**Solução:** Recarregar página (F5) e tentar novamente

---

## 📈 Relatórios e Análise

### Estatísticas Disponíveis

Na página "Minha Agenda":
- Total de agendamentos
- Agendamentos confirmados
- Agendamentos pendentes
- Atendimentos finalizados

### Dados Rastreados

Para cada agendamento:
- Data/hora de criação
- Status e histórico de mudanças (implícito nas datas)
- Tempo decorrido até finalização
- Avaliação do cliente (futuro)

---

## 🔜 Funcionalidades Futuras

- ✨ Notificações automáticas por email/SMS
- ✨ Integração com calendário (Google Calendar, Outlook)
- ✨ Relatórios em PDF
- ✨ Histórico de cancelamentos
- ✨ Rescheduling automático
- ✨ CRM com histórico de clientes
- ✨ App mobile
- ✨ Integração com pagamento

---

## 📞 Suporte

Para dúvidas ou relatos de bugs:
1. Verificar seção "Troubleshooting" acima
2. Consultar logs da aplicação (terminal)
3. Contactar administrador do sistema

---

**Versão:** 1.0.0  
**Data:** Novembro 2025  
**Autor:** Sistema de Agenda Estética

