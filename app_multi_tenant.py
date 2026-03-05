"""
Help Desk SaaS - Sistema Multi-Tenant
Arquitetura: Banco de dados isolado por tenant (SQLite)

ROTEAMENTO:
- master.helpdeskhub.com ou localhost -> Painel Master (gestão de tenants)
- empresa1.helpdeskhub.com -> Sistema da empresa 1
- empresa2.helpdeskhub.com -> Sistema da empresa 2
"""

import os
import sys
import socket
from datetime import datetime, timedelta
import hashlib
import uuid
import json
import threading
from flask import Flask, render_template_string, request, redirect, url_for, session, flash, jsonify, send_file, g
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
import pytz
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import base64
from io import BytesIO
import csv
import io
import zipfile
import sqlite3
from sqlalchemy import create_engine, Column, Integer, String, Boolean, DateTime, Text, ForeignKey
from sqlalchemy.orm import sessionmaker, scoped_session, declarative_base

# Importar módulo multi-tenant
from multi_tenant import (
    Tenant, master_db, init_master_db, get_current_tenant, 
    tenant_required, register_tenant_routes, DATABASES_DIR,
    create_tenant_engine
)
from multi_tenant.master_routes import register_master_routes

# ==================== CONFIGURAÇÃO DO APP ====================

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'helpdesk_secured_2024')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = 'static/uploads'
app.config['PERMANENT_SESSION_LIFETIME'] = 3600
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024

# Inicializar banco master
init_master_db(app)

# Criar diretórios necessários
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs(os.path.join(app.config['UPLOAD_FOLDER'], 'documents'), exist_ok=True)

# ==================== VARIÁVEIS GLOBAIS ====================

brasilia_tz = pytz.timezone('America/Sao_Paulo')

def now_brasilia():
    return datetime.now(brasilia_tz)

# Thread-local storage para sessões de tenant
tenant_db_context = threading.local()

# ==================== MODELOS ====================

# Os modelos serão definidos dinamicamente baseados no tenant
# Para isso, criamos uma factory de modelos

def get_tenant_db_models(tenant_id):
    """
    Obtém ou cria modelos SQLAlchemy para o tenant
    """
    if not hasattr(tenant_db_context, 'models'):
        tenant_db_context.models = {}
    
    if tenant_id not in tenant_db_context.models:
        tenant = Tenant.query.get(tenant_id)
        if not tenant:
            return None
        
        # Criar engine para este tenant
        engine = create_tenant_engine(tenant.banco_path)
        
        # Criar sessão
        Session = scoped_session(sessionmaker(bind=engine))
        
        # Criar base para modelos
        Base = declarative_base()
        
        # Definir modelos
        models = define_tenant_models(Base, engine, Session)
        
        # Criar todas as tabelas se não existirem
        Base.metadata.create_all(engine)
        
        tenant_db_context.models[tenant_id] = {
            'engine': engine,
            'session': Session,
            'models': models,
            'base': Base
        }
    
    return tenant_db_context.models[tenant_id]


