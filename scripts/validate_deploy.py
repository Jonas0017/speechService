#!/usr/bin/env python3
# scripts/validate_deploy.py

import os
import json
import subprocess
import sys
from pathlib import Path
import time

class DeployValidator:
    def __init__(self):
        self.project_root = Path(__file__).parent.parent
        self.validation_results = []
        
    def log_check(self, check_name, success, message, details=None):
        """Registrar resultado da validação"""
        result = {
            "check": check_name,
            "success": success,
            "message": message,
            "details": details
        }
        self.validation_results.append(result)
        
        status = "✅" if success else "❌"
        print(f"{status} {check_name}: {message}")
        
        if details and not success:
            print(f"   Detalhes: {details}")
    
    def validate_file_structure(self):
        """Validar estrutura de arquivos necessários"""
        required_files = [
            "src/servidor_whisper.py",
            "src/config.py", 
            "src/utils.py",
            "src/monitoring.py",
            "requirements.txt",
            "requirements.prod.txt",
            "docker/Dockerfile",
            "docker/Dockerfile.dev",
            "docker/docker-compose.yml",
            "config/gunicorn.conf.py",
            "config/nginx.conf",
            ".gitignore",
            "README.md"
        ]
        
        missing_files = []
        for file_path in required_files:
            full_path = self.project_root / file_path
            if not full_path.exists():
                missing_files.append(file_path)
        
        if missing_files:
            self.log_check(
                "Estrutura de Arquivos",
                False,
                f"Arquivos faltando: {', '.join(missing_files)}"
            )
            return False
        else:
            self.log_check(
                "Estrutura de Arquivos",
                True,
                "Todos os arquivos necessários presentes"
            )
            return True
    
    def validate_whisper_model(self):
        """Validar carregamento do modelo Whisper"""
        try:
            import whisper
            
            print("🤖 Testando carregamento do modelo Whisper...")
            start_time = time.time()
            model = whisper.load_model("tiny")
            load_time = time.time() - start_time
            
            self.log_check(
                "Modelo Whisper",
                True,
                f"Modelo carregado em {load_time:.2f}s"
            )
            return True
            
        except Exception as e:
            self.log_check(
                "Modelo Whisper",
                False,
                f"Erro ao carregar modelo: {e}"
            )
            return False
    
    def run_full_validation(self):
        """Executar validação completa"""
        print("🔍 VALIDAÇÃO PRÉ-DEPLOY - WHISPER SERVER")
        print("=" * 50)
        
        # Executar validações
        self.validate_file_structure()
        self.validate_whisper_model()
        
        # Resumo
        print("\n" + "=" * 50)
        print("📋 RESUMO DA VALIDAÇÃO")
        print("=" * 50)
        
        total_checks = len(self.validation_results)
        passed_checks = sum(1 for r in self.validation_results if r["success"])
        failed_checks = total_checks - passed_checks
        
        print(f"Total de verificações: {total_checks}")
        print(f"✅ Passaram: {passed_checks}")
        print(f"❌ Falharam: {failed_checks}")
        
        ready_for_deploy = all(r["success"] for r in self.validation_results)
        
        if ready_for_deploy:
            print("\n🎉 PROJETO PRONTO PARA DEPLOY!")
            print("✅ Todas as validações passaram")
        else:
            print("\n⚠️ PROJETO NÃO ESTÁ PRONTO")
            print("❌ Corrigir problemas antes do deploy")
            
            # Mostrar problemas
            print("\n🔧 PROBLEMAS A CORRIGIR:")
            for result in self.validation_results:
                if not result["success"]:
                    print(f"   - {result['check']}: {result['message']}")
        
        return ready_for_deploy

if __name__ == "__main__":
    validator = DeployValidator()
    success = validator.run_full_validation()
    
    sys.exit(0 if success else 1) 