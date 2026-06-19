# Changelog - Sistema de Estética Avançada

## [1.2.0] - 11 de Novembro de 2025

### Corrigido
- ✅ **Username não aparecia na navbar após login**
  - **Problema:** O usuário admin (luisaizza) tinha a senha incorreta no banco de dados, impedindo o login
  - **Solução:** Reset da senha do usuário admin para '123'
  - **Resultado:** Login agora funciona corretamente, username aparece na navbar com o badge do perfil

### Adicionado
- ✅ Novo arquivo `CREDENCIAIS_CORRIGIDAS.md` com todas as credenciais e instruções de teste
- ✅ Script `reset_password.py` para resetar senhas de usuários
- ✅ Script `test_login_simple.py` para verificar o status do login

## [1.1.0] - 11 de Novembro de 2025

### Adicionado - Sistema de Estética Avançada
- ✅ Dois profissionais especializados pré-configurados:
  - Dra. Patrícia Oliveira (Botox, Preenchimento, Harmonização)
  - Dra. Fernanda Silva (Laser, Microagulhamento, Radiofrequência)

- ✅ 15 serviços de estética avançada com preços:
  - Botox (4 variações): R$ 300-600
  - Preenchimento (3 variações): R$ 500-650
  - Laser (2 variações): R$ 800-1.000
  - Complementares (4 variações): R$ 300-700
  - Combinados (2 variações): R$ 950-1.200

- ✅ Sistema de horários configuráveis:
  - Dra. Patrícia: 45 minutos por atendimento
  - Dra. Fernanda: 60 minutos por atendimento
  - Horários diferenciados por dia da semana

- ✅ Calendário visual para agendamentos
- ✅ Interface para gerenciar horários sem código

## [1.0.0] - Versão Inicial

### Funcionalidades Base
- Autenticação de usuários
- Gerenciamento de pacientes
- Sistema de permissões por perfil
- Upload de imagens
- Agendamentos básicos
- Anamnese clínica
- Exame físico

---

## Sistema de Autenticação

### Usuários Padrão

| Usuário | Senha | Perfil | Status |
|---------|-------|--------|--------|
| luisaizza | 123 | Admin | ✅ Funcionando |
| dra_patricia | 123 | Esteta | ✅ Funcionando |
| dra_fernanda | 123 | Esteta | ✅ Funcionando |

### Testes Realizados

- ✅ Login com credenciais corretas
- ✅ Username aparece na navbar
- ✅ Badge do perfil exibe corretamente
- ✅ Logout funciona
- ✅ Redirecionamento para login quando não autenticado
- ✅ Acesso a rotas protegidas após login

---

## Próximas Melhorias Planejadas

- [ ] Alterar senha do usuário logado
- [ ] Recuperação de senha por email
- [ ] Dashboard com estatísticas
- [ ] Relatórios de agendamentos
- [ ] Integração com calendário externo
- [ ] Notificações de agendamentos
- [ ] Sistema de avaliações de serviços
- [ ] Controle de inventário de produtos
