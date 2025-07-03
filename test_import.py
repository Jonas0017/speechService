#!/usr/bin/env python3
# Teste de imports para debug

print("🧪 Testando imports...")

try:
    from src.config import Config
    print("✅ Config OK")
except Exception as e:
    print(f"❌ Config erro: {e}")

try:
    from src.utils import ProgressTracker, validate_wav_file, load_wav_audio
    print("✅ Utils OK")
except Exception as e:
    print(f"❌ Utils erro: {e}")
    import traceback
    traceback.print_exc()

try:
    from src.monitoring import MetricsCollector, HealthChecker
    print("✅ Monitoring OK")
except Exception as e:
    print(f"❌ Monitoring erro: {e}")
    import traceback
    traceback.print_exc()

print("�� Teste concluído!") 