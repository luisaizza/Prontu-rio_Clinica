import os
import sys
import uuid
import logging
import webbrowser
import contextvars
from contextlib import contextmanager
from threading import Timer
from datetime import datetime, timedelta, time
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.image import MIMEImage
from functools import wraps
from flask import Flask, render_template, request, redirect, url_for, flash, send_from_directory, jsonify, session
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from werkzeug.security import generate_password_hash, check_password_hash
import re
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from werkzeug.utils import secure_filename
from flask_wtf.csrf import CSRFProtect
from flask_wtf import FlaskForm
from sqlalchemy import func, extract, event
from sqlalchemy.orm import declared_attr, with_loader_criteria, Session
from wtforms import StringField, PasswordField, SubmitField, SelectField, DateField, TimeField, TextAreaField, validators, ValidationError

from config import config, validar_configuracao_producao

# --- CONFIGURAÇÃO DE LOGGING ---
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# --- CONFIGURAÇÃO INICIAL ---

# O Flask procura a pasta 'templates' por padrão.
# Como seus arquivos HTML estão na pasta raiz, ajustamos o 'template_folder'.
# A prática recomendada é mover os arquivos .html para uma pasta 'templates'.
app = Flask(__name__, template_folder='.')

ENV_NAME = os.environ.get("FLASK_ENV", "development")
validar_configuracao_producao(ENV_NAME)
app.config.from_object(config[ENV_NAME])

csrf = CSRFProtect(app)

# Quando empacotado com PyInstaller (app desktop), os caminhos relativos do
# config.py apontam para o diretório temporário de extração, não para onde o
# .exe realmente está. Nesse caso (e só nesse caso), recalculamos os caminhos
# de instância/uploads relativos ao executável.
if getattr(sys, 'frozen', False):
    BASE_DIR = os.path.dirname(sys.executable)
    app.config['INSTANCE_FOLDER'] = os.path.join(BASE_DIR, 'instance')
    if not os.environ.get('UPLOAD_FOLDER'):
        app.config['UPLOAD_FOLDER'] = os.path.join(BASE_DIR, 'uploads_clinica')
    if not os.environ.get('DATABASE_URL'):
        app.config['SQLALCHEMY_DATABASE_URI'] = (
            f"sqlite:///{os.path.join(app.config['INSTANCE_FOLDER'], 'clinica.db')}"
        )
else:
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))

INSTANCE_FOLDER = app.config['INSTANCE_FOLDER']
UPLOAD_FOLDER = app.config['UPLOAD_FOLDER']

# Criar pastas se não existirem (a pasta de instância só é necessária para SQLite local)
if app.config['SQLALCHEMY_DATABASE_URI'].startswith('sqlite'):
    os.makedirs(INSTANCE_FOLDER, exist_ok=True)
os.makedirs(UPLOAD_FOLDER, exist_ok=True)


def allowed_file(filename):
    """Verifica se o arquivo tem extensão permitida"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

db = SQLAlchemy(app)
migrate = Migrate(app, db)
login_manager = LoginManager(app)
login_manager.login_view = "login"
login_manager.login_message = "Por favor, faça login para acessar esta página."

# --- DECORADORES DE AUTORIZAÇÃO ---

from flask import abort

def requer_permissao(permissao):
    """Decorador para verificar permissões do usuário"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.is_authenticated:
                return redirect(url_for('login'))
            if not current_user.tem_permissao(permissao): # A lógica de admin já está no método tem_permissao
                flash("Você não tem permissão para acessar esta página.", "danger")
                return redirect(url_for('home'))
            return f(*args, **kwargs)
        return decorated_function
    return decorator

def requer_super_admin(f):
    """Decorador para rotas exclusivas do admin da plataforma (vê/opera em qualquer clínica)."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            return redirect(url_for('login'))
        if not current_user.eh_super_admin:
            abort(403)
        return f(*args, **kwargs)
    return decorated_function

def requer_perfil(perfil):
    """Decorador para verificar o perfil específico do usuário"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.is_authenticated:
                return redirect(url_for('login'))
            if current_user.perfil != perfil and current_user.perfil != 'admin':
                flash("Você não tem permissão para acessar esta página.", "danger")
                return redirect(url_for('home'))
            return f(*args, **kwargs)
        return decorated_function
    return decorator

# --- PROCESSADOR DE CONTEXTO ---

@app.context_processor
def inject_utilities():
    """Injeta utilitários em todos os templates."""
    estabelecimento_atual = None
    if current_user.is_authenticated:
        if current_user.eh_super_admin:
            entrou_id = session.get('super_admin_estabelecimento_id')
            estabelecimento_atual = db.session.get(Estabelecimento, entrou_id) if entrou_id else None
        else:
            estabelecimento_atual = current_user.estabelecimento
    return {
        'current_year': datetime.now().year,
        'now': datetime.now(),
        'timedelta': timedelta,
        'estabelecimento_atual': estabelecimento_atual,
    }

# --- FUNÇÕES DE E-MAIL ---

def enviar_email(estabelecimento, destinatario, assunto, corpo):
    """Envia um e-mail usando as credenciais SMTP daquele estabelecimento (clínica)."""
    with app.app_context():
        if not estabelecimento or not estabelecimento.email_clinica or not estabelecimento.senha_email_clinica:
            logger.warning(f"Tentativa de envio de e-mail sem credenciais configuradas (estabelecimento {estabelecimento.id if estabelecimento else '?'}).")
            return False

        remetente = estabelecimento.email_clinica
        senha = estabelecimento.senha_email_clinica

        msg = MIMEMultipart('related')
        msg['From'] = remetente
        msg['To'] = destinatario
        msg['Subject'] = assunto

        msg_alternative = MIMEMultipart('alternative')
        msg.attach(msg_alternative)
        msg_alternative.attach(MIMEText(corpo, 'html'))

        # Tentar anexar o logo do estabelecimento se existir, senão o logo genérico do sistema
        logo_path = None
        if estabelecimento.logo_filename:
            candidato = os.path.join(app.config['UPLOAD_FOLDER'], 'logos', estabelecimento.logo_filename)
            if os.path.exists(candidato):
                logo_path = candidato
        if not logo_path:
            candidato = os.path.join(BASE_DIR, 'static', 'logo.png')
            if os.path.exists(candidato):
                logo_path = candidato
        if logo_path:
            try:
                with open(logo_path, 'rb') as f:
                    logo_data = f.read()
                logo_image = MIMEImage(logo_data)
                logo_image.add_header('Content-ID', '<logo_clinica>')
                logo_image.add_header('Content-Disposition', 'inline', filename='logo.png')
                msg.attach(logo_image)
            except Exception as e:
                logger.error(f"Erro ao anexar logo no email: {e}")

        try:
            # Configuração automática do servidor SMTP
            smtp_server = 'smtp.gmail.com'
            smtp_port = 587
            
            # Ajuste automático para Outlook/Hotmail/Live
            if any(domain in remetente.lower() for domain in ['outlook', 'hotmail', 'live']):
                smtp_server = 'smtp.office365.com'
            elif 'yahoo' in remetente.lower():
                smtp_server = 'smtp.mail.yahoo.com'

            server = smtplib.SMTP(smtp_server, smtp_port)
            server.starttls()
            server.login(remetente, senha)
            text = msg.as_string()
            server.sendmail(remetente, destinatario, text)
            server.quit()
            return True
        except Exception as e:
            logger.error(f"Falha ao enviar e-mail via {smtp_server}: {e}")
            return False

# --- FILTROS DE TEMPLATE ---

@app.template_filter('dateformat')
def dateformat(value, format='%d/%m/%Y'):
    if not value:
        return ""
    if isinstance(value, str):
        try:
            # Tenta converter de string para data, se necessário
            value = datetime.strptime(value, '%Y-%m-%d')
        except ValueError:
            return value # Retorna a string original se não conseguir converter
    return value.strftime(format) if hasattr(value, 'strftime') else value

@app.template_filter('datetimeformat')
def datetimeformat(value, format='%d/%m/%Y às %H:%M'):
    if not value:
        return ""
    return value.strftime(format)

# --- ISOLAMENTO MULTI-TENANT (ESTABELECIMENTOS) ---
#
# Cada clínica cadastrada é um "Estabelecimento". Os modelos que herdam de
# TenantMixin pertencem a um estabelecimento e são automaticamente filtrados
# pelo estabelecimento "ativo" no contexto atual — tanto em requests HTTP
# (definido após o login, ver before_request mais abaixo) quanto em comandos
# CLI/cron (definidos explicitamente via `usar_estabelecimento`).
#
# Por que um filtro automático em vez de `.filter_by(estabelecimento_id=...)`
# em cada rota: aqui um "vazamento entre tenants" é um vazamento de prontuário
# médico de uma clínica para outra. Confiar em lembrar de filtrar manualmente
# em ~40 rotas é um risco alto demais para esse tipo de dado; um filtro central
# no nível da sessão do SQLAlchemy garante a separação mesmo que uma rota nova
# esqueça de filtrar.

current_estabelecimento_id = contextvars.ContextVar('current_estabelecimento_id', default=None)


@contextmanager
def usar_estabelecimento(estabelecimento_id):
    """Define o estabelecimento ativo no contexto atual (usado por comandos CLI/cron,
    que não passam pelo before_request que faz isso automaticamente nas requests web)."""
    token = current_estabelecimento_id.set(estabelecimento_id)
    try:
        yield
    finally:
        current_estabelecimento_id.reset(token)


class TenantMixin:
    """Mixin para modelos pertencentes a um Estabelecimento (isolamento entre clínicas)."""

    @declared_attr
    def estabelecimento_id(cls):
        return db.Column(db.Integer, db.ForeignKey('estabelecimento.id'), nullable=False)


@event.listens_for(Session, "do_orm_execute")
def _filtrar_por_estabelecimento_atual(execute_state):
    """Injeta automaticamente `estabelecimento_id == <atual>` em todo SELECT
    de modelos TenantMixin. Sem isso, qualquer `Modelo.query...` esquecido
    sem filtro vazaria dados entre clínicas diferentes."""
    if not execute_state.is_select:
        return
    estabelecimento_id = current_estabelecimento_id.get()
    if estabelecimento_id is None:
        return
    execute_state.statement = execute_state.statement.options(
        with_loader_criteria(
            TenantMixin,
            lambda cls: cls.estabelecimento_id == estabelecimento_id,
            include_aliases=True,
        )
    )


@event.listens_for(Session, "before_flush")
def _preencher_estabelecimento_id_automaticamente(session, flush_context, instances):
    """Preenche `estabelecimento_id` em registros novos com base no estabelecimento
    ativo do contexto, para que a maioria das rotas não precise setar o campo
    manualmente em todo `db.session.add(...)`. Se o código já setou o campo
    explicitamente (ex: ao criar o primeiro admin de um novo estabelecimento),
    esse valor é respeitado e não é sobrescrito."""
    estabelecimento_id = current_estabelecimento_id.get()
    if estabelecimento_id is None:
        return
    for obj in session.new:
        if isinstance(obj, TenantMixin) and getattr(obj, 'estabelecimento_id', None) is None:
            obj.estabelecimento_id = estabelecimento_id


# --- MODELOS DO BANCO DE DADOS ---

class Estabelecimento(db.Model):
    """Modelo para a clínica/empresa cadastrada (tenant do SaaS)."""
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(150), nullable=False)
    logo_filename = db.Column(db.String(200), nullable=True)
    # Identificador público usado no link de agendamento (/agendar/<slug>),
    # para não expor o id numérico interno nem o estabelecimento de outra clínica.
    slug = db.Column(db.String(160), unique=True, nullable=True)

    # Tema/marca (antes em Configuracao, agora por estabelecimento)
    cor_novos_pacientes = db.Column(db.String(50), default='text-success')
    cor_cabecalho = db.Column(db.String(50), default='bg-light navbar-light')
    email_clinica = db.Column(db.String(120))
    senha_email_clinica = db.Column(db.String(200))
    dias_reenvio_lembrete_retorno = db.Column(db.Integer, default=7)

    # Assinatura/trial
    status = db.Column(db.String(20), default='trial', nullable=False)  # trial, ativo, inadimplente, cancelado
    trial_termina_em = db.Column(db.DateTime)
    data_criacao = db.Column(db.DateTime, default=datetime.now)

    def __repr__(self):
        return f'<Estabelecimento {self.nome}>'

    def em_periodo_de_leitura_apenas(self):
        """True quando o estabelecimento não pode mais criar/editar/excluir dados."""
        return self.status in ('inadimplente', 'cancelado')

    def dias_restantes_trial(self):
        if self.status != 'trial' or not self.trial_termina_em:
            return 0
        restante = (self.trial_termina_em - datetime.now()).days
        return max(restante, 0)


def gerar_slug_unico(nome):
    """Gera um slug (ex: 'clinica-bela-pele') a partir do nome da clínica,
    garantindo unicidade global (o slug identifica a clínica no link público
    de agendamento, então não pode colidir entre estabelecimentos diferentes)."""
    import unicodedata
    sem_acento = unicodedata.normalize('NFKD', nome.strip().lower()).encode('ascii', 'ignore').decode('ascii')
    base = re.sub(r'[^a-z0-9]+', '-', sem_acento).strip('-') or 'clinica'
    slug = base
    contador = 2
    while Estabelecimento.query.filter_by(slug=slug).first():
        slug = f"{base}-{contador}"
        contador += 1
    return slug


class User(TenantMixin, UserMixin, db.Model):
    """Modelo para o Profissional/Usuário do sistema"""
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    perfil = db.Column(db.String(20), default='esteta', nullable=False)  # 'admin', 'secretaria', 'esteta'
    # Admin da plataforma (não de uma clínica específica): vê e opera em
    # qualquer Estabelecimento, "entrando" nele via /admin-plataforma. O
    # estabelecimento_id dele aponta para um Estabelecimento "âncora" só para
    # satisfazer a FK do TenantMixin — não é usado para isolar dados dele.
    eh_super_admin = db.Column(db.Boolean, default=False, nullable=False, server_default=db.false())
    estabelecimento = db.relationship('Estabelecimento', backref='usuarios')

    def tem_permissao(self, permissao):
        """Verifica se o usuário tem uma permissão específica"""
        # Super admin e admin têm todas as permissões
        if self.eh_super_admin or self.perfil == 'admin':
            return True
            
        permissoes = {
            # Admin é tratado acima, mas mantemos a lista para clareza
            'admin': ['gerenciar_usuarios', 'gerenciar_pacientes', 'gerenciar_servicos', 'gerenciar_profissionais', 'agendar', 'atender', 'visualizar_relatorios'],
            'secretaria': ['agendar', 'gerenciar_agendamentos', 'gerenciar_pacientes', 'visualizar_pacientes'],
            'esteta': ['visualizar_relatorios', 'atender', 'minha_agenda', 'visualizar_pacientes', 'agendar', 'gerenciar_pacientes']
        }
        return permissao in permissoes.get(self.perfil, [])

class Paciente(TenantMixin, db.Model):
    """Modelo para o Paciente"""
    id = db.Column(db.Integer, primary_key=True)
    nome_completo = db.Column(db.String(150), nullable=False)
    cpf = db.Column(db.String(14), nullable=True) # CPF único *dentro do estabelecimento* (ver UniqueConstraint)
    data_nascimento = db.Column(db.Date)
    telefone = db.Column(db.String(20))
    email = db.Column(db.String(120))
    historico_medico = db.Column(db.Text)
    data_cadastro = db.Column(db.DateTime, default=datetime.utcnow)
    atendimentos = db.relationship('Atendimento', backref='paciente', lazy=True, cascade="all, delete-orphan")
    anamneses = db.relationship('Anamnese', backref='paciente', lazy=True, cascade="all, delete-orphan")
    exames_fisicos = db.relationship('ExameFisico', backref='paciente', lazy=True, cascade="all, delete-orphan")

    __table_args__ = (
        db.UniqueConstraint('estabelecimento_id', 'cpf', name='uq_paciente_estabelecimento_cpf'),
    )

class Anamnese(TenantMixin, db.Model):
    """Modelo para a Anamnese do Paciente"""
    id = db.Column(db.Integer, primary_key=True)
    data_anamnese = db.Column(db.DateTime, default=datetime.utcnow)
    queixa_principal = db.Column(db.Text)
    historico_doenca_atual = db.Column(db.Text)
    historico_patologico_pregresso = db.Column(db.Text)
    historico_familiar = db.Column(db.Text)
    habitos_vida = db.Column(db.Text)
    medicamentos_uso = db.Column(db.Text)
    alergias = db.Column(db.Text)
    paciente_id = db.Column(db.Integer, db.ForeignKey('paciente.id'), nullable=False)

