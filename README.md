# 🎙️ Servidor Whisper WAV - SpeechService

Servidor de transcrição de áudio usando OpenAI Whisper **sem dependência de FFmpeg**, otimizado para arquivos WAV e deploy em produção.

## 🚀 Características

✅ **Zero FFmpeg** - Usa apenas bibliotecas Python nativas  
✅ **Suporte WAV nativo** - Processamento direto de arquivos WAV  
✅ **Docker Ready** - Configuração completa para containers  
✅ **Testes automatizados** - Suite completa de testes  
✅ **Monitoramento** - Métricas e health checks integrados  
✅ **Produção Ready** - Configuração Gunicorn + Nginx  

## 📁 Estrutura do Projeto

```
SpeechService/
├── src/                        # Código fonte principal
│   ├── servidor_whisper.py     # Servidor Flask principal
│   ├── config.py               # Configurações centralizadas
│   ├── utils.py                # Funções auxiliares
│   └── monitoring.py           # Monitoramento e métricas
├── docker/                     # Configurações Docker
│   ├── Dockerfile              # Container produção
│   ├── Dockerfile.dev          # Container desenvolvimento
│   └── docker-compose.yml      # Orquestração local
├── scripts/                    # Scripts de automação
│   ├── setup_local.py          # Setup automático
│   ├── test_api.py             # Testes da API
│   ├── load_test.py            # Testes de carga
│   └── validate_deploy.py      # Validação pré-deploy
├── tests/                      # Testes automatizados
│   ├── test_audio/             # Arquivos WAV para teste
│   ├── unit_tests.py           # Testes unitários
│   └── integration_tests.py    # Testes integração
├── config/                     # Configurações
│   ├── nginx.conf              # Configuração proxy
│   ├── gunicorn.conf.py        # Configuração produção
│   └── .env.template           # Template variáveis
└── logs/                       # Diretório de logs
```

## ⚡ Quick Start

### 🔧 Setup Automático
```bash
# 1. Executar setup completo
python scripts/setup_local.py

# 2. Ativar ambiente virtual
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows

# 3. Iniciar servidor
python src/servidor_whisper.py
```

### 🧪 Testes
```bash
# Testar API
python scripts/test_api.py

# Teste de carga
python scripts/load_test.py --requests 10

# Validar deploy
python scripts/validate_deploy.py
```

### 🐳 Docker
```bash
# Build e execução
docker build -f docker/Dockerfile -t whisper-api .
docker run -p 5555:5555 whisper-api

# Desenvolvimento com hot-reload
docker-compose -f docker/docker-compose.yml up
```

## 📋 API Endpoints

### Health Check
```bash
GET /health
```
**Response:**
```json
{
  "status": "ok",
  "model": "tiny",
  "language": "pt",
  "uptime": "2h 15m"
}
```

### Transcrição
```bash
POST /transcribe
Content-Type: multipart/form-data
audioFile: arquivo.wav
```
**Response:**
```json
{
  "transcription": "texto transcrito do áudio",
  "duration": 2.5,
  "file_size": 1024000,
  "processing_time": 1.2
}
```

## ⚙️ Configuração

### Variáveis de Ambiente
```bash
# Servidor
FLASK_ENV=development          # development/production
DEBUG=True                     # true/false
HOST=0.0.0.0                  # Host do servidor
PORT=5555                     # Porta do servidor

# Whisper
WHISPER_MODEL=tiny            # tiny/base/small/medium/large
LANGUAGE=pt                   # Idioma padrão
MAX_FILE_SIZE=10485760        # Tamanho máximo (10MB)

# Logs
LOG_LEVEL=DEBUG               # DEBUG/INFO/WARNING/ERROR
LOG_FILE=logs/whisper.log     # Arquivo de log

# Segurança
SECRET_KEY=your-secret-key    # Chave secreta
ALLOWED_ORIGINS=*             # CORS origins
```

### Modelos Whisper Disponíveis
| Modelo | Tamanho | Velocidade | Qualidade |
|--------|---------|------------|-----------|
| tiny   | 39 MB   | ~32x       | Básica    |
| base   | 74 MB   | ~16x       | Boa       |
| small  | 244 MB  | ~6x        | Melhor    |
| medium | 769 MB  | ~2x        | Excelente |
| large  | 1550 MB | ~1x        | Superior  |

## 🔧 Desenvolvimento

### Requisitos
- Python 3.8+
- 4GB RAM (mínimo)
- Espaço livre: 2GB

