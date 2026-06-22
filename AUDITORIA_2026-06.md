# Auditoria Técnica — Prontuário_Clínica (2026-06-21)

> Diagnóstico baseado em leitura direta do código-fonte atual (`app_clinica.py`, `config.py`, `render.yaml`, `.env.example`, templates), não nos relatórios anteriores do projeto (`RELATORIO_FINAL.md`, `RESUMO_EXECUTIVO.md` etc.), que são auto-avaliações otimistas de sessões passadas e não foram usados como fonte de verdade aqui.

## Como ler este documento

Esta auditoria foi feita em duas passadas: uma exploração ampla do código, seguida de verificação manual dos achados mais graves antes de serem listados aqui. Um achado inicial de "IDOR crítico entre clínicas" foi descartado nessa segunda passada — o sistema já implementa isolamento multi-tenant a nível de sessão do SQLAlchemy (`with_loader_criteria` sobre o evento `do_orm_execute`, em `app_clinica.py:262-293`), que filtra automaticamente todo SELECT em modelos `TenantMixin`, mesmo `.query.all()` sem filtro explícito. É uma decisão arquitetural correta e já documentada no próprio código. Isso não significa que não haja gaps reais — eles estão listados abaixo, já verificados.

---

## ETAPA 1 — DIAGNÓSTICO

### 1.1 Funcionalidades concluídas

| Área | O que existe |
|---|---|
| Multi-tenancy | Isolamento automático por `estabelecimento_id` via `TenantMixin` + `ContextVar` + listener de sessão SQLAlchemy. Cobre todas as entidades de clínica (pacientes, agendamentos, serviços, profissionais, usuários, audit log). |
| Autenticação | Flask-Login, hash de senha via `werkzeug.security` (PBKDF2), CSRF habilitado globalmente via Flask-WTF. |
| RBAC | 3 perfis (`admin`, `secretaria`, `esteta`) + flag `eh_super_admin` (admin da plataforma, fora do tenant). Permissões centralizadas em `User.tem_permissao()`. |
| Prontuário clínico | Paciente, Anamnese, Exame Físico, Atendimento (com fotos antes/depois), Procedimentos por atendimento. |
| Agendamento | Profissionais com horários configuráveis por dia da semana, calendário visual, agendamento público sem login via slug da clínica (`/agendar/<slug>`), agendamento interno por secretaria/esteta. |
| Customização por clínica | Logo e cores próprias (`Estabelecimento.cor_primaria` etc.), e-mail SMTP próprio por clínica. |
| Billing básico | Status de assinatura (`trial`, `ativo`, `inadimplente`, `cancelado`), expiração de trial lazy (checada a cada request), gate de leitura-apenas quando inadimplente. |
| Admin da plataforma | Painel super-admin para listar clínicas e "entrar" em uma clínica específica para suporte. |
| Auditoria (parcial) | `AuditLog` registra `DELETE_USER`, `RESET_PASSWORD`, `CHANGE_PROFILE`. |
| Upload de imagens | Fotos de atendimento e logo, com extensão whitelisted, nome randomizado via UUID, limite de 16MB. |
| Testes | `test_app_clinica.py` com testes automatizados reais (`unittest`, com assertions) cobrindo login, CRUD de pacientes, anamnese, exame físico, atendimento. |

### 1.2 Funcionalidades incompletas

- **Auditoria de acesso a dados clínicos**: `AuditLog` cobre só ações administrativas sobre usuários. Não há registro de quem visualizou/editou anamnese, exame físico, prontuário ou fotos — relevante tanto para segurança quanto para LGPD/trilha de auditoria.
- **Autorização granular em rotas de prontuário**: rotas como criar atendimento, criar anamnese e criar exame físico (`app_clinica.py:1551-1768`) usam só `@login_required`, sem `@requer_permissao`. Qualquer perfil autenticado da clínica pode escrever prontuário, mesmo perfis que talvez não devessem (depende de você decidir se isso é intencional).
- **Controle de acesso a arquivos enviados**: `/uploads/<filename>` e `/uploads/logos/<filename>` (`app_clinica.py:2582-2592`) exigem login mas não verificam se o arquivo pertence ao estabelecimento do usuário — a proteção real hoje é só o nome de arquivo ser um UUID imprevisível, não um controle de autorização.
- **Rate limiting**: inexistente (sem Flask-Limiter ou equivalente) — login e agendamento público (`/agendar/<slug>`) ficam expostos a brute-force/abuso sem limitação.
- **Verificação de tipo real de arquivo**: validação é só por extensão (`allowed_file`), sem checagem de magic bytes. Pillow está nas dependências mas não é usado para revalidar/reprocessar a imagem.
- **Cookies de sessão**: `SESSION_COOKIE_SAMESITE` não está configurado explicitamente (depende do default do navegador).

