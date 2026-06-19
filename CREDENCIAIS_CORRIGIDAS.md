# Credenciais de Acesso - Sistema de Estética Avançada

## Status: ✓ CORRIGIDO

O problema com o username não aparecer na home foi resolvido. O issue era que a senha do usuário admin estava incorreta.

## Credenciais para Teste

### Admin
- **Usuário:** `luisaizza`
- **Senha:** `123`
- **Perfil:** Administrador
- **Acesso:** Todas as funcionalidades do sistema

### Dra. Patrícia Oliveira
- **Usuário:** `dra_patricia`
- **Senha:** `123`
- **Perfil:** Esteta
- **Especialidade:** Botox, Preenchimento Facial, Harmonização Orofacial
- **Horários:** 
  - Segunda a Sexta: 10:00-17:00
  - Quarta estendida: 14:00-20:00  
  - Sábado: 10:00-14:00
- **Intervalo:** 45 minutos

### Dra. Fernanda Silva
- **Usuário:** `dra_fernanda`
- **Senha:** `123`
- **Perfil:** Esteta
- **Especialidade:** Laser, Microagulhamento, Radiofrequência, Peeling Químico
- **Horários:**
  - Segunda a Sexta: 09:00-18:00
  - Sábado: 09:00-13:00
- **Intervalo:** 60 minutos

## Como Fazer Login

1. Acesse: http://127.0.0.1:5000/
2. Você será redirecionado para a página de login
3. Digite o usuário (ex: `luisaizza`)
4. Digite a senha: `123`
5. Clique em "Entrar"

## O que Você Verá Após o Login

### Na Barra de Navegação (Navbar)
- Seu nome de usuário será exibido no canto superior direito
- Um badge indicará seu perfil (ADMIN ou ESTETA)
- Um menu dropdown com a opção de "Sair"

### Funcionalidades Disponíveis
- **Home:** Lista de pacientes com busca
- **Novo Agendamento:** Agendar serviços para pacientes
- **Calendário:** Visualizar agenda em formato calendário
- **Meu Perfil:** Informações do profissional (se esteta)
- **Admin (apenas admin):**
  - Gerenciar Serviços
  - Gerenciar Profissionais e Horários

## Serviços Disponíveis (15 no Total)

### Botox (4 serviços)
- Botox - Testa e Glabela: R$ 450,00
- Botox - Olhos (Pés de Galinha): R$ 400,00
- Botox - Completo (Testa, Glabela, Olhos): R$ 600,00
- Botox - Retoque: R$ 300,00

### Preenchimento Facial (3 serviços)
- Preenchimento Labial: R$ 500,00
- Preenchimento de Maçãs: R$ 650,00
- Preenchimento de Sulco Nasogeniano: R$ 550,00

### Laser (2 serviços)
- Laser - Remoção de Manchas: R$ 800,00
- Laser - Rejuvenescimento Facial: R$ 1.000,00

### Complementares (4 serviços)
- Microagulhamento Facial: R$ 400,00
- Peeling Superficial: R$ 300,00
- Peeling Médio: R$ 500,00
- Radiofrequência Facial: R$ 700,00

### Combinados (2 serviços)
- Harmonização Orofacial Completa: R$ 1.200,00
- Botox + Preenchimento: R$ 950,00

## Testando o Sistema

### Teste 1: Fazer Login
1. Use as credenciais acima
2. Verifique se seu nome aparece na barra de navegação
3. Clique no dropdown para ver o perfil

### Teste 2: Criar Agendamento
1. Vá para "Home"
2. Clique em "Novo Agendamento"
3. Selecione um paciente existente
4. Escolha um serviço (deve mostrar os 15 novos serviços)
5. Selecione Dra. Patrícia ou Dra. Fernanda
6. Escolha uma data e hora disponível
7. Confirme o agendamento

### Teste 3: Ver Calendário
1. Vá para "Calendário"
2. Selecione uma profissional
3. Navegue pelos meses
4. Veja os agendamentos em formato calendário

## Correções Aplicadas Nesta Sessão

1. ✅ **Username não aparecia na home** 
   - Causa: Senha do admin incorreta no banco de dados
   - Solução: Reset da senha do usuário 'luisaizza' para '123'

2. ✅ **Navbar agora mostra:**
   - Nome do usuário autenticado
   - Badge com o perfil (ADMIN/ESTETA)
   - Menu dropdown com opção de logout

3. ✅ **Todos os usuários têm senhas corretas:**
   - luisaizza: 123 (admin)
   - dra_patricia: 123 (esteta)
   - dra_fernanda: 123 (esteta)

## Sistema Funcionando

- ✅ Autenticação por usuário/senha
- ✅ Profissionais especializados (2)
- ✅ 15 Serviços de Estética Avançada pré-configurados
- ✅ Calendário de agendamentos
- ✅ Horários configuráveis
- ✅ Navbar com informações do usuário