class ExameFisico(TenantMixin, db.Model):
    """Modelo para o Exame Físico do Paciente"""
    id = db.Column(db.Integer, primary_key=True)
    data_exame = db.Column(db.DateTime, default=datetime.utcnow)
    estado_geral = db.Column(db.String(100))
    pele_mucosas = db.Column(db.Text)
    aparelho_respiratorio = db.Column(db.Text)
    aparelho_cardiovascular = db.Column(db.Text)
    abdome = db.Column(db.Text)
    sistema_nervoso = db.Column(db.Text)
    sistema_musculo_esqueletico = db.Column(db.Text)
    pressao_arterial = db.Column(db.String(20))
    frequencia_cardiaca = db.Column(db.String(20))
    temperatura = db.Column(db.String(20))
    saturacao_o2 = db.Column(db.String(20))
    observacoes_gerais = db.Column(db.Text)
    paciente_id = db.Column(db.Integer, db.ForeignKey('paciente.id'), nullable=False)

class Atendimento(TenantMixin, db.Model):
    """Modelo para o Prontuário/Registro de Atendimento"""
    id = db.Column(db.Integer, primary_key=True)
    data_atendimento = db.Column(db.DateTime, default=datetime.utcnow)
    anotacoes = db.Column(db.Text)
    foto_antes = db.Column(db.String(200)) # Nome do arquivo da foto "antes"
    foto_depois = db.Column(db.String(200)) # Nome do arquivo da foto "depois"
    paciente_id = db.Column(db.Integer, db.ForeignKey('paciente.id'), nullable=False)
    procedimentos = db.relationship('ProcedimentoAtendimento', backref='atendimento', lazy=True, cascade="all, delete-orphan")

class ProcedimentoAtendimento(db.Model):
    """Modelo para registrar múltiplos procedimentos em um atendimento.

    Sem estabelecimento_id próprio: só é acessado através de `atendimento_id`,
    e herda o isolamento do Atendimento pai (não precisa de filtro próprio)."""
    id = db.Column(db.Integer, primary_key=True)
    nome_procedimento = db.Column(db.String(200), nullable=False)
    observacoes_procedimento = db.Column(db.Text)
    atendimento_id = db.Column(db.Integer, db.ForeignKey('atendimento.id'), nullable=False)

# --- MODELOS PARA AGENDA ESTÉTICA ---

class ServicoEstetico(TenantMixin, db.Model):
    """Modelo para Serviços/Tratamentos Estéticos oferecidos"""
    id = db.Column(db.Integer, primary_key=True)
    nome_servico = db.Column(db.String(150), nullable=False)
    descricao = db.Column(db.Text)
    duracao_minutos = db.Column(db.Integer, default=60)  # Duração em minutos
    preco = db.Column(db.Float, default=0.0)
    ativo = db.Column(db.Boolean, default=True)
    data_criacao = db.Column(db.DateTime, default=datetime.now)
    # Dias após o atendimento finalizado para enviar lembrete de retorno (ex: 90 para Botox).
    # None/0 desativa o lembrete de retorno para este serviço.
    dias_lembrete_retorno = db.Column(db.Integer, nullable=True)
    agendamentos = db.relationship('AgendamentoServico', backref='servico', lazy=True, cascade="all, delete-orphan")

    __table_args__ = (
        db.UniqueConstraint('estabelecimento_id', 'nome_servico', name='uq_servico_estabelecimento_nome'),
    )

    def __repr__(self):
        return f'<ServicoEstetico {self.nome_servico}>'

class ProfissionalEstetico(TenantMixin, db.Model):
    """Modelo para Profissionais/Esteticistas"""
    id = db.Column(db.Integer, primary_key=True)
    usuario_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    especialidades = db.Column(db.String(500))  # Separadas por vírgula
    telefone_contato = db.Column(db.String(20))
    disponibilidade_status = db.Column(db.String(50), default='disponível')  # disponível, indisponível, de_ferias
    data_inicio_ferias = db.Column(db.Date)
    data_fim_ferias = db.Column(db.Date)
    usuario = db.relationship('User', backref='perfil_profissional')
    horarios_disponíveis = db.relationship('HorarioAtendimento', backref='profissional', lazy=True, cascade="all, delete-orphan")
    agendamentos = db.relationship('AgendamentoServico', backref='profissional', lazy=True)

    def __repr__(self):
        return f'<ProfissionalEstetico {self.usuario.username}>'

    def esta_disponivel(self, data=None):
        """Verifica se o profissional está disponível"""
        if self.disponibilidade_status != 'disponível':
            return False
        if data and self.data_inicio_ferias and self.data_fim_ferias:
            if self.data_inicio_ferias <= data <= self.data_fim_ferias:
                return False
        return True

class HorarioAtendimento(TenantMixin, db.Model):
    """Modelo para Horários de Disponibilidade do Profissional"""
    id = db.Column(db.Integer, primary_key=True)
    profissional_id = db.Column(db.Integer, db.ForeignKey('profissional_estetico.id'), nullable=False)
    dia_semana = db.Column(db.Integer)  # 0=Segunda, 1=Terça, ..., 6=Domingo
    hora_inicio = db.Column(db.Time, nullable=False)  # Ex: 09:00
    hora_fim = db.Column(db.Time, nullable=False)  # Ex: 18:00
    intervalo_minutos = db.Column(db.Integer, default=30)  # Intervalo entre agendamentos
    ativo = db.Column(db.Boolean, default=True)

    DIAS_SEMANA = {
        0: 'Segunda-feira',
        1: 'Terça-feira',
        2: 'Quarta-feira',
        3: 'Quinta-feira',
        4: 'Sexta-feira',
        5: 'Sábado',
        6: 'Domingo'
    }

    def __repr__(self):
        return f'<HorarioAtendimento {self.DIAS_SEMANA.get(self.dia_semana, "")}: {self.hora_inicio}-{self.hora_fim}>'

    def get_nome_dia(self):
        return self.DIAS_SEMANA.get(self.dia_semana, "Desconhecido")

class AgendamentoServico(TenantMixin, db.Model):
    """Modelo para Agendamentos de Serviços Estéticos"""
    id = db.Column(db.Integer, primary_key=True)
    paciente_id = db.Column(db.Integer, db.ForeignKey('paciente.id'), nullable=False)
    profissional_id = db.Column(db.Integer, db.ForeignKey('profissional_estetico.id'), nullable=False)
    servico_id = db.Column(db.Integer, db.ForeignKey('servico_estetico.id'), nullable=False)
    data_agendamento = db.Column(db.DateTime, nullable=False)  # Data e hora do agendamento
    data_criacao = db.Column(db.DateTime, default=datetime.now)
    status = db.Column(db.String(50), default='agendado')  # agendado, confirmado, em_andamento, finalizado, cancelado, no_show
    observacoes = db.Column(db.Text)
    
    # Campos para avaliação pós-atendimento
    avaliacao = db.Column(db.Integer)  # 1-5 estrelas
    comentario_cliente = db.Column(db.Text)

    # Campos para lembretes (CORREÇÃO)
    data_hora_lembrete_enviado = db.Column(db.DateTime, nullable=True)
    metodo_lembrete = db.Column(db.String(50), nullable=True)

    # Lembrete de retorno (recorrência do procedimento): marca o último envio
    # referente a este atendimento finalizado, para controlar a cadência de reenvio.
    data_ultimo_lembrete_retorno_enviado = db.Column(db.DateTime, nullable=True)

    # Relacionamentos
    paciente = db.relationship('Paciente', backref='agendamentos_servicos')

    def __repr__(self):
        return f'<AgendamentoServico {self.paciente.nome_completo} - {self.servico.nome_servico}>'

    def esta_passado(self):
        """Verifica se o agendamento já passou"""
        return self.data_agendamento < datetime.now()

    def pode_cancelar(self):
        """Verifica se o agendamento pode ser cancelado (não está em andamento ou finalizado)"""
        return self.status not in ['em_andamento', 'finalizado', 'cancelado']

    def tempo_restante(self):
        """Retorna tempo restante até o agendamento em minutos"""
        agora = datetime.now()
        if self.data_agendamento < agora:
            return 0
        delta = self.data_agendamento - agora
        return int(delta.total_seconds() / 60)

class AuditLog(TenantMixin, db.Model):
    """Modelo para registrar logs de auditoria de ações importantes."""
    id = db.Column(db.Integer, primary_key=True)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id')) # ID do admin que fez a ação
    username = db.Column(db.String(80)) # Nome do admin
    action = db.Column(db.String(100), nullable=False) # Ex: 'DELETE_USER', 'RESET_PASSWORD'
    target_user_id = db.Column(db.Integer) # ID do usuário afetado
    target_username = db.Column(db.String(80)) # Nome do usuário afetado
    details = db.Column(db.Text) # Detalhes adicionais

    user = db.relationship('User', foreign_keys=[user_id])

# --- ROTAS DE AUTENTICAÇÃO ---

@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))

# --- CONTEXTO DE TENANT E GATE DE ASSINATURA (a cada request) ---

# Rotas que continuam acessíveis mesmo com o estabelecimento em modo
# somente-leitura (trial vencido/inadimplente/cancelado).
ENDPOINTS_ISENTOS_DO_GATE_DE_ASSINATURA = {'assinatura', 'assinatura_checkout', 'logout', 'static'}

# Rotas que o admin da plataforma pode acessar mesmo sem ter "entrado" em
# nenhuma clínica ainda (antes de escolher uma no painel).
ENDPOINTS_PERMITIDOS_SUPER_ADMIN_SEM_CLINICA = {
    'admin_plataforma', 'admin_plataforma_entrar', 'logout', 'static', 'perfil',
}


@app.before_request
def _gerenciar_contexto_multi_tenant():
    """Define o estabelecimento ativo da request e aplica o gate de assinatura.

    A ordem aqui importa: o contexto é resetado para None *antes* de qualquer
    acesso a `current_user` nesta função. Em servidores com múltiplos workers
    sync (Gunicorn), a mesma thread atende várias requests em sequência, e o
    ContextVar não é limpo automaticamente entre elas — se não resetarmos
    primeiro, o próprio `load_user()` (chamado internamente pelo Flask-Login
    ao acessar `current_user` por baixo dos panos) poderia ser filtrado pelo
    estabelecimento de uma request *anterior*, atendida pela mesma thread, e
    deixar de encontrar o usuário desta request.
    """
    current_estabelecimento_id.set(None)

    if not current_user.is_authenticated:
        return

    if current_user.eh_super_admin:
        # Admin da plataforma: o estabelecimento "ativo" é o que ele escolheu
        # no painel /admin-plataforma (guardado na sessão), não o estabelecimento
        # "âncora" do próprio usuário. Sem clínica escolhida, só pode acessar o
        # próprio painel. Nunca passa pelo gate de assinatura — não é cliente
        # pagante, é da equipe da plataforma.
        estabelecimento_entrado_id = session.get('super_admin_estabelecimento_id')
        if estabelecimento_entrado_id:
            current_estabelecimento_id.set(estabelecimento_entrado_id)
        elif request.endpoint not in ENDPOINTS_PERMITIDOS_SUPER_ADMIN_SEM_CLINICA:
            return redirect(url_for('admin_plataforma'))
        return

    estabelecimento = current_user.estabelecimento
    current_estabelecimento_id.set(estabelecimento.id if estabelecimento else None)

    if not estabelecimento:
        return

    # Expira o trial de forma "lazy", checado a cada request, sem depender de cron.
    if estabelecimento.status == 'trial' and estabelecimento.trial_termina_em and datetime.now() > estabelecimento.trial_termina_em:
        estabelecimento.status = 'inadimplente'
        db.session.commit()

    if estabelecimento.em_periodo_de_leitura_apenas():
        eh_escrita = request.method in ('POST', 'PUT', 'PATCH', 'DELETE')
        if eh_escrita and request.endpoint not in ENDPOINTS_ISENTOS_DO_GATE_DE_ASSINATURA:
            flash("Sua assinatura expirou. Assine para continuar criando e editando registros.", "warning")
            return redirect(url_for('assinatura'))

# --- HEALTH CHECK ---

@app.route("/healthz")
def healthz():
    """Usado pelo health check do Render para liberar deploys sem downtime."""
    return {"status": "ok"}, 200

# --- GERENCIADOR DE ERROS ---

@app.errorhandler(404)
def not_found_error(error):
    """Erro 404 - Página não encontrada"""
    logger.warning(f"Página não encontrada: {request.url}")
    return render_template('404.html'), 404

@app.errorhandler(403)
def forbidden_error(error):
    """Erro 403 - Acesso proibido"""
    logger.warning(f"Acesso proibido para: {current_user.username if current_user.is_authenticated else 'anônimo'}")
    return render_template('403.html'), 403

@app.errorhandler(500)
def internal_error(error):
    """Erro 500 - Erro interno do servidor"""
    logger.error(f"Erro interno do servidor: {error}")
    db.session.rollback()
    return render_template('500.html'), 500

# --- FORMULÁRIOS (WTForms) ---

class LoginForm(FlaskForm):
    """Formulário de login."""
    username = StringField('Usuário')
    password = PasswordField('Senha')
    submit = SubmitField('Entrar')
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        user = User.query.filter_by(username=username).first()

        if user and check_password_hash(user.password_hash, password):
            login_user(user)
            return redirect(url_for("home"))
        else:
            flash("Usuário ou senha inválidos.", "danger")
            return redirect(url_for("login"))

    form = LoginForm() # Cria uma instância do formulário
    return render_template("login_clinica.html", form=form)

class RegistroForm(FlaskForm):
    """Formulário de registro."""
    username = StringField('Usuário')
    password = PasswordField('Senha')
    password_confirm = PasswordField('Confirmar Senha')
    perfil = StringField('Perfil') # Campo para o admin selecionar
    submit = SubmitField('Criar Conta')

class AgendamentoForm(FlaskForm):
    """Formulário para agendar/editar um serviço."""
    profissional_id = SelectField('Profissional', coerce=int)
    servico_id = SelectField('Serviço', coerce=int)
    data_agendamento = DateField('Data')
    hora_agendamento = SelectField('Hora')
    observacoes = TextAreaField('Observações')
    submit = SubmitField('Agendar Serviço')

class ProfissionalForm(FlaskForm):
    """Formulário para criar/editar um perfil profissional."""
    usuario_id = SelectField('Usuário', coerce=int, validators=[validators.DataRequired()])
    especialidades = StringField('Especialidades')
    telefone_contato = StringField('Telefone de Contato')
    submit = SubmitField('Salvar Profissional')

class EditarProfissionalForm(FlaskForm):
    """Formulário para editar um perfil profissional existente."""
    especialidades = StringField('Especialidades')
    telefone_contato = StringField('Telefone de Contato')
    submit = SubmitField('Salvar Alterações')

class PacienteForm(FlaskForm):
    """Formulário para criar/editar um paciente."""
    nome_completo = StringField('Nome Completo', validators=[validators.DataRequired()])
    cpf = StringField('CPF')
    data_nascimento = DateField('Data de Nascimento', format='%Y-%m-%d', validators=[validators.Optional()])
    telefone = StringField('Telefone')
    email = StringField('E-mail', validators=[validators.Optional(), validators.Email()])
    historico_medico = TextAreaField('Histórico Médico')
    submit = SubmitField('Salvar Paciente')

    def validate_cpf(self, field):
        """Validador customizado para o campo CPF."""
        if field.data: # Executa apenas se o campo foi preenchido
            if not is_cpf_valid(field.data):
                raise ValidationError('CPF inválido. Verifique o número digitado.')

def is_cpf_valid(cpf: str) -> bool:
    """
    Valida um CPF brasileiro, verificando seus dígitos verificadores.
    Remove formatação e checa casos inválidos conhecidos.
    """
    # 1. Limpa o CPF de caracteres não numéricos
    cpf = ''.join(re.findall(r'\d', str(cpf)))

    # 2. Verifica se tem 11 dígitos
    if len(cpf) != 11:
        return False

    # 3. Verifica se todos os dígitos são iguais (ex: 111.111.111-11)
    if cpf == cpf[0] * 11:
        return False

    # 4. Cálculo do primeiro dígito verificador
    soma = sum(int(cpf[i]) * (10 - i) for i in range(9))
    digito_1 = (soma * 10) % 11
    if digito_1 == 10:
        digito_1 = 0
    if digito_1 != int(cpf[9]):
        return False

    # 5. Cálculo do segundo dígito verificador
    soma = sum(int(cpf[i]) * (11 - i) for i in range(10))
    digito_2 = (soma * 10) % 11
    if digito_2 == 10:
        digito_2 = 0
    if digito_2 != int(cpf[10]):
        return False

    return True

