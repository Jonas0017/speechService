#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from flask import Flask, request, jsonify
from flask_cors import CORS
import tempfile
import os
import logging
import warnings
import time

# Importar módulos da nova estrutura
try:
    from config import get_config
    from utils import load_wav_audio, format_file_size, cleanup_temp_file, get_local_ip
    from monitoring import metrics_collector, get_health_status
    MODULES_AVAILABLE = True
except ImportError as e:
    print(f"⚠️ Módulos não disponíveis: {e}")
    print("📦 Executando em modo compatibilidade...")
    MODULES_AVAILABLE = False
    
    # Fallback para funcionalidade básica
    import socket
    def get_local_ip():
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            ip = s.getsockname()[0]
            s.close()
            return ip
        except:
            return "localhost"

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Suprimir warnings
warnings.filterwarnings("ignore")

# Inicializar Flask
app = Flask(__name__)
CORS(app)

# Carregar configurações
if MODULES_AVAILABLE:
    try:
        config = get_config()
        logger.info("✅ Configurações carregadas dos módulos")
    except Exception as e:
        logger.warning(f"⚠️ Erro ao carregar config: {e}")
        MODULES_AVAILABLE = False

# 🔥 CARREGAR WHISPER UMA VEZ NO INÍCIO
logger.info("🤖 Carregando modelo Whisper...")
import whisper

# Usar configuração ou fallback
if MODULES_AVAILABLE and hasattr(config, 'WHISPER_MODEL'):
    model_name = config.WHISPER_MODEL
else:
    model_name = os.getenv('WHISPER_MODEL', 'tiny')

model = whisper.load_model(model_name)  
logger.info(f"✅ Modelo Whisper '{model_name}' carregado!")

# Fallback para load_wav_audio se módulo não disponível
if not MODULES_AVAILABLE:
    import numpy as np
    import wave
    
    def load_wav_audio(file_path):
        """
        🔥 CARREGA ÁUDIO WAV USANDO BIBLIOTECA NATIVA PYTHON (SEM FFMPEG)
        """
        try:
            logger.info(f"🎵 Carregando WAV: {os.path.basename(file_path)}")
            
            with wave.open(file_path, 'rb') as wav_file:
                # Obter informações do arquivo
                frames = wav_file.readframes(-1)
                sample_rate = wav_file.getframerate()
                channels = wav_file.getnchannels()
                sample_width = wav_file.getsampwidth()
                
                logger.info(f"📊 WAV info: {sample_rate}Hz, {channels}ch, {sample_width}bytes")
                
                # Converter para numpy array
                if sample_width == 1:
                    dtype = np.uint8
                    audio_data = np.frombuffer(frames, dtype=dtype).astype(np.float32) / 128.0 - 1.0
                elif sample_width == 2:
                    dtype = np.int16
                    audio_data = np.frombuffer(frames, dtype=dtype).astype(np.float32) / 32768.0
                elif sample_width == 4:
                    dtype = np.int32
                    audio_data = np.frombuffer(frames, dtype=dtype).astype(np.float32) / 2147483648.0
                else:
                    raise ValueError(f"Sample width {sample_width} não suportado")
                
                # Converter para mono se necessário
                if channels == 2:
                    audio_data = audio_data.reshape(-1, 2).mean(axis=1)
                
                # Resample para 16kHz se necessário
                if sample_rate != 16000:
                    try:
                        from scipy.signal import resample
                        num_samples = int(len(audio_data) * 16000 / sample_rate)
                        audio_data = resample(audio_data, num_samples)
                        logger.info(f"🔄 Resampled de {sample_rate}Hz para 16000Hz")
                    except ImportError:
                        logger.warning("⚠️ scipy não disponível, mantendo sample rate original")
                
                logger.info(f"✅ WAV carregado: {len(audio_data)} samples")
                return audio_data
                
        except Exception as e:
            logger.error(f"❌ Erro ao carregar WAV: {e}")
            raise e

