#!/usr/bin/env python3
# tests/integration_tests.py

import requests
import json
import time
import os
import wave
import numpy as np
import tempfile
from pathlib import Path

class WhisperAPIIntegrationTests:
    """Testes de integração para API Whisper"""
    
    def __init__(self, base_url="http://localhost:5555"):
        self.base_url = base_url
        self.test_results = []
    
    def log_test_result(self, test_name, success, message, duration=None):
        """Registrar resultado do teste"""
        result = {
            "test": test_name,
            "success": success,
            "message": message,
            "duration": duration
        }
        self.test_results.append(result)
        
        status = "✅" if success else "❌"
        duration_str = f" ({duration:.3f}s)" if duration else ""
        print(f"{status} {test_name}: {message}{duration_str}")
    
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
    
    def test_server_health(self):
        """Testar endpoint de saúde"""
        try:
            start_time = time.time()
            response = requests.get(f"{self.base_url}/health", timeout=10)
            duration = time.time() - start_time
            
            if response.status_code == 200:
                data = response.json()
                if "status" in data:
                    self.log_test_result("Health Check", True, "Servidor respondendo", duration)
                    return True
                else:
                    self.log_test_result("Health Check", False, "Response sem status")
            else:
                self.log_test_result("Health Check", False, f"HTTP {response.status_code}")
        except requests.exceptions.ConnectionError:
            self.log_test_result("Health Check", False, "Conexão falhou")
        except Exception as e:
            self.log_test_result("Health Check", False, f"Erro: {e}")
        
        return False
    
    def test_transcribe_no_file(self):
        """Testar transcrição sem arquivo"""
        try:
            start_time = time.time()
            response = requests.post(f"{self.base_url}/transcribe", timeout=10)
            duration = time.time() - start_time
            
            if response.status_code == 400:
                self.log_test_result("Transcribe No File", True, "Validação funcionando", duration)
                return True
            else:
                self.log_test_result("Transcribe No File", False, f"HTTP {response.status_code}")
        except Exception as e:
            self.log_test_result("Transcribe No File", False, f"Erro: {e}")
        
        return False
    
    def test_transcribe_with_wav(self):
        """Testar transcrição com arquivo WAV válido"""
        # Criar arquivo WAV temporário
        with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as temp_file:
            temp_path = temp_file.name
        
        try:
            # Gerar WAV de teste
            self.generate_test_wav(temp_path, duration=2.0, frequency=440)
            
            start_time = time.time()
            with open(temp_path, 'rb') as f:
                files = {'audioFile': f}
                response = requests.post(f"{self.base_url}/transcribe", files=files, timeout=30)
            duration = time.time() - start_time
            
            if response.status_code == 200:
                data = response.json()
                if "transcription" in data:
                    self.log_test_result("Transcribe WAV", True, "Transcrição funcionando", duration)
                    return True
                else:
                    self.log_test_result("Transcribe WAV", False, "Sem transcription no response")
            else:
                self.log_test_result("Transcribe WAV", False, f"HTTP {response.status_code}")
        except Exception as e:
            self.log_test_result("Transcribe WAV", False, f"Erro: {e}")
        finally:
            # Limpar arquivo temporário
            if os.path.exists(temp_path):
                os.unlink(temp_path)
        
        return False
    
    def test_invalid_file_format(self):
        """Testar rejeição de formato inválido"""
        # Criar arquivo texto falso
        with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as temp_file:
            temp_path = temp_file.name
            temp_file.write(b"Este nao e um arquivo WAV valido")
        
        try:
            start_time = time.time()
            with open(temp_path, 'rb') as f:
                files = {'audioFile': f}
                response = requests.post(f"{self.base_url}/transcribe", files=files, timeout=10)
            duration = time.time() - start_time
            
            if response.status_code == 400:
                self.log_test_result("Invalid Format", True, "Formato inválido rejeitado", duration)
                return True
            else:
                self.log_test_result("Invalid Format", False, f"HTTP {response.status_code}")
        except Exception as e:
            self.log_test_result("Invalid Format", False, f"Erro: {e}")
        finally:
            # Limpar arquivo temporário
            if os.path.exists(temp_path):
                os.unlink(temp_path)
        
        return False
    
    def test_large_file_rejection(self):
        """Testar rejeição de arquivo muito grande"""
        # Criar arquivo muito grande (> 10MB)
        with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as temp_file:
            temp_path = temp_file.name
            # Escrever 11MB de dados
            temp_file.write(b'0' * (11 * 1024 * 1024))
        
        try:
            start_time = time.time()
            with open(temp_path, 'rb') as f:
                files = {'audioFile': f}
                response = requests.post(f"{self.base_url}/transcribe", files=files, timeout=10)
            duration = time.time() - start_time
            
            if response.status_code == 413:
                self.log_test_result("Large File Rejection", True, "Arquivo grande rejeitado", duration)
                return True
            else:
                self.log_test_result("Large File Rejection", False, f"HTTP {response.status_code}")
        except Exception as e:
            self.log_test_result("Large File Rejection", False, f"Erro: {e}")
        finally:
            # Limpar arquivo temporário
            if os.path.exists(temp_path):
                os.unlink(temp_path)
        
        return False
    
    def test_concurrent_requests(self):
        """Testar requisições concorrentes básicas"""
        import threading
        
        results = []
        
        def make_request():
            try:
                response = requests.get(f"{self.base_url}/health", timeout=5)
                results.append(response.status_code == 200)
            except:
                results.append(False)
        
        # Fazer 5 requisições concorrentes
        threads = []
        start_time = time.time()
        
        for _ in range(5):
            thread = threading.Thread(target=make_request)
            thread.start()
            threads.append(thread)
        
        # Aguardar conclusão
        for thread in threads:
            thread.join()
        
        duration = time.time() - start_time
        success_count = sum(results)
        
        if success_count >= 4:  # Pelo menos 4 de 5 devem funcionar
            self.log_test_result("Concurrent Requests", True, f"{success_count}/5 sucessos", duration)
            return True
        else:
            self.log_test_result("Concurrent Requests", False, f"Apenas {success_count}/5 sucessos")
        
        return False
    
    def run_all_tests(self):
        """Executar todos os testes de integração"""
        print("🔗 TESTES DE INTEGRAÇÃO - API WHISPER")
        print("=" * 50)
        
        # Lista de testes para executar
        tests = [
            self.test_server_health,
            self.test_transcribe_no_file,
            self.test_transcribe_with_wav,
            self.test_invalid_file_format,
            self.test_large_file_rejection,
            self.test_concurrent_requests
        ]
        
        # Executar testes
        passed = 0
        for test in tests:
            if test():
                passed += 1
        
        # Resumo
        total = len(tests)
        print("\n" + "=" * 50)
        print("📊 RESUMO DOS TESTES DE INTEGRAÇÃO")
        print("=" * 50)
        print(f"Total: {total}")
        print(f"✅ Passaram: {passed}")
        print(f"❌ Falharam: {total - passed}")
        print(f"📈 Taxa de sucesso: {(passed/total)*100:.1f}%")
        
        # Salvar relatório
        report_file = Path(__file__).parent.parent / "logs" / "integration_test_report.json"
        report_file.parent.mkdir(exist_ok=True)
        
        report = {
            "test_summary": {
                "total_tests": total,
                "passed_tests": passed,
                "failed_tests": total - passed,
                "success_rate": (passed/total)*100
            },
            "detailed_results": self.test_results
        }
        
        with open(report_file, 'w') as f:
            json.dump(report, f, indent=2)
        
        print(f"📄 Relatório salvo: {report_file}")
        
        return passed == total

if __name__ == "__main__":
    tester = WhisperAPIIntegrationTests()
    success = tester.run_all_tests()
    print(f"\n🎯 Resultado: {'SUCESSO' if success else 'FALHA'}") 