@app.route("/registro", methods=["GET", "POST"])
@login_required
@requer_permissao('gerenciar_usuarios')
def registro():
    """Cria um novo usuário dentro do estabelecimento do admin logado.

    Para criar uma clínica nova (com seu próprio estabelecimento), veja
    `/criar-clinica` — esta rota é só para adicionar membros da equipe a uma
    clínica já existente.
    """
    form = RegistroForm()

    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        password_confirm = request.form.get("password_confirm", "")

        if not username:
            flash("Nome de usuário é obrigatório.", "warning")
            return render_template("registro_clinica.html", form=form)

        if len(username) < 3:
            flash("Nome de usuário deve ter pelo menos 3 caracteres.", "warning")
            return render_template("registro_clinica.html", form=form)

        # Username é único globalmente (entre todos os estabelecimentos), pois
        # o login não pede qual clínica — então essa checagem precisa ignorar
        # o filtro automático por tenant (que filtraria só dentro da clínica atual).
        with usar_estabelecimento(None):
            usuario_existente = User.query.filter_by(username=username).first()
        if usuario_existente:
            flash("Este usuário já existe. Escolha outro nome.", "danger")
            return render_template("registro_clinica.html", form=form)

        # Validação de complexidade da senha
        if len(password) < 8 or not re.search("[a-z]", password) or \
           not re.search("[A-Z]", password) or not re.search("[0-9]", password) or \
           not re.search("[!@#$%^&*()-_=+]", password):
            flash(
                "A senha deve ter pelo menos 8 caracteres, incluindo uma letra maiúscula, "
                "uma minúscula, um número e um símbolo (!@#$%^&*).",
                "warning"
            )
            return render_template("registro_clinica.html", form=form)

        if password != password_confirm:
            flash("As senhas não correspondem.", "warning")
            return render_template("registro_clinica.html", form=form)

        perfil_selecionado = request.form.get("perfil", "esteta")
        perfil = perfil_selecionado if perfil_selecionado in ['admin', 'secretaria', 'esteta'] else 'esteta'

        hashed_password = generate_password_hash(password)
        novo_usuario = User(
            username=username,
            password_hash=hashed_password,
            perfil=perfil,
            estabelecimento_id=current_user.estabelecimento_id,
        )
        db.session.add(novo_usuario)
        db.session.commit()

        flash(f"Usuário '{username}' criado com sucesso! Perfil: {perfil.upper()}.", "success")
        return redirect(url_for("gerenciar_usuarios"))

    return render_template("registro_clinica.html", form=form)

@app.route("/logout")
@login_required
def logout():
    logout_user()
    flash("Você saiu da sua conta.", "info")
    return redirect(url_for("login"))

@app.route("/gerenciar-usuarios")
@login_required
@requer_permissao('gerenciar_usuarios')
def gerenciar_usuarios():
    """Página para gerenciar usuários (apenas ADM)"""
    usuarios = User.query.all()
    return render_template("gerenciar_usuarios.html", usuarios=usuarios)

@app.route("/usuarios/<int:usuario_id>/alterar-perfil/<perfil>", methods=["POST"])
@login_required
@requer_permissao('gerenciar_usuarios')
def alterar_perfil_usuario(usuario_id, perfil):
    """Altera o perfil de um usuário"""
    usuario = db.session.get(User, usuario_id)
    if not usuario:
        flash("Usuário não encontrado.", "danger")
        return redirect(url_for("gerenciar_usuarios"))
    
    if usuario.id == current_user.id:
        flash("Você não pode alterar seu próprio perfil.", "warning")
        return redirect(url_for("gerenciar_usuarios"))
    
    if usuario.username == 'luisaizza':
        flash("Não é permitido alterar o perfil do administrador principal.", "danger")
        return redirect(url_for("gerenciar_usuarios"))
        
    if perfil not in ['admin', 'secretaria', 'esteta']:
        flash("Perfil inválido.", "danger")
        return redirect(url_for("gerenciar_usuarios"))
    
    # Log de auditoria
    log_entry = AuditLog(
        user_id=current_user.id,
        username=current_user.username,
        action='CHANGE_PROFILE',
        target_user_id=usuario.id,
        target_username=usuario.username,
        details=f"Perfil alterado de '{usuario.perfil}' para '{perfil}'."
    )
    db.session.add(log_entry)
    usuario.perfil = perfil
    db.session.commit()
    flash(f"Perfil de '{usuario.username}' alterado para {perfil.upper()}.", "success")
    return redirect(url_for("gerenciar_usuarios"))

@app.route("/usuarios/<int:usuario_id>/deletar", methods=["POST"])
@login_required
@requer_permissao('gerenciar_usuarios')
def deletar_usuario(usuario_id):
    """Deleta um usuário"""
    usuario = db.session.get(User, usuario_id)
    if not usuario:
        flash("Usuário não encontrado.", "danger")
        return redirect(url_for("gerenciar_usuarios"))
    
    if usuario.id == current_user.id:
        flash("Você não pode deletar sua própria conta.", "warning")
        return redirect(url_for("gerenciar_usuarios"))
    
    if usuario.username == 'luisaizza':
        flash("Não é permitido deletar o administrador principal.", "danger")
        return redirect(url_for("gerenciar_usuarios"))
        
    # CORREÇÃO: Deletar o perfil profissional associado antes de deletar o usuário
    # para evitar erro de integridade do banco de dados.
    perfil_profissional = ProfissionalEstetico.query.filter_by(usuario_id=usuario.id).first()
    if perfil_profissional:
        db.session.delete(perfil_profissional)

    username = usuario.username
    db.session.delete(usuario)
    
    # Log de auditoria
    log_entry = AuditLog(
        user_id=current_user.id,
        username=current_user.username,
        action='DELETE_USER',
        target_user_id=usuario_id,
        target_username=username
    )
    db.session.add(log_entry)
    db.session.commit()
    flash(f"Usuário '{username}' deletado com sucesso.", "success")
    return redirect(url_for("gerenciar_usuarios"))

@app.route("/usuarios/<int:usuario_id>/resetar-senha", methods=["POST"])
@login_required
@requer_permissao('gerenciar_usuarios')
def resetar_senha_usuario(usuario_id):
    """Reseta a senha de um usuário para um valor padrão."""
    usuario = db.session.get(User, usuario_id)
    if not usuario:
        flash("Usuário não encontrado.", "danger")
        return redirect(url_for("gerenciar_usuarios"))

    if usuario.id == current_user.id:
        flash("Você não pode resetar sua própria senha por aqui.", "warning")
        return redirect(url_for("gerenciar_usuarios"))

    # Define uma senha padrão forte
    nova_senha_padrao = "Mudar@123"
    usuario.password_hash = generate_password_hash(nova_senha_padrao)
    
    # Log de auditoria
    log_entry = AuditLog(
        user_id=current_user.id,
        username=current_user.username,
        action='RESET_PASSWORD',
        target_user_id=usuario.id,
        target_username=usuario.username
    )
    db.session.add(log_entry)
    db.session.commit()

    logger.info(f"Senha do usuário '{usuario.username}' resetada por '{current_user.username}'.")
    flash(f"A senha do usuário '{usuario.username}' foi resetada para '{nova_senha_padrao}'. O usuário deverá alterá-la no primeiro acesso.", "success")
    return redirect(url_for("gerenciar_usuarios"))

@app.route("/criar-clinica", methods=["GET", "POST"])
def criar_clinica():
    """Cadastro self-service: cria um novo Estabelecimento (clínica) com seu
    primeiro usuário administrador, e inicia o período de trial gratuito.

    Substitui o antigo bootstrap manual via `/setup` — agora qualquer pessoa
    pode criar sua própria clínica diretamente por aqui.
    """
    if current_user.is_authenticated:
        return redirect(url_for("home"))

    if request.method == "POST":
        nome_clinica = request.form.get("nome_clinica", "").strip()
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        password_confirm = request.form.get("password_confirm", "")

        if not nome_clinica:
            flash("O nome da clínica é obrigatório.", "warning")
            return render_template("criar_clinica.html")

        if not username or len(username) < 3:
            flash("Nome de usuário deve ter pelo menos 3 caracteres.", "warning")
            return render_template("criar_clinica.html")

        if User.query.filter_by(username=username).first():
            flash("Este nome de usuário já está em uso. Escolha outro.", "danger")
            return render_template("criar_clinica.html")

        if len(password) < 8 or not re.search("[a-z]", password) or \
           not re.search("[A-Z]", password) or not re.search("[0-9]", password) or \
           not re.search("[!@#$%^&*()-_=+]", password):
            flash(
                "A senha deve ter pelo menos 8 caracteres, incluindo uma letra maiúscula, "
                "uma minúscula, um número e um símbolo (!@#$%^&*).",
                "warning"
            )
            return render_template("criar_clinica.html")

        if password != password_confirm:
            flash("As senhas não correspondem.", "warning")
            return render_template("criar_clinica.html")

        novo_estabelecimento = Estabelecimento(
            nome=nome_clinica,
            slug=gerar_slug_unico(nome_clinica),
            status='trial',
            trial_termina_em=datetime.now() + timedelta(days=30),
        )
        db.session.add(novo_estabelecimento)
        db.session.flush()  # garante novo_estabelecimento.id antes de criar o admin

        admin_user = User(
            username=username,
            password_hash=generate_password_hash(password),
            perfil='admin',
            estabelecimento_id=novo_estabelecimento.id,
        )
        db.session.add(admin_user)
        db.session.commit()

        login_user(admin_user)
        flash(f"Clínica '{nome_clinica}' criada com sucesso! Você tem 30 dias de teste grátis.", "success")
        return redirect(url_for("home"))

    return render_template("criar_clinica.html")

# --- AGENDAMENTO PÚBLICO (paciente agenda sozinho, sem login) ---
#
# Fluxo: paciente acessa /agendar/<slug-da-clinica> (link que o admin
# compartilha), escolhe o serviço, depois profissional + dia/horário
# disponíveis (mesma lógica de disponibilidade usada internamente), e por
# fim seus próprios dados. O agendamento nasce com status='agendado' — o
# mesmo estado "pendente" que qualquer agendamento já nasce hoje — então o
# profissional/equipe precisa confirmar pela agenda normal antes de valer.
# Como não há usuário logado, o contexto do tenant é setado manualmente com
# `usar_estabelecimento(...)` em vez de vir do before_request.

def _resolver_estabelecimento_publico(slug):
    estabelecimento = Estabelecimento.query.filter_by(slug=slug).first()
    if not estabelecimento:
        abort(404)
    return estabelecimento

@app.route("/agendar/<slug>")
def agendar_publico_inicio(slug):
    """Primeira etapa: escolher o serviço desejado."""
    estabelecimento = _resolver_estabelecimento_publico(slug)
    with usar_estabelecimento(estabelecimento.id):
        servicos = ServicoEstetico.query.filter_by(ativo=True).order_by(ServicoEstetico.nome_servico).all()
    return render_template("agendar_publico_servico.html", estabelecimento=estabelecimento,
                           estabelecimento_atual=estabelecimento, servicos=servicos)

@app.route("/agendar/<slug>/horario", methods=["GET", "POST"])
def agendar_publico_horario(slug):
    """Segunda etapa: escolher profissional, dia/horário e informar os próprios dados."""
    estabelecimento = _resolver_estabelecimento_publico(slug)
    servico_id = request.args.get("servico_id", type=int) or request.form.get("servico_id", type=int)

    with usar_estabelecimento(estabelecimento.id):
        servico = db.session.get(ServicoEstetico, servico_id) if servico_id else None
        if not servico or not servico.ativo:
            flash("Selecione um serviço válido para continuar.", "warning")
            return redirect(url_for("agendar_publico_inicio", slug=slug))

        profissionais = ProfissionalEstetico.query.join(User).all()

        if estabelecimento.em_periodo_de_leitura_apenas():
            flash("Esta clínica está temporariamente indisponível para novos agendamentos. Entre em contato diretamente com ela.", "warning")
            return redirect(url_for("agendar_publico_inicio", slug=slug))

        if request.method == "POST":
            profissional_id = request.form.get("profissional_id", type=int)
            data_str = request.form.get("data_agendamento")
            hora_str = request.form.get("hora_agendamento")
            nome_completo = (request.form.get("nome_completo") or "").strip()
            cpf = (request.form.get("cpf") or "").strip()
            telefone = (request.form.get("telefone") or "").strip()
            email = (request.form.get("email") or "").strip()

            erro = None
            if not all([profissional_id, data_str, hora_str, nome_completo, cpf, telefone]):
                erro = "Preencha todos os campos obrigatórios."
            elif not is_cpf_valid(cpf):
                erro = "CPF inválido. Verifique o número digitado."

            data_hora = None
            if not erro:
                try:
                    data_hora = datetime.strptime(f"{data_str} {hora_str}", "%Y-%m-%d %H:%M")
                    if data_hora < datetime.now():
                        erro = "Não é possível agendar para uma data/hora no passado."
                except ValueError:
                    erro = "Data ou horário inválido."

            if not erro:
                # Revalida disponibilidade no servidor (o horário pode ter sido
                # ocupado por outra pessoa entre a página carregar e o envio).
                horarios_validos = calcular_horarios_disponiveis(profissional_id, data_hora.date(), servico.duracao_minutos)
                if data_hora not in horarios_validos:
                    erro = "Este horário não está mais disponível. Escolha outro."

            if erro:
                flash(erro, "danger")
                return render_template("agendar_publico_horario.html",
                                       estabelecimento=estabelecimento, estabelecimento_atual=estabelecimento,
                                       servico=servico, profissionais=profissionais, now=datetime.now())

            paciente = Paciente.query.filter_by(cpf=cpf).first()
            if not paciente:
                paciente = Paciente(nome_completo=nome_completo, cpf=cpf, telefone=telefone, email=email or None)
                db.session.add(paciente)
            else:
                paciente.telefone = telefone or paciente.telefone
                paciente.email = email or paciente.email
            db.session.flush()

            novo_agendamento = AgendamentoServico(
                paciente_id=paciente.id,
                profissional_id=profissional_id,
                servico_id=servico.id,
                data_agendamento=data_hora,
                status='agendado',
                observacoes="Agendado pelo próprio paciente via link público.",
            )
            db.session.add(novo_agendamento)
            db.session.commit()

            logger.info(f"Agendamento público criado: {paciente.nome_completo} - {servico.nome_servico} em {data_hora} (estabelecimento {estabelecimento.id})")
            return redirect(url_for("agendar_publico_sucesso", slug=slug))

        return render_template("agendar_publico_horario.html",
                               estabelecimento=estabelecimento, estabelecimento_atual=estabelecimento,
                               servico=servico, profissionais=profissionais, now=datetime.now())

@app.route("/agendar/<slug>/sucesso")
def agendar_publico_sucesso(slug):
    estabelecimento = _resolver_estabelecimento_publico(slug)
    return render_template("agendar_publico_sucesso.html", estabelecimento=estabelecimento,
                           estabelecimento_atual=estabelecimento)

@app.route("/agendar/<slug>/api/dias-disponiveis/<int:profissional_id>")
def agendar_publico_dias_disponiveis(slug, profissional_id):
    """Equivalente público de /api/profissional/<id>/dias-disponiveis."""
    estabelecimento = _resolver_estabelecimento_publico(slug)
    with usar_estabelecimento(estabelecimento.id):
        dias_trabalho = db.session.query(HorarioAtendimento.dia_semana).filter(
            HorarioAtendimento.profissional_id == profissional_id,
            HorarioAtendimento.ativo == True
        ).distinct().all()
    return jsonify({'dias_disponiveis': [dia[0] for dia in dias_trabalho]})

@app.route("/agendar/<slug>/api/horarios-disponiveis/<int:profissional_id>")
def agendar_publico_horarios_disponiveis(slug, profissional_id):
    """Equivalente público de /agenda/horarios-disponiveis/<id>."""
    estabelecimento = _resolver_estabelecimento_publico(slug)
    data_str = request.args.get('data')
    servico_id = request.args.get('servico_id', type=int)
    if not data_str:
        return jsonify({'erro': 'Data não fornecida'}), 400
    try:
        data = datetime.strptime(data_str, "%Y-%m-%d").date()
    except ValueError:
        return jsonify({'erro': 'Formato de data inválido'}), 400

    with usar_estabelecimento(estabelecimento.id):
        duracao_minutos = 60
        if servico_id:
            servico = db.session.get(ServicoEstetico, servico_id)
            if servico and servico.duracao_minutos:
                duracao_minutos = servico.duracao_minutos
        horarios = calcular_horarios_disponiveis(profissional_id, data, duracao_minutos)
    return jsonify({'horarios': [h.strftime("%H:%M") for h in horarios]})

@app.route("/assinatura")
@login_required
def assinatura():
    """Mostra o status do trial/assinatura do estabelecimento e permite assinar."""
    estabelecimento = current_user.estabelecimento
    return render_template("assinatura.html", estabelecimento=estabelecimento)

