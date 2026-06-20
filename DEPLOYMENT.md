# 🚀 Guia de Deployment em Produção

## ☁️ Deploy no Render (recomendado para este projeto)

O repositório inclui um `render.yaml` (Blueprint). **A versão atual está configurada para o plano `free` do Render**, para validar o sistema sem custo, com duas limitações importantes (detalhadas abaixo): uploads não são persistentes e não há cron job de lembretes.

### Passo a passo

1. **Suba o código para um repositório Git** (GitHub/GitLab) — o Render faz deploy a partir de um repo conectado. Confirme que `.venv/`, `build/`, `dist/`, `instance/` e `uploads_clinica/*` não foram versionados (já estão no `.gitignore`).
2. No painel do Render, escolha **New → Blueprint** (não "Web Service" manual — só o Blueprint lê o `render.yaml`) e selecione o repositório. O Render vai propor a criação de:
   - `prontuario-clinica` (Web Service, Gunicorn, plano free)
   - `prontuario-clinica-db` (Postgres gerenciado, plano free)
3. `SECRET_KEY` é gerada automaticamente pelo Render (`generateValue: true`) — não precisa configurar manualmente.
4. `DATABASE_URL` é injetada automaticamente a partir do Postgres criado — não precisa configurar manualmente.
5. Após o primeiro deploy, o `preDeployCommand: flask db upgrade` já cria todas as tabelas no Postgres.
6. **Não há mais bootstrap manual de admin**: o sistema é multi-tenant self-service. Cada clínica se cadastra sozinha em `https://seu-servico.onrender.com/criar-clinica`, o que cria o `Estabelecimento` (com 30 dias de trial) e o primeiro usuário administrador daquela clínica. Não existe mais a rota `/setup` nem as variáveis `SETUP_ENABLED`/`SETUP_USERNAME`/`SETUP_PASSWORD`.

### ⚠️ Limitações do plano free (aceitas por ora, para testar sem custo)
- **Uploads não persistem**: o plano free do Render não permite disco persistente. Fotos de pacientes e logo da clínica são salvos num diretório local efêmero (`uploads_clinica/`, dentro do próprio serviço) e **somem a cada novo deploy ou restart**. Para resolver de vez, é preciso voltar para um plano pago com `disk:` no `render.yaml` (como na versão anterior deste arquivo) ou migrar os uploads para um storage externo (S3-compatível).
- **Sem lembretes automáticos**: o Cron Job (`flask lembretes-diarios` / `flask lembretes-retorno`) foi removido do `render.yaml` porque Cron Jobs no Render exigem plano pago. Os lembretes por e-mail (de agendamento e de retorno de procedimento) não disparam sozinhos enquanto isso. Pra rodar manualmente, use o **Shell** do serviço web no painel do Render e execute `flask lembretes-diarios` ou `flask lembretes-retorno` à mão.
- **Postgres free expira em 90 dias**: o Render apaga bancos no plano free após 90 dias de inatividade do plano (não de uso) — para produção real, faça upgrade antes do prazo.
- Quando for para produção paga, restaure o `disk:` no serviço web, o `UPLOAD_FOLDER=/var/data/uploads_clinica`, o serviço de `type: cron`, e troque `plan: free` por `plan: starter` (ou outro pago) no banco e no web service.

### Atualizações futuras
- Ao alterar modelos do banco, gere uma nova migration localmente (`flask db migrate -m "descrição"`) e faça commit da pasta `migrations/`. O próprio `preDeployCommand` aplica (`flask db upgrade`) no próximo deploy.
- Dados de demonstração (profissionais/serviços de exemplo) **não** são criados automaticamente em produção; use `flask seed-demo` apenas localmente, em ambiente de desenvolvimento (ele cria/usa um estabelecimento "Clínica Demo" isolado).

### Multi-tenant (estabelecimentos) e assinatura
- Cada clínica é um `Estabelecimento` isolado: pacientes, prontuários, serviços, profissionais, agenda e tema (logo/cores/e-mail) pertencem a um único estabelecimento e nunca aparecem para outro.
- Ao expirar o trial de 30 dias sem assinatura, o estabelecimento muda automaticamente para `inadimplente` e entra em **modo somente leitura**: continua possível visualizar pacientes/agenda/prontuário, mas criar, editar ou excluir fica bloqueado até assinar.
- A tela `/assinatura` e a rota `/assinatura/checkout` já existem, mas **não há gateway de pagamento integrado ainda** (Stripe/Mercado Pago a definir) — o checkout hoje só exibe "integração em breve". Esse é o ponto de extensão para plugar o gateway escolhido no futuro.
- Os comandos de cron (`flask lembretes-diarios`, `flask lembretes-retorno`) já iteram por todos os estabelecimentos ativos/em trial automaticamente.

---

## ⚠️ Checklist de Segurança

Antes de colocar em produção, execute estas verificações:

### 1. Segurança da Aplicação

- [ ] Altere `SECRET_KEY` em `.env` para um valor criptográfico forte
- [ ] Defina `FLASK_ENV=production`
- [ ] Defina `FLASK_DEBUG=False`
- [ ] Configure `SESSION_COOKIE_SECURE=True` (requer HTTPS)
- [ ] Use HTTPS com certificado SSL válido
- [ ] Atualize todas as dependências: `pip install -U -r requirements.txt`

