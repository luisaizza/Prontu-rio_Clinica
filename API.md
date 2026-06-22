# API Pública (v1)

API REST simples para integrações externas (ex: agendar a partir de outro sistema, sincronizar dados). Escopo: dados da clínica do usuário dono do token, respeitando as permissões desse usuário.

## Autenticação

1. Faça login no sistema e vá em **Meu Perfil** → **Token de API** → **Gerar Token de API**.
2. Copie o token mostrado (só aparece uma vez).
3. Envie em todo request no header:

```
Authorization: Bearer <seu_token>
```

Sem esse header (ou com token inválido/revogado), toda rota `/api/v1/*` responde `401`.

## Endpoints

### `GET /api/v1/pacientes`

Lista os pacientes ativos (não excluídos) da clínica.

```bash
curl -H "Authorization: Bearer SEU_TOKEN" https://sua-clinica.onrender.com/api/v1/pacientes
```

### `GET /api/v1/pacientes/<id>`

Detalhe de um paciente específico.

### `GET /api/v1/agendamentos?inicio=YYYY-MM-DD&fim=YYYY-MM-DD`

Lista agendamentos no período (padrão: próximos 30 dias a partir de agora).

### `POST /api/v1/agendamentos`

Cria um agendamento. Exige que o usuário do token tenha a permissão `agendar` (perfil admin, secretaria ou esteta — não funciona com um token de usuário sem essa permissão).

```bash
curl -X POST https://sua-clinica.onrender.com/api/v1/agendamentos \
  -H "Authorization: Bearer SEU_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "paciente_id": 1,
    "profissional_id": 2,
    "servico_id": 3,
    "data_agendamento": "2026-07-01 14:00",
    "observacoes": "Criado via API"
  }'
```

Retorna `201` com `{"id": ..., "status": "agendado"}`, ou `409` se o horário já estiver ocupado para aquele profissional.

## Limites

Todos os endpoints têm rate limiting (60/min para leitura, 30/min para criação) por IP.

## O que NÃO existe ainda

- Paginação (listagens retornam tudo de uma vez — cuidado em clínicas com muitos pacientes/agendamentos).
- Webhooks (a API é só para você consultar/empurrar dados, não para o sistema te avisar de eventos).
- Endpoints de escrita para anamnese/exame físico/atendimento (dados clínicos sensíveis) — só leitura/escrita de cadastro de paciente e agendamento por enquanto.
