#!/usr/bin/env python3
"""
Sistema de Gestão Completo - Aplicativo Principal Kivy
Gerencia orçamentos, materiais, custos fixos e projetos
"""

import os
import sys
import logging
import threading
import asyncio
from datetime import datetime
from typing import Dict, List, Optional

# Configurar path para imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Imports Kivy
from kivy.app import App
from kivy.uix.screenmanager import ScreenManager, Screen, SlideTransition
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.textinput import TextInput
from kivy.uix.popup import Popup
from kivy.uix.scrollview import ScrollView
from kivy.clock import Clock
from kivy.metrics import dp
from kivy.core.window import Window

# KivyMD para Material Design
from kivymd.app import MDApp
from kivymd.uix.screen import MDScreen
from kivymd.uix.screenmanager import MDScreenManager
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.gridlayout import MDGridLayout
from kivymd.uix.card import MDCard
from kivymd.uix.label import MDLabel
from kivymd.uix.button import MDRaisedButton, MDIconButton, MDFlatButton
from kivymd.uix.textfield import MDTextField
from kivymd.uix.list import MDList, OneLineListItem, TwoLineListItem, ThreeLineListItem
from kivymd.uix.dialog import MDDialog
from kivymd.uix.toolbar import MDTopAppBar
from kivymd.uix.navigationdrawer import MDNavigationDrawer, MDNavigationDrawerMenu
from kivymd.uix.scrollview import MDScrollView
from kivymd.theming import ThemableBehavior

# Imports locais
from database_manager import get_database_manager, close_database

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('app.log'),
        logging.StreamHandler()
    ]
)

class BaseScreen(MDScreen):
    """Classe base para todas as telas"""
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.db = get_database_manager()
        self.logger = logging.getLogger(self.__class__.__name__)
        self.dialog = None
    
    def show_error_dialog(self, title: str, text: str):
        """Mostra dialog de erro"""
        if self.dialog:
            self.dialog.dismiss()
        
        self.dialog = MDDialog(
            title=title,
            text=text,
            buttons=[
                MDFlatButton(
                    text="OK",
                    on_release=lambda x: self.dialog.dismiss()
                )
            ]
        )
        self.dialog.open()
    
    def show_success_dialog(self, title: str, text: str):
        """Mostra dialog de sucesso"""
        if self.dialog:
            self.dialog.dismiss()
        
        self.dialog = MDDialog(
            title=title,
            text=text,
            buttons=[
                MDFlatButton(
                    text="OK",
                    on_release=lambda x: self.dialog.dismiss()
                )
            ]
        )
        self.dialog.open()
    
    def format_currency(self, value: float) -> str:
        """Formata valor como moeda brasileira"""
        return f"R$ {value:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