### 1.3 Funcionalidades ausentes (esperadas em um SaaS de saúde/estética moderno)

- Consentimento informado (LGPD) — coleta, versionamento e prova de aceite por paciente.
- Soft delete / retenção controlada de dados de saúde (hoje, deletar é exclusão física e definitiva).
- Direito à portabilidade/exportação de dados do paciente.
- Anonimização/pseudonimização de dados ao encerrar relação com paciente.
- Notificações (e-mail/SMS/WhatsApp) de confirmação e lembrete de agendamento — só existe campo de controle (`data_hora_lembrete_enviado`, `metodo_lembrete`), sem implementação de envio automatizado visível além do SMTP de e-mail configurado por clínica.
- Financeiro: controle de pagamentos por atendimento, comissão de profissional, faturamento, NF-e.
- Relatórios/BI: ocupação de agenda, taxa de retorno, ticket médio, funil de conversão do agendamento público.
- Prontuário eletrônico com assinatura digital/certificação (o `/assinatura` existente é sobre cobrança de assinatura SaaS, não assinatura digital de documento clínico).
- API pública/integrações (nenhuma rota `/api/*` documentada além de `dashboard-stats` interno).
- 2FA para perfis admin.
- Versionamento de prontuário (histórico de edições de anamnese/exame/atendimento).

---

## ETAPA 2 — GAP ANALYSIS

Comparação qualitativa com práticas comuns em iClinic, Feegow, Doctoralia, Ninsaúde e Clinicorp (com base em conhecimento geral de mercado, não em levantamento ao vivo dos produtos):

| Módulo | Status Atual | Melhor Prática de Mercado | Prioridade |
|---|---|---|---|
| Prontuário eletrônico | Texto livre, sem versionamento, sem log de acesso | Estruturado + texto livre, trilha de auditoria por campo, exportação PDF | Alta |
| Consentimento/LGPD | Ausente | Termo de consentimento versionado, aceite registrado com timestamp/IP | Alta |
| Notificações | Apenas e-mail manual via SMTP da clínica | WhatsApp Business API + SMS + e-mail automatizados, confirmação com 1 clique | Alta |
| Financeiro | Ausente | Contas a receber, comissão, fechamento de caixa, NF-e/boleto | Alta (monetização) |
| Auditoria | Só ações admin sobre usuário | Log completo de acesso/edição a dado clínico, exportável | Alta |
| Relatórios/BI | Ausente (só `dashboard-stats` básico) | Dashboards de ocupação, retenção, ticket médio, funil | Média |
| App mobile/PWA | Ausente | App nativo ou PWA para profissional e paciente | Média |
| Agendamento público | Existe, sem autenticação do paciente | Login do paciente, histórico de agendamentos, reagendamento self-service | Média |
| Multi-unidade dentro do mesmo tenant | Não modelado (1 `Estabelecimento` = 1 unidade) | Clínicas com múltiplas unidades/filiais sob um único contrato | Média |
| Assinatura digital de documentos | Ausente | Assinatura eletrônica de termos/laudos (ICP-Brasil ou equivalente) | Baixa/Média |
| Integrações (Google Calendar, contabilidade) | Ausente | Integrações via API/webhooks | Baixa |
| 2FA | Ausente | 2FA obrigatório para perfis admin | Média (mitiga risco de senha fraca) |

---

## ETAPA 4 (parcial) — SEGURANÇA: achados verificados

### Reais (confirmados lendo o código)

