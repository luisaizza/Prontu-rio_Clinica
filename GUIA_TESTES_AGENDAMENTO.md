# 🧪 Guia de Testes Rápidos

## Dados de Acesso para Testes

### Usuário Administrador:
- **Usuário:** luisaizza
- **Senha:** 123
- **Perfil:** ADMIN

### Dra. Patrícia (Botox/Preenchimento):
- **Usuário:** dra_patricia
- **Senha:** 123
- **Perfil:** ESTETICISTA

### Dra. Fernanda (Laser/Microagulhamento):
- **Usuário:** dra_fernanda
- **Senha:** 123
- **Perfil:** ESTETICISTA

---

## ✅ Teste 1: Verificar Profissionais Especializadas

**Objetivo:** Confirmar que as Dras. Patrícia e Fernanda foram criadas com seus horários específicos.

**Passos:**
1. Faça login como `luisaizza` (admin)
2. Vá para Menu → Admin → Gerenciar Profissionais
3. Verifique se **Dra. Patrícia** e **Dra. Fernanda** aparecem na lista.
4. Veja se os horários estão listados (botão "Horários")

**Resultado Esperado:**
- ✅ Dois profissionais aparecem na lista
- ✅ SARAH com horários 09:00-18:00 (Seg-Sex) e 09:00-14:00 (Sab)
- ✅ CIDINHA com horários 10:00-19:00 (Seg-Sex) e 10:00-15:00 (Sab)
- ✅ **Dra. Patrícia** com seus horários (ex: Seg-Sex 10:00-17:00, intervalo 45 min).
- ✅ **Dra. Fernanda** com seus horários (ex: Seg-Sex 09:00-18:00, intervalo 60 min).

---

## ✅ Teste 2: Adicionar Novo Horário

**Objetivo:** Testar se conseguimos adicionar horários pelo painel

**Passos:**
1. Login como `luisaizza`
2. Menu → Admin → Gerenciar Profissionais
3. Clique no botão "Horários" da **Dra. Patrícia**.
4. Preencha o formulário:
   - Dia: Domingo
   - Início: 09:00
   - Término: 14:00
   - Intervalo: 30 minutos
5. Clique "Adicionar Horário"

**Resultado Esperado:**
- ✅ Mensagem de sucesso aparece
- ✅ Novo horário aparece na lista de "Horários Configurados"

---

## ✅ Teste 3: Visualizar Calendário

**Objetivo:** Testar a visualização em calendário

**Passos:**
1. Login como `luisaizza`
2. Menu → Agenda → **Calendário**
3. Navegue entre meses (anterior/próximo)
4. Filtre por profissional (**Dra. Patrícia** ou **Dra. Fernanda**)

**Resultado Esperado:**
- ✅ Calendário mensal aparece
- ✅ Botões de navegação funcionam
- ✅ Filtro funciona corretamente

---

## ✅ Teste 4: Agendar Serviço - Paciente Existente

**Objetivo:** Testar agendamento para paciente já cadastrado

**Passos:**
1. Login como `luisaizza`
2. Vá para Pacientes (página inicial)
3. Clique em "Novo Agendamento" → "Para Paciente Existente"
4. Procure por um paciente (ex: "Maria")
5. Clique no paciente
6. Preencha:
   - Profissional: **Dra. Patrícia**
   - Serviço: (escolher um)
   - Data: data futura
   - Horário: será carregado automaticamente
7. Clique "Agendar Serviço"

**Resultado Esperado:**
- ✅ Modal com pacientes abre
- ✅ Busca filtra os pacientes
- ✅ Após selecionar, vai para página de agendamento
- ✅ Horários são carregados conforme data escolhida
- ✅ Agendamento é criado com sucesso
- ✅ Você é redirecionado para o prontuário do paciente

---

## ✅ Teste 5: Agendar Serviço - Novo Paciente

**Objetivo:** Testar agendamento com criação de novo paciente

**Passos:**
1. Login como `luisaizza`
2. Vá para Pacientes
3. Clique em "Novo Agendamento" → "Criar Novo Paciente e Agendar"
4. Preencha dados do novo paciente:
   - Nome: "Test Patient"
   - Data nascimento: data
   - Telefone: número
   - Email: email
5. Clique "Salvar Paciente"
6. Você deve ser redirecionado para a página de agendamento
7. Preencha os dados do agendamento:
   - Profissional: **Dra. Fernanda**
   - Serviço: escolher
   - Data e hora
8. Clique "Agendar Serviço"