@app.route("/assinatura/checkout", methods=["POST"])
@login_required
def assinatura_checkout():
    """Ponto de extensão para a integração com o gateway de pagamento.

    Ainda não há gateway escolhido/conectado — quando houver (Stripe, Mercado
    Pago, etc.), esta rota deve iniciar a cobrança e, via webhook, atualizar
    `estabelecimento.status` para 'ativo' após a confirmação do pagamento.
    """
    flash("A integração de pagamento ainda será configurada em breve. Entre em contato com o suporte para assinar.", "info")
    return redirect(url_for('assinatura'))

# --- PAINEL DO ADMIN DA PLATAFORMA (super admin) ---

@app.route("/admin-plataforma")
@requer_super_admin
def admin_plataforma():
    """Lista todas as clínicas cadastradas, para o admin da plataforma escolher uma e entrar."""
    estabelecimentos = Estabelecimento.query.order_by(Estabelecimento.data_criacao.desc()).all()
    contagens = {}
    with usar_estabelecimento(None):
        for estabelecimento in estabelecimentos:
            contagens[estabelecimento.id] = {
                'usuarios': User.query.filter_by(estabelecimento_id=estabelecimento.id).count(),
                'pacientes': Paciente.query.filter_by(estabelecimento_id=estabelecimento.id).count(),
            }
    estabelecimento_atual_id = session.get('super_admin_estabelecimento_id')
    return render_template(
        "admin_plataforma.html",
        estabelecimentos=estabelecimentos,
        contagens=contagens,
        estabelecimento_atual_id=estabelecimento_atual_id,
    )

@app.route("/admin-plataforma/entrar/<int:estabelecimento_id>", methods=["POST"])
@requer_super_admin
def admin_plataforma_entrar(estabelecimento_id):
    """Admin da plataforma passa a operar dentro da clínica escolhida."""
    estabelecimento = db.session.get(Estabelecimento, estabelecimento_id)
    if not estabelecimento:
        abort(404)
    session['super_admin_estabelecimento_id'] = estabelecimento.id
    flash(f"Você entrou na clínica '{estabelecimento.nome}'.", "success")
    return redirect(url_for('home'))

@app.route("/admin-plataforma/sair", methods=["POST"])
@requer_super_admin
def admin_plataforma_sair():
    """Sai da clínica atual e volta para a lista de clínicas."""
    session.pop('super_admin_estabelecimento_id', None)
    return redirect(url_for('admin_plataforma'))

@app.route("/perfil", methods=["GET", "POST"])
@login_required
def perfil():
    """Página para o usuário alterar sua própria senha."""
    if request.method == "POST":
        senha_atual = request.form.get("senha_atual")
        nova_senha = request.form.get("nova_senha")
        confirmar_senha = request.form.get("confirmar_senha")

        # 1. Verificar se a senha atual está correta
        if not check_password_hash(current_user.password_hash, senha_atual):
            flash("Sua senha atual está incorreta. Tente novamente.", "danger")
            return redirect(url_for('perfil'))

        # 2. Verificar se a nova senha é válida
        if len(nova_senha) < 8 or not re.search("[a-z]", nova_senha) or \
           not re.search("[A-Z]", nova_senha) or not re.search("[0-9]", nova_senha) or \
           not re.search("[!@#$%^&*()-_=+]", nova_senha):
            flash(
                "A nova senha deve ter pelo menos 8 caracteres, incluindo uma letra maiúscula, "
                "uma minúscula, um número e um símbolo (!@#$%^&*).", 
                "warning"
            )
            return redirect(url_for('perfil'))

        # 3. Verificar se a nova senha e a confirmação são iguais
        if nova_senha != confirmar_senha:
            flash("A nova senha e a confirmação não correspondem.", "warning")
            return redirect(url_for('perfil'))
        
        # 4. Atualizar a senha
        current_user.password_hash = generate_password_hash(nova_senha)
        db.session.commit()
        
        flash("Sua senha foi alterada com sucesso!", "success")
        return redirect(url_for('perfil'))

    return render_template("perfil_usuario.html")
# --- ROTAS DA APLICAÇÃO ---

def buscar_proximos_horarios_livres(limite=5):
    """
    Busca os próximos horários livres na clínica, considerando todos os profissionais.
    """
    # Criar uma nova sessão de banco de dados para esta consulta específica.
    # Isso isola a consulta e previne conflitos de 'lazy loading' com outras partes da aplicação,
    # como a busca de horários na página de agendamento.
    from sqlalchemy.orm import sessionmaker, joinedload
    Session = sessionmaker(bind=db.engine)
    session = Session()
    
    try:
        horarios_encontrados = []
        agora = datetime.now()
        
        for dias_a_frente in range(14):
            data_busca = (agora + timedelta(days=dias_a_frente)).date()
            dia_semana = data_busca.weekday()

            # Usamos joinedload para carregar o profissional e o usuário na mesma consulta,
            # evitando o DetachedInstanceError quando a sessão for fechada.
            blocos_de_trabalho = session.query(HorarioAtendimento).options(
                joinedload(HorarioAtendimento.profissional).joinedload(ProfissionalEstetico.usuario)
            ).join(ProfissionalEstetico).filter(
                HorarioAtendimento.dia_semana == dia_semana,
                HorarioAtendimento.ativo == True,
                ProfissionalEstetico.usuario_id.isnot(None),
                ProfissionalEstetico.disponibilidade_status == 'disponível'
            ).order_by(HorarioAtendimento.profissional_id, HorarioAtendimento.hora_inicio).all()

            if not blocos_de_trabalho:
                continue

            agendamentos_do_dia = {
                ag.data_agendamento
                for ag in session.query(AgendamentoServico.data_agendamento).filter(
                    AgendamentoServico.data_agendamento.between(
                        datetime.combine(data_busca, time.min),
                        datetime.combine(data_busca, time.max)
                    ),
                    AgendamentoServico.status != 'cancelado'
                ).all()
            }

            for bloco in blocos_de_trabalho:
                hora_atual = datetime.combine(data_busca, bloco.hora_inicio)
                hora_fim = datetime.combine(data_busca, bloco.hora_fim)

                while hora_atual < hora_fim:
                    if hora_atual > agora and hora_atual not in agendamentos_do_dia:
                        horarios_encontrados.append({
                            'data_hora': hora_atual,
                            'profissional': bloco.profissional
                        })
                        if len(horarios_encontrados) >= limite:
                            return sorted(horarios_encontrados, key=lambda x: x['data_hora'])
                    hora_atual += timedelta(minutes=bloco.intervalo_minutos)

        return sorted(horarios_encontrados, key=lambda x: x['data_hora'])
    finally:
        session.close()


@app.route("/")
@login_required
def home():
    """Página inicial com a lista de pacientes ou dashboard do admin."""
    
    # Se o admin ou esteta clicar no card de pacientes, redireciona para a lista
    if current_user.perfil in ['admin', 'esteta'] and request.args.get('ver') == 'pacientes':
        return redirect(url_for('home_pacientes'))

    # Se for admin ou esteta, mostra o dashboard com estatísticas
    if current_user.perfil in ['admin', 'esteta']:
        from datetime import date, time
        from sqlalchemy import func, select
        total_pacientes = db.session.execute(select(func.count(Paciente.id))).scalar_one()
        total_profissionais = ProfissionalEstetico.query.count()
        
        today_start = datetime.combine(date.today(), time.min)
        today_end = datetime.combine(date.today(), time.max)
        
        agendamentos_hoje_count = AgendamentoServico.query.filter(
            AgendamentoServico.data_agendamento >= today_start,
            AgendamentoServico.data_agendamento <= today_end,
            AgendamentoServico.status != 'cancelado'
        ).count()

        # Agendamentos futuros ainda não confirmados pela equipe — inclui os
        # que vieram do link público de agendamento, que sempre nascem assim.
        aguardando_confirmacao_count = AgendamentoServico.query.filter(
            AgendamentoServico.data_agendamento >= datetime.now(),
            AgendamentoServico.status == 'agendado'
        ).count()

        proximos_agendamentos = AgendamentoServico.query.filter(
            AgendamentoServico.data_agendamento >= datetime.now(),
            AgendamentoServico.status.in_(['agendado', 'confirmado'])
        ).order_by(AgendamentoServico.data_agendamento.asc()).limit(5).all()

        # Nova lógica para buscar horários livres
        proximos_horarios_livres = buscar_proximos_horarios_livres(limite=5)

        # Checklist de primeiros passos: só aparece enquanto a clínica ainda
        # não terminou a configuração básica necessária para o link público
        # de agendamento funcionar de ponta a ponta.
        tem_profissional = ProfissionalEstetico.query.count() > 0
        tem_servico = ServicoEstetico.query.filter_by(ativo=True).count() > 0
        tem_horario = HorarioAtendimento.query.filter_by(ativo=True).count() > 0
        onboarding_completo = tem_profissional and tem_servico and tem_horario

        link_agendamento_publico = None
        if current_user.estabelecimento and current_user.estabelecimento.slug:
            link_agendamento_publico = url_for(
                'agendar_publico_inicio', slug=current_user.estabelecimento.slug, _external=True
            )

        return render_template("home_admin_dashboard.html",
                               total_pacientes=total_pacientes,
                               agendamentos_hoje_count=agendamentos_hoje_count,
                               aguardando_confirmacao_count=aguardando_confirmacao_count,
                               total_profissionais=total_profissionais,
                               proximos_agendamentos=proximos_agendamentos,
                               proximos_horarios_livres=proximos_horarios_livres,
                               tem_profissional=tem_profissional,
                               tem_servico=tem_servico,
                               tem_horario=tem_horario,
                               onboarding_completo=onboarding_completo,
                               link_agendamento_publico=link_agendamento_publico)

    # Para outros perfis, mostra a lista de pacientes
    query = request.args.get('q', '') # Pega o termo de busca da URL
    if query:
        pacientes = Paciente.query.filter(Paciente.nome_completo.ilike(f'%{query}%')).order_by(Paciente.nome_completo).all()
    else:
        pacientes = Paciente.query.order_by(Paciente.nome_completo).all()
    
    return render_template("home_clinica.html", pacientes=pacientes, query=query)

@app.route("/pacientes")
@login_required
@requer_permissao('gerenciar_pacientes')
def home_pacientes():
    """Página dedicada para o admin gerenciar todos os pacientes."""
    query = request.args.get('q', '')
    if query:
        pacientes = Paciente.query.filter(Paciente.nome_completo.ilike(f'%{query}%')).order_by(Paciente.nome_completo).all()
    else:
        pacientes = Paciente.query.order_by(Paciente.nome_completo).all()
    return render_template("home_clinica.html", pacientes=pacientes, query=query)

@app.route("/pacientes/novo", methods=["GET", "POST"])
@login_required
@requer_permissao('gerenciar_pacientes')
def novo_paciente():
    """Formulário para adicionar um novo paciente."""
    form = PacienteForm()
    if form.validate_on_submit():
        cpf = form.cpf.data
        # Validação de CPF único
        if cpf:
            paciente_existente = Paciente.query.filter_by(cpf=cpf).first()
            if paciente_existente:
                flash("Este CPF já está cadastrado no sistema.", "danger")
                return render_template("novo_paciente.html", form=form)

        novo = Paciente(
            nome_completo=form.nome_completo.data,
            cpf=cpf,
            data_nascimento=form.data_nascimento.data,
            telefone=form.telefone.data,
            email=form.email.data,
            historico_medico=form.historico_medico.data
        )
        db.session.add(novo)
        db.session.commit()
        flash("Paciente cadastrado com sucesso!", "success")
        
        # Redireciona para agendamento se o parâmetro 'agendar' estiver presente
        agendar = request.args.get("agendar")
        if agendar:
            return redirect(url_for("agendar_servico", paciente_id=novo.id))
        return redirect(url_for("home"))

    return render_template("novo_paciente.html", form=form)

@app.route("/pacientes/<int:paciente_id>/editar", methods=["GET", "POST"])
@login_required
def editar_paciente(paciente_id):
    """Formulário para editar os dados de um paciente."""
    paciente = db.session.get(Paciente, paciente_id) # CORREÇÃO: Uso de db.session.get
    if not paciente:
        flash("Paciente não encontrado.", "danger")
        return redirect(url_for("home"))

    if request.method == "POST":
        cpf = request.form.get("cpf")
        # Validação de CPF único ao editar
        if cpf:
            paciente_existente = Paciente.query.filter(Paciente.cpf == cpf, Paciente.id != paciente_id).first()
            if paciente_existente:
                flash(f"O CPF '{cpf}' já pertence a outro paciente ({paciente_existente.nome_completo}).", "danger")
                return render_template("editar_paciente.html", paciente=paciente)

        # Converte a string da data para um objeto date
        data_nasc_str = request.form.get("data_nascimento")
        data_nasc_obj = None
        if data_nasc_str:
            data_nasc_obj = datetime.strptime(data_nasc_str, '%Y-%m-%d').date()

        paciente.nome_completo = request.form.get("nome_completo")
        paciente.cpf = cpf
        paciente.data_nascimento = data_nasc_obj
        paciente.telefone = request.form.get("telefone")
        paciente.email = request.form.get("email")
        paciente.historico_medico = request.form.get("historico_medico")
        db.session.commit()
        flash("Dados do paciente atualizados com sucesso!", "success")
        return redirect(url_for("ver_paciente", paciente_id=paciente.id))

    return render_template("editar_paciente.html", paciente=paciente)

@app.route("/pacientes/<int:paciente_id>/deletar", methods=["POST"])
@login_required
def deletar_paciente(paciente_id):
    paciente = db.session.get(Paciente, paciente_id) # CORREÇÃO: Uso de db.session.get
    if paciente:
        db.session.delete(paciente)
        db.session.commit()
        flash("Paciente excluído com sucesso.", "success")
    return redirect(url_for("home"))

@app.route("/pacientes/<int:paciente_id>")
@login_required
@requer_permissao('visualizar_pacientes')
def ver_paciente(paciente_id):
    """Página de detalhes de um paciente e seus atendimentos."""
    paciente = db.session.get(Paciente, paciente_id) # CORREÇÃO: Uso de db.session.get
    if not paciente:
        flash("Paciente não encontrado.", "danger")
        return redirect(url_for("home"))
    
    # Ordena os atendimentos do mais recente para o mais antigo (direto no banco de dados)
    atendimentos = Atendimento.query.filter_by(
        paciente_id=paciente_id
    ).order_by(Atendimento.data_atendimento.desc()).all()

    return render_template("ver_paciente.html", paciente=paciente, atendimentos=atendimentos, agendamentos_servicos=paciente.agendamentos_servicos)

@app.route("/pacientes/<int:paciente_id>/atendimento/novo", methods=["POST"])
@login_required
def novo_atendimento(paciente_id):
    """Adiciona um novo registro de atendimento para um paciente."""
    paciente = db.session.get(Paciente, paciente_id) # CORREÇÃO: Uso de db.session.get
    if not paciente:
        flash("Paciente não encontrado.", "danger")
        return redirect(url_for("home"))

    try:
        # Lógica para salvar as fotos
        foto_antes_filename = None
        foto_depois_filename = None

        foto_antes_file = request.files.get('foto_antes')
        if foto_antes_file and foto_antes_file.filename:
            if not allowed_file(foto_antes_file.filename):
                flash("Formato de arquivo não permitido para foto 'antes'. Use apenas .jpg, .jpeg ou .png", "warning")
                return redirect(url_for("ver_paciente", paciente_id=paciente_id))
            
            # Garante que a extensão seja preservada e o nome seja seguro
            ext = foto_antes_file.filename.rsplit('.', 1)[1].lower()
            name = secure_filename(foto_antes_file.filename.rsplit('.', 1)[0])
            if not name: name = "imagem"
            foto_antes_filename = f"{uuid.uuid4().hex}_{name}.{ext}"
            
            foto_antes_file.save(os.path.join(app.config["UPLOAD_FOLDER"], foto_antes_filename))

        foto_depois_file = request.files.get('foto_depois')
        if foto_depois_file and foto_depois_file.filename:
            if not allowed_file(foto_depois_file.filename):
                flash("Formato de arquivo não permitido para foto 'depois'. Use apenas .jpg, .jpeg ou .png", "warning")
                return redirect(url_for("ver_paciente", paciente_id=paciente_id))
            
            ext = foto_depois_file.filename.rsplit('.', 1)[1].lower()
            name = secure_filename(foto_depois_file.filename.rsplit('.', 1)[0])
            if not name: name = "imagem"
            foto_depois_filename = f"{uuid.uuid4().hex}_{name}.{ext}"
            
            foto_depois_file.save(os.path.join(app.config["UPLOAD_FOLDER"], foto_depois_filename))
    except Exception as e:
        logger.error(f"Erro ao salvar imagens: {e}")
        flash("Erro ao processar as imagens. Verifique o tamanho e o formato.", "danger")
        return redirect(url_for("ver_paciente", paciente_id=paciente_id))

    atendimento = Atendimento(
        anotacoes=request.form.get("anotacoes"),
        foto_antes=foto_antes_filename,
        foto_depois=foto_depois_filename,
        paciente_id=paciente_id
    )
    db.session.add(atendimento)
    db.session.commit()

    # Lógica para múltiplos procedimentos
    procedimentos_str = request.form.get("procedimentos_realizados")
    if procedimentos_str:
        procedimentos_list = [p.strip() for p in procedimentos_str.split(',') if p.strip()]
        for proc_name in procedimentos_list:
            novo_procedimento = ProcedimentoAtendimento(
                nome_procedimento=proc_name,
                atendimento_id=atendimento.id
            )
            db.session.add(novo_procedimento)
        db.session.commit() # Commit after adding all procedures

    flash("Novo atendimento registrado com sucesso!", "success")
    return redirect(url_for("ver_paciente", paciente_id=paciente_id))

