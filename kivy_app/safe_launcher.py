#!/usr/bin/env python3
"""
Sistema de Inicialização Segura para Aplicativo de Gestão Kivy
Previne erros 502 Bad Gateway e garante inicialização estável
"""

import os
import sys
import time
import threading
import asyncio
import logging
import signal
import socket
import subprocess
from typing import Optional, Dict, Any
from concurrent.futures import ThreadPoolExecutor
import psutil
import json

# Importar verificador de sistema
from check_memory import SystemChecker

class SafeLauncher:
    """Launcher seguro para aplicativo Kivy"""
    
    def __init__(self, debug_mode: bool = False):
        self.debug_mode = debug_mode
        self.app_process: Optional[subprocess.Popen] = None
        self.server_ready = False
        self.shutdown_requested = False
        self.max_startup_time = 60  # 60 segundos timeout
        self.port = 8000
        self.host = 'localhost'
        
        # Configurar logging
        log_level = logging.DEBUG if debug_mode else logging.INFO
        logging.basicConfig(
            level=log_level,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('app_launcher.log'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
        
        # Configurar handlers de sinal
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
        
        self.logger.info("🚀 Safe Launcher inicializado")
    
    def _signal_handler(self, signum, frame):
        """Handler para sinais de sistema"""
        self.logger.info(f"📡 Sinal recebido: {signum}")
        self.shutdown_requested = True
        self._cleanup()
        sys.exit(0)
    
    def _cleanup(self):
        """Limpeza de recursos"""
        self.logger.info("🧹 Iniciando limpeza de recursos...")
        
        if self.app_process and self.app_process.poll() is None:
            self.logger.info("⏹️  Terminando processo do aplicativo...")
            try:
                self.app_process.terminate()
                self.app_process.wait(timeout=10)
            except subprocess.TimeoutExpired:
                self.logger.warning("⚠️  Forçando encerramento do processo...")
                self.app_process.kill()
        
        # Liberar porta se estiver em uso
        self._free_port(self.port)
        
        # Garbage collection
        import gc
        gc.collect()
        
        self.logger.info("✅ Limpeza concluída")
    
    def _free_port(self, port: int):
        """Libera porta se estiver em uso"""
        try:
            # Verificar se porta está em uso
            connections = psutil.net_connections()
            for conn in connections:
                if conn.laddr and conn.laddr.port == port:
                    if conn.pid:
                        try:
                            process = psutil.Process(conn.pid)
                            self.logger.info(f"🔓 Liberando porta {port} (PID: {conn.pid})")
                            process.terminate()
                            process.wait(timeout=5)
                        except (psutil.NoSuchProcess, psutil.TimeoutExpired):
                            pass
        except Exception as e:
            self.logger.error(f"❌ Erro ao liberar porta {port}: {e}")
    
    def _check_port_available(self, port: int, host: str = 'localhost') -> bool:
        """Verifica se porta está disponível"""
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                sock.settimeout(1)
                result = sock.connect_ex((host, port))
                return result != 0  # 0 significa que a conexão foi bem-sucedida (porta ocupada)
        except Exception:
            return True  # Assumir disponível em caso de erro
    
    def _wait_for_server(self, timeout: int = 30) -> bool:
        """Aguarda servidor ficar disponível"""
        self.logger.info(f"⏳ Aguardando servidor em {self.host}:{self.port}...")
        
        start_time = time.time()
        while time.time() - start_time < timeout:
            if self.shutdown_requested:
                return False
                
            try:
                with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                    sock.settimeout(2)
                    result = sock.connect_ex((self.host, self.port))
                    if result == 0:
                        self.logger.info("✅ Servidor respondendo!")
                        self.server_ready = True
                        return True
            except Exception as e:
                self.logger.debug(f"Tentativa de conexão falhou: {e}")
            
            time.sleep(1)
            self.logger.info("⏳ Servidor carregando...")
        
        self.logger.error("❌ Timeout aguardando servidor")
        return False
    
    def _monitor_process(self):
        """Monitora processo do aplicativo"""
        while not self.shutdown_requested and self.app_process:
            try:
                if self.app_process.poll() is not None:
                    self.logger.error("❌ Processo do aplicativo terminou inesperadamente")
                    break
                
                # Verificar uso de memória
                try:
                    process = psutil.Process(self.app_process.pid)
                    memory_mb = process.memory_info().rss / (1024 * 1024)
                    cpu_percent = process.cpu_percent()
                    
                    if self.debug_mode:
                        self.logger.debug(f"📊 Uso: {memory_mb:.1f}MB RAM, {cpu_percent:.1f}% CPU")
                    
                    # Alerta se uso de memória muito alto
                    if memory_mb > 1024:  # > 1GB
                        self.logger.warning(f"⚠️  Alto uso de memória: {memory_mb:.1f}MB")
                        
                except psutil.NoSuchProcess:
                    break
                    
            except Exception as e:
                self.logger.error(f"❌ Erro no monitoramento: {e}")
            
            time.sleep(5)  # Verificar a cada 5 segundos
    
    def _pre_launch_checks(self) -> bool:
        """Verificações antes do lançamento"""
        self.logger.info("🔍 Executando verificações pré-lançamento...")
        
        # Verificar recursos do sistema
        checker = SystemChecker()
        system_ok = checker.run_full_check()
        
        if not system_ok['overall_status']:
            self.logger.error("❌ Sistema não atende aos requisitos mínimos")
            for rec in system_ok['recommendations']:
                self.logger.error(f"⚠️  {rec}")
            return False
        
        # Otimizar memória
        checker.optimize_memory()
        
        # Verificar se porta está livre
        if not self._check_port_available(self.port):
            self.logger.warning(f"⚠️  Porta {self.port} em uso, liberando...")
            self._free_port(self.port)
            time.sleep(2)
            
            if not self._check_port_available(self.port):
                self.logger.error(f"❌ Não foi possível liberar porta {self.port}")
                return False
        
        # Verificar dependências Python
        required_modules = ['kivy', 'kivymd', 'sqlite3', 'json']
        for module in required_modules:
            try:
                __import__(module)
                self.logger.debug(f"✅ Módulo {module} disponível")
            except ImportError:
                self.logger.error(f"❌ Módulo {module} não encontrado")
                return False
        
        self.logger.info("✅ Todas as verificações pré-lançamento passaram")
        return True
    
    def _launch_app_process(self) -> bool:
        """Lança processo do aplicativo"""
        try:
            self.logger.info("🚀 Iniciando processo do aplicativo...")
            
            # Comando para executar o aplicativo principal
            cmd = [sys.executable, 'main.py']
            
            if self.debug_mode:
                cmd.append('--debug')
            
            # Configurar ambiente
            env = os.environ.copy()
            env['KIVY_LOG_LEVEL'] = 'debug' if self.debug_mode else 'info'
            env['PYTHONUNBUFFERED'] = '1'
            
            # Iniciar processo
            self.app_process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                universal_newlines=True,
                env=env,
                cwd=os.path.dirname(os.path.abspath(__file__))
            )
            
            self.logger.info(f"✅ Processo iniciado (PID: {self.app_process.pid})")
            
            # Iniciar monitoramento em thread separada
            monitor_thread = threading.Thread(target=self._monitor_process, daemon=True)
            monitor_thread.start()
            
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Erro ao iniciar processo: {e}")
            return False
    
    def _show_startup_progress(self):
        """Mostra progresso da inicialização"""
        progress_chars = ['⠋', '⠙', '⠹', '⠸', '⠼', '⠴', '⠦', '⠧', '⠇', '⠏']
        char_index = 0
        
        start_time = time.time()
        while not self.server_ready and not self.shutdown_requested:
            elapsed = int(time.time() - start_time)
            char = progress_chars[char_index % len(progress_chars)]
            
            print(f"\r{char} Inicialização em progresso... ({elapsed}s)", end='', flush=True)
            
            char_index += 1
            time.sleep(0.1)
            
            if elapsed > self.max_startup_time:
                print(f"\n❌ Timeout na inicialização ({self.max_startup_time}s)")
                break
        
        if self.server_ready:
            print(f"\n✅ Aplicativo pronto! ({int(time.time() - start_time)}s)")
    
    def launch(self) -> bool:
        """Lança aplicativo com verificações de segurança"""
        try:
            self.logger.info("=" * 50)
            self.logger.info("🚀 INICIANDO SISTEMA DE GESTÃO KIVY")
            self.logger.info("=" * 50)
            
            # Verificações pré-lançamento
            if not self._pre_launch_checks():
                self.logger.error("❌ Falha nas verificações pré-lançamento")
                return False
            
            # Lançar processo do aplicativo
            if not self._launch_app_process():
                self.logger.error("❌ Falha ao iniciar processo do aplicativo")
                return False
            
            # Mostrar progresso da inicialização
            progress_thread = threading.Thread(target=self._show_startup_progress, daemon=True)
            progress_thread.start()
            
            # Aguardar servidor ficar pronto
            if not self._wait_for_server(self.max_startup_time):
                self.logger.error("❌ Servidor não ficou pronto no tempo esperado")
                self._cleanup()
                return False
            
            self.logger.info("🎉 APLICATIVO INICIADO COM SUCESSO!")
            self.logger.info(f"🌐 Acesse: http://{self.host}:{self.port}")
            
            # Manter aplicativo rodando
            self._keep_alive()
            
            return True
            
        except KeyboardInterrupt:
            self.logger.info("⏹️  Interrupção solicitada pelo usuário")
            return True
        except Exception as e:
            self.logger.error(f"❌ Erro crítico no launcher: {e}")
            return False
        finally:
            self._cleanup()
    
    def _keep_alive(self):
        """Mantém aplicativo vivo e monitora saúde"""
        self.logger.info("💓 Monitoramento ativo - Pressione Ctrl+C para sair")
        
        last_health_check = time.time()
        
        try:
            while not self.shutdown_requested:
                # Verificar se processo ainda está rodando
                if self.app_process and self.app_process.poll() is not None:
                    self.logger.error("❌ Processo do aplicativo terminou")
                    break
                
                # Health check periódico
                if time.time() - last_health_check > 30:  # A cada 30 segundos
                    self._health_check()
                    last_health_check = time.time()
                
                time.sleep(1)
                
        except KeyboardInterrupt:
            self.logger.info("⏹️  Shutdown solicitado")
    
    def _health_check(self):
        """Verificação de saúde do aplicativo"""
        try:
            # Verificar conectividade
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                sock.settimeout(5)
                result = sock.connect_ex((self.host, self.port))
                if result != 0:
                    self.logger.warning("⚠️  Servidor não está respondendo")
                    return False
            
            # Verificar uso de recursos
            if self.app_process:
                try:
                    process = psutil.Process(self.app_process.pid)
                    memory_mb = process.memory_info().rss / (1024 * 1024)
                    
                    if memory_mb > 2048:  # > 2GB
                        self.logger.warning(f"⚠️  Alto uso de memória: {memory_mb:.1f}MB")
                        # Tentar otimizar
                        import gc
                        gc.collect()
                        
                except psutil.NoSuchProcess:
                    self.logger.error("❌ Processo do aplicativo não encontrado")
                    return False
            
            self.logger.debug("💚 Health check OK")
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Erro no health check: {e}")
            return False

def main():
    """Função principal"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Safe Launcher para Aplicativo de Gestão Kivy')
    parser.add_argument('--debug', action='store_true', help='Ativar modo debug')
    parser.add_argument('--port', type=int, default=8000, help='Porta do servidor (padrão: 8000)')
    parser.add_argument('--timeout', type=int, default=60, help='Timeout de inicialização em segundos')
    
    args = parser.parse_args()
    
    # Criar launcher
    launcher = SafeLauncher(debug_mode=args.debug)
    launcher.port = args.port
    launcher.max_startup_time = args.timeout
    
    # Executar
    success = launcher.launch()
    
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())