@app.route('/health', methods=['GET'])
def health_check():
    """Endpoint para verificar se o serviço está funcionando"""
    if MODULES_AVAILABLE:
        try:
            # Usar sistema de monitoramento avançado
            health_data = get_health_status()
            return jsonify(health_data), 200
        except Exception as e:
            logger.warning(f"⚠️ Erro no health avançado: {e}")
    
    # Fallback para health básico
    return jsonify({
        "status": "ok", 
        "message": "Servidor Whisper WAV NATIVO - SEM FFMPEG",
        "model": model_name,
        "audio_loader": "wave (Python nativo)",
        "formats_supported": ["WAV apenas"],
        "modules_loaded": MODULES_AVAILABLE
    }), 200

@app.route('/metrics', methods=['GET'])
def get_metrics():
    """Endpoint para métricas (se disponível)"""
    if MODULES_AVAILABLE:
        try:
            metrics_data = metrics_collector.get_metrics()
            return jsonify(metrics_data), 200
        except Exception as e:
            return jsonify({"error": f"Erro ao obter métricas: {e}"}), 500
    else:
        return jsonify({"error": "Módulo de monitoramento não disponível"}), 404

@app.route('/transcribe', methods=['POST'])
def transcribe_audio():
    """Endpoint para transcrever áudio WAV APENAS"""
    start_time = time.time()
    temp_path = None
    
    try:
        logger.info("🎯 Iniciando transcrição WAV...")
        
        # Verificar se arquivo foi enviado
        if 'audioFile' not in request.files:
            logger.error("❌ Nenhum arquivo de áudio enviado")
            if MODULES_AVAILABLE:
                metrics_collector.record_request(success=False)
            return jsonify({"error": "Nenhum arquivo de áudio enviado"}), 400
        
        audio_file = request.files['audioFile']
        logger.info(f"📁 Arquivo recebido: {audio_file.filename}")
        
        if audio_file.filename == '':
            if MODULES_AVAILABLE:
                metrics_collector.record_request(success=False)
            return jsonify({"error": "Nenhum arquivo selecionado"}), 400
        
        # 🔥 SÓ ACEITA WAV
        if not audio_file.filename.lower().endswith('.wav'):
            if MODULES_AVAILABLE:
                metrics_collector.record_request(success=False)
            return jsonify({
                "error": "Apenas arquivos WAV são suportados",
                "received_file": audio_file.filename,
                "supported_formats": ["WAV"]
            }), 400
        
        # Criar arquivo temporário WAV
        with tempfile.NamedTemporaryFile(delete=False, suffix='.wav') as temp_file:
            temp_path = temp_file.name
        
        # Salvar arquivo
        audio_file.save(temp_path)
        file_size = os.path.getsize(temp_path)
        
        # Verificar tamanho máximo
        max_size = 10 * 1024 * 1024  # 10MB padrão
        if MODULES_AVAILABLE and hasattr(config, 'MAX_FILE_SIZE'):
            max_size = config.MAX_FILE_SIZE
        
        if file_size > max_size:
            if MODULES_AVAILABLE:
                metrics_collector.record_request(success=False)
            return jsonify({
                "error": f"Arquivo muito grande. Máximo: {max_size/1024/1024:.1f}MB"
            }), 413
        
        logger.info(f"💾 Arquivo WAV salvo: {temp_path} ({file_size} bytes)")
        
        # 🔥 PROCESSAR WAV COM BIBLIOTECA NATIVA (SEM FFMPEG)
        logger.info("🎵 Processando WAV com biblioteca nativa Python...")
        audio_data = load_wav_audio(temp_path)
        
        # 🔥 TRANSCREVER USANDO ARRAY NUMPY (SEM FFMPEG)
        logger.info("🎯 Transcrevendo com Whisper...")
        
        # Usar configuração de idioma ou fallback
        language = "pt"
        if MODULES_AVAILABLE and hasattr(config, 'LANGUAGE'):
            language = config.LANGUAGE
        
        result = model.transcribe(
            audio_data,  # Array numpy, não caminho de arquivo
            language=language,
            fp16=False,
            verbose=False,
            word_timestamps=False
        )
        
        transcription = str(result["text"]).strip()
        processing_time = time.time() - start_time
        
        logger.info(f"✅ TRANSCRIÇÃO COMPLETA: '{transcription}' ({processing_time:.2f}s)")
        
        if not transcription:
            transcription = "Áudio não contém fala detectável"
        
        # Registrar métricas se disponível
        if MODULES_AVAILABLE:
            metrics_collector.record_request(
                success=True, 
                transcription_time=processing_time,
                file_size=file_size
            )
        
        # Resposta
        response_data = {
            "transcription": transcription,
            "status": "success", 
            "file_size": file_size,
            "method": "wave_nativo + whisper",
            "file_type": "WAV",
            "audio_duration": f"{len(audio_data)/16000:.2f}s",
            "processing_time": f"{processing_time:.2f}s",
            "note": "100% sem FFmpeg"
        }
        
        # Adicionar informações de módulos se disponível
        if MODULES_AVAILABLE:
            response_data["modules_loaded"] = True
            response_data["config_source"] = "módulos"
        else:
            response_data["modules_loaded"] = False
            response_data["config_source"] = "fallback"
        
        return jsonify(response_data), 200
        
    except Exception as e:
        import traceback
        error_details = traceback.format_exc()
        processing_time = time.time() - start_time
        
        logger.error(f"❌ Erro na transcrição: {str(e)}")
        logger.error(f"📜 Detalhes: {error_details}")
        
        # Registrar erro nas métricas se disponível
        if MODULES_AVAILABLE:
            metrics_collector.record_request(success=False)
        
        return jsonify({
            "error": f"Erro interno: {str(e)}", 
            "details": error_details,
            "processing_time": f"{processing_time:.2f}s",
            "note": "Servidor só processa WAV com bibliotecas nativas Python"
        }), 500
        
    finally:
        # Limpar arquivo temporário
        if temp_path:
            if MODULES_AVAILABLE:
                cleanup_temp_file(temp_path)
            else:
                try:
                    if os.path.exists(temp_path):
                        os.unlink(temp_path)
                        logger.info(f"🗑️ Arquivo temporário removido")
                except:
                    pass