def define_tenant_models(Base, engine, Session):
    """Define todos os modelos do sistema"""
    
    class User(Base):
        __tablename__ = 'user'
        id = Column(Integer, primary_key=True)
        name = Column(String(120))
        department = Column(String(120))
        username = Column(String(80), unique=True)
        password_hash = Column(String(200))
        role = Column(String(20))
        region = Column(String(50))
        online = Column(Boolean, default=False)
        pause_start = Column(DateTime, nullable=True)
        total_attended = Column(Integer, default=0)
        full_name = Column(String(200))
        first_name = Column(String(100))
        last_name = Column(String(100))
        position = Column(String(100))
        company = Column(String(100))
        third_party_company = Column(String(100))
        department_extended = Column(String(100))
        needs_password_reset = Column(Boolean, default=False)
        blocked = Column(Boolean, default=False)
        active = Column(Boolean, default=True)
        vip = Column(Boolean, default=False)
        manager = Column(Boolean, default=False)
        senior_manager = Column(Boolean, default=False)
        registration = Column(String(50))
        email = Column(String(120))
        date_format = Column(String(20), default='dd/MM/aaaa')
        business_phone = Column(String(20))
        cell_phone = Column(String(20))
        group_id = Column(Integer, ForeignKey('support_group.id'), nullable=True)
        manager_id = Column(Integer, ForeignKey('user.id'), nullable=True)
        senior_manager_id = Column(Integer, ForeignKey('user.id'), nullable=True)
        cab_access = Column(Boolean, default=False)

    class Config(Base):
        __tablename__ = 'config'
        id = Column(Integer, primary_key=True)
        company_name = Column(String(100), default='Help Desk')
        logo_path = Column(String(200), default='')
        primary_color = Column(String(7), default="#0467FA")
        secondary_color = Column(String(7), default='#2196F3')
        waiting_color = Column(String(7), default="#FD1C1C")
        progress_color = Column(String(7), default='#8BC34A')

    class SupportGroup(Base):
        __tablename__ = 'support_group'
        id = Column(Integer, primary_key=True)
        name = Column(String(100), unique=True)
        description = Column(Text)
        created_at = Column(DateTime, default=datetime.utcnow)

    class Category(Base):
        __tablename__ = 'category'
        id = Column(Integer, primary_key=True)
        area = Column(String(50))
        name = Column(String(120))

    class Session(Base):
        __tablename__ = 'session'
        id = Column(Integer, primary_key=True)
        user_id = Column(Integer)
        category = Column(String(120))
        region = Column(String(50))
        status = Column(String(30), default='waiting')
        created_at = Column(DateTime, default=datetime.utcnow)
        assigned_at = Column(DateTime, nullable=True)
        finished_at = Column(DateTime, nullable=True)
        analyst_id = Column(Integer, nullable=True)

    class Message(Base):
        __tablename__ = 'message'
        id = Column(Integer, primary_key=True)
        session_id = Column(Integer)
        sender = Column(String(20))
        content = Column(Text)
        created_at = Column(DateTime, default=datetime.utcnow)

    class Document(Base):
        __tablename__ = 'document'
        id = Column(Integer, primary_key=True)
        session_id = Column(Integer)
        user_id = Column(Integer)
        filename = Column(String(255))
        original_filename = Column(String(255))
        file_type = Column(String(50))
        uploaded_at = Column(DateTime, default=datetime.utcnow)

    class TicketCategory(Base):
        __tablename__ = 'ticket_category'
        id = Column(Integer, primary_key=True)
        name = Column(String(100))
        description = Column(Text)
        group_id = Column(Integer, ForeignKey('support_group.id'))
        sla_hours = Column(Integer, default=24)
        requires_approval = Column(Boolean, default=False)

    class SubCategory(Base):
        __tablename__ = 'sub_category'
        id = Column(Integer, primary_key=True)
        name = Column(String(100))
        description = Column(Text)
        category_id = Column(Integer, ForeignKey('ticket_category.id'))
        requires_approval = Column(Boolean, default=False)
        created_at = Column(DateTime, default=datetime.utcnow)

    class Ticket(Base):
        __tablename__ = 'ticket'
        id = Column(Integer, primary_key=True)
        number = Column(String(20), unique=True)
        type = Column(String(20))
        title = Column(String(200))
        description = Column(Text)
        priority = Column(String(20), default='Medium')
        status = Column(String(30), default='open')
        created_by = Column(Integer, ForeignKey('user.id'))
        assigned_to = Column(Integer, ForeignKey('user.id'), nullable=True)
        assigned_group = Column(Integer, ForeignKey('support_group.id'), nullable=True)
        category_id = Column(Integer, ForeignKey('ticket_category.id'))
        subcategory_id = Column(Integer, ForeignKey('sub_category.id'), nullable=True)
        created_at = Column(DateTime, default=datetime.utcnow)
        updated_at = Column(DateTime, default=datetime.utcnow)
        assigned_at = Column(DateTime, nullable=True)
        resolved_at = Column(DateTime, nullable=True)
        closed_at = Column(DateTime, nullable=True)
        sla_due = Column(DateTime, nullable=True)
        requires_approval = Column(Boolean, default=False)
        approved_by = Column(Integer, ForeignKey('user.id'), nullable=True)
        approved_at = Column(DateTime, nullable=True)
        pending_reason = Column(Text, nullable=True)
        current_owner = Column(Integer, ForeignKey('user.id'), nullable=True)
        resolution_notes = Column(Text, nullable=True)
        user_accepted = Column(Boolean, nullable=True)
        user_rejection_reason = Column(Text, nullable=True)

    class TicketComment(Base):
        __tablename__ = 'ticket_comment'
        id = Column(Integer, primary_key=True)
        ticket_id = Column(Integer, ForeignKey('ticket.id'))
        user_id = Column(Integer, ForeignKey('user.id'))
        content = Column(Text)
        is_internal = Column(Boolean, default=False)
        created_at = Column(DateTime, default=datetime.utcnow)

    class RoutingRule(Base):
        __tablename__ = 'routing_rule'
        id = Column(Integer, primary_key=True)
        name = Column(String(100))
        condition_type = Column(String(50))
        condition_value = Column(String(200))
        target_group_id = Column(Integer, ForeignKey('support_group.id'))
        priority = Column(Integer, default=1)
        active = Column(Boolean, default=True)

    class ChangeRequest(Base):
        __tablename__ = 'change_request'
        id = Column(Integer, primary_key=True)
        number = Column(String(20), unique=True)
        title = Column(String(200))
        description = Column(Text)
        priority = Column(String(20), default='Medium')
        impact = Column(String(20), default='Medium')
        systems_affected = Column(Text)
        implementation_date = Column(DateTime)
        start_date = Column(DateTime)
        end_date = Column(DateTime)
        meeting_date = Column(DateTime)
        status = Column(String(30), default='draft')
        created_by = Column(Integer, ForeignKey('user.id'))
        created_at = Column(DateTime, default=datetime.utcnow)
        updated_at = Column(DateTime, default=datetime.utcnow)
        approved_by = Column(Integer, ForeignKey('user.id'), nullable=True)
        approved_at = Column(DateTime, nullable=True)
        rejection_reason = Column(Text, nullable=True)

    class CABComment(Base):
        __tablename__ = 'cab_comment'
        id = Column(Integer, primary_key=True)
        change_request_id = Column(Integer, ForeignKey('change_request.id'))
        user_id = Column(Integer, ForeignKey('user.id'))
        content = Column(Text)
        risk_assessment = Column(Text)
        created_at = Column(DateTime, default=datetime.utcnow)

    class ChangeLog(Base):
        __tablename__ = 'change_log'
        id = Column(Integer, primary_key=True)
        change_request_id = Column(Integer, ForeignKey('change_request.id'))
        user_id = Column(Integer, ForeignKey('user.id'))
        action = Column(String(50))
        details = Column(Text)
        created_at = Column(DateTime, default=datetime.utcnow)

    class CABDocument(Base):
        __tablename__ = 'cab_document'
        id = Column(Integer, primary_key=True)
        change_request_id = Column(Integer, ForeignKey('change_request.id'))
        user_id = Column(Integer, ForeignKey('user.id'))
        filename = Column(String(255))
        original_filename = Column(String(255))
        file_type = Column(String(50))
        uploaded_at = Column(DateTime, default=datetime.utcnow)

    return {
        'User': User,
        'Config': Config,
        'SupportGroup': SupportGroup,
        'Category': Category,
        'Session': Session,
        'Message': Message,
        'Document': Document,
        'TicketCategory': TicketCategory,
        'SubCategory': SubCategory,
        'Ticket': Ticket,
        'TicketComment': TicketComment,
        'RoutingRule': RoutingRule,
        'ChangeRequest': ChangeRequest,
        'CABComment': CABComment,
        'ChangeLog': ChangeLog,
        'CABDocument': CABDocument
    }