class DashboardScreen(BaseScreen):
    """Tela do Dashboard com métricas"""
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.name = 'dashboard'
        self.build_ui()
        
        # Atualizar dados a cada 30 segundos
        Clock.schedule_interval(self.update_stats, 30)
    
    def build_ui(self):
        """Constrói interface do dashboard"""
        main_layout = MDBoxLayout(orientation='vertical', spacing=dp(10), padding=dp(10))
        
        # Título
        title = MDLabel(
            text="Dashboard - Visão Geral",
            theme_text_color="Primary",
            size_hint_y=None,
            height=dp(50),
            font_style="H5"
        )
        main_layout.add_widget(title)
        
        # Cards de estatísticas
        stats_layout = MDGridLayout(cols=2, spacing=dp(10), size_hint_y=None)
        stats_layout.bind(minimum_height=stats_layout.setter('height'))
        
        # Cards serão criados dinamicamente
        self.stats_cards = {}
        
        # Card de Contratos Este Mês
        self.stats_cards['contratos_mes'] = self.create_stat_card(
            "Contratos Este Mês", "0", "contratos fechados"
        )
        stats_layout.add_widget(self.stats_cards['contratos_mes'])
        
        # Card de Total de Orçamentos
        self.stats_cards['total_orcamentos'] = self.create_stat_card(
            "Total de Orçamentos", "0", "orçamentos criados"
        )
        stats_layout.add_widget(self.stats_cards['total_orcamentos'])
        
        # Card de Custos Fixos
        self.stats_cards['custos_fixos'] = self.create_stat_card(
            "Custos Fixos Mensais", "R$ 0,00", "custos cadastrados"
        )
        stats_layout.add_widget(self.stats_cards['custos_fixos'])
        
        # Card de Valor Total
        self.stats_cards['valor_total'] = self.create_stat_card(
            "Valor Total Aprovado", "R$ 0,00", "contratos aprovados"
        )
        stats_layout.add_widget(self.stats_cards['valor_total'])
        
        main_layout.add_widget(stats_layout)
        
        # Botão de atualizar
        refresh_btn = MDRaisedButton(
            text="Atualizar Dados",
            size_hint_y=None,
            height=dp(40),
            on_release=self.update_stats
        )
        main_layout.add_widget(refresh_btn)
        
        # ScrollView para o conteúdo
        scroll = MDScrollView()
        scroll.add_widget(main_layout)
        
        self.add_widget(scroll)
        
        # Carregar dados iniciais
        Clock.schedule_once(lambda dt: self.update_stats(), 0.1)
    
    def create_stat_card(self, title: str, value: str, subtitle: str) -> MDCard:
        """Cria card de estatística"""
        card = MDCard(
            size_hint_y=None,
            height=dp(120),
            elevation=2,
            padding=dp(10)
        )
        
        layout = MDBoxLayout(orientation='vertical', spacing=dp(5))
        
        title_label = MDLabel(
            text=title,
            theme_text_color="Primary",
            font_style="Subtitle1",
            size_hint_y=None,
            height=dp(30)
        )
        layout.add_widget(title_label)
        
        value_label = MDLabel(
            text=value,
            theme_text_color="Primary",
            font_style="H4",
            size_hint_y=None,
            height=dp(50)
        )
        layout.add_widget(value_label)
        
        subtitle_label = MDLabel(
            text=subtitle,
            theme_text_color="Secondary",
            font_style="Caption",
            size_hint_y=None,
            height=dp(20)
        )
        layout.add_widget(subtitle_label)
        
        card.add_widget(layout)
        
        # Armazenar referências para atualização
        card.title_label = title_label
        card.value_label = value_label
        card.subtitle_label = subtitle_label
        
        return card
    
    def update_stats(self, *args):
        """Atualiza estatísticas do dashboard"""
        try:
            stats = self.db.obter_estatisticas_dashboard()
            
            # Atualizar cards
            self.stats_cards['contratos_mes'].value_label.text = str(stats.get('contratos_este_mes', 0))
            self.stats_cards['total_orcamentos'].value_label.text = str(stats.get('total_orcamentos', 0))
            self.stats_cards['custos_fixos'].value_label.text = self.format_currency(stats.get('total_custos_fixos', 0))
            self.stats_cards['valor_total'].value_label.text = self.format_currency(stats.get('valor_total_aprovados', 0))
            
            self.logger.info("✅ Estatísticas do dashboard atualizadas")
            
        except Exception as e:
            self.logger.error(f"❌ Erro ao atualizar estatísticas: {e}")
            self.show_error_dialog("Erro", f"Erro ao atualizar dados: {str(e)}")

