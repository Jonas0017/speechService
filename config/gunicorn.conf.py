# Configuração Gunicorn para Produção
import multiprocessing
import os

# Servidor
bind = "0.0.0.0:5555"
workers = min(4, multiprocessing.cpu_count())
worker_class = "sync"
worker_connections = 1000
max_requests = 100
max_requests_jitter = 20
timeout = 120
keepalive = 2

# Logs
accesslog = "/app/logs/access.log"
errorlog = "/app/logs/error.log"
loglevel = "info"

# Processo
pidfile = "/tmp/gunicorn.pid"
preload_app = True
worker_tmp_dir = "/dev/shm"

# Development
reload = os.getenv('FLASK_ENV') == 'development' 