# ==================== MIDDLEWARE ====================

@app.before_request
def before_request():
    """
    Middleware executado antes de cada requisição
    Detecta o tenant e configura o contexto apropriado
    """
    # Detectar tenant baseado no host
    tenant = get_current_tenant()
    
    # Armazenar no contexto global do Flask
    g.current_tenant = tenant
    g.is_master = tenant is None
    
    # Se for tenant, configurar sessão do banco
    if tenant:
        # Verificar se tenant está ativo e não expirado
        if not tenant.ativo:
            if request.endpoint not in ['tenant_inactive', 'static']:
                return redirect(url_for('tenant_inactive'))
        
        if tenant.data_expiracao and datetime.utcnow() > tenant.data_expiracao:
            if request.endpoint not in ['tenant_expired', 'static']:
                return redirect(url_for('tenant_expired'))
        
        # Configurar sessão do banco para este tenant
        db_context = get_tenant_db_models(tenant.id)
        if db_context:
            g.tenant_session = db_context['session']
            g.tenant_models = db_context['models']
            
            # Configurar db para usar a sessão do tenant
            # Isso permite que as queries usem o banco correto
            db.session.remove()
            db.session = db_context['session']


@app.teardown_request
def teardown_request(exception=None):
    """Limpa recursos após cada requisição"""
    if hasattr(g, 'tenant_session'):
        try:
            g.tenant_session.remove()
        except:
            pass


