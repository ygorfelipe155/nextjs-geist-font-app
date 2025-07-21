#!/usr/bin/env python3
"""
Gerenciador de Banco de Dados para Sistema de Gestão
Gerencia dados de materiais, custos fixos, orçamentos e projetos
"""

import sqlite3
import json
import logging
import threading
import os
from datetime import datetime
from typing import Dict, List, Optional, Any, Tuple
from contextlib import contextmanager
import weakref

class DatabaseManager:
    """Gerenciador de banco de dados SQLite com thread safety"""
    
    def __init__(self, db_path: str = "gestao_app.db"):
        self.db_path = db_path
        self.logger = logging.getLogger(__name__)
        self._local = threading.local()
        self._connections = weakref.WeakSet()
        
        # Criar banco e tabelas se não existirem
        self._initialize_database()
        
        self.logger.info(f"✅ Database Manager inicializado: {db_path}")
    
    def _get_connection(self) -> sqlite3.Connection:
        """Obtém conexão thread-local"""
        if not hasattr(self._local, 'connection'):
            self._local.connection = sqlite3.connect(
                self.db_path,
                check_same_thread=False,
                timeout=30.0
            )
            self._local.connection.row_factory = sqlite3.Row
            self._local.connection.execute("PRAGMA foreign_keys = ON")
            self._connections.add(self._local.connection)
        
        return self._local.connection
    
    @contextmanager
    def get_cursor(self):
        """Context manager para cursor de banco"""
        conn = self._get_connection()
        cursor = conn.cursor()
        try:
            yield cursor
            conn.commit()
        except Exception as e:
            conn.rollback()
            self.logger.error(f"❌ Erro na transação: {e}")
            raise
        finally:
            cursor.close()
    
    def _initialize_database(self):
        """Inicializa banco de dados e cria tabelas"""
        try:
            with self.get_cursor() as cursor:
                # Tabela de materiais
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS materiais (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        nome TEXT NOT NULL UNIQUE,
                        valor REAL NOT NULL,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                
                # Tabela de custos fixos
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS custos_fixos (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        nome TEXT NOT NULL UNIQUE,
                        valor REAL NOT NULL,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                
                # Tabela de orçamentos
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS orcamentos (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        cliente_nome TEXT,
                        dias_trabalhados INTEGER NOT NULL,
                        lucro_liquido REAL NOT NULL,
                        orcamento_minimo REAL NOT NULL,
                        acrescimo REAL NOT NULL,
                        desconto REAL NOT NULL,
                        valor_total REAL NOT NULL,
                        status TEXT DEFAULT 'pendente',
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                
                # Tabela de materiais do orçamento
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS orcamento_materiais (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        orcamento_id INTEGER NOT NULL,
                        material_id INTEGER NOT NULL,
                        quantidade INTEGER NOT NULL,
                        valor_unitario REAL NOT NULL,
                        FOREIGN KEY (orcamento_id) REFERENCES orcamentos (id) ON DELETE CASCADE,
                        FOREIGN KEY (material_id) REFERENCES materiais (id)
                    )
                """)
                
                # Tabela de projetos
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS projetos (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        cliente_nome TEXT NOT NULL,
                        nome_projeto TEXT NOT NULL,
                        etapa_atual TEXT NOT NULL,
                        proxima_acao TEXT NOT NULL,
                        prazo DATE NOT NULL,
                        status TEXT DEFAULT 'em-andamento',
                        orcamento_id INTEGER,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (orcamento_id) REFERENCES orcamentos (id)
                    )
                """)
                
                # Índices para performance
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_materiais_nome ON materiais(nome)")
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_orcamentos_status ON orcamentos(status)")
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_orcamentos_created ON orcamentos(created_at)")
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_projetos_status ON projetos(status)")
                
                self.logger.info("✅ Banco de dados inicializado com sucesso")
                
        except Exception as e:
            self.logger.error(f"❌ Erro ao inicializar banco: {e}")
            raise
    
    # === MATERIAIS ===
    
    def adicionar_material(self, nome: str, valor: float) -> int:
        """Adiciona novo material"""
        try:
            with self.get_cursor() as cursor:
                cursor.execute(
                    "INSERT INTO materiais (nome, valor) VALUES (?, ?)",
                    (nome.strip(), valor)
                )
                material_id = cursor.lastrowid
                self.logger.info(f"✅ Material adicionado: {nome} (ID: {material_id})")
                return material_id
                
        except sqlite3.IntegrityError:
            self.logger.error(f"❌ Material já existe: {nome}")
            raise ValueError(f"Material '{nome}' já existe")
        except Exception as e:
            self.logger.error(f"❌ Erro ao adicionar material: {e}")
            raise
    
    def listar_materiais(self) -> List[Dict]:
        """Lista todos os materiais"""
        try:
            with self.get_cursor() as cursor:
                cursor.execute(
                    "SELECT id, nome, valor, created_at FROM materiais ORDER BY nome"
                )
                materiais = [dict(row) for row in cursor.fetchall()]
                self.logger.debug(f"📋 {len(materiais)} materiais listados")
                return materiais
                
        except Exception as e:
            self.logger.error(f"❌ Erro ao listar materiais: {e}")
            return []
    
    def atualizar_material(self, material_id: int, nome: str = None, valor: float = None) -> bool:
        """Atualiza material existente"""
        try:
            updates = []
            params = []
            
            if nome is not None:
                updates.append("nome = ?")
                params.append(nome.strip())
            
            if valor is not None:
                updates.append("valor = ?")
                params.append(valor)
            
            if not updates:
                return False
            
            updates.append("updated_at = CURRENT_TIMESTAMP")
            params.append(material_id)
            
            with self.get_cursor() as cursor:
                cursor.execute(
                    f"UPDATE materiais SET {', '.join(updates)} WHERE id = ?",
                    params
                )
                
                if cursor.rowcount > 0:
                    self.logger.info(f"✅ Material atualizado (ID: {material_id})")
                    return True
                else:
                    self.logger.warning(f"⚠️  Material não encontrado (ID: {material_id})")
                    return False
                    
        except sqlite3.IntegrityError:
            self.logger.error(f"❌ Nome de material já existe: {nome}")
            raise ValueError(f"Material '{nome}' já existe")
        except Exception as e:
            self.logger.error(f"❌ Erro ao atualizar material: {e}")
            raise
    
    def remover_material(self, material_id: int) -> bool:
        """Remove material"""
        try:
            with self.get_cursor() as cursor:
                cursor.execute("DELETE FROM materiais WHERE id = ?", (material_id,))
                
                if cursor.rowcount > 0:
                    self.logger.info(f"✅ Material removido (ID: {material_id})")
                    return True
                else:
                    self.logger.warning(f"⚠️  Material não encontrado (ID: {material_id})")
                    return False
                    
        except Exception as e:
            self.logger.error(f"❌ Erro ao remover material: {e}")
            raise
    
    # === CUSTOS FIXOS ===
    
    def adicionar_custo_fixo(self, nome: str, valor: float) -> int:
        """Adiciona novo custo fixo"""
        try:
            with self.get_cursor() as cursor:
                cursor.execute(
                    "INSERT INTO custos_fixos (nome, valor) VALUES (?, ?)",
                    (nome.strip(), valor)
                )
                custo_id = cursor.lastrowid
                self.logger.info(f"✅ Custo fixo adicionado: {nome} (ID: {custo_id})")
                return custo_id
                
        except sqlite3.IntegrityError:
            self.logger.error(f"❌ Custo fixo já existe: {nome}")
            raise ValueError(f"Custo fixo '{nome}' já existe")
        except Exception as e:
            self.logger.error(f"❌ Erro ao adicionar custo fixo: {e}")
            raise
    
    def listar_custos_fixos(self) -> List[Dict]:
        """Lista todos os custos fixos"""
        try:
            with self.get_cursor() as cursor:
                cursor.execute(
                    "SELECT id, nome, valor, created_at FROM custos_fixos ORDER BY nome"
                )
                custos = [dict(row) for row in cursor.fetchall()]
                self.logger.debug(f"📋 {len(custos)} custos fixos listados")
                return custos
                
        except Exception as e:
            self.logger.error(f"❌ Erro ao listar custos fixos: {e}")
            return []
    
    def atualizar_custo_fixo(self, custo_id: int, nome: str = None, valor: float = None) -> bool:
        """Atualiza custo fixo existente"""
        try:
            updates = []
            params = []
            
            if nome is not None:
                updates.append("nome = ?")
                params.append(nome.strip())
            
            if valor is not None:
                updates.append("valor = ?")
                params.append(valor)
            
            if not updates:
                return False
            
            updates.append("updated_at = CURRENT_TIMESTAMP")
            params.append(custo_id)
            
            with self.get_cursor() as cursor:
                cursor.execute(
                    f"UPDATE custos_fixos SET {', '.join(updates)} WHERE id = ?",
                    params
                )
                
                if cursor.rowcount > 0:
                    self.logger.info(f"✅ Custo fixo atualizado (ID: {custo_id})")
                    return True
                else:
                    self.logger.warning(f"⚠️  Custo fixo não encontrado (ID: {custo_id})")
                    return False
                    
        except sqlite3.IntegrityError:
            self.logger.error(f"❌ Nome de custo fixo já existe: {nome}")
            raise ValueError(f"Custo fixo '{nome}' já existe")
        except Exception as e:
            self.logger.error(f"❌ Erro ao atualizar custo fixo: {e}")
            raise
    
    def remover_custo_fixo(self, custo_id: int) -> bool:
        """Remove custo fixo"""
        try:
            with self.get_cursor() as cursor:
                cursor.execute("DELETE FROM custos_fixos WHERE id = ?", (custo_id,))
                
                if cursor.rowcount > 0:
                    self.logger.info(f"✅ Custo fixo removido (ID: {custo_id})")
                    return True
                else:
                    self.logger.warning(f"⚠️  Custo fixo não encontrado (ID: {custo_id})")
                    return False
                    
        except Exception as e:
            self.logger.error(f"❌ Erro ao remover custo fixo: {e}")
            raise
    
    def calcular_total_custos_fixos(self) -> float:
        """Calcula total dos custos fixos"""
        try:
            with self.get_cursor() as cursor:
                cursor.execute("SELECT COALESCE(SUM(valor), 0) as total FROM custos_fixos")
                total = cursor.fetchone()['total']
                return float(total)
                
        except Exception as e:
            self.logger.error(f"❌ Erro ao calcular custos fixos: {e}")
            return 0.0
    
    # === ORÇAMENTOS ===
    
    def adicionar_orcamento(self, dados_orcamento: Dict, materiais: List[Dict]) -> int:
        """Adiciona novo orçamento com materiais"""
        try:
            with self.get_cursor() as cursor:
                # Inserir orçamento
                cursor.execute("""
                    INSERT INTO orcamentos 
                    (cliente_nome, dias_trabalhados, lucro_liquido, orcamento_minimo, 
                     acrescimo, desconto, valor_total, status)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    dados_orcamento.get('cliente_nome'),
                    dados_orcamento['dias_trabalhados'],
                    dados_orcamento['lucro_liquido'],
                    dados_orcamento['orcamento_minimo'],
                    dados_orcamento['acrescimo'],
                    dados_orcamento['desconto'],
                    dados_orcamento['valor_total'],
                    dados_orcamento.get('status', 'pendente')
                ))
                
                orcamento_id = cursor.lastrowid
                
                # Inserir materiais do orçamento
                for material in materiais:
                    cursor.execute("""
                        INSERT INTO orcamento_materiais 
                        (orcamento_id, material_id, quantidade, valor_unitario)
                        VALUES (?, ?, ?, ?)
                    """, (
                        orcamento_id,
                        material['material_id'],
                        material['quantidade'],
                        material['valor_unitario']
                    ))
                
                self.logger.info(f"✅ Orçamento adicionado (ID: {orcamento_id})")
                return orcamento_id
                
        except Exception as e:
            self.logger.error(f"❌ Erro ao adicionar orçamento: {e}")
            raise
    
    def listar_orcamentos(self, status: str = None) -> List[Dict]:
        """Lista orçamentos com filtro opcional por status"""
        try:
            with self.get_cursor() as cursor:
                if status:
                    cursor.execute("""
                        SELECT id, cliente_nome, dias_trabalhados, lucro_liquido,
                               orcamento_minimo, acrescimo, desconto, valor_total,
                               status, created_at
                        FROM orcamentos 
                        WHERE status = ?
                        ORDER BY created_at DESC
                    """, (status,))
                else:
                    cursor.execute("""
                        SELECT id, cliente_nome, dias_trabalhados, lucro_liquido,
                               orcamento_minimo, acrescimo, desconto, valor_total,
                               status, created_at
                        FROM orcamentos 
                        ORDER BY created_at DESC
                    """)
                
                orcamentos = []
                for row in cursor.fetchall():
                    orcamento = dict(row)
                    
                    # Buscar materiais do orçamento
                    cursor.execute("""
                        SELECT om.quantidade, om.valor_unitario, m.nome
                        FROM orcamento_materiais om
                        JOIN materiais m ON om.material_id = m.id
                        WHERE om.orcamento_id = ?
                    """, (orcamento['id'],))
                    
                    orcamento['materiais'] = [dict(mat) for mat in cursor.fetchall()]
                    orcamentos.append(orcamento)
                
                self.logger.debug(f"📋 {len(orcamentos)} orçamentos listados")
                return orcamentos
                
        except Exception as e:
            self.logger.error(f"❌ Erro ao listar orçamentos: {e}")
            return []
    
    def atualizar_status_orcamento(self, orcamento_id: int, status: str) -> bool:
        """Atualiza status do orçamento"""
        try:
            with self.get_cursor() as cursor:
                cursor.execute(
                    "UPDATE orcamentos SET status = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
                    (status, orcamento_id)
                )
                
                if cursor.rowcount > 0:
                    self.logger.info(f"✅ Status do orçamento atualizado (ID: {orcamento_id}, Status: {status})")
                    return True
                else:
                    self.logger.warning(f"⚠️  Orçamento não encontrado (ID: {orcamento_id})")
                    return False
                    
        except Exception as e:
            self.logger.error(f"❌ Erro ao atualizar status do orçamento: {e}")
            raise
    
    def remover_orcamento(self, orcamento_id: int) -> bool:
        """Remove orçamento e seus materiais"""
        try:
            with self.get_cursor() as cursor:
                cursor.execute("DELETE FROM orcamentos WHERE id = ?", (orcamento_id,))
                
                if cursor.rowcount > 0:
                    self.logger.info(f"✅ Orçamento removido (ID: {orcamento_id})")
                    return True
                else:
                    self.logger.warning(f"⚠️  Orçamento não encontrado (ID: {orcamento_id})")
                    return False
                    
        except Exception as e:
            self.logger.error(f"❌ Erro ao remover orçamento: {e}")
            raise
    
    # === ESTATÍSTICAS ===
    
    def obter_estatisticas_dashboard(self) -> Dict:
        """Obtém estatísticas para o dashboard"""
        try:
            with self.get_cursor() as cursor:
                stats = {}
                
                # Contadores de orçamentos
                cursor.execute("SELECT COUNT(*) as total FROM orcamentos")
                stats['total_orcamentos'] = cursor.fetchone()['total']
                
                cursor.execute("SELECT COUNT(*) as aprovados FROM orcamentos WHERE status = 'aprovado'")
                stats['orcamentos_aprovados'] = cursor.fetchone()['aprovados']
                
                cursor.execute("SELECT COUNT(*) as pendentes FROM orcamentos WHERE status = 'pendente'")
                stats['orcamentos_pendentes'] = cursor.fetchone()['pendentes']
                
                cursor.execute("SELECT COUNT(*) as rejeitados FROM orcamentos WHERE status = 'rejeitado'")
                stats['orcamentos_rejeitados'] = cursor.fetchone()['rejeitados']
                
                # Valor total dos orçamentos aprovados
                cursor.execute("SELECT COALESCE(SUM(valor_total), 0) as total FROM orcamentos WHERE status = 'aprovado'")
                stats['valor_total_aprovados'] = cursor.fetchone()['total']
                
                # Total de custos fixos
                stats['total_custos_fixos'] = self.calcular_total_custos_fixos()
                
                # Contadores de materiais
                cursor.execute("SELECT COUNT(*) as total FROM materiais")
                stats['total_materiais'] = cursor.fetchone()['total']
                
                # Orçamentos este mês
                cursor.execute("""
                    SELECT COUNT(*) as este_mes 
                    FROM orcamentos 
                    WHERE status = 'aprovado' 
                    AND strftime('%Y-%m', created_at) = strftime('%Y-%m', 'now')
                """)
                stats['contratos_este_mes'] = cursor.fetchone()['este_mes']
                
                return stats
                
        except Exception as e:
            self.logger.error(f"❌ Erro ao obter estatísticas: {e}")
            return {}
    
    def backup_database(self, backup_path: str = None) -> str:
        """Cria backup do banco de dados"""
        try:
            if not backup_path:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                backup_path = f"backup_gestao_{timestamp}.db"
            
            # Criar backup usando SQL
            with self.get_cursor() as cursor:
                backup_conn = sqlite3.connect(backup_path)
                cursor.connection.backup(backup_conn)
                backup_conn.close()
            
            self.logger.info(f"✅ Backup criado: {backup_path}")
            return backup_path
            
        except Exception as e:
            self.logger.error(f"❌ Erro ao criar backup: {e}")
            raise
    
    def close_all_connections(self):
        """Fecha todas as conexões"""
        try:
            for conn in list(self._connections):
                try:
                    conn.close()
                except:
                    pass
            
            if hasattr(self._local, 'connection'):
                try:
                    self._local.connection.close()
                    delattr(self._local, 'connection')
                except:
                    pass
            
            self.logger.info("✅ Todas as conexões fechadas")
            
        except Exception as e:
            self.logger.error(f"❌ Erro ao fechar conexões: {e}")

# Instância global do gerenciador
_db_manager = None

def get_database_manager() -> DatabaseManager:
    """Obtém instância singleton do gerenciador de banco"""
    global _db_manager
    if _db_manager is None:
        _db_manager = DatabaseManager()
    return _db_manager

def close_database():
    """Fecha banco de dados"""
    global _db_manager
    if _db_manager:
        _db_manager.close_all_connections()
        _db_manager = None