@app.route("/atendimento/procedimento/<int:procedimento_id>/deletar", methods=["POST"])
@login_required
def deletar_procedimento(procedimento_id):
    """Remove um procedimento de um atendimento."""
    proc = db.session.get(ProcedimentoAtendimento, procedimento_id)
    if proc:
        # Verifica permissão (quem pode atender pode gerenciar procedimentos)
        if not current_user.tem_permissao('atender'):
             flash("Você não tem permissão para excluir procedimentos.", "danger")
             return redirect(url_for('home'))
             
        atendimento_id = proc.atendimento_id
        paciente_id = proc.atendimento.paciente_id
        db.session.delete(proc)
        db.session.commit()
        flash("Procedimento removido com sucesso.", "success")
        return redirect(url_for("ver_paciente", paciente_id=paciente_id))
    
    flash("Procedimento não encontrado.", "danger")
    return redirect(url_for("home"))

@app.route("/pacientes/<int:paciente_id>/anamnese/nova", methods=["GET", "POST"])
@login_required
def nova_anamnese(paciente_id):
    """Adiciona um novo registro de anamnese para um paciente."""
    paciente = db.session.get(Paciente, paciente_id) # CORREÇÃO: Uso de db.session.get
    if not paciente:
        flash("Paciente não encontrado.", "danger")
        return redirect(url_for("home"))

    if request.method == "POST":
        nova = Anamnese(
            queixa_principal=request.form.get("queixa_principal"),
            historico_doenca_atual=request.form.get("historico_doenca_atual"),
            historico_patologico_pregresso=request.form.get("historico_patologico_pregresso"),
            historico_familiar=request.form.get("historico_familiar"),
            habitos_vida=request.form.get("habitos_vida"),
            medicamentos_uso=request.form.get("medicamentos_uso"),
            alergias=request.form.get("alergias"),
            paciente_id=paciente_id
        )
        db.session.add(nova)
        db.session.commit()
        flash("Anamnese registrada com sucesso!", "success")
        return redirect(url_for("ver_paciente", paciente_id=paciente_id))

    return render_template("nova_anamnese.html", paciente=paciente)

@app.route("/pacientes/<int:paciente_id>/exame_fisico/novo", methods=["GET", "POST"])
@login_required
def novo_exame_fisico(paciente_id):
    """Adiciona um novo registro de exame físico para um paciente."""
    paciente = db.session.get(Paciente, paciente_id) # CORREÇÃO: Uso de db.session.get
    if not paciente:
        flash("Paciente não encontrado.", "danger")
        return redirect(url_for("home"))

    try:
        if request.method == "POST":
            novo = ExameFisico(
                estado_geral=request.form.get("estado_geral"),
                pele_mucosas=request.form.get("pele_mucosas"),
                aparelho_respiratorio=request.form.get("aparelho_respiratorio"),
                aparelho_cardiovascular=request.form.get("aparelho_cardiovascular"),
                abdome=request.form.get("abdome"),
                sistema_nervoso=request.form.get("sistema_nervoso"),
                sistema_musculo_esqueletico=request.form.get("sistema_musculo_esqueletico"),
                pressao_arterial=request.form.get("pressao_arterial"),
                frequencia_cardiaca=request.form.get("frequencia_cardiaca"),
                temperatura=request.form.get("temperatura"),
                saturacao_o2=request.form.get("saturacao_o2"),
                observacoes_gerais=request.form.get("observacoes_gerais"),
                paciente_id=paciente_id
            )
            db.session.add(novo)
            db.session.commit()
            flash("Exame físico registrado com sucesso!", "success")
            return redirect(url_for("ver_paciente", paciente_id=paciente_id))
    except Exception as e:
        db.session.rollback()
        logger.error(f"Erro ao salvar exame físico: {e}")
        flash("Erro ao salvar o exame físico. Tente novamente.", "danger")

    return render_template("novo_exame_fisico.html", paciente=paciente)

@app.route("/pacientes/<int:paciente_id>/anamnese/<int:anamnese_id>/editar", methods=["GET", "POST"])
@login_required
@requer_permissao('atender')
def editar_anamnese(paciente_id, anamnese_id):
    """Edita um registro de anamnese existente."""
    anamnese = db.session.get(Anamnese, anamnese_id)
    if not anamnese or anamnese.paciente_id != paciente_id:
        flash("Registro de anamnese não encontrado ou não pertence a este paciente.", "danger")
        return redirect(url_for('ver_paciente', paciente_id=paciente_id))

    if request.method == "POST":
        try:
            anamnese.queixa_principal = request.form.get("queixa_principal")
            anamnese.historico_doenca_atual = request.form.get("historico_doenca_atual")
            anamnese.historico_patologico_pregresso = request.form.get("historico_patologico_pregresso")
            anamnese.historico_familiar = request.form.get("historico_familiar")
            anamnese.habitos_vida = request.form.get("habitos_vida")
            anamnese.medicamentos_uso = request.form.get("medicamentos_uso")
            anamnese.alergias = request.form.get("alergias")
            db.session.commit()
            flash("Anamnese atualizada com sucesso!", "success")
            return redirect(url_for("ver_paciente", paciente_id=paciente_id))
        except Exception as e:
            db.session.rollback()
            logger.error(f"Erro ao editar anamnese: {e}")
            flash("Ocorreu um erro ao atualizar a anamnese. Tente novamente.", "danger")

    return render_template("editar_anamnese.html", paciente=anamnese.paciente, anamnese=anamnese)


@app.route("/pacientes/<int:paciente_id>/exame_fisico/<int:exame_id>/editar", methods=["GET", "POST"])
@login_required
@requer_permissao('atender')
def editar_exame_fisico(paciente_id, exame_id):
    """Edita um registro de exame físico existente."""
    exame = db.session.get(ExameFisico, exame_id)
    if not exame or exame.paciente_id != paciente_id:
        flash("Registro de exame físico não encontrado ou não pertence a este paciente.", "danger")
        return redirect(url_for('ver_paciente', paciente_id=paciente_id))

    if request.method == "POST":
        try:
            exame.estado_geral = request.form.get("estado_geral")
            exame.pele_mucosas = request.form.get("pele_mucosas")
            exame.aparelho_respiratorio = request.form.get("aparelho_respiratorio")
            exame.aparelho_cardiovascular = request.form.get("aparelho_cardiovascular")
            exame.abdome = request.form.get("abdome")
            exame.sistema_nervoso = request.form.get("sistema_nervoso")
            exame.sistema_musculo_esqueletico = request.form.get("sistema_musculo_esqueletico")
            exame.pressao_arterial = request.form.get("pressao_arterial")
            exame.frequencia_cardiaca = request.form.get("frequencia_cardiaca")
            exame.temperatura = request.form.get("temperatura")
            exame.saturacao_o2 = request.form.get("saturacao_o2")
            exame.observacoes_gerais = request.form.get("observacoes_gerais")
            db.session.commit()
            flash("Exame físico atualizado com sucesso!", "success")
            return redirect(url_for("ver_paciente", paciente_id=paciente_id))
        except Exception as e:
            db.session.rollback()
            logger.error(f"Erro ao editar exame físico: {e}")
            flash("Ocorreu um erro ao atualizar o exame físico. Tente novamente.", "danger")

    return render_template("editar_exame_fisico.html", paciente=exame.paciente, exame=exame)
# --- ROTAS DE AGENDA ESTÉTICA ---

@app.route("/agenda")
@login_required
def agenda():
    """Visualiza a agenda geral de atendimentos"""
    pagina = request.args.get('pagina', 1, type=int)
    
    # Filtra agendamentos por data (próximos 30 dias)
    data_inicio = datetime.now()
    data_fim = data_inicio + timedelta(days=30)
    
    agendamentos = AgendamentoServico.query.filter(
        AgendamentoServico.data_agendamento >= data_inicio,
        AgendamentoServico.data_agendamento <= data_fim
    ).order_by(AgendamentoServico.data_agendamento.asc()).paginate(page=pagina, per_page=10)
    
    logger.info(f"Usuário {current_user.username} acessou a agenda")
    return render_template("agenda_clinica.html", agendamentos=agendamentos)

@app.route("/agenda/minha")
@login_required
def minha_agenda():
    """Visualiza a agenda do cliente (seus agendamentos)"""
    pagina = request.args.get('pagina', 1, type=int)
    
    # Busca pacientes do usuário (se for profissional) ou seus agendamentos como cliente
    if hasattr(current_user, 'perfil_profissional') and current_user.perfil_profissional:
        # Mostra agendamentos como profissional
        agendamentos = AgendamentoServico.query.filter_by(
            profissional_id=current_user.perfil_profissional[0].id
        ).order_by(AgendamentoServico.data_agendamento.asc()).paginate(page=pagina, per_page=10)
    else:
        # Mostra agendamentos do paciente (se o usuário for um paciente)
        # Esta lógica pode ser ajustada se usuários puderem ser pacientes
        agendamentos = AgendamentoServico.query.filter_by(
            paciente_id=current_user.id # Assumindo que o ID do usuário pode ser um ID de paciente
        ).order_by(AgendamentoServico.data_agendamento.asc()).paginate(page=pagina, per_page=10)
    
    return render_template("minha_agenda.html", agendamentos=agendamentos)

@app.route("/agenda-calendario")
@login_required
def agenda_calendario():
    """Exibe agenda em formato de calendário"""
    # Buscar todos os agendamentos
    agendamentos_db = AgendamentoServico.query.all()
    
    # Converter para formato JSON
    agendamentos_json = []
    for ag in agendamentos_db:
        agendamentos_json.append({
            'id': ag.id,
            'paciente_id': ag.paciente_id,
            'paciente': ag.paciente.nome_completo,
            'profissional': ag.profissional.usuario.username.upper(),
            'profissional_id': ag.profissional_id,
            'servico': ag.servico.nome_servico,
            'data': ag.data_agendamento.strftime('%Y-%m-%d'),
            'hora': ag.data_agendamento.strftime('%H:%M'),
            'status': ag.status,
            'observacoes': ag.observacoes or ''
        })
    
    profissionais = ProfissionalEstetico.query.all()
    profissionais_dados = [{'id': p.id, 'nome': p.usuario.username.upper()} for p in profissionais]
    
    return render_template("agenda_calendario.html", 
                         agendamentos=agendamentos_json,
                         profissionais=profissionais,
                         profissionais_dados=profissionais_dados)

@app.route("/admin/horarios-profissional/<int:profissional_id>", methods=["GET", "POST"])
@login_required
def gerenciar_horarios_profissional(profissional_id):
    """Gerencia horários de disponibilidade de um profissional"""
    profissional = db.session.get(ProfissionalEstetico, profissional_id) # CORREÇÃO: Uso de db.session.get
    if not profissional:
        flash("Profissional não encontrado.", "danger")
        return redirect(url_for("listar_profissionais"))
    
    if request.method == "POST":
        acao = request.form.get("acao")

        if acao == "adicionar":
            try:
                dia_semana = int(request.form.get("dia_semana"))
                hora_inicio = time.fromisoformat(request.form.get("hora_inicio"))
                hora_fim = time.fromisoformat(request.form.get("hora_fim"))
                intervalo = int(request.form.get("intervalo_minutos"))

                if hora_inicio >= hora_fim:
                    flash("A hora de início deve ser anterior à hora de término.", "warning")
                    return redirect(url_for("gerenciar_horarios_profissional", profissional_id=profissional_id))

                # Verifica se já existe um horário idêntico
                existe = HorarioAtendimento.query.filter_by(
                    profissional_id=profissional_id,
                    dia_semana=dia_semana,
                    hora_inicio=hora_inicio,
                    hora_fim=hora_fim
                ).first()

                if existe:
                    flash("Este bloco de horário exato já está cadastrado.", "warning")
                else:
                    novo_horario = HorarioAtendimento(
                        profissional_id=profissional_id,
                        dia_semana=dia_semana,
                        hora_inicio=hora_inicio,
                        hora_fim=hora_fim,
                        intervalo_minutos=intervalo,
                        ativo=True
                    )
                    db.session.add(novo_horario)
                    db.session.commit()
                    flash(f"Novo bloco de horário adicionado para {HorarioAtendimento.DIAS_SEMANA[dia_semana]}!", "success")
            except (ValueError, TypeError):
                flash("Dados inválidos. Verifique os campos e tente novamente.", "danger")
            except Exception as e:
                db.session.rollback()
                flash(f"Erro ao adicionar horário: {str(e)}", "danger")
                logger.error(f"Erro em gerenciar_horarios: {e}")

        elif acao == "deletar":
            horario_id = request.form.get("horario_id", type=int)
            horario = db.session.get(HorarioAtendimento, horario_id)
            if horario and horario.profissional_id == profissional_id:
                db.session.delete(horario)
                db.session.commit()
                flash("Bloco de horário removido com sucesso!", "success")

        elif acao == "alternar_status":
            horario_id = request.form.get("horario_id", type=int)
            horario = db.session.get(HorarioAtendimento, horario_id)
            if horario and horario.profissional_id == profissional_id:
                horario.ativo = not horario.ativo
                db.session.commit()
                status = "ativado" if horario.ativo else "desativado"
                flash(f"Horário {status} com sucesso!", "success")
        
        return redirect(url_for("gerenciar_horarios_profissional", profissional_id=profissional_id))
    
    horarios = HorarioAtendimento.query.filter_by(profissional_id=profissional_id).order_by(
        HorarioAtendimento.dia_semana,
        HorarioAtendimento.hora_inicio
    ).all()
    
    return render_template("gerenciar_horarios.html", 
                         profissional=profissional,
                         horarios=horarios,
                         dias_semana=HorarioAtendimento.DIAS_SEMANA)