class MaterialScreen(BaseScreen):
    """Tela de gerenciamento de materiais"""
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.name = 'material'
        self.build_ui()
    
    def build_ui(self):
        """Constrói interface de materiais"""
        main_layout = MDBoxLayout(orientation='vertical', spacing=dp(10), padding=dp(10))
        
        # Título
        title = MDLabel(
            text="Gerenciamento de Materiais",
            theme_text_color="Primary",
            size_hint_y=None,
            height=dp(50),
            font_style="H5"
        )
        main_layout.add_widget(title)
        
        # Formulário de adição
        form_card = MDCard(size_hint_y=None, height=dp(200), padding=dp(10))
        form_layout = MDBoxLayout(orientation='vertical', spacing=dp(10))
        
        form_title = MDLabel(
            text="Adicionar Novo Material",
            font_style="H6",
            size_hint_y=None,
            height=dp(30)
        )
        form_layout.add_widget(form_title)
        
        # Campos do formulário
        self.nome_field = MDTextField(
            hint_text="Nome do Material",
            size_hint_y=None,
            height=dp(40)
        )
        form_layout.add_widget(self.nome_field)
        
        self.valor_field = MDTextField(
            hint_text="Valor (R$)",
            input_filter='float',
            size_hint_y=None,
            height=dp(40)
        )
        form_layout.add_widget(self.valor_field)
        
        # Botões
        btn_layout = MDBoxLayout(orientation='horizontal', spacing=dp(10), size_hint_y=None, height=dp(40))
        
        add_btn = MDRaisedButton(
            text="Adicionar Material",
            on_release=self.adicionar_material
        )
        btn_layout.add_widget(add_btn)
        
        refresh_btn = MDFlatButton(
            text="Atualizar Lista",
            on_release=self.carregar_materiais
        )
        btn_layout.add_widget(refresh_btn)
        
        form_layout.add_widget(btn_layout)
        form_card.add_widget(form_layout)
        main_layout.add_widget(form_card)
        
        # Lista de materiais
        list_title = MDLabel(
            text="Materiais Cadastrados",
            font_style="H6",
            size_hint_y=None,
            height=dp(40)
        )
        main_layout.add_widget(list_title)
        
        # ScrollView para lista
        self.materials_list = MDList()
        scroll = MDScrollView()
        scroll.add_widget(self.materials_list)
        main_layout.add_widget(scroll)
        
        self.add_widget(main_layout)
        
        # Carregar materiais iniciais
        Clock.schedule_once(lambda dt: self.carregar_materiais(), 0.1)
    
    def adicionar_material(self, *args):
        """Adiciona novo material"""
        try:
            nome = self.nome_field.text.strip()
            valor_str = self.valor_field.text.strip()
            
            if not nome or not valor_str:
                self.show_error_dialog("Erro", "Preencha todos os campos")
                return
            
            try:
                valor = float(valor_str.replace(',', '.'))
                if valor <= 0:
                    raise ValueError("Valor deve ser positivo")
            except ValueError:
                self.show_error_dialog("Erro", "Valor inválido")
                return
            
            # Adicionar ao banco
            material_id = self.db.adicionar_material(nome, valor)
            
            # Limpar campos
            self.nome_field.text = ""
            self.valor_field.text = ""
            
            # Recarregar lista
            self.carregar_materiais()
            
            self.show_success_dialog("Sucesso", f"Material '{nome}' adicionado com sucesso!")
            
        except ValueError as e:
            self.show_error_dialog("Erro", str(e))
        except Exception as e:
            self.logger.error(f"❌ Erro ao adicionar material: {e}")
            self.show_error_dialog("Erro", f"Erro ao adicionar material: {str(e)}")
    
    def carregar_materiais(self, *args):
        """Carrega lista de materiais"""
        try:
            self.materials_list.clear_widgets()
            
            materiais = self.db.listar_materiais()
            
            if not materiais:
                item = OneLineListItem(text="Nenhum material cadastrado")
                self.materials_list.add_widget(item)
                return
            
            for material in materiais:
                valor_formatado = self.format_currency(material['valor'])
                
                item = ThreeLineListItem(
                    text=material['nome'],
                    secondary_text=f"Valor: {valor_formatado}",
                    tertiary_text=f"Cadastrado em: {material['created_at'][:10]}",
                    on_release=lambda x, mat_id=material['id']: self.show_material_options(mat_id)
                )
                
                self.materials_list.add_widget(item)
            
            self.logger.info(f"✅ {len(materiais)} materiais carregados")
            
        except Exception as e:
            self.logger.error(f"❌ Erro ao carregar materiais: {e}")
            self.show_error_dialog("Erro", f"Erro ao carregar materiais: {str(e)}")
    
    def show_material_options(self, material_id: int):
        """Mostra opções para material selecionado"""
        # Implementar dialog com opções de editar/remover
        pass

