#!/usr/bin/env python3
# scripts/load_test.py

import requests
import threading
import time
import json
import statistics
from pathlib import Path
import sys
import argparse

class LoadTester:
    def __init__(self, base_url="http://localhost:5555", max_concurrent=5):
        self.base_url = base_url
        self.max_concurrent = max_concurrent
        self.results = []
        self.lock = threading.Lock()
        
    def single_request_test(self, test_id, wav_file):
        """Executar uma única requisição de teste"""
        start_time = time.time()
        
        try:
            with open(wav_file, 'rb') as f:
                files = {'audioFile': f}
                response = requests.post(
                    f"{self.base_url}/transcribe",
                    files=files,
                    timeout=60
                )
                
            end_time = time.time()
            duration = end_time - start_time
            
            result = {
                'test_id': test_id,
                'success': response.status_code == 200,
                'status_code': response.status_code,
                'duration': duration,
                'timestamp': start_time
            }
            
            if response.status_code == 200:
                data = response.json()
                result['transcription_length'] = len(data.get('transcription', ''))
            
        except Exception as e:
            result = {
                'test_id': test_id,
                'success': False,
                'error': str(e),
                'duration': time.time() - start_time,
                'timestamp': start_time
            }
        
        with self.lock:
            self.results.append(result)
            
        return result
    
    def run_concurrent_test(self, num_requests=20, wav_file=None):
        """Executar teste de carga concurrent"""
        print(f"🚀 Iniciando teste de carga: {num_requests} requisições")
        print(f"🎯 URL: {self.base_url}")
        print(f"⚡ Concorrência máxima: {self.max_concurrent}")
        
        if not wav_file:
            # Usar arquivo de teste padrão
            test_audio_dir = Path(__file__).parent.parent / "tests" / "test_audio"
            wav_files = list(test_audio_dir.glob("*.wav"))
            if not wav_files:
                print("❌ Nenhum arquivo WAV encontrado para teste")
                return False
            wav_file = wav_files[0]
            
        print(f"🎵 Arquivo de teste: {wav_file}")
        print("-" * 50)
        
        # Limpar resultados anteriores
        self.results = []
        
        # Função para worker thread
        def worker():
            while True:
                with self.lock:
                    if len(self.results) >= num_requests:
                        break
                    test_id = len(self.results) + 1
                
                result = self.single_request_test(test_id, wav_file)
                
                # Progress update
                status = "✅" if result['success'] else "❌"
                duration = result.get('duration', 0)
                print(f"{status} Test {result['test_id']}: {duration:.2f}s")
        
        # Iniciar threads
        threads = []
        start_time = time.time()
        
        for _ in range(min(self.max_concurrent, num_requests)):
            thread = threading.Thread(target=worker)
            thread.start()
            threads.append(thread)
        
        # Aguardar conclusão
        for thread in threads:
            thread.join()
            
        total_time = time.time() - start_time
        
        # Analisar resultados
        self.analyze_results(total_time)
        
        return True
    
    def analyze_results(self, total_time):
        """Analisar resultados do teste de carga"""
        print("\n" + "=" * 50)
        print("📊 ANÁLISE DOS RESULTADOS")
        print("=" * 50)
        
        if not self.results:
            print("❌ Nenhum resultado para analisar")
            return
            
        # Estatísticas básicas
        total_requests = len(self.results)
        successful_requests = sum(1 for r in self.results if r['success'])
        failed_requests = total_requests - successful_requests
        success_rate = (successful_requests / total_requests) * 100
        
        # Tempos de resposta
        successful_durations = [r['duration'] for r in self.results if r['success']]
        
        if successful_durations:
            avg_duration = statistics.mean(successful_durations)
            median_duration = statistics.median(successful_durations)
            min_duration = min(successful_durations)
            max_duration = max(successful_durations)
            
            if len(successful_durations) > 1:
                std_deviation = statistics.stdev(successful_durations)
            else:
                std_deviation = 0
        else:
            avg_duration = median_duration = min_duration = max_duration = std_deviation = 0
            
        # Throughput
        requests_per_second = total_requests / total_time if total_time > 0 else 0
        successful_rps = successful_requests / total_time if total_time > 0 else 0
        
        # Imprimir resultados
        print(f"🎯 Total de requisições: {total_requests}")
        print(f"✅ Sucessos: {successful_requests}")
        print(f"❌ Falhas: {failed_requests}")
        print(f"📈 Taxa de sucesso: {success_rate:.1f}%")
        print(f"⏱️  Tempo total: {total_time:.2f}s")
        print(f"🚀 Requisições/segundo: {requests_per_second:.2f}")
        print(f"✅ Sucessos/segundo: {successful_rps:.2f}")
        
        if successful_durations:
            print("\n⏱️ TEMPOS DE RESPOSTA (sucessos):")
            print(f"   Média: {avg_duration:.3f}s")
            print(f"   Mediana: {median_duration:.3f}s")
            print(f"   Mínimo: {min_duration:.3f}s")
            print(f"   Máximo: {max_duration:.3f}s")
            print(f"   Desvio padrão: {std_deviation:.3f}s")
            
        # Erros por código de status
        error_codes = {}
        for result in self.results:
            if not result['success']:
                code = result.get('status_code', 'error')
                error_codes[code] = error_codes.get(code, 0) + 1
                
        if error_codes:
            print("\n❌ ERROS POR CÓDIGO:")
            for code, count in error_codes.items():
                print(f"   {code}: {count} ocorrências")
        
        # Salvar relatório detalhado
        report = {
            'test_summary': {
                'total_requests': total_requests,
                'successful_requests': successful_requests,
                'failed_requests': failed_requests,
                'success_rate': success_rate,
                'total_time': total_time,
                'requests_per_second': requests_per_second,
                'successful_rps': successful_rps
            },
            'response_times': {
                'average': avg_duration,
                'median': median_duration,
                'minimum': min_duration,
                'maximum': max_duration,
                'std_deviation': std_deviation
            },
            'error_codes': error_codes,
            'detailed_results': self.results
        }
        
        # Salvar relatório
        report_file = Path(__file__).parent.parent / "logs" / "load_test_report.json"
        report_file.parent.mkdir(exist_ok=True)
        
        with open(report_file, 'w') as f:
            json.dump(report, f, indent=2)
            
        print(f"\n📄 Relatório detalhado: {report_file}")
        
        # Recomendações
        print("\n💡 RECOMENDAÇÕES:")
        if success_rate < 95:
            print("   ⚠️ Taxa de sucesso baixa - verificar logs de erro")
        if avg_duration > 10:
            print("   ⚠️ Tempo de resposta alto - considerar otimizações")
        if successful_rps < 1:
            print("   ⚠️ Throughput baixo - verificar recursos do servidor")
        else:
            print("   ✅ Performance satisfatória para o modelo tiny")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Teste de carga para API Whisper')
    parser.add_argument('--url', default='http://localhost:5555', 
                       help='URL base da API')
    parser.add_argument('--requests', type=int, default=20, 
                       help='Número de requisições')
    parser.add_argument('--concurrent', type=int, default=5, 
                       help='Máximo de requisições simultâneas')
    parser.add_argument('--file', help='Arquivo WAV específico para teste')
    
    args = parser.parse_args()
    
    tester = LoadTester(args.url, args.concurrent)
    success = tester.run_concurrent_test(args.requests, args.file)
    
    sys.exit(0 if success else 1) 