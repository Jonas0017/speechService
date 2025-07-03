#!/usr/bin/env python3
# scripts/setup_local.py

import os
import sys
import subprocess
import platform
import shutil
from pathlib import Path

class LocalSetup:
    def __init__(self):
        self.project_root = Path(__file__).parent.parent
        self.python_cmd = "python" if platform.system() == "Windows" else "python3"
        
    def check_prerequisites(self):
        """Verificar pré-requisitos do sistema"""
        print("🔍 Verificando pré-requisitos...")
        
        # Verificar Python
        try:
            result = subprocess.run([self.python_cmd, "--version"], 
                                  capture_output=True, text=True)
            if result.returncode == 0:
                version = result.stdout.strip()
                print(f"✅ {version}")
            else:
                raise Exception("Python não encontrado")
        except Exception as e:
            print(f"❌ Python: {e}")
            return False
            
        # Verificar Docker
        try:
            result = subprocess.run(["docker", "--version"], 
                                  capture_output=True, text=True)
            if result.returncode == 0:
                version = result.stdout.strip()
                print(f"✅ {version}")
            else:
                print("⚠️ Docker não encontrado - deploy limitado")
        except:
            print("⚠️ Docker não encontrado - deploy limitado")
            
        # Verificar curl (para testes)
        try:
            subprocess.run(["curl", "--version"], 
                         capture_output=True, check=True)
            print("✅ curl OK")
        except:
            print("⚠️ curl não encontrado - alguns testes podem falhar")
            
        return True
    
    def setup_virtual_environment(self):
        """Configurar ambiente virtual Python"""
        print("🐍 Configurando ambiente virtual...")
        
        venv_path = self.project_root / "venv"
        
        if not venv_path.exists():
            subprocess.run([self.python_cmd, "-m", "venv", str(venv_path)], 
                         check=True)
            print("✅ Virtual environment criado")
        else:
            print("✅ Virtual environment já existe")
            
        # Ativar e instalar dependências
        if platform.system() == "Windows":
            pip_cmd = str(venv_path / "Scripts" / "pip.exe")
            python_cmd = str(venv_path / "Scripts" / "python.exe")
        else:
            pip_cmd = str(venv_path / "bin" / "pip")
            python_cmd = str(venv_path / "bin" / "python")
            
        # Atualizar pip
        subprocess.run([python_cmd, "-m", "pip", "install", "--upgrade", "pip"], 
                      check=True)
        
        # Instalar dependências
        requirements_file = self.project_root / "requirements.txt"
        if requirements_file.exists():
            subprocess.run([pip_cmd, "install", "-r", str(requirements_file)], 
                         check=True)
            print("✅ Dependências instaladas")
            
        return python_cmd, pip_cmd
    
    def generate_test_audio_files(self):
        """Gerar arquivos de áudio para teste"""
        print("🎵 Gerando arquivos de teste...")
        
        test_audio_dir = self.project_root / "tests" / "test_audio"
        
        # Script para gerar WAV de teste usando numpy
        generate_script = f'''
import numpy as np
import wave
import os

def generate_test_wav(filename, duration=1.0, frequency=440, sample_rate=16000):
    """Gerar arquivo WAV de teste"""
    t = np.linspace(0, duration, int(sample_rate * duration))
    audio_data = np.sin(2 * np.pi * frequency * t)
    audio_data = (audio_data * 32767 * 0.5).astype(np.int16)
    
    with wave.open(filename, 'w') as wav_file:
        wav_file.setnchannels(1)
        wav_file.setsampwidth(2)
        wav_file.setframerate(sample_rate)
        wav_file.writeframes(audio_data.tobytes())

# Gerar diferentes arquivos de teste
test_files = [
    ("test_1s_440hz.wav", 1.0, 440),      # 1 segundo, Lá 4
    ("test_3s_880hz.wav", 3.0, 880),      # 3 segundos, Lá 5
    ("test_5s_220hz.wav", 5.0, 220),      # 5 segundos, Lá 3
    ("test_empty.wav", 0.1, 0),           # Arquivo quase vazio
]

for filename, duration, freq in test_files:
    filepath = "{test_audio_dir}" + "/" + filename
    generate_test_wav(filepath, duration, freq)
    print(f"✅ {{filename}}")

print("🎵 Arquivos de teste gerados!")
'''
        
        # Executar geração usando subprocess
        try:
            subprocess.run([self.python_cmd, "-c", generate_script], check=True)
        except Exception as e:
            print(f"⚠️ Erro ao gerar arquivos de teste: {e}")
        
    def create_env_file(self):
        """Criar arquivo .env local"""
        print("⚙️ Criando arquivo .env...")
        
        env_content = '''# Configurações do Servidor Whisper
FLASK_ENV=development
DEBUG=True
PORT=5555

# Whisper
WHISPER_MODEL=tiny
LANGUAGE=pt
MAX_FILE_SIZE=10485760

# Logs
LOG_LEVEL=DEBUG
LOG_FILE=logs/whisper.log

# Rate Limiting (para produção)
REDIS_URL=redis://localhost:6379
RATE_LIMIT_ENABLED=false

# Segurança
SECRET_KEY=dev-key-change-in-production
ALLOWED_ORIGINS=http://localhost:3000,http://127.0.0.1:3000

# Monitoring
METRICS_ENABLED=true
HEALTH_CHECK_INTERVAL=30
'''
        
        env_file = self.project_root / ".env"
        with open(env_file, "w") as f:
            f.write(env_content)
            
        print("✅ Arquivo .env criado")
    
    def run_setup(self):
        """Executar setup completo"""
        print("🚀 SETUP AUTOMÁTICO - WHISPER SERVER")
        print("=" * 50)
        
        if not self.check_prerequisites():
            print("❌ Pré-requisitos não atendidos")
            return False
            
        python_cmd, pip_cmd = self.setup_virtual_environment()
        self.generate_test_audio_files()
        self.create_env_file()
        
        print("=" * 50)
        print("🎉 SETUP CONCLUÍDO COM SUCESSO!")
        print(f"📁 Projeto: {self.project_root}")
        print(f"🐍 Python: {python_cmd}")
        print("🔧 Próximos passos:")
        if platform.system() == "Windows":
            print("   1. Ativar venv: venv\\Scripts\\activate")
        else:
            print("   1. Ativar venv: source venv/bin/activate")
        print("   2. Executar: python scripts/test_api.py")
        print("   3. Executar: python scripts/validate_deploy.py")
        
        return True

if __name__ == "__main__":
    setup = LocalSetup()
    setup.run_setup() 