# ==================== FUNÇÕES AUXILIARES ====================

def current_user():
    """Obtém usuário atual da sessão"""
    uid = session.get('user_id')
    if not uid:
        return None
    
    # Usar sessão do tenant se disponível
    if hasattr(g, 'tenant_models') and hasattr(g, 'tenant_session'):
        User = g.tenant_models.get('User')
        if User:
            return g.tenant_session.query(User).get(uid)
    
    return None


def get_config():
    """Obtém configuração do sistema"""
    if hasattr(g, 'tenant_session') and hasattr(g, 'tenant_models'):
        Config = g.tenant_models.get('Config')
        if Config:
            return g.tenant_session.query(Config).first()
    return None


# ==================== ROTAS ====================

# Registrar rotas do painel master
register_master_routes(app)

# Registrar rotas utilitárias de tenant
register_tenant_routes(app)


@app.route('/')
def index():
    """Rota principal - redireciona baseado no tenant"""
    tenant = g.current_tenant
    
    if tenant is None:
        # Acesso ao domínio master
        if session.get('master_authenticated'):
            return redirect(url_for('master_dashboard'))
        return redirect(url_for('master_login'))
    
    # Acesso de tenant
    u = current_user()
    if u:
        if u.role == 'admin':
            return redirect(url_for('admin_panel'))
        if u.role == 'analyst':
            return redirect(url_for('analyst_panel'))
        if u.manager or u.senior_manager:
            return redirect(url_for('manager_dashboard'))
        return redirect(url_for('user_dashboard'))
    
    return redirect(url_for('login'))