class CustoFixoScreen(BaseScreen):
    """Tela de gerenciamento de custos fixos"""
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.name = 'custo_fixo'
        self.build_ui()
    
    def build_ui(self):
        """Constrói interface de custos fixos"""
        main_layout = MDBoxLayout(orientation='vertical', spacing=dp(10), padding=dp(10))
        
        # Título
        title = MDLabel(
            text="Custos Fixos Mensais",
            theme_text_color="Primary",
            size_hint_y=None,
            height=dp(50),
            font_style="H5"
        )
        main_layout.add_widget(title)
        
        # Cards de cálculos
        calc_layout = MDGridLayout(cols=2, spacing=dp(10), size_hint_y=None, height=dp(120))
        
        self.total_card = self.create_calc_card("Total Mensal", "R$ 0,00")
        calc_layout.add_widget(self.total_card)
        
        self.diario_card = self.create_calc_card("Custo Diário", "R$ 0,00")
        calc_layout.add_widget(self.diario_card)
        
        main_layout.add_widget(calc_layout)
        
        # Configurações de cálculo
        config_card = MDCard(size_hint_y=None, height=dp(120), padding=dp(10))
        config_layout = MDBoxLayout(orientation='horizontal', spacing=dp(10))
        
        dias_layout = MDBoxLayout(orientation='vertical')
        dias_label = MDLabel(text="Dias Trabalhados:", size_hint_y=None, height=dp(30))
        self.dias_field = MDTextField(
            text="30",
            input_filter='int',
            size_hint_y=None,
            height=dp(40),
            on_text=self.calcular_custos
        )
        dias_layout.add_widget(dias_label)
        dias_layout.add_widget(self.dias_field)
        config_layout.add_widget(dias_layout)
        
        equipes_layout = MDBoxLayout(orientation='vertical')
        equipes_label = MDLabel(text="Número de Equipes:", size_hint_y=None, height=dp(30))
        self.equipes_field = MDTextField(
            text="1",
            input_filter='int',
            size_hint_y=None,
            height=dp(40),
            on_text=self.calcular_custos
        )
        equipes_layout.add_widget(equipes_label)
        equipes_layout.add_widget(self.equipes_field)
        config_layout.add_widget(equipes_layout)
        
        config_card.add_widget(config_layout)
        main_layout.add_widget(config_card)
        
        # Formulário de adição
        form_card = MDCard(size_hint_y=None, height=dp(160), padding=dp(10))
        form_layout = MDBoxLayout(orientation='vertical', spacing=dp(10))
        
        form_title = MDLabel(
            text="Adicionar Custo Fixo",
            font_style="H6",
            size_hint_y=None,
            height=dp(30)
        )
        form_layout.add_widget(form_title)
        
        self.nome_custo_field = MDTextField(
            hint_text="Nome do Custo (ex: Aluguel, Energia)",
            size_hint_y=None,
            height=dp(40)
        )
        form_layout.add_widget(self.nome_custo_field)
        
        self.valor_custo_field = MDTextField(
            hint_text="Valor Mensal (R$)",
            input_filter='float',
            size_hint_y=None,
            height=dp(40)
        )
        form_layout.add_widget(self.valor_custo_field)
        
        add_custo_btn = MDRaisedButton(
            text="Adicionar Custo",
            size_hint_y=None,
            height=dp(40),
            on_release=self.adicionar_custo_fixo
        )
        form_layout.add_widget(add_custo_btn)
        
        form_card.add_widget(form_layout)
        main_layout.add_widget(form_card)
        
        # Lista de custos
        list_title = MDLabel(
            text="Custos Fixos Cadastrados",
            font_style="H6",
            size_hint_y=None,
            height=dp(40)
        )
        main_layout.add_widget(list_title)
        
        self.custos_list = MDList()
        scroll = MDScrollView()
        scroll.add_widget(self.custos_list)
        main_layout.add_widget(scroll)
        
        self.add_widget(main_layout)
        
        # Carregar dados iniciais
        Clock.schedule_once(lambda dt: self.carregar_custos_fixos(), 0.1)
    
    def create_calc_card(self, title: str, value: str) -> MDCard:
        """Cria card de cálculo"""
        card = MDCard(size_hint_y=None, height=dp(120), padding=dp(10))
        layout = MDBoxLayout(orientation='vertical', spacing=dp(5))
        
        title_label = MDLabel(
            text=title,
            font_style="Subtitle1",
            size_hint_y=None,
            height=dp(30)
        )
        layout.add_widget(title_label)
        
        value_label = MDLabel(
            text=value,
            font_style="H5",
            theme_text_color="Primary",
            size_hint_y=None,
            height=dp(50)
        )
        layout.add_widget(value_label)
        
        card.add_widget(layout)
        card.value_label = value_label
        
        return card
    
    def adicionar_custo_fixo(self, *args):
        """Adiciona novo custo fixo"""
        try:
            nome = self.nome_custo_field.text.strip()
            valor_str = self.valor_custo_field.text.strip()
            
            if not nome or not valor_str:
                self.show_error_dialog("Erro", "Preencha todos os campos")
                return
            
            try:
                valor = float(valor_str.replace(',', '.'))
                if valor <= 0:
                    raise ValueError("Valor deve ser positivo")
            except ValueError:
                self.show_error_dialog("Erro", "Valor inválido")
                return
            
            # Adicionar ao banco
            custo_id = self.db.adicionar_custo_fixo(nome, valor)
            
            # Limpar campos
            self.nome_custo_field.text = ""
            self.valor_custo_field.text = ""
            
            # Recarregar lista e recalcular
            self.carregar_custos_fixos()
            self.calcular_custos()
            
            self.show_success_dialog("Sucesso", f"Custo fixo '{nome}' adicionado com sucesso!")
            
        except ValueError as e:
            self.show_error_dialog("Erro", str(e))
        except Exception as e:
            self.logger.error(f"❌ Erro ao adicionar custo fixo: {e}")
            self.show_error_dialog("Erro", f"Erro ao adicionar custo fixo: {str(e)}")
    
    def carregar_custos_fixos(self, *args):
        """Carrega lista de custos fixos"""
        try:
            self.custos_list.clear_widgets()
            
            custos = self.db.listar_custos_fixos()
            
            if not custos:
                item = OneLineListItem(text="Nenhum custo fixo cadastrado")
                self.custos_list.add_widget(item)
                return
            
            for custo in custos:
                valor_formatado = self.format_currency(custo['valor'])
                
                item = TwoLineListItem(
                    text=custo['nome'],
                    secondary_text=f"Valor: {valor_formatado}",
                    on_release=lambda x, custo_id=custo['id']: self.show_custo_options(custo_id)
                )
                
                self.custos_list.add_widget(item)
            
            self.logger.info(f"✅ {len(custos)} custos fixos carregados")
            
        except Exception as e:
            self.logger.error(f"❌ Erro ao carregar custos fixos: {e}")
            self.show_error_dialog("Erro", f"Erro ao carregar custos fixos: {str(e)}")
    
    def calcular_custos(self, *args):
        """Calcula custos diários e por equipe"""
        try:
            total_custos = self.db.calcular_total_custos_fixos()
            dias = int(self.dias_field.text) if self.dias_field.text else 30
            equipes = int(self.equipes_field.text) if self.equipes_field.text else 1
            
            custo_diario = total_custos / dias if dias > 0 else 0
            custo_por_equipe = custo_diario / equipes if equipes > 0 else 0
            
            # Atualizar cards
            self.total_card.value_label.text = self.format_currency(total_custos)
            self.diario_card.value_label.text = self.format_currency(custo_diario)
            
        except Exception as e:
            self.logger.error(f"❌ Erro ao calcular custos: {e}")
    
    def show_custo_options(self, custo_id: int):
        """Mostra opções para custo selecionado"""
        # Implementar dialog com opções de editar/remover
        pass

