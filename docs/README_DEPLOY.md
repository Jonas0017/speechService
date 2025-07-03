# 🚀 Guia Completo de Deploy - Servidor Whisper

## 📋 Visão Geral

Este é um servidor Flask otimizado para transcrição de áudio WAV usando OpenAI Whisper, preparado para deploy em produção no Coolify.

## 🏗️ Estrutura do Projeto

```
SpeechService/
├── src/                          # Código fonte
│   └── servidor_whisper.py       # Aplicação Flask principal
├── config/                       # Configurações
│   ├── env.template              # Template de variáveis
│   ├── gunicorn.conf.py          # Configuração produção
│   └── nginx.conf                # Configuração proxy
├── docker/                       # Containerização
│   ├── Dockerfile                # Imagem otimizada
│   └── docker-compose.yml        # Orquestração local
├── scripts/                      # Automação
│   ├── setup_local.py            # Setup automático
│   ├── test_api.py               # Testes da API
│   ├── validate_deploy.py        # Validação pré-deploy
│   └── quick_start.bat           # Scripts rápidos
├── tests/                        # Testes
│   └── test_audio/               # Arquivos WAV teste
├── logs/                         # Logs da aplicação
└── requirements.txt              # Dependências Python
```

## 🚀 Quick Start

### 1. Setup Automático
```bash
# Windows
quick_start.bat setup

# Ou manualmente
python scripts/setup_local.py
```

### 2. Ativar Ambiente Virtual
```bash
# Windows
venv\Scripts\activate

# Linux/Mac
source venv/bin/activate
```

### 3. Executar em Desenvolvimento
```bash
# Via script
quick_start.bat dev

# Ou diretamente
python src/servidor_whisper.py
```

### 4. Testar API
```bash
# Executar testes
quick_start.bat test

# Ou diretamente
python scripts/test_api.py
```

## 🧪 Testes Automatizados

### Testes Incluídos
- ✅ Health Check endpoint
- ✅ Validação de uploads
- ✅ Transcrição de WAV
- ✅ Rejeição de arquivos inválidos
- ✅ Limite de tamanho de arquivo
- ✅ Performance e tempo de resposta

### Executar Testes
```bash
# Testes básicos
python scripts/test_api.py

# Testes contra URL específica
python scripts/test_api.py http://localhost:5555
```

## 🐳 Docker

### Build Local
```bash
# Via script
quick_start.bat docker

# Ou manualmente
docker build -f docker/Dockerfile -t whisper-api .
docker run -p 5555:5555 whisper-api
```

### Docker Compose (Desenvolvimento)
```bash
cd docker
docker-compose up
```

### Serviços Incluídos
- **whisper-api**: Servidor principal (porta 5555)
- **nginx**: Proxy reverso (porta 8080)
- **redis**: Cache para rate limiting (porta 6379)

## 🔍 Validação Pré-Deploy

```bash
# Validar antes do deploy
quick_start.bat validate

# Ou diretamente
python scripts/validate_deploy.py
```

### Verificações Incluídas
- ✅ Estrutura de arquivos necessários
- ✅ Modelo Whisper carregando corretamente
- ✅ Build do Docker funcionando
- ✅ Container executando
- ✅ Health checks passando

## 🌐 Endpoints da API

### GET /health
Verificar status do servidor
```bash
curl http://localhost:5555/health
```

**Resposta:**
```json
{
  "status": "ok",
  "message": "Servidor Whisper WAV NATIVO - SEM FFMPEG",
  "model": "tiny",
  "formats_supported": ["WAV apenas"]
}
```

### POST /transcribe
Transcrever arquivo WAV
```bash
curl -X POST \
  -F "audioFile=@exemplo.wav" \
  http://localhost:5555/transcribe
```

**Resposta:**
```json
{
  "transcription": "Texto transcrito do áudio",
  "status": "success",
  "file_size": 1234567,
  "method": "wave_nativo + whisper",
  "audio_duration": "3.45s"
}
```

## ⚙️ Variáveis de Ambiente

### Desenvolvimento (.env)
```env
FLASK_ENV=development
DEBUG=True
PORT=5555
WHISPER_MODEL=tiny
LANGUAGE=pt
MAX_FILE_SIZE=10485760
LOG_LEVEL=DEBUG
```

