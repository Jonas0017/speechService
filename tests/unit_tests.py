#!/usr/bin/env python3
# tests/unit_tests.py

import unittest
import tempfile
import os
import sys
import wave
import numpy as np
from unittest.mock import patch, MagicMock
from pathlib import Path

# Adicionar o diretório src ao path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

try:
    from config import Config, get_config
    from utils import format_file_size, get_audio_duration, cleanup_temp_file
    from monitoring import MetricsCollector, HealthChecker
except ImportError as e:
    print(f"❌ Erro ao importar módulos: {e}")
    sys.exit(1)

class TestConfig(unittest.TestCase):
    """Testes para configurações"""
    
    def test_default_config(self):
        """Testar configurações padrão"""
        config = Config()
        
        self.assertEqual(config.WHISPER_MODEL, 'tiny')
        self.assertEqual(config.LANGUAGE, 'pt')
        self.assertEqual(config.PORT, 5555)
        self.assertTrue(config.DEBUG)
    
    def test_config_validation(self):
        """Testar validação de configurações"""
        # Configuração válida deve passar
        with patch.dict(os.environ, {
            'WHISPER_MODEL': 'tiny',
            'PORT': '5555',
            'MAX_FILE_SIZE': '10485760'
        }):
            self.assertTrue(Config.validate())
    
    def test_invalid_model(self):
        """Testar modelo inválido"""
        with patch.dict(os.environ, {'WHISPER_MODEL': 'invalid_model'}):
            with self.assertRaises(ValueError):
                Config.validate()
    
    def test_invalid_port(self):
        """Testar porta inválida"""
        with patch.dict(os.environ, {'PORT': '99999'}):
            with self.assertRaises(ValueError):
                Config.validate()

class TestUtils(unittest.TestCase):
    """Testes para funções utilitárias"""
    
    def test_format_file_size(self):
        """Testar formatação de tamanho de arquivo"""
        self.assertEqual(format_file_size(0), "0B")
        self.assertEqual(format_file_size(512), "512.0B")
        self.assertEqual(format_file_size(1024), "1.0KB")
        self.assertEqual(format_file_size(1048576), "1.0MB")
        self.assertEqual(format_file_size(1073741824), "1.0GB")
    
    def test_get_audio_duration(self):
        """Testar cálculo de duração de áudio"""
        # 16000 samples a 16kHz = 1 segundo
        audio_data = np.zeros(16000)
        duration = get_audio_duration(audio_data, 16000)
        self.assertEqual(duration, 1.0)
        
        # 32000 samples a 16kHz = 2 segundos
        audio_data = np.zeros(32000)
        duration = get_audio_duration(audio_data, 16000)
        self.assertEqual(duration, 2.0)
    
    def test_cleanup_temp_file(self):
        """Testar limpeza de arquivo temporário"""
        # Criar arquivo temporário
        with tempfile.NamedTemporaryFile(delete=False) as temp_file:
            temp_path = temp_file.name
            temp_file.write(b"test data")
        
        # Verificar que existe
        self.assertTrue(os.path.exists(temp_path))
        
        # Limpar
        cleanup_temp_file(temp_path)
        
        # Verificar que foi removido
        self.assertFalse(os.path.exists(temp_path))