@app.route("/agendar-servico/<int:paciente_id>", methods=["GET", "POST"])
@login_required
@requer_permissao('agendar')
def agendar_servico(paciente_id):
    """Agenda um serviço estético para um paciente"""
    paciente = db.session.get(Paciente, paciente_id) # CORREÇÃO: Uso de db.session.get
    if not paciente:
        flash("Paciente não encontrado.", "danger")
        return redirect(url_for("home"))
    
    # Verifica permissão
    if not current_user.tem_permissao('agendar'):
        flash("Você não tem permissão para agendar serviços.", "danger")
        return redirect(url_for("home"))
    
    servicos = ServicoEstetico.query.filter_by(ativo=True).all()
    profissionais = ProfissionalEstetico.query.all()
    
    form = AgendamentoForm()
    form.servico_id.choices = [(s.id, s.nome_servico) for s in servicos]
    form.profissional_id.choices = [(p.id, p.usuario.username.upper()) for p in profissionais]

    if request.method == "POST":
        profissional_id = request.form.get("profissional_id", type=int)
        servico_id = request.form.get("servico_id", type=int)
        data_str = request.form.get("data_agendamento")
        hora_str = request.form.get("hora_agendamento")
        observacoes = request.form.get("observacoes")
        # Validações
        if not all([profissional_id, servico_id, data_str, hora_str]):
            flash("Todos os campos são obrigatórios.", "warning")
            return render_template("agendar_servico.html", 
                                 paciente=paciente, 
                                 servicos=servicos, 
                                 profissionais=profissionais,
                                 now=datetime.now(),
                                 form=form)
        
        try:
            # Combina data e hora
            data_hora = datetime.strptime(f"{data_str} {hora_str}", "%Y-%m-%d %H:%M")
            
            # Verifica se o horário está no passado
            if data_hora < datetime.now():
                flash("Não é possível agendar para uma data/hora no passado.", "warning")
                return render_template("agendar_servico.html", 
                                     paciente=paciente, 
                                     servicos=servicos, 
                                     profissionais=profissionais,
                                     now=datetime.now(),
                                     form=form)
            
            # Verifica conflitos de agendamento
            conflito = AgendamentoServico.query.filter(
                AgendamentoServico.profissional_id == profissional_id,
                AgendamentoServico.status != 'cancelado',  # CORREÇÃO: Usar filter() para operadores !=
                AgendamentoServico.data_agendamento == data_hora
            ).first()
            
            if conflito:
                flash("Este horário já está agendado. Escolha outro.", "danger")
                return render_template("agendar_servico.html", 
                                     paciente=paciente, 
                                     servicos=servicos, 
                                     profissionais=profissionais,
                                     now=datetime.now(),
                                     form=form)
            
            # Cria novo agendamento
            novo_agendamento = AgendamentoServico(
                paciente_id=paciente_id,
                profissional_id=profissional_id,
                servico_id=servico_id,
                data_agendamento=data_hora,
                status='agendado',
                observacoes=observacoes
            )
            
            db.session.add(novo_agendamento)
            db.session.commit()

            # Enviar e-mail de confirmação
            if paciente.email:
                assunto = f"Confirmação de Agendamento - {current_user.estabelecimento.nome}"
                corpo = f"""
                <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; border: 1px solid #e0e0e0; border-radius: 8px; overflow: hidden;">
                    <div style="background-color: #f8f9fa; padding: 20px; text-align: center; border-bottom: 1px solid #e0e0e0;">
                        <img src="cid:logo_clinica" alt="Logo Clínica" style="max-height: 80px;">
                    </div>
                    <div style="padding: 30px; background-color: #ffffff;">
                        <h2 style="color: #0d6efd; margin-top: 0; text-align: center;">Agendamento Confirmado!</h2>
                        <p style="color: #555; font-size: 16px;">Olá, <strong>{paciente.nome_completo}</strong>!</p>
                        <p style="color: #555; font-size: 16px;">Seu agendamento foi realizado com sucesso. Confira os detalhes abaixo:</p>
                        
                        <div style="background-color: #f8f9fa; border-left: 4px solid #0d6efd; padding: 15px; margin: 20px 0;">
                            <p style="margin: 5px 0; color: #333;"><strong>Serviço:</strong> {novo_agendamento.servico.nome_servico}</p>
                            <p style="margin: 5px 0; color: #333;"><strong>Data:</strong> {data_hora.strftime('%d/%m/%Y')}</p>
                            <p style="margin: 5px 0; color: #333;"><strong>Horário:</strong> {data_hora.strftime('%H:%M')}</p>
                            <p style="margin: 5px 0; color: #333;"><strong>Profissional:</strong> {novo_agendamento.profissional.usuario.username.upper()}</p>
                        </div>
                        
                        <p style="color: #555; font-size: 14px; text-align: center;">Caso precise reagendar, entre em contato conosco.</p>
                    </div>
                    <div style="background-color: #f8f9fa; padding: 15px; text-align: center; color: #888; font-size: 12px; border-top: 1px solid #e0e0e0;">
                        <p style="margin: 0;">&copy; {datetime.now().year} {current_user.estabelecimento.nome}. Todos os direitos reservados.</p>
                    </div>
                </div>
                """
                enviar_email(current_user.estabelecimento, paciente.email, assunto, corpo)
            
            logger.info(f"Agendamento criado: {paciente.nome_completo} - {novo_agendamento.servico.nome_servico} em {data_hora}")
            flash(f"Serviço agendado com sucesso para {data_hora.strftime('%d/%m/%Y às %H:%M')}!", "success")
            return redirect(url_for("ver_paciente", paciente_id=paciente_id))
        
        except ValueError as e:
            flash(f"Erro ao processar data/hora: {str(e)}", "danger")
            return render_template("agendar_servico.html", 
                                 paciente=paciente, 
                                 servicos=servicos, 
                                 profissionais=profissionais,
                                 now=datetime.now(),
                                 form=form)
    
    return render_template("agendar_servico.html", 
                         paciente=paciente, 
                         servicos=servicos, 
                         profissionais=profissionais,
                         now=datetime.now(),
                         form=form)

def calcular_horarios_disponiveis(profissional_id, data, duracao_minutos=60, ignorar_agendamento_id=None):
    """Calcula os horários de início disponíveis para um profissional numa data.

    Considera a duração do serviço: um horário só entra na lista se o
    profissional estiver livre durante *todo* o atendimento, não só no
    instante inicial — evita oferecer um horário que sobreporia o fim de um
    atendimento mais longo já agendado (ex: um Botox de 90min agendado às
    14h bloqueia até as 15h30, não só o slot das 14h)."""
    profissional = db.session.get(ProfissionalEstetico, profissional_id)
    if not profissional or not profissional.esta_disponivel(data):
        return []

    dia_semana = data.weekday()
    horarios_do_dia = HorarioAtendimento.query.filter_by(
        profissional_id=profissional_id,
        dia_semana=dia_semana,
        ativo=True
    ).order_by(HorarioAtendimento.hora_inicio).all()

    if not horarios_do_dia:
        return []

    query_agendamentos = AgendamentoServico.query.filter(
        AgendamentoServico.profissional_id == profissional_id,
        db.func.date(AgendamentoServico.data_agendamento) == data,
        AgendamentoServico.status != 'cancelado'
    )
    if ignorar_agendamento_id:
        query_agendamentos = query_agendamentos.filter(AgendamentoServico.id != ignorar_agendamento_id)

    ocupados = []
    for ag in query_agendamentos.all():
        inicio_ocupado = ag.data_agendamento
        duracao_ocupada = ag.servico.duracao_minutos if ag.servico and ag.servico.duracao_minutos else 60
        ocupados.append((inicio_ocupado, inicio_ocupado + timedelta(minutes=duracao_ocupada)))

    agora = datetime.now()
    duracao = timedelta(minutes=duracao_minutos or 60)
    horarios = []

    for horario_bloco in horarios_do_dia:
        hora_atual = datetime.combine(data, horario_bloco.hora_inicio)
        hora_fim_bloco = datetime.combine(data, horario_bloco.hora_fim)

        while hora_atual + duracao <= hora_fim_bloco:
            fim_candidato = hora_atual + duracao
            conflita = any(
                hora_atual < fim_ocupado and fim_candidato > inicio_ocupado
                for inicio_ocupado, fim_ocupado in ocupados
            )
            if not conflita and hora_atual > agora:
                horarios.append(hora_atual)
            hora_atual += timedelta(minutes=horario_bloco.intervalo_minutos)

    return horarios


@app.route("/agenda/horarios-disponiveis/<int:profissional_id>")
@login_required
@requer_permissao('agendar')
def horarios_disponiveis(profissional_id):
    """Retorna horários disponíveis para um profissional (JSON)"""
    data_str = request.args.get('data')
    servico_id = request.args.get('servico_id', type=int)
    ignorar_agendamento_id = request.args.get('ignorar_agendamento_id', type=int)

    if not data_str:
        return jsonify({'erro': 'Data não fornecida'}), 400

    try:
        data = datetime.strptime(data_str, "%Y-%m-%d").date()
    except ValueError:
        return jsonify({'erro': 'Formato de data inválido'}), 400

    duracao_minutos = 60
    if servico_id:
        servico = db.session.get(ServicoEstetico, servico_id)
        if servico and servico.duracao_minutos:
            duracao_minutos = servico.duracao_minutos

    horarios = calcular_horarios_disponiveis(profissional_id, data, duracao_minutos, ignorar_agendamento_id)
    return jsonify({'horarios': [h.strftime("%H:%M") for h in horarios]})

@app.route("/agendamento/<int:agendamento_id>/editar", methods=["GET", "POST"])
@login_required
@requer_permissao('agendar')
def editar_agendamento(agendamento_id):
    """Edita ou reagenda um serviço estético."""
    agendamento = db.session.get(AgendamentoServico, agendamento_id)
    if not agendamento:
        flash("Agendamento não encontrado.", "danger")
        return redirect(url_for("agenda"))

    if agendamento.status in ['finalizado', 'cancelado']:
        flash(f"Não é possível editar um agendamento com status '{agendamento.status}'.", "warning")
        return redirect(url_for('ver_paciente', paciente_id=agendamento.paciente_id))

    if request.method == "POST":
        profissional_id = request.form.get("profissional_id", type=int)
        servico_id = request.form.get("servico_id", type=int)
        data_str = request.form.get("data_agendamento")
        hora_str = request.form.get("hora_agendamento")
        observacoes = request.form.get("observacoes")

        if not all([profissional_id, servico_id, data_str, hora_str]):
            flash("Todos os campos são obrigatórios.", "warning")
            return redirect(url_for('editar_agendamento', agendamento_id=agendamento_id))

        try:
            data_hora = datetime.strptime(f"{data_str} {hora_str}", "%Y-%m-%d %H:%M")

            if data_hora < datetime.now():
                flash("Não é possível agendar para uma data/hora no passado.", "warning")
                return redirect(url_for('editar_agendamento', agendamento_id=agendamento_id))

            # Verifica conflitos, ignorando o próprio agendamento
            conflito = AgendamentoServico.query.filter(
                AgendamentoServico.id != agendamento_id,
                AgendamentoServico.profissional_id == profissional_id,
                AgendamentoServico.status != 'cancelado',
                AgendamentoServico.data_agendamento == data_hora
            ).first()

            if conflito:
                flash("Este horário já está ocupado por outro agendamento. Escolha outro.", "danger")
                return redirect(url_for('editar_agendamento', agendamento_id=agendamento_id))

            # Atualiza o agendamento
            agendamento.profissional_id = profissional_id
            agendamento.servico_id = servico_id
            agendamento.data_agendamento = data_hora
            agendamento.observacoes = observacoes
            # Se foi reagendado, pode voltar para 'agendado'
            if agendamento.status != 'em_andamento':
                 agendamento.status = 'agendado'

            db.session.commit()
            flash("Agendamento atualizado com sucesso!", "success")
            return redirect(url_for("ver_paciente", paciente_id=agendamento.paciente_id))

        except ValueError as e:
            flash(f"Erro ao processar data/hora: {str(e)}", "danger")
            return redirect(url_for('editar_agendamento', agendamento_id=agendamento_id))

    # GET request
    servicos = ServicoEstetico.query.filter_by(ativo=True).all()
    profissionais = ProfissionalEstetico.query.all()
    return render_template("editar_agendamento.html",
                         agendamento=agendamento, paciente=agendamento.paciente,
                         servicos=servicos, profissionais=profissionais, now=datetime.now())

@app.route("/api/profissional/<int:profissional_id>/dias-disponiveis")
@login_required
def dias_disponiveis_profissional(profissional_id):
    """Retorna os dias da semana em que um profissional trabalha."""
    dias_trabalho = db.session.query(HorarioAtendimento.dia_semana).filter(
        HorarioAtendimento.profissional_id == profissional_id,
        HorarioAtendimento.ativo == True
    ).distinct().all()
    
    # Extrai os números dos dias da tupla (ex: [(0,), (1,)]) para uma lista (ex: [0, 1])
    dias_lista = [dia[0] for dia in dias_trabalho]
    
    return jsonify({'dias_disponiveis': dias_lista})


@app.route("/agenda/<int:agendamento_id>/cancelar", methods=["POST"])
@login_required
def cancelar_agendamento(agendamento_id):
    """Cancela um agendamento"""
    agendamento = db.session.get(AgendamentoServico, agendamento_id) # CORREÇÃO: Uso de db.session.get
    
    if not agendamento:
        flash("Agendamento não encontrado.", "danger")
        return redirect(url_for("agenda"))
    
    # Verifica permissão (pode cancelar o próprio agendamento ou ser admin)
    # CORREÇÃO: perfil_profissional é uma lista (relationship sem uselist=False),
    # não um objeto único — acessar `.id` direto quebrava para qualquer perfil
    # não-admin (ex: secretaria) que tentasse cancelar um agendamento.
    perfil_profissional = current_user.perfil_profissional[0] if current_user.perfil_profissional else None
    if current_user.perfil != 'admin' and (not perfil_profissional or perfil_profissional.id != agendamento.profissional_id):
        flash("Você não tem permissão para cancelar este agendamento.", "danger")
        return redirect(url_for("agenda"))
    
    if not agendamento.pode_cancelar():
        flash("Este agendamento não pode ser cancelado.", "warning")
        return redirect(url_for("agenda"))
    
    agendamento.status = 'cancelado'
    db.session.commit()
    
    logger.info(f"Agendamento {agendamento_id} cancelado por {current_user.username}")
    flash("Agendamento cancelado com sucesso.", "success")
    return redirect(url_for("agenda"))

@app.route("/agenda/<int:agendamento_id>/confirmar", methods=["POST"])
@login_required
@requer_permissao('agendar')
def confirmar_agendamento(agendamento_id):
    """Confirma um agendamento"""
    agendamento = db.session.get(AgendamentoServico, agendamento_id) # CORREÇÃO: Uso de db.session.get
    
    if not agendamento:
        flash("Agendamento não encontrado.", "danger")
        return redirect(url_for("agenda"))
    
    if agendamento.status not in ['agendado']:
        flash("Apenas agendamentos em status 'agendado' podem ser confirmados.", "warning")
        return redirect(url_for("agenda"))
    
    agendamento.status = 'confirmado'
    db.session.commit()
    
    logger.info(f"Agendamento {agendamento_id} confirmado por {current_user.username}")
    flash("Agendamento confirmado com sucesso.", "success")
    return redirect(url_for("agenda"))

@app.route("/agenda/<int:agendamento_id>/iniciar", methods=["POST"])
@login_required
@requer_permissao('atender')
def iniciar_atendimento(agendamento_id):
    """Marca um agendamento como 'em_andamento'"""
    agendamento = db.session.get(AgendamentoServico, agendamento_id)
    
    if not agendamento:
        flash("Agendamento não encontrado.", "danger")
        return redirect(url_for("agenda"))
    
    agendamento.status = 'em_andamento'
    db.session.commit()
    
    logger.info(f"Atendimento {agendamento_id} iniciado por {current_user.username}")
    flash("Atendimento iniciado.", "success")
    return redirect(url_for("ver_paciente", paciente_id=agendamento.paciente_id))

@app.route("/agenda/<int:agendamento_id>/finalizar", methods=["POST"])
@login_required
@requer_permissao('atender')
def finalizar_atendimento(agendamento_id):
    """Marca um agendamento como 'finalizado'"""
    agendamento = db.session.get(AgendamentoServico, agendamento_id)
    
    if not agendamento:
        flash("Agendamento não encontrado.", "danger")
        return redirect(url_for("agenda"))
    
    agendamento.status = 'finalizado'
    db.session.commit()
    
    logger.info(f"Atendimento {agendamento_id} finalizado por {current_user.username}")
    flash("Atendimento finalizado com sucesso.", "success")
    return redirect(url_for("ver_paciente", paciente_id=agendamento.paciente_id))

# --- ROTAS PARA GERENCIAR SERVIÇOS ESTÉTICOS (ADMIN) ---

@app.route("/admin/servicos")
@login_required
@requer_permissao('gerenciar_servicos')
def listar_servicos():
    """Lista todos os serviços estéticos"""
    pagina = request.args.get('pagina', 1, type=int)
    servicos = ServicoEstetico.query.paginate(page=pagina, per_page=15)
    return render_template("listar_servicos.html", servicos=servicos)

@app.route("/admin/servicos/<int:servico_id>/editar", methods=["POST"])
@login_required
@requer_permissao('gerenciar_servicos')
def editar_servico(servico_id):
    """Edita um serviço estético."""
    servico = db.session.get(ServicoEstetico, servico_id)
    if not servico:
        flash("Serviço não encontrado.", "danger")
        return redirect(url_for('listar_servicos'))
    
    try:
        servico.nome_servico = request.form.get("nome_servico", servico.nome_servico)
        servico.descricao = request.form.get("descricao", servico.descricao)
        servico.duracao_minutos = request.form.get("duracao_minutos", servico.duracao_minutos, type=int)
        servico.preco = request.form.get("preco", servico.preco, type=float)
        servico.dias_lembrete_retorno = request.form.get("dias_lembrete_retorno", type=int)
        servico.ativo = 'ativo' in request.form

        db.session.commit()
        flash(f"Serviço '{servico.nome_servico}' atualizado com sucesso!", "success")
    except Exception as e:
        db.session.rollback()
        flash(f"Erro ao editar o serviço: {str(e)}", "danger")
        logger.error(f"Erro ao editar serviço ID {servico_id}: {e}")
        
    return redirect(url_for('listar_servicos'))

