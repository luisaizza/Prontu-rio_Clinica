"""
Configurações da aplicação.

Toda configuração de ambiente (banco, uploads, segredo) deve vir de variáveis
de ambiente. Os valores aqui são apenas defaults seguros para desenvolvimento
local.
"""
import os
from datetime import timedelta

BASE_DIR = os.path.dirname(os.path.abspath(__file__))


def _normalizar_database_url(url: str) -> str:
    """Render (e outros provedores) entregam DATABASE_URL com o prefixo
    'postgres://', mas o SQLAlchemy >= 1.4 exige 'postgresql://'."""
    if url.startswith("postgres://"):
        url = url.replace("postgres://", "postgresql://", 1)
    return url


class Config:
    """Configurações base"""
    # Segurança
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SECURE = False  # Sobrescrito em ProductionConfig
    SESSION_COOKIE_SAMESITE = 'Lax'
    PERMANENT_SESSION_LIFETIME = timedelta(hours=1)
    SECRET_KEY = os.environ.get("SECRET_KEY", "dev-key-change-in-production")

    # Banco de dados
    INSTANCE_FOLDER = os.path.join(BASE_DIR, 'instance')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    _database_url = os.environ.get("DATABASE_URL")
    if _database_url:
        SQLALCHEMY_DATABASE_URI = _normalizar_database_url(_database_url)
    else:
        SQLALCHEMY_DATABASE_URI = f'sqlite:///{os.path.join(INSTANCE_FOLDER, "clinica.db")}'

    # Upload de arquivos
    UPLOAD_FOLDER = os.environ.get(
        "UPLOAD_FOLDER", os.path.join(BASE_DIR, 'uploads_clinica')
    )
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'}

    JSON_AS_ASCII = False


class DevelopmentConfig(Config):
    """Configurações de desenvolvimento"""
    DEBUG = True
    TESTING = False


class ProductionConfig(Config):
    """Configurações de produção"""
    DEBUG = False
    TESTING = False
    SESSION_COOKIE_SECURE = True


class TestingConfig(Config):
    """Configurações de testes"""
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    WTF_CSRF_ENABLED = False
    RATELIMIT_ENABLED = False


config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}


def validar_configuracao_producao(env: str) -> None:
    """Falha rápido se a app for iniciada em produção sem SECRET_KEY própria."""
    if env == 'production' and not os.environ.get("SECRET_KEY"):
        raise RuntimeError(
            "SECRET_KEY não foi definida. Configure a variável de ambiente "
            "SECRET_KEY antes de subir em produção."
        )
