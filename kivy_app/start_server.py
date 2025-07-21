#!/usr/bin/env python3
"""
Script de Inicialização Segura do Sistema de Gestão
Previne erros 502 Bad Gateway e garante inicialização estável
"""

import os
import sys
import time
import subprocess
import logging
from pathlib import Path

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('startup.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

def check_python_version():
    """Verifica versão do Python"""
    if sys.version_info < (3, 8):
        logger.error("❌ Python 3.8+ é necessário")
        return False
    
    logger.info(f"✅ Python {sys.version_info.major}.{sys.version_info.minor} detectado")
    return True

def install_dependencies():
    """Instala dependências necessárias"""
    try:
        logger.info("📦 Instalando dependências...")
        
        # Verificar se requirements.txt existe
        req_file = Path(__file__).parent / "requirements.txt"
        if not req_file.exists():
            logger.error("❌ Arquivo requirements.txt não encontrado")
            return False
        
        # Instalar dependências
        cmd = [sys.executable, "-m", "pip", "install", "-r", str(req_file)]
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode != 0:
            logger.error(f"❌ Erro ao instalar dependências: {result.stderr}")
            return False
        
        logger.info("✅ Dependências instaladas com sucesso")
        return True
        
    except Exception as e:
        logger.error(f"❌ Erro na instalação: {e}")
        return False

def run_system_check():
    """Executa verificação do sistema"""
    try:
        logger.info("🔍 Executando verificação do sistema...")
        
        # Executar check_memory.py
        cmd = [sys.executable, "check_memory.py"]
        result = subprocess.run(cmd, capture_output=True, text=True, cwd=Path(__file__).parent)
        
        if result.returncode != 0:
            logger.error("❌ Sistema não atende aos requisitos mínimos")
            logger.error(result.stdout)
            return False
        
        logger.info("✅ Sistema aprovado na verificação")
        return True
        
    except Exception as e:
        logger.error(f"❌ Erro na verificação: {e}")
        return False

def start_application():
    """Inicia aplicação usando safe_launcher"""
    try:
        logger.info("🚀 Iniciando aplicação...")
        
        # Usar safe_launcher para iniciar
        cmd = [sys.executable, "safe_launcher.py"]
        
        # Executar em modo interativo
        process = subprocess.Popen(
            cmd,
            cwd=Path(__file__).parent,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            universal_newlines=True,
            bufsize=1
        )
        
        # Monitorar saída em tempo real
        while True:
            output = process.stdout.readline()
            if output == '' and process.poll() is not None:
                break
            if output:
                print(output.strip())
        
        return_code = process.poll()
        
        if return_code == 0:
            logger.info("✅ Aplicação encerrada normalmente")
        else:
            logger.error(f"❌ Aplicação encerrada com erro (código: {return_code})")
        
        return return_code == 0
        
    except KeyboardInterrupt:
        logger.info("⏹️  Interrompido pelo usuário")
        return True
    except Exception as e:
        logger.error(f"❌ Erro ao iniciar aplicação: {e}")
        return False

def main():
    """Função principal do startup"""
    logger.info("=" * 60)
    logger.info("🚀 SISTEMA DE GESTÃO - INICIALIZAÇÃO SEGURA")
    logger.info("=" * 60)
    
    try:
        # 1. Verificar Python
        if not check_python_version():
            return 1
        
        # 2. Instalar dependências
        if not install_dependencies():
            return 1
        
        # 3. Verificar sistema
        if not run_system_check():
            logger.warning("⚠️  Sistema não passou na verificação, mas continuando...")
        
        # 4. Iniciar aplicação
        if not start_application():
            return 1
        
        logger.info("🎉 Startup concluído com sucesso!")
        return 0
        
    except Exception as e:
        logger.error(f"❌ Erro crítico no startup: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