### Dependências Principais
```
openai-whisper==20231117
Flask==3.0.0
numpy==1.24.3
soundfile==0.12.1
flask-cors==4.0.0
psutil==5.9.6
```

### Estrutura de Desenvolvimento
```bash
# Instalar dependências de desenvolvimento
pip install -r requirements.txt

# Executar em modo debug
FLASK_ENV=development python src/servidor_whisper.py

# Executar testes
python -m pytest tests/

# Verificar código
flake8 src/
black src/
```

## 🚀 Deploy em Produção

### Coolify (Recomendado)
1. **Conectar repositório** ao Coolify
2. **Configurar variáveis** de ambiente
3. **Deploy automático** via Git push

### Docker Swarm
```bash
# Build da imagem
docker build -t whisper-api:latest .

# Deploy no swarm
docker service create \
  --name whisper-api \
  --replicas 3 \
  --publish 5555:5555 \
  --env WHISPER_MODEL=small \
  whisper-api:latest
```

### Kubernetes
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: whisper-api
spec:
  replicas: 3
  selector:
    matchLabels:
      app: whisper-api
  template:
    metadata:
      labels:
        app: whisper-api
    spec:
      containers:
      - name: whisper-api
        image: whisper-api:latest
        ports:
        - containerPort: 5555
        env:
        - name: WHISPER_MODEL
          value: "small"
```

## 📊 Monitoramento

### Métricas Disponíveis
- **Requests totais/sucessos/erros**
- **Tempo médio de transcrição**
- **Uso de CPU/Memória**
- **Uptime do servidor**
- **Taxa de throughput**

### Health Checks
```bash
# Status básico
curl http://localhost:5555/health

# Métricas detalhadas
curl http://localhost:5555/metrics
```

### Logs
```bash
# Logs em tempo real
tail -f logs/whisper.log

# Logs com filtro
grep "ERROR" logs/whisper.log
grep "transcription" logs/whisper.log
```

## 🔒 Segurança

### Validações Implementadas
✅ **Formato de arquivo** - Apenas WAV aceito  
✅ **Tamanho máximo** - Limite configurável  
✅ **Rate limiting** - Proteção contra spam  
✅ **CORS** - Controle de origens  
✅ **Sanitização** - Nomes de arquivo seguros  

### Recomendações Produção
- Usar HTTPS (SSL/TLS)
- Configurar firewall
- Implementar autenticação
- Monitorar logs de segurança
- Backup regular

## 🐛 Troubleshooting

### Problemas Comuns

**Erro: "FFmpeg não encontrado"**
```bash
# Este projeto NÃO usa FFmpeg
# Use apenas arquivos WAV
```

**Erro: "Modelo não carrega"**
```bash
# Verificar espaço em disco
df -h

# Limpar cache
rm -rf ~/.cache/whisper
```

**Erro: "Out of memory"**
```bash
# Usar modelo menor
export WHISPER_MODEL=tiny

# Ou aumentar RAM do container
docker run -m 4g whisper-api
```

**Erro: "Arquivo muito grande"**
```bash
# Verificar configuração
echo $MAX_FILE_SIZE

# Ou usar arquivo menor (<10MB)
```

## 📈 Performance

### Benchmarks (Modelo Tiny)
- **Arquivo 1s WAV**: ~0.5s processamento
- **Arquivo 10s WAV**: ~2s processamento
- **Throughput**: 5-10 req/s (4GB RAM)
- **Concorrência**: 3-5 requests simultâneas

### Otimizações
- **Cache de modelo** - Modelo carregado uma vez
- **Processamento assíncrono** - Não bloqueia servidor
- **Garbage collection** - Limpeza automática de memória
- **Connection pooling** - Reutilização de conexões

## 🤝 Contribuindo

### Como Contribuir
1. **Fork** o repositório
2. **Criar branch** para feature
3. **Implementar** mudanças
4. **Executar testes**
5. **Submit PR**

### Padrões de Código
- **PEP 8** para Python
- **Type hints** quando possível
- **Docstrings** para funções
- **Testes** para novas features

## 📄 Licença

MIT License - veja [LICENSE](LICENSE) para detalhes.

## 🆘 Suporte

- **Issues**: Use o GitHub Issues
- **Documentação**: Ver `/docs`
- **Exemplos**: Ver `/examples`

---

**Desenvolvido com ❤️ para deploy em produção**