### Produção (Coolify)
```env
FLASK_ENV=production
DEBUG=False
PORT=5555
WHISPER_MODEL=tiny
LANGUAGE=pt
MAX_FILE_SIZE=10485760
LOG_LEVEL=INFO
SECRET_KEY=seu-secret-key-forte
```

## 🚀 Deploy no Coolify

### 1. Preparação
```bash
# Validar projeto
python scripts/validate_deploy.py

# Commit alterações
git add .
git commit -m "Preparado para deploy"
git push origin main
```

### 2. Configuração no Coolify

1. **Criar novo serviço**
   - Type: Docker
   - Source: Git Repository
   - Repository: `seu-repo/whisper-server`
   - Branch: `main`

2. **Configurar build**
   - Dockerfile Path: `docker/Dockerfile`
   - Build Context: `.`

3. **Variáveis de ambiente**
   ```
   FLASK_ENV=production
   PORT=5555
   WHISPER_MODEL=tiny
   LANGUAGE=pt
   ```

4. **Port mapping**
   - Container Port: `5555`
   - Public Port: `80` (ou conforme necessário)

5. **Health check**
   - Path: `/health`
   - Interval: 30s

### 3. Deploy
- Click "Deploy"
- Aguardar build e inicialização
- Verificar logs para confirmar carregamento do modelo

## 📊 Monitoramento

### Health Check
```bash
# Verificar status
curl https://seu-dominio.com/health

# Deve retornar status 200 com JSON
```

### Logs
```bash
# Via Coolify dashboard
# Ou via Docker
docker logs container-name
```

### Métricas de Performance
- **Tempo de carregamento do modelo**: ~10-30s
- **Tempo de transcrição**: ~1-5s (modelo tiny)
- **Memória RAM**: ~500MB-1GB
- **CPU**: Moderado durante transcrição

## 🔧 Troubleshooting

### Problemas Comuns

#### 1. Modelo Whisper não carrega
```bash
# Verificar dependências
pip install openai-whisper

# Teste manual
python -c "import whisper; whisper.load_model('tiny')"
```

#### 2. Container falha no build
```bash
# Verificar Dockerfile
docker build -f docker/Dockerfile -t whisper-test .

# Verificar logs
docker logs container-name
```

#### 3. API não responde
```bash
# Verificar porta
netstat -tlnp | grep 5555

# Teste local
curl http://localhost:5555/health
```

#### 4. Transcrição falha
```bash
# Verificar formato WAV
file audio.wav

# Deve ser: RIFF (little-endian) data, WAVE audio
```

### Logs de Debug
```bash
# Modo desenvolvimento
export DEBUG=True
export LOG_LEVEL=DEBUG

# Verificar logs
tail -f logs/whisper.log
```

## 📈 Otimizações

### Performance
- Modelo `tiny` para velocidade
- Processamento WAV nativo (sem FFmpeg)
- Cache do modelo Whisper
- Worker processes otimizados

### Segurança
- Validação rigorosa de uploads
- Limite de tamanho de arquivo
- CORS configurado
- Usuário não-root no container

### Escalabilidade
- Stateless design
- Health checks configurados
- Logs estruturados
- Métricas exportáveis

## 🎯 Checklist Final

### Antes do Deploy
- [ ] ✅ Todos os testes passando
- [ ] ✅ Validação pré-deploy OK
- [ ] ✅ Docker build funcionando
- [ ] ✅ Variáveis de ambiente configuradas
- [ ] ✅ Health checks funcionando
- [ ] ✅ Logs estruturados
- [ ] ✅ Documentação atualizada

### Após Deploy
- [ ] ✅ Health check público funcionando
- [ ] ✅ Transcrição de teste funcionando
- [ ] ✅ Logs sendo gerados
- [ ] ✅ Performance aceitável
- [ ] ✅ Monitoramento ativo

## 📞 Suporte

### Logs Importantes
```bash
# Aplicação
logs/whisper.log

# Container
docker logs whisper-container

# Sistema
/var/log/messages
```

### Contatos
- **Documentação**: Este README
- **Código**: GitHub repository
- **Issues**: GitHub Issues
- **Deploy**: Coolify dashboard

---

🎉 **Projeto pronto para produção!** 
Siga este guia para um deploy tranquilo e sem surpresas. 