@app.route('/login', methods=['GET', 'POST'])
def login():
    """Login de usuários do tenant"""
    tenant = g.current_tenant
    
    if not tenant:
        return redirect(url_for('master_login'))
    
    config = get_config()
    
    # Se já estiver logado, redireciona
    u = current_user()
    if u:
        if u.role == 'admin':
            return redirect(url_for('admin_panel'))
        elif u.role == 'analyst':
            return redirect(url_for('analyst_panel'))
        elif u.manager or u.senior_manager:
            return redirect(url_for('manager_dashboard'))
        else:
            return redirect(url_for('user_dashboard'))

    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '').strip()

        # Buscar usuário no banco do tenant
        if hasattr(g, 'tenant_session'):
            u = g.tenant_session.query(User).filter_by(username=username).first()
        else:
            u = None

        if u:
            # Verificar senha
            if check_password_hash(u.password_hash, password):
                session['user_id'] = u.id
                session['tenant_id'] = tenant.id
                session.permanent = True
                flash(f'Bem-vindo, {u.name}!', 'success')

                # Redirecionar baseado no role
                if u.role == 'admin':
                    return redirect(url_for('admin_panel'))
                elif u.role == 'analyst':
                    return redirect(url_for('analyst_panel'))
                elif u.manager or u.senior_manager:
                    return redirect(url_for('manager_dashboard'))
                else:
                    return redirect(url_for('user_dashboard'))
            else:
                flash('Senha incorreta!', 'error')
        else:
            flash('Usuário não encontrado!', 'error')

    # Template de login simplificado
    config_name = tenant.nome if tenant else 'Help Desk'
    
    html = '''
    <!DOCTYPE html>
    <html lang="pt-BR">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>''' + config_name + ''' - Login</title>
        <style>
            * { margin: 0; padding: 0; box-sizing: border-box; font-family: 'Segoe UI', sans-serif; }
            body { 
                background: linear-gradient(135deg, #0c0c0c 0%, #1a1a2e 50%, #16213e 100%); 
                min-height: 100vh; 
                display: flex; 
                align-items: center; 
                justify-content: center;
            }
            .login-container { 
                max-width: 400px; 
                width: 100%; 
                padding: 20px;
            }
            .login-card { 
                background: rgba(255, 255, 255, 0.05); 
                backdrop-filter: blur(20px); 
                border: 1px solid rgba(255, 255, 255, 0.1); 
                border-radius: 20px; 
                padding: 40px 30px;
            }
            .logo-section { text-align: center; margin-bottom: 30px; }
            .logo-section h1 { 
                color: white; 
                font-size: 28px; 
                margin-bottom: 5px;
            }
            .logo-section p { color: rgba(255, 255, 255, 0.7); font-size: 14px; }
            .form-group { margin-bottom: 20px; }
            .form-group input { 
                width: 100%; 
                padding: 15px 20px; 
                background: rgba(255, 255, 255, 0.1); 
                border: 1px solid rgba(255, 255, 255, 0.2); 
                border-radius: 12px; 
                color: white; 
                font-size: 16px;
            }
            .login-btn { 
                width: 100%; 
                padding: 15px; 
                background: linear-gradient(45deg, #0467FA, #2196F3); 
                border: none; 
                border-radius: 12px; 
                color: white; 
                font-size: 16px; 
                font-weight: 600; 
                cursor: pointer;
            }
            .alert { 
                padding: 10px; 
                border-radius: 8px; 
                margin-bottom: 20px;
                text-align: center;
            }
            .alert-error { background: rgba(244, 67, 54, 0.2); color: #ff6b6b; }
            .alert-success { background: rgba(76, 175, 80, 0.2); color: #4CAF50; }
        </style>
    </head>
    <body>
        <div class="login-container">
            <div class="login-card">
                <div class="logo-section">
                    <h1>⚡''' + config_name + '''</h1>
                    <p>Intelligent Support System</p>
                </div>
                {% with messages = get_flashed_messages(with_categories=true) %}
                    {% if messages %}
                        {% for category, message in messages %}
                            <div class="alert alert-{{ category }}">{{ message }}</div>
                        {% endfor %}
                    {% endif %}
                {% endwith %}
                <form method="post">
                    <div class="form-group">
                        <input type="text" name="username" placeholder="👤 Usuário" required>
                    </div>
                    <div class="form-group">
                        <input type="password" name="password" placeholder="🔒 Senha" required>
                    </div>
                    <button type="submit" class="login-btn">🚀 ACESSAR SISTEMA</button>
                </form>
            </div>
        </div>
    </body>
    </html>
    '''
    
    return render_template_string(html)


@app.route('/logout')
def logout():
    """Logout do usuário"""
    session.clear()
    flash('Você saiu do sistema.', 'info')
    return redirect(url_for('login'))


# ==================== ROTAS DE EXEMPLO (Funcionais) ====================