class TestMetricsCollector(unittest.TestCase):
    """Testes para coletor de métricas"""
    
    def setUp(self):
        """Setup para cada teste"""
        self.metrics = MetricsCollector()
    
    def test_initial_metrics(self):
        """Testar métricas iniciais"""
        metrics_data = self.metrics.get_metrics()
        
        self.assertEqual(metrics_data['requests']['total'], 0)
        self.assertEqual(metrics_data['requests']['success'], 0)
        self.assertEqual(metrics_data['requests']['error'], 0)
        self.assertEqual(metrics_data['requests']['success_rate'], 0)
    
    def test_record_successful_request(self):
        """Testar registro de requisição bem-sucedida"""
        self.metrics.record_request(success=True, transcription_time=2.5, file_size=1024)
        
        metrics_data = self.metrics.get_metrics()
        
        self.assertEqual(metrics_data['requests']['total'], 1)
        self.assertEqual(metrics_data['requests']['success'], 1)
        self.assertEqual(metrics_data['requests']['error'], 0)
        self.assertEqual(metrics_data['requests']['success_rate'], 100.0)
    
    def test_record_failed_request(self):
        """Testar registro de requisição falhada"""
        self.metrics.record_request(success=False)
        
        metrics_data = self.metrics.get_metrics()
        
        self.assertEqual(metrics_data['requests']['total'], 1)
        self.assertEqual(metrics_data['requests']['success'], 0)
        self.assertEqual(metrics_data['requests']['error'], 1)
        self.assertEqual(metrics_data['requests']['success_rate'], 0.0)
    
    def test_mixed_requests(self):
        """Testar mix de requisições"""
        # 3 sucessos, 1 erro
        for _ in range(3):
            self.metrics.record_request(success=True, transcription_time=1.0)
        self.metrics.record_request(success=False)
        
        metrics_data = self.metrics.get_metrics()
        
        self.assertEqual(metrics_data['requests']['total'], 4)
        self.assertEqual(metrics_data['requests']['success'], 3)
        self.assertEqual(metrics_data['requests']['error'], 1)
        self.assertEqual(metrics_data['requests']['success_rate'], 75.0)

class TestHealthChecker(unittest.TestCase):
    """Testes para verificador de saúde"""
    
    def setUp(self):
        """Setup para cada teste"""
        self.metrics = MetricsCollector()
        self.health_checker = HealthChecker(self.metrics)
    
    def test_empty_checks(self):
        """Testar sem verificações"""
        results = self.health_checker.run_checks()
        
        self.assertEqual(results['status'], 'healthy')
        self.assertEqual(len(results['checks']), 0)
    
    def test_healthy_check(self):
        """Testar verificação saudável"""
        def dummy_check():
            return 50  # Valor baixo, dentro dos limites
        
        self.health_checker.add_check('test_check', dummy_check, 80, 95)
        results = self.health_checker.run_checks()
        
        self.assertEqual(results['status'], 'healthy')
        self.assertEqual(len(results['checks']), 1)
        self.assertEqual(results['checks'][0]['status'], 'healthy')
    
    def test_warning_check(self):
        """Testar verificação com aviso"""
        def dummy_check():
            return 85  # Entre warning e error
        
        self.health_checker.add_check('test_check', dummy_check, 80, 95)
        results = self.health_checker.run_checks()
        
        self.assertEqual(results['status'], 'warning')
        self.assertEqual(results['checks'][0]['status'], 'warning')
    
    def test_error_check(self):
        """Testar verificação com erro"""
        def dummy_check():
            return 98  # Acima do threshold de erro
        
        self.health_checker.add_check('test_check', dummy_check, 80, 95)
        results = self.health_checker.run_checks()
        
        self.assertEqual(results['status'], 'error')
        self.assertEqual(results['checks'][0]['status'], 'error')
    
    def test_exception_in_check(self):
        """Testar exceção em verificação"""
        def failing_check():
            raise Exception("Test exception")
        
        self.health_checker.add_check('failing_check', failing_check)
        results = self.health_checker.run_checks()
        
        self.assertEqual(results['status'], 'error')
        self.assertEqual(results['checks'][0]['status'], 'error')
        self.assertIn('Test exception', results['checks'][0]['message'])