**Resultado Esperado:**
- ✅ Novo paciente é criado
- ✅ Você é redirecionado para página de agendamento (automático)
- ✅ Agendamento é criado
- ✅ Sucesso completo do fluxo

---

## ✅ Teste 6: Validações de Agendamento

**Objetivo:** Testar regras de validação

**Teste 6.1: Não permitir data no passado**
1. Tente agendar para uma data/hora passada
2. Deve aparecer mensagem de erro

**Teste 6.2: Não permitir conflito de horário**
1. Crie um agendamento para SARAH às 14:00 numa data
2. Tente criar outro para a **Dra. Patrícia** no mesmo horário.
3. Deve aparecer mensagem dizendo que o horário está ocupado

**Teste 6.3: Campos obrigatórios**
1. Tente agendar sem preencher algum campo obrigatório
2. Deve aparecer mensagem de erro

**Resultado Esperado:**
- ✅ Todas as validações funcionam
- ✅ Mensagens de erro aparecem corretamente
- ✅ Nenhum agendamento inválido é criado

---

## ✅ Teste 7: Desativar/Ativar Horário

**Objetivo:** Testar ativação/desativação de horários

**Passos:**
1. Login como `luisaizza`
2. Menu → Admin → Gerenciar Profissionais
3. Clique "Horários" da **Dra. Patrícia**.
4. Localize um horário (ex: segunda-feira 09:00-12:00)
5. Clique no ícone de olho (👁️) para desativar
6. Clique novamente para ativar

**Resultado Esperado:**
- ✅ Badge muda de "Ativo" para "Inativo" e vice-versa
- ✅ Horário inativo não aparece nas opções de agendamento

---

## ✅ Teste 8: Deletar Horário

**Objetivo:** Testar remoção de horários

**Passos:**
1. Login como `luisaizza`
2. Menu → Admin → Gerenciar Profissionais
3. Clique "Horários" da **Dra. Fernanda**.
4. Localize um horário
5. Clique no ícone de lixo (🗑️)
6. Confirme a exclusão

**Resultado Esperado:**
- ✅ Horário desaparece da lista
- ✅ Mensagem de sucesso aparece
- ✅ Horário não mais disponível para agendamento

---

## ✅ Teste 9: Logout

**Objetivo:** Testar se logout funciona

**Passos:**
1. Faça login com qualquer usuário
2. Clique no nome do usuário (canto superior direito)
3. Clique em "Sair"

**Resultado Esperado:**
- ✅ Você é desconectado
- ✅ Redirecionado para página de login
- ✅ Tenta acessar página protegida sem login: erro 401

---

## ✅ Teste 10: Visualizar Minha Agenda

**Objetivo:** Testar se profissional vê apenas seus agendamentos

**Passos:**
1. Faça login como `dra_patricia`
2. Menu → Agenda → Minha Agenda
3. Verifique se aparecem apenas agendamentos da **Dra. Patrícia**.

**Passos 2 (Opcional):**
1. Logout
2. Login como `dra_fernanda`
3. Menu → Agenda → Minha Agenda
4. Verifique se aparecem apenas agendamentos da **Dra. Fernanda**.

**Resultado Esperado:**
- ✅ Cada profissional vê apenas seus agendamentos
- ✅ Dados estão corretos

---

## 📋 Checklist de Testes Completo

- [ ] Teste 1: Profissionais pré-cadastrados
- [ ] Teste 2: Adicionar novo horário
- [ ] Teste 3: Visualizar calendário
- [ ] Teste 4: Agendar para paciente existente
- [ ] Teste 5: Agendar novo paciente
- [ ] Teste 6: Validações
  - [ ] Data no passado
  - [ ] Conflito de horário
  - [ ] Campos obrigatórios
- [ ] Teste 7: Desativar/ativar horário
- [ ] Teste 8: Deletar horário
- [ ] Teste 9: Logout
- [ ] Teste 10: Minha agenda

---

## 🐛 Se Algo Não Funcionar:

1. **Verifique se a aplicação está rodando:**
   ```bash
   python app_clinica.py
   ```

2. **Verifique o console do navegador (F12) para erros de JavaScript**

3. **Verifique o terminal onde rodou a aplicação para erros Python**

4. **Limpe o banco de dados (apague `instance/clinica.db`) e reinicie para começar do zero**

5. **Entre em contato com o desenvolvedor com os detalhes do erro**

---

**Data dos testes:** 11/11/2025  
**Versão:** 3.0 (Estética Avançada)
