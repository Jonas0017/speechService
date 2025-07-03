#!/usr/bin/env python3
# src/utils.py

import os
import time
import hashlib
import tempfile
import wave
import numpy as np
import socket
from pathlib import Path
from functools import wraps
import logging

logger = logging.getLogger(__name__)

def get_local_ip():
    """Obter IP local da máquina"""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return "localhost"

def validate_wav_file(file_obj):
    """
    Validar se o arquivo é um WAV válido
    
    Args:
        file_obj: Objeto de arquivo Flask
        
    Returns:
        tuple: (is_valid, error_message)
    """
    if not file_obj:
        return False, "Nenhum arquivo fornecido"
    
    if not file_obj.filename:
        return False, "Nome do arquivo vazio"
    
    # Verificar extensão
    if not file_obj.filename.lower().endswith('.wav'):
        return False, "Apenas arquivos WAV são suportados"
    
    # Tentar ler como WAV
    try:
        # Salvar temporariamente para validação
        with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as temp_file:
            temp_path = temp_file.name
            file_obj.save(temp_path)
        
        # Tentar abrir com wave
        with wave.open(temp_path, 'rb') as wav_file:
            frames = wav_file.getnframes()
            channels = wav_file.getnchannels()
            sample_rate = wav_file.getframerate()
            sample_width = wav_file.getsampwidth()
            
            # Validações básicas
            if frames == 0:
                return False, "Arquivo WAV vazio"
            
            if channels not in [1, 2]:
                return False, f"Canais não suportados: {channels} (suportado: 1 ou 2)"
            
            if sample_width not in [1, 2, 4]:
                return False, f"Sample width não suportado: {sample_width}"
            
            if sample_rate < 8000 or sample_rate > 48000:
                return False, f"Sample rate fora do range: {sample_rate}Hz (8000-48000Hz)"
        
        # Limpar arquivo temporário
        os.unlink(temp_path)
        return True, "Arquivo WAV válido"
        
    except wave.Error as e:
        if 'temp_path' in locals() and os.path.exists(temp_path):
            os.unlink(temp_path)
        return False, f"Erro ao ler WAV: {e}"
    except Exception as e:
        if 'temp_path' in locals() and os.path.exists(temp_path):
            os.unlink(temp_path)
        return False, f"Erro na validação: {e}"

def load_wav_audio(file_path):
    """
    Carregar áudio WAV usando biblioteca nativa Python (sem FFmpeg)
    
    Args:
        file_path (str): Caminho para o arquivo WAV
        
    Returns:
        np.ndarray: Array de áudio normalizado para Whisper
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
            
            # Resample para 16kHz se necessário (usando scipy se disponível)
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
        raise

def generate_file_hash(file_path):
    """Gerar hash MD5 de um arquivo"""
    hash_md5 = hashlib.md5()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_md5.update(chunk)
    return hash_md5.hexdigest()

def format_file_size(size_bytes):
    """Formatar tamanho de arquivo em formato legível"""
    if size_bytes == 0:
        return "0B"
    
    size_names = ["B", "KB", "MB", "GB"]
    i = 0
    while size_bytes >= 1024 and i < len(size_names) - 1:
        size_bytes /= 1024.0
        i += 1
    
    return f"{size_bytes:.1f}{size_names[i]}"

def format_duration(seconds):
    """Formatar duração em formato MM:SS"""
    if seconds < 60:
        return f"{seconds:.1f}s"
    
    minutes = int(seconds // 60)
    seconds = seconds % 60
    return f"{minutes}:{seconds:04.1f}"

def timer(func):
    """Decorator para medir tempo de execução de funções"""
    @wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.time()
        result = func(*args, **kwargs)
        end_time = time.time()
        
        execution_time = end_time - start_time
        logger.debug(f"⏱️ {func.__name__} executado em {execution_time:.3f}s")
        
        return result
    return wrapper

def safe_filename(filename):
    """Criar nome de arquivo seguro removendo caracteres perigosos"""
    import re
    # Remover caracteres perigosos
    safe_name = re.sub(r'[<>:"/\\|?*]', '_', filename)
    # Limitar tamanho
    safe_name = safe_name[:100]
    # Garantir que não está vazio
    if not safe_name or safe_name in ['.', '..']:
        safe_name = 'audio_file'
    
    return safe_name

def cleanup_temp_file(file_path):
    """Limpar arquivo temporário se existir"""
    try:
        if os.path.exists(file_path):
            os.unlink(file_path)
            logger.info(f"🗑️ Arquivo temporário removido: {file_path}")
    except Exception as e:
        logger.warning(f"⚠️ Erro ao limpar arquivo temporário {file_path}: {e}")

def get_audio_duration(audio_data, sample_rate=16000):
    """Calcular duração do áudio em segundos"""
    return len(audio_data) / sample_rate

def validate_audio_duration(audio_data, min_seconds=0.1, max_seconds=300):
    """
    Validar duração do áudio
    
    Args:
        audio_data: Array numpy do áudio
        min_seconds: Duração mínima (padrão: 0.1s)
        max_seconds: Duração máxima (padrão: 5 minutos)
        
    Returns:
        tuple: (is_valid, duration, message)
    """
    duration = get_audio_duration(audio_data)
    
    if duration < min_seconds:
        return False, duration, f"Áudio muito curto: {duration:.1f}s (mínimo: {min_seconds}s)"
    
    if duration > max_seconds:
        return False, duration, f"Áudio muito longo: {duration:.1f}s (máximo: {max_seconds}s)"
    
    return True, duration, "Duração válida"

def get_system_info():
    """Obter informações do sistema para debugging"""
    import platform
    import psutil
    
    return {
        'platform': platform.platform(),
        'python_version': platform.python_version(),
        'cpu_count': os.cpu_count(),
        'memory_gb': round(psutil.virtual_memory().total / (1024**3), 2),
        'disk_free_gb': round(psutil.disk_usage('/').free / (1024**3), 2) if os.name != 'nt' else 'N/A'
    }

class ProgressTracker:
    """Classe para rastrear progresso de operações longas"""
    
    def __init__(self, total_steps, description="Processando"):
        self.total_steps = total_steps
        self.current_step = 0
        self.description = description
        self.start_time = time.time()
    
    def update(self, step=None, message=None):
        """Atualizar progresso"""
        if step is not None:
            self.current_step = step
        else:
            self.current_step += 1
        
        percentage = (self.current_step / self.total_steps) * 100
        elapsed = time.time() - self.start_time
        
        if self.current_step > 0:
            eta = (elapsed / self.current_step) * (self.total_steps - self.current_step)
            eta_str = f"ETA: {eta:.1f}s"
        else:
            eta_str = "ETA: --"
        
        status_msg = f"{self.description}: {percentage:.1f}% ({self.current_step}/{self.total_steps}) - {eta_str}"
        
        if message:
            status_msg += f" - {message}"
        
        logger.info(status_msg)
        return percentage
    
    def finish(self, message="Concluído"):
        """Finalizar progresso"""
        elapsed = time.time() - self.start_time
        logger.info(f"{self.description}: {message} em {elapsed:.1f}s") 