@app.route('/admin')
def admin_panel():
    """Painel do administrador do tenant"""
    tenant = g.current_tenant
    u = current_user()
    
    if not u or u.role != 'admin':
        flash('Acesso negado!', 'error')
        return redirect(url_for('login'))
    
    # Contagens básicas
    try:
        User = g.tenant_models.get('User')
        Ticket = g.tenant_models.get('Ticket')
        Config = g.tenant_models.get('Config')
        
        total_users = g.tenant_session.query(User).count() if User else 0
        total_tickets = g.tenant_session.query(Ticket).count() if Ticket else 0
        config = g.tenant_session.query(Config).first() if Config else None
        company_name = config.company_name if config else tenant.nome
    except:
        total_users = 0
        total_tickets = 0
        company_name = tenant.nome
    
    html = '''
    <!DOCTYPE html>
    <html lang="pt-BR">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Admin - ''' + company_name + '''</title>
        <style>
            * { margin: 0; padding: 0; box-sizing: border-box; font-family: 'Segoe UI', sans-serif; }
            body { 
                background: linear-gradient(135deg, #0c0c0c 0%, #1a1a2e 50%, #16213e 100%); 
                min-height: 100vh; 
                color: white;
            }
            .header {
                background: rgba(255, 255, 255, 0.05);
                padding: 20px 40px;
                display: flex;
                justify-content: space-between;
                align-items: center;
                border-bottom: 1px solid rgba(255, 255, 255, 0.1);
            }
            .header h1 { font-size: 24px; }
            .btn {
                padding: 10px 20px;
                border-radius: 8px;
                text-decoration: none;
                font-size: 14px;
                font-weight: 600;
                cursor: pointer;
                border: none;
                margin-left: 10px;
            }
            .btn-primary { background: linear-gradient(45deg, #0467FA, #2196F3); color: white; }
            .btn-danger { background: linear-gradient(45deg, #f44336, #E91E63); color: white; }
            .main-container { max-width: 1400px; margin: 0 auto; padding: 40px; }
            .stats-grid {
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
                gap: 20px;
                margin-bottom: 40px;
            }
            .stat-card {
                background: rgba(255, 255, 255, 0.05);
                border: 1px solid rgba(255, 255, 255, 0.1);
                border-radius: 20px;
                padding: 30px;
                text-align: center;
            }
            .stat-number { font-size: 48px; font-weight: 700; margin: 10px 0; }
            .stat-label { color: rgba(255, 255, 255, 0.7); font-size: 14px; }
            .info-box {
                background: rgba(255, 255, 255, 0.05);
                border: 1px solid rgba(255, 255, 255, 0.1);
                border-radius: 15px;
                padding: 30px;
                margin-top: 30px;
            }
            .alert {
                background: rgba(76, 175, 80, 0.2);
                border: 1px solid #4CAF50;
                padding: 15px;
                border-radius: 10px;
                margin-bottom: 20px;
            }
        </style>
    </head>
    <body>
        <div class="header">
            <h1>⚡ ''' + company_name + ''' - Admin</h1>
            <div>
                <a href="/admin" class="btn btn-primary">📊 Dashboard</a>
                <a href="/logout" class="btn btn-danger">🚪 Sair</a>
            </div>
        </div>
        <div class="main-container">
            <div class="alert">
                ✅ Sistema Multi-Tenant Funcionando!
            </div>
            
            <div class="stats-grid">
                <div class="stat-card">
                    <div style="font-size: 40px;">🏢</div>
                    <div class="stat-number">''' + str(total_users) + '''</div>
                    <div class="stat-label">Total de Usuários</div>
                </div>
                <div class="stat-card">
                    <div style="font-size: 40px;">🎫</div>
                    <div class="stat-number">''' + str(total_tickets) + '''</div>
                    <div class="stat-label">Total de Tickets</div>
                </div>
                <div class="stat-card">
                    <div style="font-size: 40px;">👤</div>
                    <div class="stat-number">''' + (u.name if u else 'N/A') + '''</div>
                    <div class="stat-label">Usuário Logado</div>
                </div>
            </div>
            
            <div class="info-box">
                <h2>📋 Informações do Tenant</h2>
                <p style="margin-top: 15px;"><strong>Empresa:</strong> ''' + tenant.nome + '''</p>
                <p><strong>Subdomínio:</strong> ''' + tenant.subdominio + '''</p>
                <p><strong>Plano:</strong> ''' + tenant.plano + '''</p>
                <p><strong>Expiração:</strong> ''' + (tenant.data_expiracao.strftime('%d/%m/%Y') if tenant.data_expiracao else 'N/A') + '''</p>
                <p><strong>Dias Restantes:</strong> ''' + str(tenant.dias_restantes) + ''' dias</p>
                <p><strong>Status:</strong> <span style="color: #4CAF50;">''' + tenant.status.title() + '''</span></p>
            </div>
            
            <div class="info-box">
                <h3>🎯 Próximo: Migrar Funcionalidades Completas</h3>
                <p style="margin-top: 10px; color: rgba(255,255,255,0.7);">
                    Para completar a migração, copie as rotas do app.py original (tickets, chat, CAB, etc.) 
                    para app_multi_tenant.py, adaptando para usar g.tenant_session em vez de db.session.
                </p>
            </div>
        </div>
    </body>
    </html>
    '''
    
    return html