@app.route("/admin/servicos/<int:servico_id>/deletar", methods=["POST"])
@login_required
@requer_permissao('gerenciar_servicos')
def deletar_servico(servico_id):
    """Deleta um serviço estético."""
    servico = db.session.get(ServicoEstetico, servico_id)
    if not servico:
        flash("Serviço não encontrado.", "danger")
        return redirect(url_for('listar_servicos'))
    
    if servico.agendamentos:
        flash("Não é possível deletar um serviço que já possui agendamentos.", "warning")
        return redirect(url_for('listar_servicos'))
        
    db.session.delete(servico)
    db.session.commit()
    flash(f"Serviço '{servico.nome_servico}' deletado com sucesso.", "success")
    return redirect(url_for('listar_servicos'))

@app.route("/admin/servicos/novo", methods=["GET", "POST"])
@login_required
@requer_permissao('gerenciar_servicos')
def novo_servico():
    """Cria um novo serviço estético"""
    if request.method == "POST":
        nome = request.form.get("nome_servico")
        descricao = request.form.get("descricao")
        duracao = request.form.get("duracao_minutos", type=int, default=60)
        preco = request.form.get("preco", type=float, default=0.0)
        dias_lembrete_retorno = request.form.get("dias_lembrete_retorno", type=int)

        if not nome:
            flash("Nome do serviço é obrigatório.", "warning")
            return render_template("novo_servico.html")

        if ServicoEstetico.query.filter_by(nome_servico=nome).first():
            flash("Um serviço com este nome já existe.", "danger")
            return render_template("novo_servico.html")

        novo = ServicoEstetico(
            nome_servico=nome,
            descricao=descricao,
            duracao_minutos=duracao,
            preco=preco,
            dias_lembrete_retorno=dias_lembrete_retorno
        )
        
        db.session.add(novo)
        db.session.commit()
        
        logger.info(f"Serviço '{nome}' criado por {current_user.username}")
        flash(f"Serviço '{nome}' criado com sucesso!", "success")
        return redirect(url_for("listar_servicos"))
    
    return render_template("novo_servico.html")

@app.route("/admin/profissionais")
@login_required
@requer_permissao('gerenciar_profissionais')
def listar_profissionais():
    """Lista todos os profissionais"""
    pagina = request.args.get('pagina', 1, type=int)
    profissionais = ProfissionalEstetico.query.paginate(page=pagina, per_page=15)
    return render_template("listar_profissionais.html", profissionais=profissionais)

@app.route("/admin/profissionais/novo", methods=["GET", "POST"])
@login_required
@requer_permissao('gerenciar_profissionais')
def novo_profissional():
    """Cria um novo perfil de profissional associado a um usuário."""
    # Busca usuários que são 'esteta' e ainda não têm perfil profissional
    usuarios_sem_perfil = User.query.filter(
        User.perfil == 'esteta',
        ~User.id.in_(db.session.query(ProfissionalEstetico.usuario_id))
    ).all()
    
    form = ProfissionalForm()
    form.usuario_id.choices = [(u.id, u.username) for u in usuarios_sem_perfil]

    if form.validate_on_submit():
        usuario_id = form.usuario_id.data
        
        # Verifica se o usuário já tem um perfil profissional (dupla verificação)
        if ProfissionalEstetico.query.filter_by(usuario_id=usuario_id).first():
            flash("Este usuário já possui um perfil profissional cadastrado.", "danger")
            return redirect(url_for('listar_profissionais'))

        novo_profissional = ProfissionalEstetico(
            usuario_id=usuario_id,
            especialidades=form.especialidades.data,
            telefone_contato=form.telefone_contato.data,
            disponibilidade_status='disponível'
        )
        db.session.add(novo_profissional)
        db.session.commit()
        
        flash("Perfil profissional criado com sucesso!", "success")
        return redirect(url_for('listar_profissionais'))
    
    if not usuarios_sem_perfil:
        flash("Não há usuários com perfil 'esteta' disponíveis para criar um perfil profissional.", "info")

    return render_template("novo_profissional.html", form=form)

@app.route("/admin/profissionais/<int:profissional_id>/editar", methods=["GET", "POST"])
@login_required
@requer_permissao('gerenciar_profissionais')
def editar_profissional(profissional_id):
    """Edita os dados de um profissional."""
    form = EditarProfissionalForm()
    profissional = db.session.get(ProfissionalEstetico, profissional_id)
    if not profissional:
        flash("Profissional não encontrado.", "danger")
        return redirect(url_for('listar_profissionais'))

    if form.validate_on_submit():
        profissional.especialidades = form.especialidades.data
        profissional.telefone_contato = form.telefone_contato.data
        profissional.disponibilidade_status = request.form.get("disponibilidade_status")

        if profissional.disponibilidade_status == 'de_ferias':
            data_inicio_str = request.form.get("data_inicio_ferias")
            if data_inicio_str:
                profissional.data_inicio_ferias = datetime.strptime(data_inicio_str, '%Y-%m-%d').date()
            else:
                profissional.data_inicio_ferias = None

            data_fim_str = request.form.get("data_fim_ferias")
            if data_fim_str:
                profissional.data_fim_ferias = datetime.strptime(data_fim_str, '%Y-%m-%d').date()
            else:
                profissional.data_fim_ferias = None
        else: # Se não está de férias, limpa as datas
            profissional.data_inicio_ferias = None
            profissional.data_fim_ferias = None
            
        try:
            db.session.commit()
            flash(f"Dados do profissional '{profissional.usuario.username}' atualizados com sucesso!", "success")
            return redirect(url_for('listar_profissionais'))
        except Exception as e:
            db.session.rollback()
            flash(f"Erro ao atualizar o profissional: {str(e)}", "danger")
            logger.error(f"Erro ao editar profissional ID {profissional_id}: {e}")

    return render_template("editar_profissional.html", profissional=profissional, form=form)

@app.route("/admin/profissionais/<int:profissional_id>/deletar", methods=["POST"])
@login_required
@requer_permissao('gerenciar_profissionais')
def deletar_profissional(profissional_id):
    """Deleta um perfil profissional."""
    profissional = db.session.get(ProfissionalEstetico, profissional_id)
    if not profissional:
        flash("Profissional não encontrado.", "danger")
        return redirect(url_for('listar_profissionais'))

    # Regra de negócio: não permitir deletar profissional com agendamentos
    if profissional.agendamentos:
        flash(f"Não é possível deletar o profissional '{profissional.usuario.username}' pois ele possui agendamentos associados.", "warning")
        return redirect(url_for('listar_profissionais'))

    nome_profissional = profissional.usuario.username
    db.session.delete(profissional)
    db.session.commit()
    
    flash(f"Perfil profissional de '{nome_profissional}' deletado com sucesso.", "success")
    logger.info(f"Perfil profissional de '{nome_profissional}' (ID: {profissional_id}) foi deletado por {current_user.username}.")
    return redirect(url_for('listar_profissionais'))

@app.route("/admin/auditoria")
@login_required
@requer_permissao('gerenciar_usuarios') # Apenas admins podem ver os logs
def auditoria_logs():
    """Exibe os logs de auditoria do sistema."""
    pagina = request.args.get('pagina', 1, type=int)
    logs = AuditLog.query.order_by(AuditLog.timestamp.desc()).paginate(page=pagina, per_page=20)
    return render_template("auditoria_logs.html", logs=logs)

@app.route("/admin/personalizar-tema", methods=["GET", "POST"])
@login_required
@requer_permissao('gerenciar_usuarios') # Apenas admins podem personalizar
def personalizar_tema():
    """Página para personalizar a marca/tema do estabelecimento (cores, logo, e-mail)."""
    estabelecimento = current_user.estabelecimento

    if request.method == "POST":
        nome = request.form.get("nome")
        cor_novos = request.form.get("cor_novos_pacientes")
        cor_cabecalho = request.form.get("cor_cabecalho")
        email_clinica = request.form.get("email_clinica")
        senha_email = request.form.get("senha_email_clinica")
        dias_reenvio_retorno = request.form.get("dias_reenvio_lembrete_retorno", type=int)

        if nome:
            estabelecimento.nome = nome
        if cor_novos:
            estabelecimento.cor_novos_pacientes = cor_novos
        if cor_cabecalho:
            estabelecimento.cor_cabecalho = cor_cabecalho
        if email_clinica is not None:  # Pode ser string vazia para limpar
            estabelecimento.email_clinica = email_clinica
        if senha_email is not None:
            estabelecimento.senha_email_clinica = senha_email
        if dias_reenvio_retorno and dias_reenvio_retorno > 0:
            estabelecimento.dias_reenvio_lembrete_retorno = dias_reenvio_retorno

        logo_file = request.files.get('logo')
        if logo_file and logo_file.filename:
            if not allowed_file(logo_file.filename):
                flash("Formato de logo não permitido. Use apenas .jpg, .jpeg ou .png", "warning")
                return redirect(url_for('personalizar_tema'))
            ext = logo_file.filename.rsplit('.', 1)[1].lower()
            logo_filename = f"{uuid.uuid4().hex}.{ext}"
            pasta_logos = os.path.join(app.config['UPLOAD_FOLDER'], 'logos')
            os.makedirs(pasta_logos, exist_ok=True)
            logo_file.save(os.path.join(pasta_logos, logo_filename))
            estabelecimento.logo_filename = logo_filename

        db.session.commit()
        flash("Aparência atualizada com sucesso!", "success")
        return redirect(url_for('personalizar_tema'))

    return render_template("personalizar_tema.html", estabelecimento=estabelecimento)

@app.route("/uploads/<filename>")
@login_required
def uploaded_file(filename):
    """Serve os arquivos de imagem que foram upados."""
    return send_from_directory(app.config["UPLOAD_FOLDER"], filename)

@app.route("/uploads/logos/<filename>")
@login_required
def uploaded_logo(filename):
    """Serve as logos de estabelecimentos."""
    return send_from_directory(os.path.join(app.config["UPLOAD_FOLDER"], "logos"), filename)

@app.route("/api/dashboard-stats")
@login_required
@requer_permissao('visualizar_relatorios') # Garante que só usuários com permissão acessem
def dashboard_stats():
    """Fornece dados agregados para os gráficos do dashboard."""
    
    # 1. Agendamentos por Mês (últimos 12 meses)
    doze_meses_atras = datetime.now() - timedelta(days=365)
    agendamentos_por_mes = db.session.query(
        extract('year', AgendamentoServico.data_agendamento).label('ano'),
        extract('month', AgendamentoServico.data_agendamento).label('mes'),
        func.count(AgendamentoServico.id).label('total')
    ).filter(
        AgendamentoServico.data_agendamento >= doze_meses_atras,
        AgendamentoServico.status.in_(['finalizado', 'em_andamento']) # Apenas atendimentos realizados
    ).group_by('ano', 'mes').order_by('ano', 'mes').all()

    # Formata os dados para o Chart.js
    labels_meses = [f"{int(a.mes):02d}/{a.ano}" for a in agendamentos_por_mes]
    data_meses = [a.total for a in agendamentos_por_mes]

    # 2. Top 5 Serviços mais realizados
    top_servicos = db.session.query(
        ServicoEstetico.nome_servico,
        func.count(AgendamentoServico.id).label('total')
    ).join(ServicoEstetico).filter(
        AgendamentoServico.status.in_(['finalizado', 'em_andamento'])
    ).group_by(ServicoEstetico.nome_servico).order_by(func.count(AgendamentoServico.id).desc()).limit(5).all()

    labels_servicos = [s[0] for s in top_servicos]
    data_servicos = [s[1] for s in top_servicos]

    return jsonify({
        'agendamentos_mensais': {
            'labels': labels_meses,
            'data': data_meses
        },
        'top_servicos': {
            'labels': labels_servicos,
            'data': data_servicos
        }
    })

# --- INICIALIZAÇÃO ---

def criar_profissionais_padrao():
    """Cria profissionais padrão para Estética Avançada com Tratamentos Invasivos"""
    # Verificar se já existem
    dra_patricia_user = User.query.filter_by(username='dra_patricia').first()
    dra_fernanda_user = User.query.filter_by(username='dra_fernanda').first()
    
    try:
        if not dra_patricia_user:
            # Criar usuário DRA. PATRÍCIA
            dra_patricia_user = User(
                username='dra_patricia',
                password_hash=generate_password_hash('123'),
                perfil='esteta'
            )
            db.session.add(dra_patricia_user)
            db.session.flush()
            
            # Criar profissional DRA. PATRÍCIA
            dra_patricia_prof = ProfissionalEstetico(
                usuario_id=dra_patricia_user.id,
                especialidades='Botox, Preenchimento Facial, Harmonização Orofacial, Lifting Facial Não-Cirúrgico',
                telefone_contato='(11) 98765-4321',
                disponibilidade_status='disponível'
            )
            db.session.add(dra_patricia_prof)
            db.session.flush()
            
            # Adicionar horários de DRA. PATRÍCIA (Seg-Sex: 10:00-17:00, Qua: 14:00-20:00)
            horarios_patricia = [
                (0, time(10, 0), time(17, 0)),  # Segunda
                (1, time(10, 0), time(17, 0)),  # Terça
                (2, time(14, 0), time(20, 0)),  # Quarta (estendido)
                (3, time(10, 0), time(17, 0)),  # Quinta
                (4, time(10, 0), time(17, 0)),  # Sexta
                (5, time(10, 0), time(14, 0)),  # Sábado
            ]
            
            for dia, hora_inicio, hora_fim in horarios_patricia:
                horario = HorarioAtendimento(
                    profissional_id=dra_patricia_prof.id,
                    dia_semana=dia,
                    hora_inicio=hora_inicio,
                    hora_fim=hora_fim,
                    intervalo_minutos=45,  # Procedimentos invasivos levam mais tempo
                    ativo=True
                )
                db.session.add(horario)
            
            db.session.commit()
            print("✓ Dra. Patrícia criada com sucesso!")
        
        if not dra_fernanda_user:
            # Criar usuário DRA. FERNANDA
            dra_fernanda_user = User(
                username='dra_fernanda',
                password_hash=generate_password_hash('123'),
                perfil='esteta'
            )
            db.session.add(dra_fernanda_user)
            db.session.flush()
            
            # Criar profissional DRA. FERNANDA
            dra_fernanda_prof = ProfissionalEstetico(
                usuario_id=dra_fernanda_user.id,
                especialidades='Microagulhamento, Laser Ablativo, Peeling Químico, Radiofrequência Facial',
                telefone_contato='(11) 99876-5432',
                disponibilidade_status='disponível'
            )
            db.session.add(dra_fernanda_prof)
            db.session.flush()
            
            # Adicionar horários de DRA. FERNANDA (Seg-Sex: 09:00-18:00, Sab: 09:00-13:00)
            horarios_fernanda = [
                (0, time(9, 0), time(18, 0)),   # Segunda
                (1, time(9, 0), time(18, 0)),   # Terça
                (2, time(9, 0), time(18, 0)),   # Quarta
                (3, time(9, 0), time(18, 0)),   # Quinta
                (4, time(9, 0), time(18, 0)),   # Sexta
                (5, time(9, 0), time(13, 0)),   # Sábado
            ]
            
            for dia, hora_inicio, hora_fim in horarios_fernanda:
                horario = HorarioAtendimento(
                    profissional_id=dra_fernanda_prof.id,
                    dia_semana=dia,
                    hora_inicio=hora_inicio,
                    hora_fim=hora_fim,
                    intervalo_minutos=60,  # Procedimentos de laser/microagulhamento levam mais tempo
                    ativo=True
                )
                db.session.add(horario)
            
            db.session.commit()
            print("✓ Dra. Fernanda criada com sucesso!")
            
        if dra_patricia_user and dra_fernanda_user:
            print("✓ Profissionais de Estética Avançada já cadastradas no sistema!")
        
    except Exception as e:
        print(f"Erro ao criar profissionais: {str(e)}")
        db.session.rollback()

