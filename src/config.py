#!/usr/bin/env python3
# src/config.py

import os
from pathlib import Path

class Config:
    """Configurações centralizadas do servidor Whisper"""
    
    # Diretórios
    PROJECT_ROOT = Path(__file__).parent.parent
    LOGS_DIR = PROJECT_ROOT / "logs"
    DATA_DIR = PROJECT_ROOT / "data"
    TESTS_DIR = PROJECT_ROOT / "tests"
    
    # Servidor Flask
    FLASK_ENV = os.getenv('FLASK_ENV', 'development')
    DEBUG = os.getenv('DEBUG', 'True').lower() == 'true'
    HOST = os.getenv('HOST', '0.0.0.0')
    PORT = int(os.getenv('PORT', 5555))
    
    # Whisper
    WHISPER_MODEL = os.getenv('WHISPER_MODEL', 'tiny')
    LANGUAGE = os.getenv('LANGUAGE', 'pt')
    
    # Upload limits
    MAX_FILE_SIZE = int(os.getenv('MAX_FILE_SIZE', 10 * 1024 * 1024))  # 10MB
    ALLOWED_EXTENSIONS = ['wav']
    
    # Logs
    LOG_LEVEL = os.getenv('LOG_LEVEL', 'DEBUG')
    LOG_FILE = LOGS_DIR / os.getenv('LOG_FILE', 'whisper.log')
    
    # Rate Limiting
    REDIS_URL = os.getenv('REDIS_URL', 'redis://localhost:6379')
    RATE_LIMIT_ENABLED = os.getenv('RATE_LIMIT_ENABLED', 'false').lower() == 'true'
    
    # Segurança
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev-key-change-in-production')
    ALLOWED_ORIGINS = os.getenv('ALLOWED_ORIGINS', 'http://localhost:3000,http://127.0.0.1:3000').split(',')
    
    # Monitoring
    METRICS_ENABLED = os.getenv('METRICS_ENABLED', 'true').lower() == 'true'
    HEALTH_CHECK_INTERVAL = int(os.getenv('HEALTH_CHECK_INTERVAL', 30))
    
    @classmethod
    def validate(cls):
        """Validar configurações"""
        errors = []
        
        # Verificar modelo Whisper válido
        valid_models = ['tiny', 'base', 'small', 'medium', 'large']
        if cls.WHISPER_MODEL not in valid_models:
            errors.append(f"WHISPER_MODEL deve ser um de: {valid_models}")
        
        # Verificar porta válida
        if not (1 <= cls.PORT <= 65535):
            errors.append("PORT deve estar entre 1 e 65535")
        
        # Verificar tamanho de arquivo válido
        if cls.MAX_FILE_SIZE < 1024:  # Mínimo 1KB
            errors.append("MAX_FILE_SIZE deve ser pelo menos 1024 bytes")
        
        if errors:
            raise ValueError("Erros de configuração:\n" + "\n".join(f"- {e}" for e in errors))
        
        return True
    
    @classmethod
    def ensure_directories(cls):
        """Garantir que diretórios necessários existem"""
        for directory in [cls.LOGS_DIR, cls.DATA_DIR]:
            directory.mkdir(parents=True, exist_ok=True)
    
    @classmethod
    def get_summary(cls):
        """Obter resumo das configurações"""
        return {
            'environment': cls.FLASK_ENV,
            'debug': cls.DEBUG,
            'host': cls.HOST,
            'port': cls.PORT,
            'whisper_model': cls.WHISPER_MODEL,
            'language': cls.LANGUAGE,
            'max_file_size_mb': round(cls.MAX_FILE_SIZE / (1024 * 1024), 2),
            'log_level': cls.LOG_LEVEL,
            'metrics_enabled': cls.METRICS_ENABLED
        }

class DevelopmentConfig(Config):
    """Configurações para desenvolvimento"""
    DEBUG = True
    LOG_LEVEL = 'DEBUG'

class ProductionConfig(Config):
    """Configurações para produção"""
    DEBUG = False
    LOG_LEVEL = 'INFO'
    
# Mapping de configurações por ambiente
config_map = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}

def get_config():
    """Obter configuração baseada no ambiente"""
    env = os.getenv('FLASK_ENV', 'development')
    config_class = config_map.get(env, config_map['default'])
    
    # Validar configurações
    config_class.validate()
    config_class.ensure_directories()
    
    return config_class 