@app.route('/analyst')
def analyst_panel():
    """Painel do analista"""
    tenant = g.current_tenant
    u = current_user()
    
    if not u or u.role not in ['analyst', 'admin']:
        flash('Acesso negado!', 'error')
        return redirect(url_for('login'))
    
    return f'''
    <!DOCTYPE html>
    <html>
    <head><title>Analista - {tenant.nome}</title></head>
    <body>
        <h1>Painel do Analista - {tenant.nome}</h1>
        <p>Bem-vindo, {u.name}!</p>
        <a href="/logout">Logout</a>
    </body>
    </html>
    '''


@app.route('/manager')
@app.route('/manager/dashboard')
def manager_dashboard():
    """Painel do manager"""
    tenant = g.current_tenant
    u = current_user()
    
    if not u or (not u.manager and not u.senior_manager and u.role != 'admin'):
        flash('Acesso negado!', 'error')
        return redirect(url_for('login'))
    
    return f'''
    <!DOCTYPE html>
    <html>
    <head><title>Manager - {tenant.nome}</title></head>
    <body>
        <h1>Painel do Manager - {tenant.nome}</h1>
        <p>Bem-vindo, {u.name}!</p>
        <a href="/logout">Logout</a>
    </body>
    </html>
    '''


@app.route('/user')
@app.route('/user/dashboard')
def user_dashboard():
    """Painel do usuário"""
    tenant = g.current_tenant
    u = current_user()
    
    if not u:
        flash('Acesso negado!', 'error')
        return redirect(url_for('login'))
    
    return f'''
    <!DOCTYPE html>
    <html>
    <head><title>Minha Conta - {tenant.nome}</title></head>
    <body>
        <h1>Minha Conta - {tenant.nome}</h1>
        <p>Bem-vindo, {u.name}!</p>
        <a href="/logout">Logout</a>
    </body>
    </html>
    '''


# ==================== INICIALIZAÇÃO ====================

if __name__ == '__main__':
    print("=" * 60)
    print("🚀 Help Desk SaaS - Sistema Multi-Tenant")
    print("=" * 60)
    print(f"📁 Diretório de bancos: {DATABASES_DIR}")
    print(f"📊 Banco master: {os.path.join(DATABASES_DIR, 'master.db')}")
    print()
    print("🌐 URLs de acesso:")
    print("   - Painel Master: http://localhost:5000 (ou master.helpdeskhub.com)")
    print("   - Tenant 1: http://empresa1.localhost:5000")
    print("   - Tenant 2: http://empresa2.localhost:5000")
    print()
    print("🔐 Senha mestra padrão: Master@2024")
    print("   (Altere via variável de ambiente MASTER_PASSWORD)")
    print("=" * 60)
    
    app.run(debug=True, host='0.0.0.0', port=5000)