class TestWAVGeneration(unittest.TestCase):
    """Testes para geração de arquivos WAV de teste"""
    
    def generate_test_wav(self, filename, duration=1.0, frequency=440, sample_rate=16000):
        """Gerar arquivo WAV de teste"""
        t = np.linspace(0, duration, int(sample_rate * duration))
        audio_data = np.sin(2 * np.pi * frequency * t)
        audio_data = (audio_data * 32767 * 0.5).astype(np.int16)
        
        with wave.open(filename, 'w') as wav_file:
            wav_file.setnchannels(1)
            wav_file.setsampwidth(2)
            wav_file.setframerate(sample_rate)
            wav_file.writeframes(audio_data.tobytes())
    
    def test_wav_generation(self):
        """Testar geração de arquivo WAV"""
        with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as temp_file:
            temp_path = temp_file.name
        
        try:
            # Gerar WAV de teste
            self.generate_test_wav(temp_path, duration=1.0, frequency=440)
            
            # Verificar se arquivo foi criado
            self.assertTrue(os.path.exists(temp_path))
            
            # Verificar se é um WAV válido
            with wave.open(temp_path, 'rb') as wav_file:
                frames = wav_file.getnframes()
                channels = wav_file.getnchannels()
                sample_rate = wav_file.getframerate()
                
                self.assertGreater(frames, 0)
                self.assertEqual(channels, 1)
                self.assertEqual(sample_rate, 16000)
        
        finally:
            # Limpar arquivo temporário
            if os.path.exists(temp_path):
                os.unlink(temp_path)

class TestBasicFunctions(unittest.TestCase):
    """Testes básicos para funções utilitárias"""
    
    def test_file_operations(self):
        """Testar operações básicas de arquivo"""
        # Criar arquivo temporário
        with tempfile.NamedTemporaryFile(delete=False) as temp_file:
            temp_path = temp_file.name
            temp_file.write(b"test data")
        
        # Verificar que existe
        self.assertTrue(os.path.exists(temp_path))
        
        # Limpar
        os.unlink(temp_path)
        self.assertFalse(os.path.exists(temp_path))
    
    def test_format_file_size(self):
        """Testar formatação de tamanho de arquivo"""
        def format_file_size(size_bytes):
            if size_bytes == 0:
                return "0B"
            
            size_names = ["B", "KB", "MB", "GB"]
            i = 0
            while size_bytes >= 1024 and i < len(size_names) - 1:
                size_bytes /= 1024.0
                i += 1
            
            return f"{size_bytes:.1f}{size_names[i]}"
        
        self.assertEqual(format_file_size(0), "0B")
        self.assertEqual(format_file_size(512), "512.0B")
        self.assertEqual(format_file_size(1024), "1.0KB")
        self.assertEqual(format_file_size(1048576), "1.0MB")

def create_test_suite():
    """Criar suite de testes"""
    suite = unittest.TestSuite()
    
    # Adicionar testes
    suite.addTest(unittest.makeSuite(TestConfig))
    suite.addTest(unittest.makeSuite(TestUtils))
    suite.addTest(unittest.makeSuite(TestMetricsCollector))
    suite.addTest(unittest.makeSuite(TestHealthChecker))
    suite.addTest(unittest.makeSuite(TestWAVGeneration))
    suite.addTest(unittest.makeSuite(TestBasicFunctions))
    
    return suite

if __name__ == '__main__':
    print("🧪 EXECUTANDO TESTES UNITÁRIOS")
    print("=" * 50)
    
    # Executar testes
    runner = unittest.TextTestRunner(verbosity=2)
    suite = create_test_suite()
    result = runner.run(suite)
    
    # Resumo
    print("\n" + "=" * 50)
    print("📊 RESUMO DOS TESTES UNITÁRIOS")
    print("=" * 50)
    print(f"Testes executados: {result.testsRun}")
    print(f"✅ Sucessos: {result.testsRun - len(result.failures) - len(result.errors)}")
    print(f"❌ Falhas: {len(result.failures)}")
    print(f"💥 Erros: {len(result.errors)}")
    
    if result.failures:
        print("\n❌ FALHAS:")
        for test, trace in result.failures:
            print(f"  - {test}: {trace.split(chr(10))[-2]}")
    
    if result.errors:
        print("\n💥 ERROS:")
        for test, trace in result.errors:
            print(f"  - {test}: {trace.split(chr(10))[-2]}")
    
    # Exit code
    success = len(result.failures) == 0 and len(result.errors) == 0
    sys.exit(0 if success else 1) 