1. ~~**`/uploads/<filename>` e `/uploads/logos/<filename>` sem verificação de tenant**~~ — **CORRIGIDO em 2026-06-21.** As duas rotas agora verificam se o arquivo pertence a um `Atendimento`/`Estabelecimento` do tenant atual antes de servir o arquivo; caso contrário, 404. Verificado manualmente: logo de outra clínica passou a retornar 404, logo/foto da própria clínica continuam em 200.
2. ~~**Usuário `luisaizza` hardcoded como "admin protegido"**~~ — **CORRIGIDO em 2026-06-21**: substituído por `eh_ultimo_admin()`, que bloqueia rebaixar/excluir o último admin de **qualquer** clínica (antes só protegia um único username fixo, e não valia para as demais clínicas do SaaS).
3. ~~**Senha padrão do super-admin em texto plano em `render.yaml:29`**~~ — **CORRIGIDO em 2026-06-21** no `render.yaml` (agora `sync: false`, não fica mais commitada). **Ação manual pendente do usuário:** a senha `Esqueci001` já está exposta no histórico do git para sempre — é necessário definir uma nova senha forte na env var `SUPER_ADMIN_PASSWORD` no dashboard do Render e confirmar login com ela.
4. ~~**Sem rate limiting**~~ — **CORRIGIDO em 2026-06-21.** `/login` limitado a 15/min e `/agendar/<slug>/horario` a 30/min por IP (Flask-Limiter, storage em memória — só funciona corretamente com 1 worker, que é a configuração atual do Render). Verificado manualmente: 15ª tentativa de login em sequência retorna 429.
5. ~~**Sem verificação de magic bytes** no upload~~ — **CORRIGIDO em 2026-06-21**: `arquivo_e_imagem_valida()` abre o arquivo com Pillow e valida que o conteúdo é mesmo uma imagem decodificável, nas 3 rotas de upload (foto antes/depois, logo).
6. **Dados de saúde em texto plano no banco** (sem encryption at rest a nível de aplicação — depende inteiramente da criptografia do Postgres gerenciado do Render). (Não corrigido — fora do escopo desta rodada.)
7. ~~**`SESSION_COOKIE_SAMESITE` não configurado.**~~ — **CORRIGIDO em 2026-06-21** (`SESSION_COOKIE_SAMESITE = 'Lax'` em `config.py`).

### Falso positivo descartado
- "IDOR entre tenants via `.query.all()`" — não procede, ver explicação no topo do documento.

---

## ETAPA 5 (parcial) — LGPD: lacunas

- ~~Sem campo de consentimento/aceite por paciente~~ — **CORRIGIDO em 2026-06-21**: `Paciente.consentimento_lgpd` + `data_consentimento_lgpd` + `ip_consentimento_lgpd`, capturado obrigatoriamente no agendamento público e registrável manualmente no cadastro/edição interna.
- Sem soft delete — exclusão de paciente remove o registro permanentemente, sem grace period nem trilha do que foi removido. (Não corrigido.)
- Sem rota de exportação de dados do paciente (portabilidade, Art. 18 LGPD). (Não corrigido.)
- Sem política de retenção definida (não há job/rotina que anonimize ou expurgue dados de pacientes inativos há N anos). (Não corrigido.)
- ~~Auditoria não cobre acesso a dado de saúde~~ — **CORRIGIDO em 2026-06-21**, ver Etapa 7/V1 abaixo.

---

## ETAPA 7 — ROADMAP PROPOSTO

**MVP** — já atingido na prática: multi-tenant funcional, prontuário, agendamento, billing básico, em produção.

**V1 (necessário para vender com segurança jurídica)**
- [x] Remover senha hardcoded de `render.yaml` — feito 2026-06-21 (falta o usuário rotacionar a senha real no dashboard do Render).
- [x] Autorização de tenant na rota de uploads — feito 2026-06-21.
- [x] Rate limiting em login e agendamento público — feito 2026-06-21.
- [x] Log de acesso/edição a dado clínico — feito 2026-06-21: `AuditLog` ganhou `target_type`/`target_id`/`ip_address` genéricos; agora registra `VIEW_PACIENTE`, `CREATE_PACIENTE`, `UPDATE_PACIENTE`, `DELETE_PACIENTE`, `CREATE_ANAMNESE`, `UPDATE_ANAMNESE`, `CREATE_EXAME_FISICO`, `UPDATE_EXAME_FISICO`, `CREATE_ATENDIMENTO`. Visível em `/admin/auditoria`.
- [x] Termo de consentimento LGPD + registro de aceite — feito 2026-06-21: `Paciente` ganhou `consentimento_lgpd`/`data_consentimento_lgpd`/`ip_consentimento_lgpd`. Obrigatório (bloqueia o envio) no agendamento público self-service; opcional/registrável manualmente no cadastro e edição interna de paciente (cobre o caso de consentimento colhido em papel).

**Pendências que ficaram de fora desta rodada** (itens médios/baixos do diagnóstico original, ver Etapa 4): verificação de magic bytes no upload, `SESSION_COOKIE_SAMESITE`, encryption at rest dos dados de saúde, fragilidade do admin hardcoded (`luisaizza`), texto de consentimento ainda é um modelo genérico — recomenda-se revisão jurídica antes de uso real. Direito à portabilidade/exportação e soft delete de dados de saúde (Art. 18 LGPD) também não foram implementados — ficam para V2.

