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
        self.show_error_dialog("Em Desenvolvimento", "Opções de edição serão implementadas")

class GestaoApp(MDApp):
    """Aplicativo principal de gestão"""
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.title = "Sistema de Gestão"
        self.theme_cls.theme_style = "Light"
        self.theme_cls.primary_palette = "Blue"
        self.logger = logging.getLogger(__name__)
        
        # Configurar janela
        Window.size = (800, 600)
        Window.minimum_width = 400
        Window.minimum_height = 300
    
    def build(self):
        """Constrói aplicativo"""
        try:
            self.logger.info("🚀 Iniciando aplicativo de gestão...")
            
            # Criar gerenciador de telas
            self.screen_manager = MDScreenManager(transition=SlideTransition())
            
            # Adicionar telas
            self.screen_manager.add_widget(DashboardScreen())
            self.screen_manager.add_widget(MaterialScreen())
            
            # Layout principal com navegação
            main_layout = MDBoxLayout(orientation='vertical')
            
            # Barra superior
            toolbar = MDTopAppBar(
                title="Sistema de Gestão",
                elevation=2,
                left_action_items=[["menu", lambda x: self.open_nav_drawer()]],
                right_action_items=[["refresh", lambda x: self.refresh_current_screen()]]
            )
            main_layout.add_widget(toolbar)
            
            # Navegação inferior
            nav_layout = MDBoxLayout(
                orientation='horizontal',
                size_hint_y=None,
                height=dp(60),
                spacing=dp(5),
                padding=dp(5)
            )
            
            # Botões de navegação
            nav_buttons = [
                ("Dashboard", "dashboard", "view-dashboard"),
                ("Materiais", "material", "package-variant"),
            ]
            
            for text, screen_name, icon in nav_buttons:
                btn = MDIconButton(
                    icon=icon,
                    theme_icon_color="Custom",
                    icon_color=self.theme_cls.primary_color,
                    on_release=lambda x, name=screen_name: self.change_screen(name)
                )
                nav_layout.add_widget(btn)
            
            # Adicionar componentes ao layout principal
            main_layout.add_widget(self.screen_manager)
            main_layout.add_widget(nav_layout)
            
            self.logger.info("✅ Interface construída com sucesso")
            
            return main_layout
            
        except Exception as e:
            self.logger.error(f"❌ Erro ao construir aplicativo: {e}")
            raise
    
    def change_screen(self, screen_name: str):
        """Muda para tela especificada"""
        try:
            self.screen_manager.current = screen_name
            self.logger.debug(f"📱 Mudou para tela: {screen_name}")
        except Exception as e:
            self.logger.error(f"❌ Erro ao mudar tela: {e}")
    
    def open_nav_drawer(self):
        """Abre drawer de navegação"""
        pass
    
    def refresh_current_screen(self):
        """Atualiza tela atual"""
        try:
            current_screen = self.screen_manager.current_screen
            if hasattr(current_screen, 'carregar_materiais'):
                current_screen.carregar_materiais()
            elif hasattr(current_screen, 'update_stats'):
                current_screen.update_stats()
            
            self.logger.info("🔄 Tela atual atualizada")
            
        except Exception as e:
            self.logger.error(f"❌ Erro ao atualizar tela: {e}")
    
    def on_start(self):
        """Executado quando app inicia"""
        try:
            self.logger.info("🎉 Aplicativo iniciado com sucesso!")
            
            # Definir tela inicial
            self.screen_manager.current = 'dashboard'
            
            # Verificar integridade do banco
            db = get_database_manager()
            stats = db.obter_estatisticas_dashboard()
            self.logger.info(f"📊 Banco carregado: {stats.get('total_orcamentos', 0)} orçamentos")
            
        except Exception as e:
            self.logger.error(f"❌ Erro no startup: {e}")
    
    def on_stop(self):
        """Executado quando app para"""
        try:
            self.logger.info("⏹️  Encerrando aplicativo...")
            
            # Fechar conexões do banco
            close_database()
            
            self.logger.info("✅ Aplicativo encerrado com sucesso")
            
        except Exception as e:
            self.logger.error(f"❌ Erro ao encerrar: {e}")

def main():
    """Função principal"""
    try:
        # Configurar logging
        logging.info("🚀 Iniciando Sistema de Gestão Kivy...")
        
        # Verificar argumentos de linha de comando
        import argparse
        parser = argparse.ArgumentParser(description='Sistema de Gestão Kivy')
        parser.add_argument('--debug', action='store_true', help='Ativar modo debug')
        args = parser.parse_args()
        
        if args.debug:
            logging.getLogger().setLevel(logging.DEBUG)
            logging.info("🐛 Modo debug ativado")
        
        # Criar e executar aplicativo
        app = GestaoApp()
        app.run()
        
        return 0
        
    except KeyboardInterrupt:
        logging.info("⏹️  Interrompido pelo usuário")
        return 0
    except Exception as e:
        logging.error(f"❌ Erro crítico: {e}")
        return 1
    finally:
        # Limpeza final
        close_database()

if __name__ == "__main__":
    sys.exit(main())
