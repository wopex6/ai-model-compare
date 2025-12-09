# Gunicorn Configuration for Production
# Usage: gunicorn --config gunicorn_config.py app:app

import multiprocessing
import os

# Server socket
bind = "127.0.0.1:8000"
backlog = 2048

# Worker processes
workers = multiprocessing.cpu_count() * 2 + 1
worker_class = "sync"
worker_connections = 1000
timeout = 120
keepalive = 5

# Restart workers after this many requests (prevent memory leaks)
max_requests = 1000
max_requests_jitter = 100

# Logging
accesslog = "./logs/access.log"
errorlog = "./logs/error.log"
loglevel = "info"
access_log_format = '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s" %(D)s'

# Process naming
proc_name = "ai-model-compare"

# Server mechanics
daemon = False  # Set to True for background process
pidfile = "./gunicorn.pid"
umask = 0
user = None
group = None
tmp_upload_dir = None

# SSL (if not using Nginx proxy)
# keyfile = None
# certfile = None

# Security
limit_request_line = 4096
limit_request_fields = 100
limit_request_field_size = 8190

# Debugging (production should be False)
reload = False
reload_engine = "auto"
spew = False

# Server hooks
def on_starting(server):
    """Called just before the master process is initialized."""
    server.log.info("🚀 Starting AI Model Compare server...")

def on_reload(server):
    """Called when the server is reloaded."""
    server.log.info("🔄 Reloading AI Model Compare server...")

def when_ready(server):
    """Called just after the server is started."""
    server.log.info("✅ AI Model Compare server is ready!")
    server.log.info(f"   Listening on: {bind}")
    server.log.info(f"   Workers: {workers}")

def worker_int(worker):
    """Called when a worker receives an INT or QUIT signal."""
    worker.log.info("⚠️  Worker received interrupt signal")

def worker_abort(worker):
    """Called when a worker receives the SIGABRT signal."""
    worker.log.info("❌ Worker received abort signal")
