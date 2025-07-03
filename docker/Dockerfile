FROM python:3.11-slim

# Labels para metadata
LABEL maintainer="seu-email@example.com" \
      description="Servidor Whisper WAV sem FFmpeg" \
      version="1.0"

# Instalar dependências do sistema
RUN apt-get update && apt-get install -y \
    gcc \
    libc6-dev \
    libasound2-dev \
    libsndfile1-dev \
    portaudio19-dev \
    curl \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Criar usuário não-root
RUN useradd --create-home --shell /bin/bash --uid 1000 whisper

# Configurar diretório de trabalho
WORKDIR /app

# Copiar requirements primeiro (cache layer)
COPY requirements.txt .

# Instalar dependências Python
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Pre-download do modelo Whisper (cache layer)
RUN python -c "import whisper; whisper.load_model('tiny')" && \
    echo "✅ Modelo Whisper baixado durante build"

# Criar diretórios necessários
RUN mkdir -p logs data tests && \
    chown -R whisper:whisper /app

# Copiar código da aplicação
COPY --chown=whisper:whisper . .

# Mudar para usuário não-root
USER whisper

# Variáveis de ambiente padrão
ENV FLASK_ENV=production \
    WHISPER_MODEL=tiny \
    LANGUAGE=pt \
    PORT=5555 \
    PYTHONUNBUFFERED=1

# Expor porta
EXPOSE 5555

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:5555/health || exit 1

# Comando de inicialização
CMD ["python", "src/servidor_whisper.py"] 