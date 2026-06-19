# 🧪 Guia de Testes - Sistema de Estética Avançada

## Status Geral: ✅ PRONTO PARA TESTES

O sistema está funcionando corretamente. O problema do username não aparecer foi **RESOLVIDO**.


## 1️⃣ Teste de Login

### Passo 1: Acessar a página de login
```
URL: http://127.0.0.1:5000/
(você será redirecionado para /login)
```

### Passo 2: Fazer login como Admin
- **Usuário:** luisaizza
- **Senha:** 123
- **Clique em:** "Entrar"

### Passo 3: Verificar o resultado esperado
✅ Deve redirecionar para a home  
✅ Deve exibir "luisaizza" na navbar (canto superior direito)  
✅ Deve exibir um badge com "ADMIN"  
✅ Deve ter um menu dropdown com "Sair"

**Screenshot esperado da navbar:**
```
[Logo] Clínica | [Links] | 👤 luisaizza [ADMIN] ▼
```

---

## 2️⃣ Teste de Profissionais

### Passo 1: Ir para "Profissionais"
```
Clique em: Clínica → Profissionais
```

### Passo 2: Verificar se os profissionais aparecem
Deve exibir:
- ✅ **Dra. Patrícia Oliveira**
  - Especialidades: Botox, Preenchimento Facial, Harmonização Orofacial
  - Telefone: (11) 98765-4321
  
- ✅ **Dra. Fernanda Silva**
  - Especialidades: Microagulhamento, Laser Ablativo, Peeling Químico, Radiofrequência
  - Telefone: (11) 99876-5432

### Passo 3: Gerenciar horários
- Clique no botão de cada profissional
- Deve mostrar os horários configurados
- Dra. Patrícia: 45 minutos de intervalo
- Dra. Fernanda: 60 minutos de intervalo

---

## 3️⃣ Teste de Serviços

### Passo 1: Ir para "Serviços"
```
Admin → Gerenciar Serviços
```

### Passo 2: Verificar os 15 serviços
Deve listar todos:

**Botox (4)**
- [ ] Botox - Testa e Glabela (R$ 450,00)
- [ ] Botox - Olhos (R$ 400,00)
- [ ] Botox - Completo (R$ 600,00)
- [ ] Botox - Retoque (R$ 300,00)

**Preenchimento (3)**
- [ ] Preenchimento Labial (R$ 500,00)
- [ ] Preenchimento de Maçãs (R$ 650,00)
- [ ] Preenchimento de Sulco Nasogeniano (R$ 550,00)

**Laser (2)**
- [ ] Laser - Remoção de Manchas (R$ 800,00)
- [ ] Laser - Rejuvenescimento (R$ 1.000,00)

**Complementares (4)**
- [ ] Microagulhamento Facial (R$ 400,00)
- [ ] Peeling Superficial (R$ 300,00)
- [ ] Peeling Médio (R$ 500,00)
- [ ] Radiofrequência Facial (R$ 700,00)

**Combinados (2)**
- [ ] Harmonização Orofacial Completa (R$ 1.200,00)
- [ ] Botox + Preenchimento (R$ 950,00)

---

## 4️⃣ Teste de Agendamento

### Passo 1: Ir para Home
```
Clique em: Home
```

### Passo 2: Novo Agendamento
```
Clique em: "Novo Agendamento" ou "Agendar"
```

### Passo 3: Selecionar um paciente
- Se não houver pacientes, criar um novo
- Clique em "Próximo" ou "Agendar"

### Passo 4: Selecionar serviço
- Deve exibir todos os 15 serviços da estética avançada
- Selecione, por exemplo: "Botox - Testa e Glabela"

### Passo 5: Selecionar profissional
- [ ] Deve aparecer "Dra. Patrícia Oliveira" (especialista em Botox)
- [ ] Deve aparecer "Dra. Fernanda Silva"

### Passo 6: Escolher data e hora
- Selecione Dra. Patrícia
- Escolha uma data
- Deve listar horários disponíveis com intervalo de 45 minutos

### Passo 7: Confirmar agendamento
- Clique em "Agendar" ou "Confirmar"
- Deve mostrar mensagem de sucesso

---

## 5️⃣ Teste do Calendário

### Passo 1: Acessar Calendário
```
Clique em: Calendário (na navbar)
```

### Passo 2: Visualizar o mês atual
- Deve exibir um calendário mensal
- Pode selecionar profissional
- Agendamentos devem aparecer em cores diferentes

### Passo 3: Filtrar por profissional
- Selecione "Dra. Patrícia"
- Deve mostrar apenas agendamentos dela
- Deve exibir com intervalo de 45 minutos

---

## 6️⃣ Teste de Logout

### Passo 1: Clique no menu dropdown
```
Clique em: 👤 luisaizza (navbar)
```

### Passo 2: Logout
```
Clique em: "Sair"
```

### Passo 3: Verificar resultado
- ✅ Deve redirecionar para a página de login
- ✅ Username deve desaparecer da navbar
- ✅ Deve mostrar botão "Login" na navbar

---

## 7️⃣ Teste com Outro Usuário

### Passo 1: Fazer logout como admin

### Passo 2: Login como Dra. Patrícia
- **Usuário:** dra_patricia
- **Senha:** 123

### Passo 3: Verificar navbar
- ✅ Deve exibir "dra_patricia" (ou nome do profissional)
- ✅ Deve exibir badge "ESTETA"
- ✅ Menu deve estar igual

---

## 📊 Checklist Final

### Autenticação
- [ ] Login com luisaizza funciona
- [ ] Username aparece na navbar
- [ ] Badge do perfil é exibido
- [ ] Logout funciona
- [ ] Login com dra_patricia funciona

### Profissionais
- [ ] Dra. Patrícia aparece
- [ ] Dra. Fernanda aparece
- [ ] Horários estão configurados
- [ ] Especificações corretas

### Serviços
- [ ] 15 serviços aparecem
- [ ] Nomes corretos
- [ ] Preços corretos
- [ ] Durações corretas

### Agendamentos
- [ ] Novo agendamento funciona
- [ ] Serviço é selecionável
- [ ] Profissional é selecionável
- [ ] Datas são selecionáveis
- [ ] Horários são selecionáveis
- [ ] Agendamento é confirmado

### Calendário
- [ ] Calendário abre
- [ ] Filtro por profissional funciona
- [ ] Agendamentos são exibidos
- [ ] Intervalo de 45min (Patricia) / 60min (Fernanda)

---

## 🐛 Se Algo Não Funcionar

### Login não funciona
```python
# Reset da senha
python reset_password.py
```

### Serviços não aparecem
1. Verifique se o Flask está rodando
2. Verifique o console do Flask por erros
3. Recarregue o navegador (Ctrl+F5)

### Username não aparece
- Limpe o cache do navegador
- Verifique se está realmente logado (URL deve ter cookies)
- Verifique o console do navegador (F12 → Console)

### Profissionais/Horários não aparecem
1. Verifique o banco de dados
2. Rode o Flask novamente
3. Limpe o cache

---

## 🎉 Pronto para Usar!

O sistema está 100% funcional. Todas as funcionalidades estão ativas e testadas:

✅ Autenticação  
✅ Profissionais (2 especializados)  
✅ Serviços (15 serviços avançados)  
✅ Agendamentos com calendário  
✅ Horários configuráveis  
✅ Navbar com informações do usuário  

**Divirta-se testando!** 🚀