**V2 (necessário para escalar)**
- [x] Notificações automatizadas por e-mail — feito 2026-06-21: confirmação imediata no agendamento público (faltava, já existia no fluxo interno) + 2 cron jobs no `render.yaml` (`flask lembretes-diarios`/`flask lembretes-retorno`) que já existiam no código mas nunca eram disparados em produção. **WhatsApp/SMS ficaram de fora** — exigem conta paga em serviço de terceiro (Twilio, WhatsApp Business API) que não temos como configurar sem credenciais do usuário.
- [x] Módulo financeiro básico — feito 2026-06-21, na forma de **relatório de faturamento/comissão** (opção escolhida pelo usuário em vez de controle de pagamento completo): usa o `preço` já cadastrado em cada serviço, soma faturamento previsto/realizado e calcula comissão por profissional (novo campo `ProfissionalEstetico.comissao_percentual`, opcional). Não há cobrança real, parcelamento nem forma de pagamento — se isso for necessário no futuro, é um novo pedido de escopo maior.
- [x] Relatórios/BI de ocupação e retenção — feito 2026-06-21, na mesma página (`/admin/relatorios`): mix de status dos agendamentos (proxy de ocupação), taxa de cancelamento/no-show, taxa de retorno de pacientes.
- [x] Soft delete + exportação/portabilidade de dados — feito 2026-06-21: `Paciente.excluido_em` (exclusão lógica, com tela de "ver excluídos" e restauração) + rota de exportação em JSON (`/pacientes/<id>/exportar`), pensada para a clínica entregar ao paciente, não para autoatendimento.
- [x] 2FA para admin — feito 2026-06-21: TOTP opcional (Google Authenticator/Authy), ativado por usuário em `/perfil`, exige confirmação de um código válido antes de habilitar.

**Itens médios/baixos do diagnóstico original, resolvidos junto com o V2:** verificação de magic bytes no upload, `SESSION_COOKIE_SAMESITE`, e a fragilidade do admin hardcoded (`luisaizza`) — ver Etapa 4 atualizada abaixo.

**Ainda não implementado:** encryption at rest dos dados de saúde, controle de pagamento/cobrança real (caso o usuário queira ir alem do relatório de faturamento).

**V3 (para liderar o mercado)**
- [x] PWA — feito 2026-06-21: `manifest.json` + ícones + service worker registrado no escopo raiz (`Service-Worker-Allowed: /`). Permite "instalar" o sistema como app no celular/desktop. Cache propositalmente restrito a assets estáticos (CSS/JS/ícones) — nenhum dado clínico ou HTML dinâmico é cacheado, dado o caráter multi-tenant e sensível dos dados. **App nativo nas lojas (Play Store/App Store) fica fora de alcance** — exigiria um wrapper nativo (Capacitor/React Native) e conta de desenvolvedor nas lojas, escopo bem maior que um PWA.
- [x] Multi-unidade por tenant — feito 2026-06-21: novo modelo `Unidade` (nome, endereço, telefone), CRUD em `/admin/unidades`, vínculo opcional `ProfissionalEstetico.unidade_id`. Modelo "simples" escolhido deliberadamente (opção recomendada): tudo opcional/nullable, UI só aparece se a clínica cadastrar uma unidade, zero impacto em clínicas de unidade única. Filtro por unidade já integrado ao relatório de faturamento/comissão (`/admin/relatorios?unidade_id=`).
- [x] Assinatura eletrônica leve de consentimento — feito 2026-06-21: campo `Paciente.assinatura_consentimento` (PNG em base64), capturada via canvas HTML5 no formulário público de agendamento (`agendar_publico_horario.html`), opcional. **Não é assinatura digital com certificação ICP-Brasil** — é uma assinatura desenhada à mão, com valor probatório análogo a assinar em papel, não criptográfico. Se for necessário valor jurídico de assinatura digital qualificada, é um projeto à parte (ex.: integração com DocuSign/Clicksign ou certificado ICP-Brasil).
- [x] API pública com token — feito 2026-06-21: `/api/v1/pacientes` (GET, lista/detalhe), `/api/v1/agendamentos` (GET com filtro de período, POST para criar), autenticação via Bearer token gerado em `/perfil` (`User.api_token`). Documentada em `API.md`. **Integrações prontas com terceiros (Google Calendar, contabilidade, ERPs) ficam fora de alcance** — exigiriam credenciais OAuth/API key de cada serviço externo, que não temos como configurar sem o usuário fornecer.

**Itens fora de alcance nesta sessão (exigem decisão de produto/credenciais externas):** app nativo para lojas de aplicativo, assinatura digital com certificação ICP-Brasil, integrações com Google Calendar/contabilidade/ERPs, WhatsApp/SMS (Twilio ou similar), encryption at rest a nível de aplicação, controle de pagamento/cobrança real.