def criar_servicos_padrao():
    """Cria serviços padrão de Estética Avançada com Tratamentos Invasivos"""
    # Serviços pré-configurados
    servicos_data = [
        {
                'nome': 'Botox - Testa e Glabela',
                'descricao': 'Aplicação de toxina botulínica para rugas de expressão na testa e região entre as sobrancelhas',
                'duracao': 30,
                'preco': 450.00
            },
            {
                'nome': 'Botox - Olhos (Pés de Galinha)',
                'descricao': 'Aplicação de botox para reduzir rugas ao redor dos olhos (pés de galinha)',
                'duracao': 30,
                'preco': 400.00
            },
            {
                'nome': 'Botox - Face Completa',
                'descricao': 'Aplicação de botox em toda a face: testa, glabela, olhos e entre-olho',
                'duracao': 45,
                'preco': 600.00
            },
            {
                'nome': 'Preenchimento Labial - Ácido Hialurônico',
                'descricao': 'Aplicação de ácido hialurônico para aumentar volume e definir os lábios',
                'duracao': 30,
                'preco': 500.00
            },
            {
                'nome': 'Preenchimento Facial - Maçãs do Rosto',
                'descricao': 'Preenchimento com ácido hialurônico nas maçãs do rosto para efeito lifting',
                'duracao': 45,
                'preco': 650.00
            },
            {
                'nome': 'Preenchimento - Sulco Nasogeniano',
                'descricao': 'Preenchimento do sulco que vai do nariz até os lados da boca',
                'duracao': 30,
                'preco': 550.00
            },
            {
                'nome': 'Harmonização Orofacial Completa',
                'descricao': 'Combinação de botox e preenchimento para harmonia facial completa',
                'duracao': 90,
                'preco': 1200.00
            },
            {
                'nome': 'Microagulhamento Facial',
                'descricao': 'Tratamento com aparelho de microagulhamento para estimular colágeno e melhorar textura',
                'duracao': 60,
                'preco': 350.00
            },
            {
                'nome': 'Laser Ablativo - Remoção de Manchas',
                'descricao': 'Laser ablativo para remover manchas solares, sardas e lesões benignas',
                'duracao': 45,
                'preco': 800.00
            },
            {
                'nome': 'Laser Ablativo - Rejuvenescimento Facial',
                'descricao': 'Laser ablativo para rejuvenescimento profundo da pele com estímulo de colágeno',
                'duracao': 60,
                'preco': 1000.00
            },
            {
                'nome': 'Peeling Químico - Superficial',
                'descricao': 'Peeling químico leve para refresh e renovação celular',
                'duracao': 45,
                'preco': 300.00
            },
            {
                'nome': 'Peeling Químico - Médio',
                'descricao': 'Peeling químico de profundidade média para rugas finas e manchas',
                'duracao': 60,
                'preco': 600.00
            },
            {
                'nome': 'Radiofrequência Facial',
                'descricao': 'Tratamento com radiofrequência para lifting facial não-cirúrgico e pele firme',
                'duracao': 45,
                'preco': 750.00
            },
            {
                'nome': 'Tratamento Combinado - Botox + Preench.',
                'descricao': 'Combinação de botox com preenchimento facial no mesmo atendimento',
                'duracao': 75,
                'preco': 950.00
            },
            {
                'nome': 'Retoque de Botox',
                'descricao': 'Aplicação de reforço de botox anterior (válido até 3 meses após primeira aplicação)',
                'duracao': 30,
                'preco': 300.00
            }
        ]
    
    # Verifica quantos serviços já existem
    servicos_existentes = ServicoEstetico.query.count()
    try:
        if servicos_existentes == 0:
            for servico_data in servicos_data:
                novo_servico = ServicoEstetico(
                    nome_servico=servico_data['nome'],
                    descricao=servico_data['descricao'],
                    duracao_minutos=servico_data['duracao'],
                    preco=servico_data['preco'],
                    ativo=True
                )
                db.session.add(novo_servico)
            
            db.session.commit()
            print(f"✓ {len(servicos_data)} serviços de Estética Avançada criados com sucesso!")
        else:
            print(f"✓ Serviços já cadastrados no sistema! ({servicos_existentes} serviço(s))")
            
    except Exception as e:
        print(f"Erro ao criar serviços: {str(e)}")
        db.session.rollback()

def verificar_lembretes_diarios():
    """Verifica agendamentos para o dia seguinte e envia lembretes, em todos os
    estabelecimentos ativos.

    Executa uma única passada (sem se reagendar). Em produção, é disparada
    periodicamente pelo job de cron `flask lembretes-diarios` (ver render.yaml),
    não por uma thread dentro do processo web — isso evita que cada worker do
    Gunicorn dispare seu próprio agendamento e duplique e-mails.

    Roda explicitamente um estabelecimento por vez (`usar_estabelecimento`),
    já que comandos CLI não passam pelo before_request que define o
    estabelecimento ativo nas requests web.
    """
    with app.app_context():
        for estabelecimento in Estabelecimento.query.filter(Estabelecimento.status.in_(['trial', 'ativo'])).all():
            with usar_estabelecimento(estabelecimento.id):
                try:
                    amanha = datetime.now().date() + timedelta(days=1)
                    inicio = datetime.combine(amanha, time.min)
                    fim = datetime.combine(amanha, time.max)

                    agendamentos = AgendamentoServico.query.filter(
                        AgendamentoServico.data_agendamento >= inicio,
                        AgendamentoServico.data_agendamento <= fim,
                        AgendamentoServico.status == 'agendado',
                        AgendamentoServico.data_hora_lembrete_enviado.is_(None)
                    ).all()

                    for ag in agendamentos:
                        if ag.paciente.email:
                            assunto = f"Lembrete de Consulta Amanhã - {ag.paciente.nome_completo}"
                            corpo = f"""
                            <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; border: 1px solid #e0e0e0; border-radius: 8px; overflow: hidden;">
                                <div style="background-color: #f8f9fa; padding: 20px; text-align: center; border-bottom: 1px solid #e0e0e0;">
                                    <img src="cid:logo_clinica" alt="Logo Clínica" style="max-height: 80px;">
                                </div>
                                <div style="padding: 30px; background-color: #ffffff;">
                                    <h2 style="color: #ffc107; margin-top: 0; text-align: center;">Lembrete de Consulta</h2>
                                    <p style="color: #555; font-size: 16px;">Olá, <strong>{ag.paciente.nome_completo}</strong>!</p>
                                    <p style="color: #555; font-size: 16px;">Este é um lembrete do seu agendamento para <strong>amanhã</strong>:</p>

                                    <div style="background-color: #fff3cd; border-left: 4px solid #ffc107; padding: 15px; margin: 20px 0;">
                                        <p style="margin: 5px 0; color: #333;"><strong>Serviço:</strong> {ag.servico.nome_servico}</p>
                                        <p style="margin: 5px 0; color: #333;"><strong>Horário:</strong> {ag.data_agendamento.strftime('%H:%M')}</p>
                                        <p style="margin: 5px 0; color: #333;"><strong>Profissional:</strong> {ag.profissional.usuario.username.upper()}</p>
                                    </div>

                                    <p style="color: #555; font-size: 14px; text-align: center;">Estamos aguardando você!</p>
                                </div>
                                <div style="background-color: #f8f9fa; padding: 15px; text-align: center; color: #888; font-size: 12px; border-top: 1px solid #e0e0e0;">
                                    <p style="margin: 0;">&copy; {datetime.now().year} {estabelecimento.nome}. Todos os direitos reservados.</p>
                                </div>
                            </div>
                            """
                            if enviar_email(estabelecimento, ag.paciente.email, assunto, corpo):
                                ag.data_hora_lembrete_enviado = datetime.now()
                                ag.metodo_lembrete = 'Email'
                                db.session.commit()
                except Exception as e:
                    logger.error(f"Erro ao verificar lembretes do estabelecimento {estabelecimento.id}: {e}")


def verificar_lembretes_retorno():
    """Verifica pacientes na hora de repetir um procedimento e envia lembrete.

    Diferente de `verificar_lembretes_diarios` (que avisa sobre um agendamento
    já marcado), esta função identifica pacientes que fizeram um serviço com
    recorrência configurada (`ServicoEstetico.dias_lembrete_retorno`) e que já
    passaram do prazo para repeti-lo, mas ainda não reagendaram. O lembrete se
    repete periodicamente (cadência em `Estabelecimento.dias_reenvio_lembrete_retorno`,
    padrão 7 dias) até o paciente ter um novo agendamento futuro do mesmo
    serviço (com status diferente de 'cancelado').

    Executa uma única passada por estabelecimento ativo; é chamada pelo
    comando `flask lembretes-retorno`, agendado via cron (ver render.yaml).
    """
    with app.app_context():
        for estabelecimento in Estabelecimento.query.filter(Estabelecimento.status.in_(['trial', 'ativo'])).all():
            with usar_estabelecimento(estabelecimento.id):
                try:
                    dias_reenvio = estabelecimento.dias_reenvio_lembrete_retorno or 7
                    agora = datetime.now()
                    servicos = ServicoEstetico.query.filter(
                        ServicoEstetico.dias_lembrete_retorno.isnot(None),
                        ServicoEstetico.dias_lembrete_retorno > 0
                    ).all()

                    for servico in servicos:
                        # Último atendimento finalizado de cada paciente para este serviço
                        subq = db.session.query(
                            AgendamentoServico.paciente_id,
                            func.max(AgendamentoServico.data_agendamento).label('ultima_data')
                        ).filter(
                            AgendamentoServico.servico_id == servico.id,
                            AgendamentoServico.status == 'finalizado'
                        ).group_by(AgendamentoServico.paciente_id).subquery()

                        ultimos_atendimentos = db.session.query(AgendamentoServico).join(
                            subq,
                            db.and_(
                                AgendamentoServico.paciente_id == subq.c.paciente_id,
                                AgendamentoServico.data_agendamento == subq.c.ultima_data
                            )
                        ).filter(
                            AgendamentoServico.servico_id == servico.id,
                            AgendamentoServico.status == 'finalizado'
                        ).all()

                        for atendimento in ultimos_atendimentos:
                            data_prevista = atendimento.data_agendamento + timedelta(days=servico.dias_lembrete_retorno)
                            if agora < data_prevista:
                                continue

                            ja_reagendou = AgendamentoServico.query.filter(
                                AgendamentoServico.paciente_id == atendimento.paciente_id,
                                AgendamentoServico.servico_id == servico.id,
                                AgendamentoServico.status != 'cancelado',
                                AgendamentoServico.data_agendamento > atendimento.data_agendamento
                            ).first()
                            if ja_reagendou:
                                continue

                            ultimo_envio = atendimento.data_ultimo_lembrete_retorno_enviado
                            if ultimo_envio and (agora - ultimo_envio).days < dias_reenvio:
                                continue

                            paciente = atendimento.paciente
                            if not paciente.email:
                                continue

                            assunto = f"Hora de renovar: {servico.nome_servico}"
                            corpo = f"""
                            <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; border: 1px solid #e0e0e0; border-radius: 8px; overflow: hidden;">
                                <div style="background-color: #f8f9fa; padding: 20px; text-align: center; border-bottom: 1px solid #e0e0e0;">
                                    <img src="cid:logo_clinica" alt="Logo Clínica" style="max-height: 80px;">
                                </div>
                                <div style="padding: 30px; background-color: #ffffff;">
                                    <h2 style="color: #0d6efd; margin-top: 0; text-align: center;">Está na hora de retornar!</h2>
                                    <p style="color: #555; font-size: 16px;">Olá, <strong>{paciente.nome_completo}</strong>!</p>
                                    <p style="color: #555; font-size: 16px;">Já faz um tempo desde o seu último atendimento de <strong>{servico.nome_servico}</strong>. Que tal agendar a manutenção?</p>

                                    <div style="background-color: #e7f1ff; border-left: 4px solid #0d6efd; padding: 15px; margin: 20px 0;">
                                        <p style="margin: 5px 0; color: #333;"><strong>Serviço:</strong> {servico.nome_servico}</p>
                                        <p style="margin: 5px 0; color: #333;"><strong>Último atendimento:</strong> {atendimento.data_agendamento.strftime('%d/%m/%Y')}</p>
                                    </div>

                                    <p style="color: #555; font-size: 14px; text-align: center;">Entre em contato com a clínica para agendar seu retorno.</p>
                                </div>
                                <div style="background-color: #f8f9fa; padding: 15px; text-align: center; color: #888; font-size: 12px; border-top: 1px solid #e0e0e0;">
                                    <p style="margin: 0;">&copy; {datetime.now().year} {estabelecimento.nome}. Todos os direitos reservados.</p>
                                </div>
                            </div>
                            """
                            if enviar_email(estabelecimento, paciente.email, assunto, corpo):
                                atendimento.data_ultimo_lembrete_retorno_enviado = agora
                                db.session.commit()
                except Exception as e:
                    logger.error(f"Erro ao verificar lembretes de retorno do estabelecimento {estabelecimento.id}: {e}")


# --- COMANDOS CLI (flask <comando>) ---
# Tabelas são criadas/atualizadas via `flask db upgrade` (Flask-Migrate); cada
# estabelecimento (clínica) e seu primeiro usuário admin são criados via
# cadastro self-service em /criar-clinica. Nada disso roda automaticamente ao
# importar o módulo, para funcionar de forma previsível tanto localmente
# quanto sob Gunicorn no Render.

@app.cli.command("seed-super-admin")
def seed_super_admin_command():
    """Garante que existe um usuário super-admin fixo da plataforma (vê e opera
    em qualquer clínica via /admin-plataforma).

    Idempotente de propósito: roda em todo deploy (ver render.yaml) e nunca
    duplica nem perde o usuário — só cria na primeira vez e depois mantém
    senha/flag sincronizados com as env vars.

    Credenciais via SUPER_ADMIN_USERNAME/SUPER_ADMIN_PASSWORD; o default
    abaixo só existe para não travar o primeiro deploy — troque a senha
    pelo próprio sistema (/perfil) depois do primeiro login.
    """
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    username = os.environ.get("SUPER_ADMIN_USERNAME", "admin")
    password = os.environ.get("SUPER_ADMIN_PASSWORD", "Esqueci001")
    with app.app_context():
        with usar_estabelecimento(None):
            estabelecimento_plataforma = Estabelecimento.query.filter_by(nome='Administração da Plataforma').first()
            if not estabelecimento_plataforma:
                estabelecimento_plataforma = Estabelecimento(
                    nome='Administração da Plataforma', status='ativo',
                    slug=gerar_slug_unico('Administração da Plataforma'),
                )
                db.session.add(estabelecimento_plataforma)
                db.session.commit()

            usuario = User.query.filter_by(username=username).first()
            if usuario:
                usuario.password_hash = generate_password_hash(password)
                usuario.eh_super_admin = True
                usuario.perfil = 'admin'
                db.session.commit()
                print(f"✓ Super admin '{username}' já existia — senha/flag atualizados.")
            else:
                usuario = User(
                    username=username,
                    password_hash=generate_password_hash(password),
                    perfil='admin',
                    eh_super_admin=True,
                    estabelecimento_id=estabelecimento_plataforma.id,
                )
                db.session.add(usuario)
                db.session.commit()
                print(f"✓ Super admin '{username}' criado.")


@app.cli.command("seed-demo")
def seed_demo_command():
    """Cria (se necessário) um estabelecimento de demonstração e popula
    profissionais e serviços de exemplo dentro dele.

    Uso exclusivo de desenvolvimento local — recusa-se a rodar se
    FLASK_ENV=production, pois cria usuários com senha fraca ('123').
    """
    if ENV_NAME == "production":
        print("Comando 'seed-demo' desabilitado em produção (FLASK_ENV=production).")
        return
    if hasattr(sys.stdout, "reconfigure"):
        # Evita UnicodeEncodeError nos prints com "✓" em consoles Windows (cp1252)
        sys.stdout.reconfigure(encoding="utf-8")
    with app.app_context():
        estabelecimento = Estabelecimento.query.filter_by(nome='Clínica Demo').first()
        if not estabelecimento:
            estabelecimento = Estabelecimento(nome='Clínica Demo', status='ativo', slug=gerar_slug_unico('Clínica Demo'))
            db.session.add(estabelecimento)
            db.session.commit()
            print(f"✓ Estabelecimento 'Clínica Demo' criado (id={estabelecimento.id}).")

        with usar_estabelecimento(estabelecimento.id):
            criar_profissionais_padrao()
            criar_servicos_padrao()


@app.cli.command("lembretes-diarios")
def lembretes_diarios_command():
    """Verifica e envia, uma única vez, os lembretes de agendamentos de amanhã.

    Pensado para ser chamado por um job de cron externo (ex: Render Cron Job),
    não por uma thread de longa duração dentro do processo web.
    """
    verificar_lembretes_diarios()


@app.cli.command("lembretes-retorno")
def lembretes_retorno_command():
    """Verifica e envia, uma única vez, os lembretes de retorno de procedimento.

    Pensado para ser chamado por um job de cron externo (ex: Render Cron Job),
    junto com `lembretes-diarios`.
    """
    verificar_lembretes_retorno()


if __name__ == "__main__":
    # Execução local direta (python app_clinica.py) ou pelo .exe empacotado
    # com PyInstaller. Em produção (Render/Gunicorn) este bloco nunca é
    # executado: o WSGI server importa `wsgi:app` sem rodar __main__.
    if getattr(sys, 'frozen', False):
        # Abre o navegador automaticamente após 1.5 segundos
        Timer(1.5, lambda: webbrowser.open("http://127.0.0.1:5000")).start()
        app.run(debug=False)
    else:
        app.run(debug=True)