#!/usr/bin/env python3
# scripts/test_api.py

import requests
import json
import time
import os
from pathlib import Path
import sys

class WhisperAPITester:
    def __init__(self, base_url="http://localhost:5555"):
        self.base_url = base_url
        self.test_results = []
        
    def log_test(self, test_name, success, message, duration=None):
        """Registrar resultado do teste"""
        result = {
            "test": test_name,
            "success": success,
            "message": message,
            "duration": duration,
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
        }
        self.test_results.append(result)
        
        status = "✅" if success else "❌"
        duration_str = f" ({duration:.3f}s)" if duration else ""
        print(f"{status} {test_name}: {message}{duration_str}")
    
    def test_health_endpoint(self):
        """Testar endpoint de health check"""
        test_name = "Health Check"
        try:
            start_time = time.time()
            response = requests.get(f"{self.base_url}/health", timeout=10)
            duration = time.time() - start_time
            
            if response.status_code == 200:
                data = response.json()
                if data.get("status") == "ok":
                    self.log_test(test_name, True, "Servidor respondendo", duration)
                    return True
                else:
                    self.log_test(test_name, False, f"Status inválido: {data}")
            else:
                self.log_test(test_name, False, f"HTTP {response.status_code}")
                
        except requests.exceptions.ConnectionError:
            self.log_test(test_name, False, "Conexão falhou - servidor offline?")
        except Exception as e:
            self.log_test(test_name, False, f"Erro: {e}")
            
        return False
    
    def test_transcribe_without_file(self):
        """Testar endpoint de transcrição sem arquivo"""
        test_name = "Transcribe - Sem Arquivo"
        try:
            start_time = time.time()
            response = requests.post(f"{self.base_url}/transcribe", timeout=10)
            duration = time.time() - start_time
            
            if response.status_code == 400:
                data = response.json()
                if "error" in data:
                    self.log_test(test_name, True, "Validação funcionando", duration)
                    return True
                    
            self.log_test(test_name, False, f"Resposta inesperada: {response.status_code}")
            
        except Exception as e:
            self.log_test(test_name, False, f"Erro: {e}")
            
        return False
    
    def test_transcribe_with_wav(self, wav_file):
        """Testar transcrição com arquivo WAV"""
        test_name = f"Transcribe - {Path(wav_file).name}"
        
        if not os.path.exists(wav_file):
            self.log_test(test_name, False, "Arquivo não encontrado")
            return False
            
        try:
            start_time = time.time()
            
            with open(wav_file, 'rb') as f:
                files = {'audioFile': f}
                response = requests.post(
                    f"{self.base_url}/transcribe", 
                    files=files, 
                    timeout=30
                )
                
            duration = time.time() - start_time
            
            if response.status_code == 200:
                data = response.json()
                if "transcription" in data:
                    transcription = data["transcription"]
                    self.log_test(test_name, True, 
                                f"Transcrição: '{transcription}'", duration)
                    return True
                else:
                    self.log_test(test_name, False, "Transcription key missing")
            else:
                self.log_test(test_name, False, 
                            f"HTTP {response.status_code}: {response.text}")
                
        except requests.exceptions.Timeout:
            self.log_test(test_name, False, "Timeout - processamento demorou muito")
        except Exception as e:
            self.log_test(test_name, False, f"Erro: {e}")
            
        return False
    
    def test_large_file_rejection(self):
        """Testar rejeição de arquivo muito grande"""
        test_name = "Rejeição Arquivo Grande"
        
        # Criar arquivo temporário grande (> 10MB)
        large_file = "temp_large.wav"
        try:
            with open(large_file, 'wb') as f:
                f.write(b'0' * (11 * 1024 * 1024))  # 11MB
                
            with open(large_file, 'rb') as f:
                files = {'audioFile': f}
                response = requests.post(
                    f"{self.base_url}/transcribe", 
                    files=files, 
                    timeout=10
                )
                
            if response.status_code == 413:
                self.log_test(test_name, True, "Arquivo grande rejeitado corretamente")
                return True
            else:
                self.log_test(test_name, False, f"HTTP {response.status_code}")
                
        except Exception as e:
            self.log_test(test_name, False, f"Erro: {e}")
        finally:
            if os.path.exists(large_file):
                os.remove(large_file)
                
        return False
    
    def test_invalid_file_format(self):
        """Testar rejeição de formato inválido"""
        test_name = "Rejeição Formato Inválido"
        
        # Criar arquivo texto falso
        fake_file = "fake.wav"
        try:
            with open(fake_file, 'w') as f:
                f.write("Este não é um arquivo WAV")
                
            with open(fake_file, 'rb') as f:
                files = {'audioFile': f}
                response = requests.post(
                    f"{self.base_url}/transcribe", 
                    files=files, 
                    timeout=10
                )
                
            if response.status_code == 400:
                data = response.json()
                if "WAV" in data.get("error", ""):
                    self.log_test(test_name, True, "Formato inválido rejeitado")
                    return True
                    
            self.log_test(test_name, False, f"HTTP {response.status_code}")
            
        except Exception as e:
            self.log_test(test_name, False, f"Erro: {e}")
        finally:
            if os.path.exists(fake_file):
                os.remove(fake_file)
                
        return False
    
    def run_all_tests(self):
        """Executar todos os testes"""
        print("🧪 INICIANDO TESTES DA API WHISPER")
        print("=" * 50)
        
        # Testes básicos
        self.test_health_endpoint()
        self.test_transcribe_without_file()
        self.test_large_file_rejection()
        self.test_invalid_file_format()
        
        # Testes com arquivos WAV reais
        test_audio_dir = Path(__file__).parent.parent / "tests" / "test_audio"
        if test_audio_dir.exists():
            for wav_file in test_audio_dir.glob("*.wav"):
                self.test_transcribe_with_wav(str(wav_file))
        else:
            print("⚠️ Diretório de testes de áudio não encontrado")
            
        # Resumo dos resultados
        self.print_test_summary()
    
    def print_test_summary(self):
        """Imprimir resumo dos testes"""
        print("\n" + "=" * 50)
        print("📊 RESUMO DOS TESTES")
        print("=" * 50)
        
        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results if result["success"])
        failed_tests = total_tests - passed_tests
        
        print(f"Total de testes: {total_tests}")
        print(f"✅ Passaram: {passed_tests}")
        print(f"❌ Falharam: {failed_tests}")
        print(f"📈 Taxa de sucesso: {(passed_tests/total_tests)*100:.1f}%")
        
        # Mostrar falhas
        if failed_tests > 0:
            print("\n❌ TESTES QUE FALHARAM:")
            for result in self.test_results:
                if not result["success"]:
                    print(f"   - {result['test']}: {result['message']}")
        
        # Salvar relatório
        report_file = Path(__file__).parent.parent / "logs" / "test_report.json"
        report_file.parent.mkdir(exist_ok=True)
        
        with open(report_file, 'w') as f:
            json.dump(self.test_results, f, indent=2)
            
        print(f"\n📄 Relatório salvo: {report_file}")
        
        return failed_tests == 0

if __name__ == "__main__":
    # Permitir URL customizada
    base_url = sys.argv[1] if len(sys.argv) > 1 else "http://localhost:5555"
    
    tester = WhisperAPITester(base_url)
    success = tester.run_all_tests()
    
    sys.exit(0 if success else 1) 