### 2. Banco de Dados

- [ ] Mude de SQLite para PostgreSQL (mais robusto)
- [ ] Configure backups automáticos diários
- [ ] Teste restauração de backups
- [ ] Defina permissões restritivas no banco

### 3. Servidor Web

- [ ] Use um WSGI server como Gunicorn ou uWSGI
- [ ] Configure Nginx como proxy reverso
- [ ] Configure limites de taxa (rate limiting)
- [ ] Ative compressão GZIP

### 4. Dados Sensíveis

- [ ] Remova `.env` do versionamento (use .gitignore)
- [ ] Use variáveis de ambiente seguras do provedor
- [ ] Não commite senhas ou chaves no Git
- [ ] Configure acesso restrito ao diretório `instance/`

### 5. Monitoramento

- [ ] Configure logs centralizados
- [ ] Ative alertas para erros 500
- [ ] Monitore uso de CPU/memória
- [ ] Configure backup automático de logs

## 🔧 Deployment com Gunicorn

### 1. Instale Gunicorn
```bash
pip install gunicorn
```

### 2. Crie arquivo `wsgi.py`
```python
import os
from app_clinica import app

if __name__ == "__main__":
    app.run()
```

### 3. Inicie com Gunicorn
```bash
gunicorn --workers 4 --bind 0.0.0.0:5000 wsgi:app
```

### 4. Use Systemd (Linux)
Crie `/etc/systemd/system/prontuario-clinica.service`:
```ini
[Unit]
Description=Prontuário Clínico
After=network.target

[Service]
User=www-data
WorkingDirectory=/var/www/prontuario-clinica
ExecStart=/usr/bin/gunicorn --workers 4 --bind 0.0.0.0:5000 wsgi:app
Restart=always

[Install]
WantedBy=multi-user.target
```

Ative:
```bash
sudo systemctl enable prontuario-clinica
sudo systemctl start prontuario-clinica
```

## 🌐 Nginx Configuration

```nginx
server {
    listen 80;
    server_name clinica.com.br;
    
    # Redireciona para HTTPS
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name clinica.com.br;
    
    ssl_certificate /etc/ssl/certs/clinica.crt;
    ssl_certificate_key /etc/ssl/private/clinica.key;
    
    # Limites de taxa
    limit_req_zone $binary_remote_addr zone=api_limit:10m rate=10r/s;
    
    location / {
        limit_req zone=api_limit burst=20;
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
    
    location /static {
        alias /var/www/prontuario-clinica/static;
        expires 30d;
    }
    
    location /uploads_clinica {
        alias /var/www/prontuario-clinica/uploads_clinica;
        expires 7d;
    }
}
```

## 📊 PostgreSQL Setup

### Instale PostgreSQL
```bash
# Ubuntu/Debian
sudo apt-get install postgresql postgresql-contrib

# macOS
brew install postgresql@15
```

### Crie banco de dados
```sql
CREATE USER clinica WITH PASSWORD 'senha-forte-aqui';
CREATE DATABASE prontuario_clinica OWNER clinica;
GRANT ALL PRIVILEGES ON DATABASE prontuario_clinica TO clinica;
```

### Atualize `config.py`
```python
SQLALCHEMY_DATABASE_URI = 'postgresql://clinica:senha@localhost/prontuario_clinica'
```

### Instale driver
```bash
pip install psycopg2-binary
```

## 🔄 Backup e Restore

### Backup diário com cron
```bash
# Crie script backup.sh
#!/bin/bash
BACKUP_DIR="/backups/prontuario"
DB_NAME="prontuario_clinica"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)

pg_dump $DB_NAME > $BACKUP_DIR/backup_$TIMESTAMP.sql
tar -czf $BACKUP_DIR/uploads_$TIMESTAMP.tar.gz /var/www/prontuario-clinica/uploads_clinica

# Adicione ao crontab (diariamente às 2:00 AM)
0 2 * * * /path/to/backup.sh
```

### Restore de backup
```bash
psql -d prontuario_clinica < backup_20251110_020000.sql
tar -xzf uploads_20251110_020000.tar.gz -C /var/www/prontuario-clinica/
```

## 🛡️ Firewall e Segurança

### UFW (Uncomplicated Firewall)
```bash
sudo ufw allow 22/tcp   # SSH
sudo ufw allow 80/tcp   # HTTP
sudo ufw allow 443/tcp  # HTTPS
sudo ufw enable
```

### Fail2Ban (contra ataques)
```bash
sudo apt-get install fail2ban
sudo systemctl enable fail2ban
sudo systemctl start fail2ban
```

## 📈 Monitoramento

### Health Check
Já implementado em `app_clinica.py` na rota `GET /healthz` (usada pelo `healthCheckPath` do `render.yaml`).

### Logs
Configure logs centralizados com:
- Syslog
- ELK Stack
- Papertrail
- Datadog

## 🔄 Atualizações

### Atualize aplicação
```bash
cd /var/www/prontuario-clinica
git pull origin main
pip install -U -r requirements.txt
systemctl restart prontuario-clinica
```

## 📞 Suporte em Produção

- Configure alertas para erros
- Mantenha logs por 30 dias
- Revise logs semanalmente
- Faça testes de recover regularmente

---

**Última atualização:** Novembro 2025
