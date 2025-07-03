#!/usr/bin/env python3
# src/monitoring.py

import time
import psutil
import logging
from collections import defaultdict, deque
from datetime import datetime, timedelta
import threading

logger = logging.getLogger(__name__)

class MetricsCollector:
    """Coletor de métricas do servidor Whisper"""
    
    def __init__(self):
        self.metrics = {
            'requests_total': 0,
            'requests_success': 0,
            'requests_error': 0,
            'transcription_times': deque(maxlen=100),  # Últimas 100 transcrições
            'file_sizes': deque(maxlen=100),
            'start_time': time.time(),
            'last_health_check': time.time()
        }
        
        # Métricas por período
        self.hourly_metrics = defaultdict(int)
        self.daily_metrics = defaultdict(int)
        
        # Lock para thread safety
        self._lock = threading.Lock()
    
    def record_request(self, success=True, transcription_time=None, file_size=None):
        """Registrar uma requisição"""
        with self._lock:
            self.metrics['requests_total'] += 1
            
            if success:
                self.metrics['requests_success'] += 1
                if transcription_time:
                    self.metrics['transcription_times'].append(transcription_time)
                if file_size:
                    self.metrics['file_sizes'].append(file_size)
            else:
                self.metrics['requests_error'] += 1
            
            # Métricas por período
            now = datetime.now()
            hour_key = now.strftime('%Y-%m-%d-%H')
            day_key = now.strftime('%Y-%m-%d')
            
            self.hourly_metrics[hour_key] += 1
            self.daily_metrics[day_key] += 1
    
    def record_health_check(self):
        """Registrar health check"""
        with self._lock:
            self.metrics['last_health_check'] = time.time()
    
    def get_metrics(self):
        """Obter todas as métricas"""
        with self._lock:
            uptime = time.time() - self.metrics['start_time']
            
            # Calcular estatísticas de tempo de transcrição
            transcription_stats = {}
            if self.metrics['transcription_times']:
                times = list(self.metrics['transcription_times'])
                transcription_stats = {
                    'avg': sum(times) / len(times),
                    'min': min(times),
                    'max': max(times),
                    'count': len(times)
                }
            
            # Calcular estatísticas de tamanho de arquivo
            file_size_stats = {}
            if self.metrics['file_sizes']:
                sizes = list(self.metrics['file_sizes'])
                file_size_stats = {
                    'avg_mb': sum(sizes) / len(sizes) / (1024*1024),
                    'min_mb': min(sizes) / (1024*1024),
                    'max_mb': max(sizes) / (1024*1024),
                    'count': len(sizes)
                }
            
            return {
                'uptime_seconds': uptime,
                'uptime_formatted': self._format_uptime(uptime),
                'requests': {
                    'total': self.metrics['requests_total'],
                    'success': self.metrics['requests_success'],
                    'error': self.metrics['requests_error'],
                    'success_rate': (self.metrics['requests_success'] / max(1, self.metrics['requests_total'])) * 100
                },
                'transcription': transcription_stats,
                'file_sizes': file_size_stats,
                'last_health_check': self.metrics['last_health_check'],
                'system': self._get_system_metrics()
            }
    
    def _format_uptime(self, seconds):
        """Formatar uptime em formato legível"""
        days = int(seconds // 86400)
        hours = int((seconds % 86400) // 3600)
        minutes = int((seconds % 3600) // 60)
        
        if days > 0:
            return f"{days}d {hours}h {minutes}m"
        elif hours > 0:
            return f"{hours}h {minutes}m"
        else:
            return f"{minutes}m"
    
    def _get_system_metrics(self):
        """Obter métricas do sistema"""
        try:
            memory = psutil.virtual_memory()
            cpu_percent = psutil.cpu_percent(interval=1)
            
            return {
                'cpu_percent': cpu_percent,
                'memory_percent': memory.percent,
                'memory_used_mb': memory.used / (1024*1024),
                'memory_total_mb': memory.total / (1024*1024)
            }
        except Exception as e:
            logger.warning(f"Erro ao obter métricas do sistema: {e}")
            return {}

class HealthChecker:
    """Verificador de saúde do sistema"""
    
    def __init__(self, metrics_collector):
        self.metrics = metrics_collector
        self.checks = []
    
    def add_check(self, name, check_func, warning_threshold=None, error_threshold=None):
        """Adicionar verificação de saúde"""
        self.checks.append({
            'name': name,
            'func': check_func,
            'warning_threshold': warning_threshold,
            'error_threshold': error_threshold
        })
    
    def run_checks(self):
        """Executar todas as verificações"""
        results = {
            'status': 'healthy',
            'checks': [],
            'timestamp': datetime.now().isoformat()
        }
        
        for check in self.checks:
            try:
                value = check['func']()
                status = 'healthy'
                message = 'OK'
                
                # Verificar thresholds
                if check['error_threshold'] and value > check['error_threshold']:
                    status = 'error'
                    message = f"Valor {value} acima do limite crítico {check['error_threshold']}"
                    results['status'] = 'error'
                elif check['warning_threshold'] and value > check['warning_threshold']:
                    status = 'warning'
                    message = f"Valor {value} acima do limite de aviso {check['warning_threshold']}"
                    if results['status'] == 'healthy':
                        results['status'] = 'warning'
                
                results['checks'].append({
                    'name': check['name'],
                    'status': status,
                    'value': value,
                    'message': message
                })
                
            except Exception as e:
                results['checks'].append({
                    'name': check['name'],
                    'status': 'error',
                    'value': None,
                    'message': f"Erro na verificação: {e}"
                })
                results['status'] = 'error'
        
        return results

# Instância global
metrics_collector = MetricsCollector()
health_checker = HealthChecker(metrics_collector)

# Adicionar verificações padrão
def check_memory_usage():
    """Verificar uso de memória"""
    return psutil.virtual_memory().percent

def check_cpu_usage():
    """Verificar uso de CPU"""
    return psutil.cpu_percent(interval=1)

def check_response_time():
    """Verificar tempo médio de resposta"""
    metrics = metrics_collector.get_metrics()
    transcription = metrics.get('transcription', {})
    return transcription.get('avg', 0)

# Configurar verificações
health_checker.add_check('memory_usage', check_memory_usage, 80, 95)
health_checker.add_check('cpu_usage', check_cpu_usage, 80, 95)
health_checker.add_check('avg_response_time', check_response_time, 10, 30)

def get_health_status():
    """Obter status de saúde completo"""
    metrics_collector.record_health_check()
    health_status = health_checker.run_checks()
    metrics = metrics_collector.get_metrics()
    
    return {
        'health': health_status,
        'metrics': metrics
    } 