@app.errorhandler(413)
def file_too_large(error):
    """Handler para arquivos muito grandes"""
    if MODULES_AVAILABLE:
        metrics_collector.record_request(success=False)
    return jsonify({"error": "Arquivo muito grande. Máximo: 10MB"}), 413

if __name__ == '__main__':
    # Configurações do servidor
    max_size = 10 * 1024 * 1024  # 10MB padrão
    host = '0.0.0.0'
    port = 5555
    debug = False
    
    # Usar configurações dos módulos se disponível
    if MODULES_AVAILABLE:
        try:
            max_size = config.MAX_FILE_SIZE
            host = config.HOST
            port = config.PORT
            debug = config.DEBUG
        except:
            logger.warning("⚠️ Usando configurações padrão")
    
    app.config['MAX_CONTENT_LENGTH'] = max_size
    
    # Obter IP local
    local_ip = get_local_ip()
    
    print("🚀 Servidor Whisper WAV NATIVO - 100% SEM FFMPEG")
    print("=" * 60)
    print("📡 URLs de acesso:")
    print(f"   Local: http://localhost:{port}")
    print(f"   Rede:  http://{local_ip}:{port}")
    print("")
    print("📋 Endpoints:")
    print("   GET  /health     - Status do servidor")
    print("   POST /transcribe - Transcrever áudio WAV")
    if MODULES_AVAILABLE:
        print("   GET  /metrics    - Métricas detalhadas")
    print("")
    print("⚙️ Configurações:")
    print("   🎵 Formato: WAV APENAS")
    print("   📦 Processamento: wave (Python nativo)")
    print(f"   🤖 Modelo: Whisper {model_name}")
    print(f"   💾 Tamanho máximo: {max_size/1024/1024:.0f}MB")
    print(f"   🌐 Host: {host}")
    print(f"   🔌 Porta: {port}")
    print(f"   📊 Módulos avançados: {'✅' if MODULES_AVAILABLE else '❌'}")
    print("")
    print("🧪 Teste rápido:")
    print(f"   curl http://{local_ip}:{port}/health")
    print("")
    print("✅ Zero dependências externas - Servidor iniciando...")
    print("=" * 60)
    
    app.run(
        host=host,
        port=port,
        debug=debug,
        threaded=True,
        use_reloader=False
    )