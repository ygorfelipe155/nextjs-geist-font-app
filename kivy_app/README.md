# Sistema de Gestão Completo - Python/Kivy

## 🎯 Objetivo

Sistema robusto de gestão de orçamentos, materiais, custos fixos e projetos desenvolvido em Python/Kivy, com inicialização segura que previne erros 502 Bad Gateway e garante estabilidade em ambientes com recursos limitados.

## ✨ Funcionalidades

### 📊 Dashboard
- Visão geral com métricas importantes
- Contratos fechados no mês
- Total de orçamentos criados
- Custos fixos mensais
- Valor total de contratos aprovados
- Atualização automática de dados

### 📦 Gerenciamento de Materiais
- Cadastro de materiais com nome e valor
- Lista completa de materiais cadastrados
- Edição e remoção de materiais
- Cálculo automático de totais e médias

### 💰 Custos Fixos
- Cadastro de custos fixos mensais
- Cálculo automático de custo diário
- Configuração de dias trabalhados
- Cálculo de custo por equipe
- Relatórios de custos

### 🧾 Novo Orçamento
- Seleção de materiais cadastrados
- Cálculo automático de valores
- Configuração de lucro líquido
- Aplicação de acréscimos e descontos
- Salvamento no banco de dados

### 📋 Histórico de Orçamentos
- Lista completa de orçamentos
- Filtros por status (pendente, aprovado, rejeitado)
- Visualização de detalhes
- Alteração de status
- Relatórios de vendas

## 🛡️ Sistema de Segurança e Estabilidade

### ✅ Verificações Pré-Inicialização
- **Verificação de Memória**: Garante RAM suficiente (mín. 512MB)
- **Verificação de Disco**: Verifica espaço disponível (mín. 100MB)
- **Verificação de CPU**: Confirma recursos de processamento
- **Verificação de Python**: Valida versão 3.8+
- **Verificação de Dependências**: Confirma módulos necessários

### 🚀 Inicialização Segura
- **Safe Launcher**: Sistema de inicialização com timeout configurável
- **Monitoramento de Processo**: Acompanha saúde da aplicação
- **Recuperação Automática**: Reinicialização em caso de falha
- **Liberação de Porta**: Gerenciamento automático de portas
- **Otimização de Memória**: Garbage collection automático

### 📊 Monitoramento Contínuo
- **Health Check**: Verificação periódica de saúde
- **Logs Detalhados**: Registro completo de atividades
- **Alertas de Recursos**: Notificação de uso excessivo
- **Backup Automático**: Proteção de dados

## 📁 Estrutura do Projeto

```
kivy_app/
├── main_complete.py          # Aplicativo principal Kivy
├── safe_launcher.py          # Sistema de inicialização segura
├── start_server.py           # Script de startup
├── check_memory.py           # Verificador de recursos do sistema
├── database_manager.py       # Gerenciador de banco de dados
├── requirements.txt          # Dependências Python
└── README.md                # Esta documentação
```

## 🚀 Instalação e Execução

### Pré-requisitos
- Python 3.8 ou superior
- Pip (gerenciador de pacotes Python)
- Mínimo 512MB RAM disponível
- Mínimo 100MB espaço em disco

### Instalação Automática

1. **Clone ou baixe os arquivos do projeto**
2. **Execute o script de inicialização:**

```bash
cd kivy_app
python start_server.py
```

O script irá automaticamente:
- ✅ Verificar versão do Python
- ✅ Instalar todas as dependências
- ✅ Verificar recursos do sistema
- ✅ Iniciar a aplicação com segurança

### Instalação Manual

Se preferir instalar manualmente:

```bash
# 1. Instalar dependências
pip install -r requirements.txt

# 2. Verificar sistema (opcional)
python check_memory.py

# 3. Iniciar aplicação
python safe_launcher.py
```

### Opções de Execução

```bash
# Modo normal
python start_server.py

# Modo debug (logs detalhados)
python safe_launcher.py --debug

# Configurar porta personalizada
python safe_launcher.py --port 8080

# Configurar timeout personalizado
python safe_launcher.py --timeout 120
```

## 🔧 Configurações Avançadas

### Configuração de Memória
Edite `check_memory.py` para ajustar limites:
```python
self.min_memory_mb = 512    # Mínimo de RAM
self.min_disk_mb = 100      # Mínimo de disco
self.min_cpu_cores = 1      # Mínimo de CPU cores
```

### Configuração de Timeout
Ajuste tempo limite de inicialização:
```python
self.max_startup_time = 60  # 60 segundos
```

### Configuração de Porta
Altere porta padrão:
```python
self.port = 8000  # Porta padrão
```

## 🗄️ Banco de Dados

O sistema utiliza SQLite para armazenamento local:
- **Arquivo**: `gestao_app.db`
- **Thread-Safe**: Suporte a múltiplas conexões
- **Backup Automático**: Proteção de dados
- **Transações**: Integridade garantida

### Tabelas Principais
- `materiais`: Cadastro de materiais
- `custos_fixos`: Custos fixos mensais
- `orcamentos`: Orçamentos criados
- `orcamento_materiais`: Materiais por orçamento
- `projetos`: Projetos em andamento

## 📱 Interface Responsiva

O aplicativo é totalmente responsivo e funciona em:
- 💻 **Desktop**: Interface completa com navegação lateral
- 📱 **Mobile**: Layout adaptado para telas pequenas
- 🖥️ **Tablet**: Otimizado para telas médias

### Navegação
- **Barra Superior**: Título e ações principais
- **Navegação Inferior**: Acesso rápido às telas
- **Menu Lateral**: Navegação completa (desktop)

## 🔍 Solução de Problemas

### Erro 502 Bad Gateway
O sistema foi especificamente projetado para prevenir este erro:
- ✅ Verificação de porta antes da inicialização
- ✅ Timeout configurável para startup
- ✅ Monitoramento contínuo de saúde
- ✅ Reinicialização automática em caso de falha

### Problemas de Memória
- ✅ Verificação prévia de recursos
- ✅ Otimização automática de memória
- ✅ Alertas de uso excessivo
- ✅ Garbage collection forçado

### Problemas de Dependências
```bash
# Reinstalar dependências
pip install --upgrade -r requirements.txt

# Verificar instalação
python -c "import kivy, kivymd; print('OK')"
```

### Logs e Debugging
Os logs são salvos automaticamente:
- `app.log`: Logs da aplicação principal
- `app_launcher.log`: Logs do launcher
- `system_check.log`: Logs de verificação do sistema
- `startup.log`: Logs de inicialização

## 🔄 Atualizações e Manutenção

### Backup de Dados
```python
# Backup manual
from database_manager import get_database_manager
db = get_database_manager()
backup_path = db.backup_database()
print(f"Backup salvo em: {backup_path}")
```

### Limpeza de Logs
```bash
# Limpar logs antigos
rm *.log
```

### Atualização de Dependências
```bash
pip install --upgrade -r requirements.txt
```

## 🎯 Próximas Funcionalidades

- [ ] Integração com Firebase para sincronização
- [ ] Login com Google
- [ ] Relatórios em PDF
- [ ] Gráficos avançados
- [ ] Notificações push
- [ ] API REST para integração
- [ ] Modo offline completo

## 🤝 Suporte

Para suporte técnico:
1. Verifique os logs de erro
2. Execute `python check_memory.py` para diagnóstico
3. Use modo debug: `python safe_launcher.py --debug`
4. Consulte a documentação de troubleshooting

## 📄 Licença

Este projeto foi desenvolvido para uso interno e educacional.

---

**Sistema de Gestão v1.0** - Desenvolvido com foco em estabilidade e usabilidade