class NovoOrcamentoScreen(BaseScreen):
    """Tela de criação de novos orçamentos"""
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.name = 'novo_orcamento'
        self.materiais_selecionados = []
        self.build_ui()
    
    def build_ui(self):
        """Constrói interface de novo orçamento"""
        main_layout = MDBoxLayout(orientation='vertical', spacing=dp(10), padding=dp(10))
        
        # Título
        title = MDLabel(
            text="Novo Orçamento",
            theme_text_color="Primary",
            size_hint_y=None,
            height=dp(50),
            font_style="H5"
        )
        main_layout.add_widget(title)
        
        # Informações do cliente
        cliente_card = MDCard(size_hint_y=None, height=dp(100), padding=dp(10))
        cliente_layout = MDBoxLayout(orientation='vertical', spacing=dp(10))
        
        cliente_title = MDLabel(text="Informações do Cliente", font_style="H6", size_hint_y=None, height=dp(30))
        cliente_layout.add_widget(cliente_title)
        
        self.cliente_field = MDTextField(
            hint_text="Nome do Cliente (Opcional)",
            size_hint_y=None,
            height=dp(40)
        )
        cliente_layout.add_widget(self.cliente_field)
        
        cliente_card.add_widget(cliente_layout)
        main_layout.add_widget(cliente_card)
        
        # Seleção de materiais
        materiais_card = MDCard(size_hint_y=None, height=dp(200), padding=dp(10))
        materiais_layout = MDBoxLayout(orientation='vertical', spacing=dp(10))
        
        materiais_title = MDLabel(text="Materiais do Orçamento", font_style="H6", size_hint_y=None, height=dp(30))
        materiais_layout.add_widget(materiais_title)
        
        # Botão para adicionar materiais
        add_material_btn = MDRaisedButton(
            text="Adicionar Materiais",
            size_hint_y=None,
            height=dp(40),
            on_release=self.show_material_selector
        )
        materiais_layout.add_widget(add_material_btn)
        
        # Lista de materiais selecionados
        self.materiais_list = MDList()
        materiais_scroll = MDScrollView(size_hint_y=None, height=dp(120))
        materiais_scroll.add_widget(self.materiais_list)
        materiais_layout.add_widget(materiais_scroll)
        
        materiais_card.add_widget(materiais_layout)
        main_layout.add_widget(materiais_card)
        
        # Configurações do orçamento
        config_card = MDCard(size_hint_y=None, height=dp(200), padding=dp(10))
        config_layout = MDBoxLayout(orientation='vertical', spacing=dp(10))
        
        config_title = MDLabel(text="Configurações", font_style="H6", size_hint_y=None, height=dp(30))
        config_layout.add_widget(config_title)
        
        # Campos de configuração em grid
        config_grid = MDGridLayout(cols=2, spacing=dp(10), size_hint_y=None, height=dp(160))
        
        self.dias_field = MDTextField(hint_text="Dias Trabalhados", text="1", input_filter='int')
        config_grid.add_widget(self.dias_field)
        
        self.lucro_field = MDTextField(hint_text="Lucro Líquido (R$)", text="0", input_filter='float')
        config_grid.add_widget(self.lucro_field)
        
        self.minimo_field = MDTextField(hint_text="Orçamento Mínimo (R$)", text="0", input_filter='float')
        config_grid.add_widget(self.minimo_field)
        
        self.acrescimo_field = MDTextField(hint_text="Acréscimo (%)", text="10", input_filter='float')
        config_grid.add_widget(self.acrescimo_field)
        
        config_layout.add_widget(config_grid)
        config_card.add_widget(config_layout)
        main_layout.add_widget(config_card)
        
        # Resumo do orçamento
        resumo_card = MDCard(size_hint_y=None, height=dp(150), padding=dp(10))
        resumo_layout = MDBoxLayout(orientation='vertical', spacing=dp(5))
        
        resumo_title = MDLabel(text="Resumo do Orçamento", font_style="H6", size_hint_y=None, height=dp(30))
        resumo_layout.add_widget(resumo_title)
        
        self.valor_materiais_label = MDLabel(text="Total Materiais: R$ 0,00", size_hint_y=None, height=dp(25))
        resumo_layout.add_widget(self.valor_materiais_label)
        
        self.valor_final_label = MDLabel(
            text="VALOR FINAL: R$ 0,00",
            font_style="H6",
            theme_text_color="Primary",
            size_hint_y=None,
            height=dp(35)
        )
        resumo_layout.add_widget(self.valor_final_label)
        
        # Botão
