#!/usr/bin/env python3
"""
Sistema de Verificação de Memória e Recursos
Valida se a máquina virtual tem recursos suficientes para executar o aplicativo
"""

import psutil
import platform
import sys
import os
import logging
from typing import Dict, Tuple, bool

# Configuração de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('system_check.log'),
        logging.StreamHandler()
    ]
)

class SystemChecker:
    """Classe para verificar recursos do sistema"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.min_memory_mb = 512  # Mínimo 512MB RAM
        self.min_disk_mb = 100    # Mínimo 100MB espaço em disco
        self.min_cpu_cores = 1    # Mínimo 1 core CPU
        
    def check_memory(self) -> Tuple[bool, Dict]:
        """Verifica memória disponível"""
        try:
            memory = psutil.virtual_memory()
            memory_info = {
                'total_mb': round(memory.total / (1024 * 1024), 2),
                'available_mb': round(memory.available / (1024 * 1024), 2),
                'used_percent': memory.percent,
                'free_mb': round(memory.free / (1024 * 1024), 2)
            }
            
            is_sufficient = memory_info['available_mb'] >= self.min_memory_mb
            
            self.logger.info(f"Memória Total: {memory_info['total_mb']} MB")
            self.logger.info(f"Memória Disponível: {memory_info['available_mb']} MB")
            self.logger.info(f"Uso de Memória: {memory_info['used_percent']}%")
            
            return is_sufficient, memory_info
            
        except Exception as e:
            self.logger.error(f"Erro ao verificar memória: {e}")
            return False, {}
    
    def check_disk_space(self) -> Tuple[bool, Dict]:
        """Verifica espaço em disco"""
        try:
            disk = psutil.disk_usage('/')
            disk_info = {
                'total_mb': round(disk.total / (1024 * 1024), 2),
                'free_mb': round(disk.free / (1024 * 1024), 2),
                'used_mb': round(disk.used / (1024 * 1024), 2),
                'used_percent': round((disk.used / disk.total) * 100, 2)
            }
            
            is_sufficient = disk_info['free_mb'] >= self.min_disk_mb
            
            self.logger.info(f"Espaço Total: {disk_info['total_mb']} MB")
            self.logger.info(f"Espaço Livre: {disk_info['free_mb']} MB")
            self.logger.info(f"Uso do Disco: {disk_info['used_percent']}%")
            
            return is_sufficient, disk_info
            
        except Exception as e:
            self.logger.error(f"Erro ao verificar disco: {e}")
            return False, {}
    
    def check_cpu(self) -> Tuple[bool, Dict]:
        """Verifica CPU"""
        try:
            cpu_info = {
                'cores': psutil.cpu_count(logical=False),
                'logical_cores': psutil.cpu_count(logical=True),
                'current_freq': psutil.cpu_freq().current if psutil.cpu_freq() else 0,
                'usage_percent': psutil.cpu_percent(interval=1)
            }
            
            is_sufficient = cpu_info['cores'] >= self.min_cpu_cores
            
            self.logger.info(f"CPU Cores: {cpu_info['cores']}")
            self.logger.info(f"CPU Lógicos: {cpu_info['logical_cores']}")
            self.logger.info(f"Uso CPU: {cpu_info['usage_percent']}%")
            
            return is_sufficient, cpu_info
            
        except Exception as e:
            self.logger.error(f"Erro ao verificar CPU: {e}")
            return False, {}
    
    def check_python_version(self) -> Tuple[bool, Dict]:
        """Verifica versão do Python"""
        try:
            version_info = {
                'version': sys.version,
                'major': sys.version_info.major,
                'minor': sys.version_info.minor,
                'micro': sys.version_info.micro
            }
            
            # Requer Python 3.8+
            is_sufficient = (version_info['major'] >= 3 and version_info['minor'] >= 8)
            
            self.logger.info(f"Python Version: {version_info['version']}")
            
            return is_sufficient, version_info
            
        except Exception as e:
            self.logger.error(f"Erro ao verificar Python: {e}")
            return False, {}
    
    def check_platform(self) -> Dict:
        """Verifica informações da plataforma"""
        try:
            platform_info = {
                'system': platform.system(),
                'release': platform.release(),
                'version': platform.version(),
                'machine': platform.machine(),
                'processor': platform.processor(),
                'architecture': platform.architecture()[0]
            }
            
            self.logger.info(f"Sistema: {platform_info['system']} {platform_info['release']}")
            self.logger.info(f"Arquitetura: {platform_info['architecture']}")
            
            return platform_info
            
        except Exception as e:
            self.logger.error(f"Erro ao verificar plataforma: {e}")
            return {}
    
    def check_network_ports(self, ports: list = [8000, 5000, 3000]) -> Dict:
        """Verifica se portas estão disponíveis"""
        port_status = {}
        
        for port in ports:
            try:
                connections = psutil.net_connections()
                port_in_use = any(conn.laddr.port == port for conn in connections if conn.laddr)
                port_status[port] = {
                    'available': not port_in_use,
                    'status': 'Livre' if not port_in_use else 'Em uso'
                }
                self.logger.info(f"Porta {port}: {port_status[port]['status']}")
                
            except Exception as e:
                port_status[port] = {
                    'available': False,
                    'status': f'Erro: {e}'
                }
                self.logger.error(f"Erro ao verificar porta {port}: {e}")
        
        return port_status
    
    def run_full_check(self) -> Dict:
        """Executa verificação completa do sistema"""
        self.logger.info("=== INICIANDO VERIFICAÇÃO COMPLETA DO SISTEMA ===")
        
        results = {
            'timestamp': psutil.boot_time(),
            'checks': {},
            'overall_status': True,
            'recommendations': []
        }
        
        # Verificar memória
        memory_ok, memory_info = self.check_memory()
        results['checks']['memory'] = {
            'status': memory_ok,
            'info': memory_info
        }
        if not memory_ok:
            results['overall_status'] = False
            results['recommendations'].append(
                f"Memória insuficiente. Disponível: {memory_info.get('available_mb', 0)} MB, "
                f"Necessário: {self.min_memory_mb} MB"
            )
        
        # Verificar disco
        disk_ok, disk_info = self.check_disk_space()
        results['checks']['disk'] = {
            'status': disk_ok,
            'info': disk_info
        }
        if not disk_ok:
            results['overall_status'] = False
            results['recommendations'].append(
                f"Espaço em disco insuficiente. Disponível: {disk_info.get('free_mb', 0)} MB, "
                f"Necessário: {self.min_disk_mb} MB"
            )
        
        # Verificar CPU
        cpu_ok, cpu_info = self.check_cpu()
        results['checks']['cpu'] = {
            'status': cpu_ok,
            'info': cpu_info
        }
        if not cpu_ok:
            results['overall_status'] = False
            results['recommendations'].append(
                f"CPU insuficiente. Cores: {cpu_info.get('cores', 0)}, "
                f"Necessário: {self.min_cpu_cores}"
            )
        
        # Verificar Python
        python_ok, python_info = self.check_python_version()
        results['checks']['python'] = {
            'status': python_ok,
            'info': python_info
        }
        if not python_ok:
            results['overall_status'] = False
            results['recommendations'].append(
                f"Versão do Python inadequada. Atual: {python_info.get('major', 0)}.{python_info.get('minor', 0)}, "
                f"Necessário: 3.8+"
            )
        
        # Verificar plataforma
        results['checks']['platform'] = {
            'status': True,
            'info': self.check_platform()
        }
        
        # Verificar portas
        results['checks']['ports'] = {
            'status': True,
            'info': self.check_network_ports()
        }
        
        # Log do resultado final
        if results['overall_status']:
            self.logger.info("✅ SISTEMA APROVADO - Recursos suficientes para executar o aplicativo")
        else:
            self.logger.warning("❌ SISTEMA REPROVADO - Recursos insuficientes")
            for rec in results['recommendations']:
                self.logger.warning(f"⚠️  {rec}")
        
        self.logger.info("=== VERIFICAÇÃO COMPLETA FINALIZADA ===")
        
        return results
    
    def optimize_memory(self):
        """Otimiza uso de memória"""
        try:
            import gc
            gc.collect()  # Força garbage collection
            self.logger.info("✅ Garbage collection executado")
            
            # Verifica memória após otimização
            memory = psutil.virtual_memory()
            self.logger.info(f"Memória disponível após otimização: {round(memory.available / (1024 * 1024), 2)} MB")
            
        except Exception as e:
            self.logger.error(f"Erro na otimização de memória: {e}")

def main():
    """Função principal para executar verificação"""
    checker = SystemChecker()
    
    # Otimizar memória antes da verificação
    checker.optimize_memory()
    
    # Executar verificação completa
    results = checker.run_full_check()
    
    # Salvar resultados em arquivo
    import json
    with open('system_check_results.json', 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    
    # Retornar status
    return results['overall_status']

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
