import os
import sys
import socket
from datetime import datetime, timedelta
import hashlib
import uuid
import json
from flask import Flask, render_template_string, request, redirect, url_for, session, flash, jsonify, send_file
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

# Sistema de licenciamento
# Sistema de licenciamento - VERSÃO CORRIGIDA
class LicenseManager:
    def __init__(self):
        self.license_file = "license.key"
        self.trial_days = 30
        self.license_data = None
        self.load_license()
    
    def get_machine_fingerprint(self):
        """Gera uma fingerprint única da máquina"""
        try:
            machine_name = socket.gethostname()
            mac = ':'.join(['{:02x}'.format((uuid.getnode() >> elements) & 0xff) 
                           for elements in range(0,8*6,8)][::-1])
            fingerprint_string = f"{machine_name}_{mac}"
            return hashlib.md5(fingerprint_string.encode()).hexdigest()
        except:
            return "default_fingerprint"
    
    def load_license(self):
        """Carrega dados da licença"""
        if os.path.exists(self.license_file):
            try:
                with open(self.license_file, 'r') as f:
                    self.license_data = json.load(f)
            except:
                self.license_data = None
    
    def save_license(self, license_key):
        """Salva licença no arquivo"""
        license_info = {
            'key': license_key,
            'fingerprint': self.get_machine_fingerprint(),
            'activated_date': datetime.now().isoformat()
        }
        with open(self.license_file, 'w') as f:
            json.dump(license_info, f)
        self.license_data = license_info
    
    def validate_license(self, license_key):
        """Valida a chave de licença"""
        if not license_key or len(license_key) != 29:
            return False, "Formato de licença inválido"
        
        try:
            parts = license_key.split('-')
            if len(parts) != 5:
                return False, "Formato de licença inválido"
            
            checksum = parts[4]
            check_string = '-'.join(parts[:4])
            calculated_checksum = hashlib.md5(check_string.encode()).hexdigest()[:4]
            
            if checksum != calculated_checksum:
                return False, "Licença inválida"
            
            license_type = parts[0]
            expiry_days = {
                'HUB3M': 90,    # 3 meses
                'HUB6M': 180,   # 6 meses
                'HUB1Y': 365,   # 1 ano
                'HUB2Y': 730    # 2 anos
            }
            
            if license_type not in expiry_days:
                return False, "Tipo de licença inválido"
            
            return True, expiry_days[license_type]
            
        except Exception as e:
            return False, f"Erro na validação: {str(e)}"
    
class LicenseManager:
    def __init__(self):
        self.license_file = "license.key"
        self.trial_days = 30
        self.license_data = None
        self.load_license()

    def get_machine_fingerprint(self):
        """Gera uma fingerprint única da máquina"""
        try:
            machine_name = socket.gethostname()
            mac = ':'.join(['{:02x}'.format((uuid.getnode() >> elements) & 0xff)
                            for elements in range(0, 8 * 6, 8)][::-1])
            fingerprint_string = f"{machine_name}_{mac}"
            return hashlib.md5(fingerprint_string.encode()).hexdigest()
        except:
            return "default_fingerprint"

    def load_license(self):
        """Carrega dados da licença"""
        if os.path.exists(self.license_file):
            try:
                with open(self.license_file, 'r') as f:
                    self.license_data = json.load(f)
            except:
                self.license_data = None

    def save_license(self, license_key):
        """Salva licença no arquivo"""
        license_info = {
            'key': license_key,
            'fingerprint': self.get_machine_fingerprint(),
            'activated_date': datetime.now().isoformat()
        }
        with open(self.license_file, 'w') as f:
            json.dump(license_info, f)
        self.license_data = license_info

    def validate_license(self, license_key):
        """Valida a chave de licença"""
        if not license_key or len(license_key) != 29:
            return False, "Formato de licença inválido"

        try:
            parts = license_key.split('-')
            if len(parts) != 5:
                return False, "Formato de licença inválido"

            checksum = parts[4]
            check_string = '-'.join(parts[:4])
            calculated_checksum = hashlib.md5(check_string.encode()).hexdigest()[:4]

            if checksum != calculated_checksum:
                return False, "Licença inválida"

            license_type = parts[0]
            expiry_days = {
                'HUB3M': 90,    # 3 meses
                'HUB6M': 180,   # 6 meses
                'HUB1Y': 365,   # 1 ano
                'HUB2Y': 730    # 2 anos
            }

            if license_type not in expiry_days:
                return False, "Tipo de licença inválido"

            return True, expiry_days[license_type]

        except Exception as e:
            return False, f"Erro na validação: {str(e)}"

    def check_license_status(self):
        """Verifica status da licença"""
        if self.license_data:
            try:
                is_valid, result = self.validate_license(self.license_data['key'])

                if not is_valid:
                    return {
                        'status': 'invalid',
                        'days_left': 0,
                        'message': result
                    }

                expiry_days = result
                activated_date = datetime.fromisoformat(self.license_data['activated_date'])
                expiry_date = activated_date + timedelta(days=expiry_days)

                if datetime.now() < expiry_date:
                    days_left = (expiry_date - datetime.now()).days
                    return {
                        'status': 'licensed',
                        'days_left': days_left,
                        'message': f'Licença válida: {days_left} dias restantes'
                    }
                else:
                    return {
                        'status': 'expired',
                        'days_left': 0,
                        'message': 'Licença expirada. Renove sua licença.'
                    }

            except Exception as e:
                return {
                    'status': 'error',
                    'days_left': 0,
                    'message': f'Erro na licença: {str(e)}'
                }

        # ====== MODO TRIAL ======
        trial_file = "trial_start.date"

        if os.path.exists(trial_file):
            try:
                with open(trial_file, 'r') as f:
                    trial_start = datetime.fromisoformat(f.read().strip())

                trial_end = trial_start + timedelta(days=self.trial_days)

                if datetime.now() < trial_end:
                    days_left = (trial_end - datetime.now()).days
                    return {
                        'status': 'trial',
                        'days_left': days_left,
                        'message': f'Modo Trial: {days_left} dias restantes'
                    }
                else:
                    return {
                        'status': 'expired',
                        'days_left': 0,
                        'message': 'Período trial expirado. Ative uma licença.'
                    }
            except Exception:
                pass

        # Criar novo trial
        try:
            trial_start = datetime.now()
            with open(trial_file, 'w') as f:
                f.write(trial_start.isoformat())

            return {
                'status': 'trial',
                'days_left': self.trial_days,
                'message': f'Modo Trial Ativado: {self.trial_days} dias restantes'
            }
        except Exception as e:
            return {
                'status': 'error',
                'days_left': 0,
                'message': f'Erro ao ativar trial: {str(e)}'
            }
    
    
# Middleware de verificação de licença
def check_license():
    """Decorator para verificar licença em rotas críticas"""
    def decorator(f):
        def decorated_function(*args, **kwargs):
            license_status = license_manager.check_license_status()
            
            if license_status['status'] in ['expired', 'invalid']:
                if request.path not in ['/license', '/activate_license']:
                    return redirect('/license')
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator

license_manager = LicenseManager()

app = Flask(__name__)
app.config['SECRET_KEY'] = 'helpdesk_secured_2024'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///helpdesk.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = 'static/uploads'
app.config['PERMANENT_SESSION_LIFETIME'] = 3600
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024

db = SQLAlchemy(app)

# Criar diretórios necessários
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs(os.path.join(app.config['UPLOAD_FOLDER'], 'documents'), exist_ok=True)

brasilia_tz = pytz.timezone('America/Sao_Paulo')

def now_brasilia():
    return datetime.now(brasilia_tz)
        
def activate_license(self, license_key):
        """Ativa uma licença"""
        is_valid, result = self.validate_license(license_key)
        
        if is_valid:
            self.save_license(license_key)
            return True, "Licença ativada com sucesso!"
        else:
            return False, result



def reset_trial(self):
    """APENAS PARA DESENVOLVIMENTO - Reseta o período de trial"""
    if os.path.exists("trial_start.date"):
        os.remove("trial_start.date")
    if os.path.exists(self.license_file):
        os.remove(self.license_file)
    self.license_data = None
    return "Trial resetado com sucesso!"



# Middleware de verificação de licença
def check_license():
    """Decorator para verificar licença em rotas críticas"""
    def decorator(f):
        def decorated_function(*args, **kwargs):
            license_status = license_manager.check_license_status()
            
            if license_status['status'] in ['expired', 'invalid']:
                if request.path not in ['/license', '/activate_license', '/login']:
                    return redirect('/license')
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator

# MODELOS ATUALIZADOS
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120))
    department = db.Column(db.String(120))
    username = db.Column(db.String(80), unique=True)
    password_hash = db.Column(db.String(200))
    role = db.Column(db.String(20))
    region = db.Column(db.String(50))
    online = db.Column(db.Boolean, default=False)
    pause_start = db.Column(db.DateTime, nullable=True)
    total_attended = db.Column(db.Integer, default=0)
    full_name = db.Column(db.String(200))
    first_name = db.Column(db.String(100))
    last_name = db.Column(db.String(100))
    position = db.Column(db.String(100))
    company = db.Column(db.String(100))
    third_party_company = db.Column(db.String(100))
    department_extended = db.Column(db.String(100))
    needs_password_reset = db.Column(db.Boolean, default=False)
    blocked = db.Column(db.Boolean, default=False)
    active = db.Column(db.Boolean, default=True)
    vip = db.Column(db.Boolean, default=False)
    manager = db.Column(db.Boolean, default=False)
    senior_manager = db.Column(db.Boolean, default=False)
    registration = db.Column(db.String(50))
    email = db.Column(db.String(120))
    date_format = db.Column(db.String(20), default='dd/MM/aaaa')
    business_phone = db.Column(db.String(20))
    cell_phone = db.Column(db.String(20))
    group_id = db.Column(db.Integer, db.ForeignKey('support_group.id'), nullable=True)
    manager_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    senior_manager_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    cab_access = db.Column(db.Boolean, default=False)
    
    managed_users = db.relationship('User', foreign_keys=[manager_id], 
                                  backref=db.backref('manager_ref', remote_side=[id]))
    senior_managed_users = db.relationship('User', foreign_keys=[senior_manager_id], 
                                         backref=db.backref('senior_manager_ref', remote_side=[id]))

class Category(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    area = db.Column(db.String(50))
    name = db.Column(db.String(120))

class Session(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer)
    category = db.Column(db.String(120))
    region = db.Column(db.String(50))
    status = db.Column(db.String(30), default='waiting')
    created_at = db.Column(db.DateTime, default=now_brasilia)
    assigned_at = db.Column(db.DateTime, nullable=True)
    finished_at = db.Column(db.DateTime, nullable=True)
    analyst_id = db.Column(db.Integer, nullable=True)

class Message(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    session_id = db.Column(db.Integer)
    sender = db.Column(db.String(20))
    content = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=now_brasilia)

class Document(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    session_id = db.Column(db.Integer)
    user_id = db.Column(db.Integer)
    filename = db.Column(db.String(255))
    original_filename = db.Column(db.String(255))
    file_type = db.Column(db.String(50))
    uploaded_at = db.Column(db.DateTime, default=now_brasilia)

class Config(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    company_name = db.Column(db.String(100), default='Help Desk')
    logo_path = db.Column(db.String(200), default='')
    primary_color = db.Column(db.String(7), default="#0467FA")
    secondary_color = db.Column(db.String(7), default='#2196F3')
    waiting_color = db.Column(db.String(7), default="#FD1C1C")
    progress_color = db.Column(db.String(7), default='#8BC34A')

class SupportGroup(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True)
    description = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=now_brasilia)
    analysts = db.relationship('User', backref='support_group', lazy=True)

class SubCategory(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100))
    description = db.Column(db.Text)
    category_id = db.Column(db.Integer, db.ForeignKey('ticket_category.id'))
    requires_approval = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=now_brasilia)
    category = db.relationship('TicketCategory', backref='subcategories')

class TicketCategory(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100))
    description = db.Column(db.Text)
    group_id = db.Column(db.Integer, db.ForeignKey('support_group.id'))
    sla_hours = db.Column(db.Integer, default=24)
    requires_approval = db.Column(db.Boolean, default=False)
    group = db.relationship('SupportGroup', backref='categories')

class Ticket(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    number = db.Column(db.String(20), unique=True)
    type = db.Column(db.String(20))
    title = db.Column(db.String(200))
    description = db.Column(db.Text)
    priority = db.Column(db.String(20), default='Medium')
    status = db.Column(db.String(30), default='open')
    created_by = db.Column(db.Integer, db.ForeignKey('user.id'))
    assigned_to = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    assigned_group = db.Column(db.Integer, db.ForeignKey('support_group.id'), nullable=True)
    category_id = db.Column(db.Integer, db.ForeignKey('ticket_category.id'))
    subcategory_id = db.Column(db.Integer, db.ForeignKey('sub_category.id'), nullable=True)
    created_at = db.Column(db.DateTime, default=now_brasilia)
    updated_at = db.Column(db.DateTime, default=now_brasilia, onupdate=now_brasilia)
    assigned_at = db.Column(db.DateTime, nullable=True)
    resolved_at = db.Column(db.DateTime, nullable=True)
    closed_at = db.Column(db.DateTime, nullable=True)
    sla_due = db.Column(db.DateTime, nullable=True)
    requires_approval = db.Column(db.Boolean, default=False)
    approved_by = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    approved_at = db.Column(db.DateTime, nullable=True)
    pending_reason = db.Column(db.Text, nullable=True)
    current_owner = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    resolution_notes = db.Column(db.Text, nullable=True)
    user_accepted = db.Column(db.Boolean, nullable=True)
    user_rejection_reason = db.Column(db.Text, nullable=True)
    
    creator = db.relationship('User', foreign_keys=[created_by], backref='created_tickets')
    assignee = db.relationship('User', foreign_keys=[assigned_to], backref='assigned_tickets')
    approver = db.relationship('User', foreign_keys=[approved_by])
    category = db.relationship('TicketCategory', backref='tickets')
    subcategory = db.relationship('SubCategory', backref='tickets')
    group = db.relationship('SupportGroup', backref='tickets')
    owner = db.relationship('User', foreign_keys=[current_owner], backref='owned_tickets')

class TicketComment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    ticket_id = db.Column(db.Integer, db.ForeignKey('ticket.id'))
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    content = db.Column(db.Text)
    is_internal = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=now_brasilia)
    ticket = db.relationship('Ticket', backref='comments')
    user = db.relationship('User', backref='ticket_comments')

class RoutingRule(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100))
    condition_type = db.Column(db.String(50))
    condition_value = db.Column(db.String(200))
    target_group_id = db.Column(db.Integer, db.ForeignKey('support_group.id'))
    priority = db.Column(db.Integer, default=1)
    active = db.Column(db.Boolean, default=True)
    target_group = db.relationship('SupportGroup', backref='routing_rules')

# NOVOS MODELOS PARA CAB (Change Advisory Board)
class ChangeRequest(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    number = db.Column(db.String(20), unique=True)
    title = db.Column(db.String(200))
    description = db.Column(db.Text)
    priority = db.Column(db.String(20), default='Medium')
    impact = db.Column(db.String(20), default='Medium')
    systems_affected = db.Column(db.Text)
    implementation_date = db.Column(db.DateTime)
    start_date = db.Column(db.DateTime)
    end_date = db.Column(db.DateTime)
    meeting_date = db.Column(db.DateTime)
    status = db.Column(db.String(30), default='draft')
    created_by = db.Column(db.Integer, db.ForeignKey('user.id'))
    created_at = db.Column(db.DateTime, default=now_brasilia)
    updated_at = db.Column(db.DateTime, default=now_brasilia, onupdate=now_brasilia)
    approved_by = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    approved_at = db.Column(db.DateTime, nullable=True)
    rejection_reason = db.Column(db.Text, nullable=True)
    
    creator = db.relationship('User', foreign_keys=[created_by], backref='created_changes')
    approver = db.relationship('User', foreign_keys=[approved_by], backref='approved_changes')

class CABComment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    change_request_id = db.Column(db.Integer, db.ForeignKey('change_request.id'))
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    content = db.Column(db.Text)
    risk_assessment = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=now_brasilia)
    
    change_request = db.relationship('ChangeRequest', backref='comments')
    user = db.relationship('User', backref='cab_comments')

class ChangeLog(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    change_request_id = db.Column(db.Integer, db.ForeignKey('change_request.id'))
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    action = db.Column(db.String(50))
    details = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=now_brasilia)
    
    change_request = db.relationship('ChangeRequest', backref='logs')
    user = db.relationship('User', backref='change_logs')

class CABDocument(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    change_request_id = db.Column(db.Integer, db.ForeignKey('change_request.id'))
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    filename = db.Column(db.String(255))
    original_filename = db.Column(db.String(255))
    file_type = db.Column(db.String(50))
    uploaded_at = db.Column(db.DateTime, default=now_brasilia)
    
    change_request = db.relationship('ChangeRequest', backref='documents')
    user = db.relationship('User', backref='cab_documents')

# INICIALIZAÇÃO
# SUBSTITUIR A FUNÇÃO init_db() ORIGINAL POR ESTA:
def init_db():
    with app.app_context():
        try:
            # Verificar licença antes de inicializar
            license_status = license_manager.check_license_status()
            if license_status['status'] in ['expired', 'invalid']:
                print("❌ LICENÇA INVÁLIDA OU EXPIRADA")
                print(f"💡 Mensagem: {license_status['message']}")
                # Criar apenas tabelas básicas para permitir ativação
                db.create_all()
                return False
            
            db.create_all()
            
            config = Config.query.first()
            if not config:
                config = Config()
                db.session.add(config)
            
            admin = User.query.filter_by(username='admin').first()
            if not admin:
                admin_password = 'Hubdesk.1988'
                admin = User(
                    name='ADMIN', department='TI', username='admin',
                    password_hash=generate_password_hash(admin_password), 
                    role='admin', region='TI',
                    full_name='Administrador Sistema', first_name='Administrador', 
                    last_name='Sistema', position='Administrador', company='HubDesk', 
                    email='admin@empresa.com', active=True, manager=True, 
                    senior_manager=True, cab_access=True
                )
                db.session.add(admin)
                print(f"✅ ADMIN CRIADO - Senha: {admin_password}")
            
            analyst = User.query.filter_by(username='analista').first()
            if not analyst:
                analyst = User(
                    name='Analista', department='Suporte', username='analista',
                    password_hash=generate_password_hash('analista'), role='analyst', region='TI',
                    full_name='Analista Suporte', first_name='Analista', last_name='Suporte',
                    position='Analista de Suporte', company='hubdesk', email='analista@empresa.com',
                    active=True, cab_access=True
                )
                db.session.add(analyst)
            
            groups = SupportGroup.query.all()
            if not groups:
                helpdesk_group = SupportGroup(name='Helpdesk', description='Suporte geral e reset de senha')
                field_group = SupportGroup(name='Field Support', description='Suporte presencial e instalação de software')
                systems_group = SupportGroup(name='Systems Team', description='Time de sistemas e liberação de acesso')
                
                db.session.add_all([helpdesk_group, field_group, systems_group])
                db.session.commit()
                
                categories = [
                    TicketCategory(name='Reset de Senha', description='Solicitação de reset de senha', 
                                  group_id=helpdesk_group.id, sla_hours=2),
                    TicketCategory(name='Instalação de Software', description='Instalação de novos softwares', 
                                  group_id=field_group.id, sla_hours=24),
                    TicketCategory(name='Liberação de Acesso', description='Solicitação de acesso a sistemas', 
                                  group_id=systems_group.id, sla_hours=4, requires_approval=True),
                    TicketCategory(name='Problema com Hardware', description='Problemas com equipamentos', 
                                  group_id=field_group.id, sla_hours=8),
                    TicketCategory(name='Problema com Sistema', description='Erros em sistemas corporativos', 
                                  group_id=helpdesk_group.id, sla_hours=6)
                ]
                db.session.add_all(categories)
                
                access_category = TicketCategory.query.filter_by(name='Liberação de Acesso').first()
                if access_category:
                    subcategories = [
                        SubCategory(name='Sistema ERP', description='Acesso ao sistema ERP', category_id=access_category.id, requires_approval=True),
                        SubCategory(name='Portal do Colaborador', description='Acesso ao portal', category_id=access_category.id, requires_approval=False),
                        SubCategory(name='E-mail Corporativo', description='Criação de e-mail', category_id=access_category.id, requires_approval=True)
                    ]
                    db.session.add_all(subcategories)
                
                rules = [
                    RoutingRule(name='Reset Senha -> Helpdesk', condition_type='keyword', 
                               condition_value='reset senha', target_group_id=helpdesk_group.id),
                    RoutingRule(name='Instalação -> Field', condition_type='keyword', 
                               condition_value='instalar software', target_group_id=field_group.id),
                    RoutingRule(name='Acesso -> Systems', condition_type='keyword', 
                               condition_value='liberação acesso', target_group_id=systems_group.id),
                ]
                db.session.add_all(rules)
            
            categories = Category.query.all()
            if not categories:
                db.session.add_all([
                    Category(area='TI', name='Consulta de chamado'),
                    Category(area='TI', name='Problema com sistema'),
                    Category(area='TI', name='Outra'),
                    Category(area='RH', name='Folha'),
                    Category(area='RH', name='Benefício'),
                    Category(area='FINANCEIRO', name='Pagamento'),
                    Category(area='FINANCEIRO', name='Reembolso'),
                    Category(area='OPERACOES', name='Produção'),
                    Category(area='OPERACOES', name='Logística')
                ])
            
            db.session.commit()
            print("✅ BANCO INICIALIZADO COM SUCESSO!")
            return True
            
        except Exception as e:
            print(f"❌ ERRO AO INICIALIZAR BANCO: {str(e)}")
            import traceback
            traceback.print_exc()
            return False
        
def current_user():
    uid = session.get('user_id')
    return User.query.get(uid) if uid else None

def get_config():
    return Config.query.first()

def get_local_ip():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except:
        return "127.0.0.1"

def generate_ticket_number():
    last_ticket = Ticket.query.order_by(Ticket.id.desc()).first()
    last_number = last_ticket.number if last_ticket else "TICKET000000"
    last_num = int(last_number.replace('TICKET', ''))
    new_num = last_num + 1
    return f"TICKET{new_num:06d}"

def generate_change_number():
    last_change = ChangeRequest.query.order_by(ChangeRequest.id.desc()).first()
    last_number = last_change.number if last_change else "CHANGE000000"
    last_num = int(last_number.replace('CHANGE', ''))
    new_num = last_num + 1
    return f"CHANGE{new_num:06d}"

def apply_routing_rules(ticket):
    rules = RoutingRule.query.filter_by(active=True).order_by(RoutingRule.priority).all()
    
    for rule in rules:
        if rule.condition_type == 'keyword':
            keywords = rule.condition_value.lower().split(',')
            ticket_text = (ticket.title + ' ' + ticket.description).lower()
            if any(keyword.strip() in ticket_text for keyword in keywords):
                ticket.assigned_group = rule.target_group_id
                break
        elif rule.condition_type == 'category':
            if ticket.category_id == int(rule.condition_value):
                ticket.assigned_group = rule.target_group_id
                break
    
    if ticket.category and ticket.category.sla_hours:
        ticket.sla_due = now_brasilia() + timedelta(hours=ticket.category.sla_hours)

REGIONS = [
    'Analista de Ti', 'User comun'
]

ALLOWED_EXTENSIONS = {
    'png', 'jpg', 'jpeg', 'gif', 'bmp',
    'pdf', 'doc', 'docx', 'txt',
    'xls', 'xlsx', 'csv'
}

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# HTML TEMPLATES
LOGIN_HTML = '''<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{{ config.company_name }} - Login</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; }
        body { background: linear-gradient(135deg, #0c0c0c 0%, #1a1a2e 50%, #16213e 100%); min-height: 100vh; display: flex; align-items: center; justify-content: center; overflow: hidden; position: relative; }
        body::before { content: ''; position: absolute; top: 0; left: 0; right: 0; bottom: 0; background: radial-gradient(circle at 20% 80%, rgba(4, 103, 250, 0.1) 0%, transparent 50%), radial-gradient(circle at 80% 20%, rgba(33, 150, 243, 0.1) 0%, transparent 50%); animation: float 6s ease-in-out infinite; }
        @keyframes float { 0%, 100% { transform: translateY(0px) rotate(0deg); } 50% { transform: translateY(-20px) rotate(180deg); } }
        .login-container { position: relative; z-index: 2; width: 100%; max-width: 400px; padding: 20px; }
        .login-card { background: rgba(255, 255, 255, 0.05); backdrop-filter: blur(20px); border: 1px solid rgba(255, 255, 255, 0.1); border-radius: 20px; padding: 40px 30px; box-shadow: 0 25px 50px rgba(0, 0, 0, 0.5); position: relative; overflow: hidden; }
        .login-card::before { content: ''; position: absolute; top: 0; left: -100%; width: 100%; height: 100%; background: linear-gradient(90deg, transparent, rgba(255, 255, 255, 0.1), transparent); transition: 0.5s; }
        .login-card:hover::before { left: 100%; }
        .logo-section { text-align: center; margin-bottom: 30px; }
        .logo-section img { max-width: 80px; margin-bottom: 15px; filter: drop-shadow(0 0 20px {{ config.primary_color }}); }
        .logo-section h1 { color: white; font-size: 28px; font-weight: 300; margin-bottom: 5px; background: linear-gradient(45deg, #fff, {{ config.primary_color }}); -webkit-background-clip: text; -webkit-text-fill-color: transparent; }
        .logo-section p { color: rgba(255, 255, 255, 0.7); font-size: 14px; }
        .form-group { margin-bottom: 20px; position: relative; }
        .form-group input { width: 100%; padding: 15px 20px; background: rgba(255, 255, 255, 0.1); border: 1px solid rgba(255, 255, 255, 0.2); border-radius: 12px; color: white; font-size: 16px; transition: all 0.3s ease; }
        .form-group input::placeholder { color: rgba(255, 255, 255, 0.5); }
        .form-group input:focus { outline: none; border-color: {{ config.primary_color }}; box-shadow: 0 0 20px {{ config.primary_color }}40; background: rgba(255, 255, 255, 0.15); }
        .login-btn { width: 100%; padding: 15px; background: linear-gradient(45deg, {{ config.primary_color }}, {{ config.secondary_color }}); border: none; border-radius: 12px; color: white; font-size: 16px; font-weight: 600; cursor: pointer; transition: all 0.3s ease; position: relative; overflow: hidden; }
        .login-btn::before { content: ''; position: absolute; top: 0; left: -100%; width: 100%; height: 100%; background: linear-gradient(90deg, transparent, rgba(255, 255, 255, 0.2), transparent); transition: 0.5s; }
        .login-btn:hover::before { left: 100%; }
        .login-btn:hover { transform: translateY(-2px); box-shadow: 0 10px 30px {{ config.primary_color }}60; }
        .glow { position: absolute; width: 200px; height: 200px; background: {{ config.primary_color }}; border-radius: 50%; filter: blur(100px); opacity: 0.1; animation: pulse 4s infinite ease-in-out; }
        .glow-1 { top: 10%; left: 10%; } .glow-2 { bottom: 10%; right: 10%; }
        @keyframes pulse { 0%, 100% { opacity: 0.1; transform: scale(1); } 50% { opacity: 0.2; transform: scale(1.1); } }
    </style>
</head>
<body>
    <div class="glow glow-1"></div><div class="glow glow-2"></div>
    <div class="login-container">
        <div class="login-card">
            <div class="logo-section">
                {% if config.logo_path %}<img src="/static/uploads/{{ config.logo_path }}" alt="{{ config.company_name }}">{% else %}
                <div style="width: 80px; height: 80px; background: linear-gradient(45deg, {{ config.primary_color }}, {{ config.secondary_color }}); border-radius: 20px; margin: 0 auto 15px; display: flex; align-items: center; justify-content: center;"><span style="color: white; font-size: 24px;">⚡</span></div>{% endif %}
                <h1>{{ config.company_name }}</h1><p>Intelligent Support System</p>
            </div>
            <form method="post">
                <div class="form-group"><input type="text" name="username" placeholder="👤 Usuário" required></div>
                <div class="form-group"><input type="password" name="password" placeholder="🔒 Senha" required></div>
                <button type="submit" class="login-btn">🚀 ACESSAR SISTEMA</button>
            </form>
            {% with messages = get_flashed_messages() %}
                {% if messages %}
                    <div style="color: #ff6b6b; text-align: center; margin-top: 15px; padding: 10px; background: rgba(255,107,107,0.1); border-radius: 8px;">
                        {% for message in messages %}
                            {{ message }}
                        {% endfor %}
                    </div>
                {% endif %}
            {% endwith %}
        </div>
    </div>
</body>
</html>'''

# ROTAS PRINCIPAIS
# 🔐 ROTAS DE LICENCIAMENTO - COLOCAR AQUI ANTES DA ROTA PRINCIPAL
@app.route('/license')
def license_page():
    """Página de ativação de licença"""
    config = get_config()
    license_status = license_manager.check_license_status()
    
    status_class = license_status['status']
    if status_class == 'trial':
        status_display = 'TRIAL'
    elif status_class == 'licensed':
        status_display = 'LICENCIADO'
    else:
        status_display = 'EXPIRADO'
    
    license_html = f'''
    <!DOCTYPE html>
    <html lang="pt-BR">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Sistema de Licenciamento</title>
        <style>
            * {{ margin: 0; padding: 0; box-sizing: border-box; font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; }}
            body {{ background: linear-gradient(135deg, #0c0c0c 0%, #1a1a2e 50%, #16213e 100%); min-height: 100vh; display: flex; align-items: center; justify-content: center; color: white; }}
            .container {{ max-width: 500px; width: 100%; padding: 20px; }}
            .card {{ background: rgba(255, 255, 255, 0.05); backdrop-filter: blur(20px); border: 1px solid rgba(255, 255, 255, 0.1); border-radius: 20px; padding: 40px; text-align: center; }}
            .status {{ padding: 15px; border-radius: 10px; margin: 20px 0; font-weight: bold; }}
            .status.trial {{ background: rgba(255, 193, 7, 0.2); border: 1px solid #FFC107; }}
            .status.licensed {{ background: rgba(76, 175, 80, 0.2); border: 1px solid #4CAF50; }}
            .status.expired {{ background: rgba(244, 67, 54, 0.2); border: 1px solid #f44336; }}
            .form-group {{ margin-bottom: 20px; text-align: left; }}
            .form-group label {{ display: block; margin-bottom: 8px; color: white; }}
            .form-group input {{ width: 100%; padding: 15px; background: rgba(255, 255, 255, 0.1); border: 1px solid rgba(255, 255, 255, 0.2); border-radius: 10px; color: white; font-size: 16px; }}
            .btn {{ background: #0467FA; color: white; padding: 15px 30px; border: none; border-radius: 10px; cursor: pointer; font-size: 16px; width: 100%; }}
            .btn:hover {{ background: #0357D0; }}
            .fingerprint {{ background: rgba(255,255,255,0.1); padding: 10px; border-radius: 5px; margin: 10px 0; font-family: monospace; font-size: 12px; word-break: break-all; }}
            .message {{ padding: 10px; border-radius: 5px; margin: 10px 0; }}
            .success {{ background: rgba(76, 175, 80, 0.2); border: 1px solid #4CAF50; }}
            .error {{ background: rgba(244, 67, 54, 0.2); border: 1px solid #f44336; }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="card">
                <h1>🔐 Sistema de Licenciamento</h1>
                <div class="status {status_class}">
                    <strong>{status_display}:</strong> {license_status['message']}
                </div>
                
                <div class="fingerprint">
                    <strong>Machine Fingerprint:</strong><br>
                    {license_manager.get_machine_fingerprint()}
                </div>

                <form method="post" action="/activate_license">
                    <div class="form-group">
                        <label>Chave de Licença:</label>
                        <input type="text" name="license_key" placeholder="Digite sua chave de licença (formato: XXXX-XXXX-XXXX-XXXX-XXXX)" required style="color: white;">
                    </div>
                    <button type="submit" class="btn">🚀 Ativar Licença</button>
                </form>

                <div style="margin-top: 20px; font-size: 14px; color: #ccc;">
                    <p><strong>Formatos de Licença Válidos:</strong></p>
                    <p>• HUB3M-XXXX-XXXX-XXXX-XXXX (3 meses)</p>
                    <p>• HUB6M-XXXX-XXXX-XXXX-XXXX (6 meses)</p>
                    <p>• HUB1Y-XXXX-XXXX-XXXX-XXXX (1 ano)</p>
                    <p>• HUB2Y-XXXX-XXXX-XXXX-XXXX (2 anos)</p>
                </div>
            </div>
        </div>
    </body>
    </html>
    '''
    return license_html

@app.route('/activate_license', methods=['POST'])
def activate_license():
    """Processa a ativação da licença"""
    license_key = request.form.get('license_key', '').strip()
    
    if not license_key:
        flash('Por favor, digite uma chave de licença!', 'error')
        return redirect('/license')
    
    success, message = license_manager.activate_license(license_key)
    
    if success:
        flash(message, 'success')
        # Reinicializar o banco após ativação bem-sucedida
        init_db()
        return redirect('/')
    else:
        flash(message, 'error')
        return redirect('/license')

# 🏠 ROTA PRINCIPAL - ESTA JÁ DEVE EXISTIR, SÓ MODIFICAR
@app.route('/')
def index():
    license_status = license_manager.check_license_status()
    
    # Se a licença estiver expirada ou inválida, redirecionar para página de licença
    if license_status['status'] in ['expired', 'invalid']:
        return redirect('/license')
    
    u = current_user()
    if u:
        if u.role == 'admin': return redirect(url_for('admin_panel'))
        if u.role == 'analyst': return redirect(url_for('analyst_panel'))
        if u.manager or u.senior_manager: return redirect(url_for('manager_dashboard'))
        return redirect(url_for('user_dashboard'))
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
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
        
        print(f"🔐 TENTATIVA DE LOGIN: {username}")
        
        # Buscar usuário
        u = User.query.filter_by(username=username).first()
        
        if u:
            print(f"✅ USUÁRIO ENCONTRADO: {u.name} | Role: {u.role}")
            print(f"🔑 Senha fornecida: {password}")
            print(f"🔑 Hash no banco: {u.password_hash}")
            
            # Verificar senha
            if check_password_hash(u.password_hash, password):
                session['user_id'] = u.id
                session.permanent = True
                print(f"🎉 LOGIN BEM-SUCEDIDO: {u.name}")
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
                print("❌ SENHA INCORRETA")
                flash('Senha incorreta!', 'error')
        else:
            print("❌ USUÁRIO NÃO ENCONTRADO")
            flash('Usuário não encontrado!', 'error')
    
    return render_template_string(LOGIN_HTML, config=config)


@app.route('/logout')
def logout():
    session.clear()
    flash('Você saiu do sistema.', 'info')
    return redirect(url_for('login'))

# CORREÇÃO 1: DETALHES DO TICKET - CORRIGIR TypeError
@app.route('/ticket/<int:ticket_id>', methods=['GET', 'POST'])
def ticket_detail(ticket_id):
    config = get_config()
    u = current_user()
    if not u: 
        flash('Acesso negado!', 'error')
        return redirect(url_for('login'))
    
    ticket = Ticket.query.get_or_404(ticket_id)
    
    if u.role == 'user' and ticket.created_by != u.id:
        flash('Acesso negado!', 'error')
        return redirect(url_for('user_dashboard'))
    
    # Processar aceitação/rejeição do usuário
    if request.method == 'POST' and u.role == 'user' and ticket.created_by == u.id:
        action = request.form.get('action')
        if action == 'accept':
            ticket.status = 'closed'
            ticket.user_accepted = True
            ticket.closed_at = now_brasilia()
            db.session.commit()
            flash('Ticket aceito e finalizado com sucesso!', 'success')
        elif action == 'reject':
            ticket.status = 'open'
            ticket.user_accepted = False
            ticket.user_rejection_reason = request.form.get('rejection_reason', '')
            ticket.assigned_to = None
            db.session.commit()
            flash('Ticket rejeitado e reaberto para o analista!', 'warning')
        return redirect(f'/ticket/{ticket_id}')
    
    if u.role == 'user':
        comments = TicketComment.query.filter_by(ticket_id=ticket_id, is_internal=False).order_by(TicketComment.created_at).all()
    else:
        comments = TicketComment.query.filter_by(ticket_id=ticket_id).order_by(TicketComment.created_at).all()
    
    # CORREÇÃO: Verificar se resolution_notes não é None antes de concatenar
    resolution_notes = ticket.resolution_notes or ""
    pending_reason = ticket.pending_reason or ""
    
    detail_html = f'''
    <!DOCTYPE html>
    <html lang="pt-BR">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Ticket {ticket.number} - {config.company_name}</title>
        <style>
            * {{ margin: 0; padding: 0; box-sizing: border-box; font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; }}
            body {{ background: linear-gradient(135deg, #0c0c0c 0%, #1a1a2e 50%, #16213e 100%); min-height: 100vh; color: white; }}
            .header {{ background: rgba(255, 255, 255, 0.05); backdrop-filter: blur(20px); border-bottom: 1px solid rgba(255, 255, 255, 0.1); padding: 20px 40px; }}
            .header-content {{ display: flex; justify-content: space-between; align-items: center; max-width: 1000px; margin: 0 auto; }}
            .btn {{ background: {config.primary_color}; color: white; padding: 10px 20px; border: none; border-radius: 8px; cursor: pointer; text-decoration: none; display: inline-block; }}
            .main-container {{ max-width: 1000px; margin: 0 auto; padding: 40px; }}
            .card {{ background: rgba(255, 255, 255, 0.05); border: 1px solid rgba(255, 255, 255, 0.1); border-radius: 15px; padding: 25px; margin-bottom: 20px; }}
            .ticket-header {{ display: grid; grid-template-columns: 1fr 1fr; gap: 20px; margin-bottom: 20px; }}
            .ticket-info div {{ margin-bottom: 10px; }}
            .status-badge {{ padding: 5px 10px; border-radius: 5px; font-weight: bold; }}
            .priority-Low {{ background: #4CAF50; }} .priority-Medium {{ background: #FF9800; }} 
            .priority-High {{ background: #f44336; }} .priority-Critical {{ background: #9C27B0; }}
            .comments-section {{ margin-top: 30px; }}
            .comment {{ background: rgba(255,255,255,0.05); padding: 15px; border-radius: 10px; margin-bottom: 15px; }}
            .comment-header {{ display: flex; justify-content: space-between; margin-bottom: 10px; font-size: 14px; color: #ccc; }}
            .comment-internal {{ border-left: 3px solid #FF9800; background: rgba(255,152,0,0.1); }}
            .comment-form {{ margin-top: 20px; }}
            .form-group {{ margin-bottom: 15px; }}
            .form-group label {{ display: block; margin-bottom: 5px; color: white; }}
            .form-group textarea {{ width: 100%; padding: 10px; background: rgba(255,255,255,0.1); border: 1px solid rgba(255,255,255,0.3); border-radius: 5px; color: white; }}
            .btn-success {{ background: #4CAF50; }} .btn-warning {{ background: #FF9800; }} .btn-danger {{ background: #f44336; }}
            .attachment-section {{ background: rgba(255,255,255,0.1); padding: 15px; border-radius: 10px; margin-top: 15px; }}
            .user-response {{ background: rgba(76, 175, 80, 0.1); border: 1px solid #4CAF50; padding: 15px; border-radius: 10px; margin-top: 20px; }}
            .user-rejection {{ background: rgba(244, 67, 54, 0.1); border: 1px solid #f44336; padding: 15px; border-radius: 10px; margin-top: 20px; }}
        </style>
    </head>
    <body>
        <div class="header">
            <div class="header-content">
                <h1>Ticket {ticket.number}</h1>
                <div>
                    {'<a href="/ticket/' + str(ticket.id) + '/edit" class="btn btn-warning">✏️ Editar</a>' if u.role in ['analyst', 'admin'] else ''}
                    <a href="{'/admin/tickets' if u.role == 'admin' else '/analyst/tickets' if u.role == 'analyst' else '/user/dashboard'}" class="btn">← Voltar</a>
                </div>
            </div>
        </div>

        <div class="main-container">
            <div class="card">
                <div class="ticket-header">
                    <div class="ticket-info">
                        <div><strong>Título:</strong> {ticket.title}</div>
                        <div><strong>Status:</strong> <span class="status-badge">{ticket.status.replace('_', ' ').title()}</span></div>
                        <div><strong>Prioridade:</strong> <span class="status-badge priority-{ticket.priority}">{ticket.priority}</span></div>
                        <div><strong>Tipo:</strong> {'🚨 Incidente' if ticket.type == 'incident' else '📋 Solicitação'}</div>
                    </div>
                    <div class="ticket-info">
                        <div><strong>Criado em:</strong> {ticket.created_at.strftime('%d/%m/%Y %H:%M')}</div>
                        <div><strong>Atualizado em:</strong> {ticket.updated_at.strftime('%d/%m/%Y %H:%M')}</div>
                        <div><strong>Categoria:</strong> {ticket.category.name if ticket.category else 'N/A'}</div>
                        <div><strong>Subcategoria:</strong> {ticket.subcategory.name if ticket.subcategory else 'N/A'}</div>
                        <div><strong>Grupo:</strong> {ticket.group.name if ticket.group else 'Não atribuído'}</div>
                        <div><strong>Analista:</strong> {ticket.assignee.name if ticket.assignee else 'Não atribuído'}</div>
                    </div>
                </div>
                
                <div>
                    <h3>Descrição:</h3>
                    <p>{ticket.description}</p>
                </div>

                {('<div style="margin-top: 15px; padding: 10px; background: rgba(255,152,0,0.1); border-radius: 5px;"><strong>Motivo da Pendência:</strong><br>' + pending_reason + '</div>') if pending_reason else ''}
                
                {('<div style="margin-top: 15px; padding: 10px; background: rgba(76,175,80,0.1); border-radius: 5px;"><strong>Notas de Resolução:</strong><br>' + resolution_notes + '</div>') if resolution_notes and u.role == 'user' and ticket.status == 'resolved' else ''}
            </div>

            {('<div class="user-response"><h3>✅ Resolução Proposta</h3><p>' + resolution_notes + '</p><form method="post"><div class="form-group"><label>Motivo da rejeição (se aplicável):</label><textarea name="rejection_reason" rows="3" placeholder="Explique por que a solução não atende suas necessidades..."></textarea></div><div style="display: flex; gap: 10px; margin-top: 15px;"><button type="submit" name="action" value="accept" class="btn btn-success">✅ Aceitar Solução</button><button type="submit" name="action" value="reject" class="btn btn-danger">❌ Rejeitar Solução</button></div></form></div>') if u.role == 'user' and ticket.created_by == u.id and ticket.status == 'resolved' and ticket.user_accepted is None else ''}

            {('<div class="user-rejection"><h3>❌ Solução Rejeitada</h3><p><strong>Motivo:</strong> ' + (ticket.user_rejection_reason or "") + '</p></div>') if u.role in ['analyst', 'admin'] and ticket.user_accepted == False else ''}

            <div class="card comments-section">
                <h3>💬 Comentários e Interações</h3>
    '''
    
    if comments:
        for comment in comments:
            internal_class = 'comment-internal' if comment.is_internal else ''
            internal_badge = ' 🔒 Interno' if comment.is_internal else ''
            detail_html += f'''
                <div class="comment {internal_class}">
                    <div class="comment-header">
                        <span>{comment.user.name if comment.user else 'Sistema'}{internal_badge}</span>
                        <span>{comment.created_at.strftime('%d/%m/%Y %H:%M')}</span>
                    </div>
                    <div>{comment.content}</div>
                </div>
            '''
    else:
        detail_html += '<p style="color: #ccc;">Nenhum comentário ainda.</p>'
    
    if u.role in ['analyst', 'admin']:
        detail_html += f'''
                <div class="comment-form">
                    <h4>Adicionar Comentário</h4>
                    <form method="post" action="/ticket/{ticket.id}/comment" enctype="multipart/form-data">
                        <div class="form-group">
                            <textarea name="content" rows="4" placeholder="Digite seu comentário..." required></textarea>
                        </div>
                        <div class="form-group">
                            <label>
                                <input type="checkbox" name="is_internal" value="1"> 
                                Comentário interno (visível apenas para a equipe)
                            </label>
                        </div>
                        {('<div class="form-group"><label><input type="checkbox" name="mark_resolved" value="1"> Marcar como resolvido e enviar para aprovação do usuário</label><textarea name="resolution_notes" rows="3" placeholder="Descreva a solução aplicada..." style="margin-top: 10px;"></textarea></div>') if ticket.status in ['open', 'in_progress'] else ''}
                        <div class="attachment-section">
                            <label style="display: block; margin-bottom: 5px;">📎 Anexar Arquivo (Opcional):</label>
                            <input type="file" name="attachment" accept=".png,.jpg,.jpeg,.gif,.pdf,.doc,.docx,.txt,.xls,.xlsx,.csv" style="color: white;">
                            <div style="font-size: 12px; color: #ccc; margin-top: 5px;">
                                Tipos permitidos: PNG, JPG, GIF, PDF, DOC, TXT, XLS (Max: 16MB)
                            </div>
                        </div>
                        <button type="submit" class="btn btn-success">📤 Enviar Comentário</button>
                    </form>
                </div>
        '''
    
    detail_html += '''
            </div>
        </div>
    </body>
    </html>
    '''
    
    return detail_html

# CORREÇÃO 2: AJUSTAR CORES DOS CAMPOS DE SELEÇÃO
def apply_global_styles():
    return '''
    <style>
        /* CORREÇÃO: Ajustar cores dos campos de seleção para texto visível */
        select, input, textarea {
            color: white !important;
            background: rgba(255, 255, 255, 0.1) !important;
        }
        select option {
            background: #1a1a2e !important;
            color: white !important;
        }
        input::placeholder, textarea::placeholder {
            color: rgba(255, 255, 255, 0.5) !important;
        }
    </style>
    '''

# CORREÇÃO 3: EXPANDIR SISTEMA CAB COM MAIS FUNCIONALIDADES
@app.route('/cab/new', methods=['GET', 'POST'])
def cab_new_change():
    config = get_config()
    u = current_user()
    if not u or (not u.cab_access and u.role not in ['admin', 'analyst'] and not u.manager and not u.senior_manager): 
        flash('Acesso negado!', 'error')
        return redirect(url_for('login'))
    
    if request.method == 'POST':
        change = ChangeRequest(
            number=generate_change_number(),
            title=request.form['title'],
            description=request.form['description'],
            priority=request.form['priority'],
            impact=request.form['impact'],
            systems_affected=request.form['systems_affected'],
            implementation_date=datetime.strptime(request.form['implementation_date'], '%Y-%m-%d') if request.form['implementation_date'] else None,
            start_date=datetime.strptime(request.form['start_date'], '%Y-%m-%dT%H:%M') if request.form['start_date'] else None,
            end_date=datetime.strptime(request.form['end_date'], '%Y-%m-%dT%H:%M') if request.form['end_date'] else None,
            meeting_date=datetime.strptime(request.form['meeting_date'], '%Y-%m-%dT%H:%M') if request.form['meeting_date'] else None,
            created_by=u.id,
            status='draft'
        )
        db.session.add(change)
        db.session.commit()
        
        # Processar anexos
        if 'documents' in request.files:
            files = request.files.getlist('documents')
            for file in files:
                if file and file.filename != '' and allowed_file(file.filename):
                    filename = secure_filename(file.filename)
                    unique_filename = f"cab_{change.id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{filename}"
                    file_path = os.path.join(app.config['UPLOAD_FOLDER'], 'documents', unique_filename)
                    file.save(file_path)
                    
                    document = CABDocument(
                        change_request_id=change.id,
                        user_id=u.id,
                        filename=unique_filename,
                        original_filename=filename,
                        file_type=filename.rsplit('.', 1)[1].lower()
                    )
                    db.session.add(document)
        
        # Log da criação
        log = ChangeLog(
            change_request_id=change.id,
            user_id=u.id,
            action='created',
            details='Mudança criada como rascunho'
        )
        db.session.add(log)
        db.session.commit()
        
        flash('Mudança criada com sucesso!', 'success')
        return redirect('/cab/dashboard')
    
    global_styles = apply_global_styles()
    
    return f'''
    <!DOCTYPE html>
    <html lang="pt-BR">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Nova Mudança - CAB</title>
        {global_styles}
        <style>
            * {{ margin: 0; padding: 0; box-sizing: border-box; font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; }}
            body {{ background: linear-gradient(135deg, #0c0c0c 0%, #1a1a2e 50%, #16213e 100%); min-height: 100vh; color: white; }}
            .header {{ background: rgba(255, 255, 255, 0.05); backdrop-filter: blur(20px); border-bottom: 1px solid rgba(255, 255, 255, 0.1); padding: 20px 40px; }}
            .header-content {{ display: flex; justify-content: space-between; align-items: center; max-width: 1000px; margin: 0 auto; }}
            .btn {{ background: #9C27B0; color: white; padding: 10px 20px; border: none; border-radius: 8px; cursor: pointer; text-decoration: none; display: inline-block; }}
            .main-container {{ max-width: 1000px; margin: 0 auto; padding: 40px; }}
            .card {{ background: rgba(255, 255, 255, 0.05); border: 1px solid rgba(255, 255, 255, 0.1); border-radius: 15px; padding: 25px; }}
            .form-group {{ margin-bottom: 20px; }}
            .form-group label {{ display: block; margin-bottom: 8px; color: white; }}
            .form-group input, .form-group select, .form-group textarea {{ 
                width: 100%; padding: 12px; background: rgba(255, 255, 255, 0.1); 
                border: 1px solid rgba(255, 255, 255, 0.3); border-radius: 8px; 
                color: white; font-size: 16px;
            }}
            .form-group textarea {{ height: 150px; resize: vertical; }}
            .btn-success {{ background: #4CAF50; }}
            .form-grid {{ display: grid; grid-template-columns: 1fr 1fr; gap: 20px; }}
            .attachment-section {{ background: rgba(255,255,255,0.1); padding: 15px; border-radius: 10px; margin-top: 15px; }}
        </style>
    </head>
    <body>
        <div class="header">
            <div class="header-content">
                <h1>➕ Nova Mudança CAB</h1>
                <a href="/cab/dashboard" class="btn">← Voltar</a>
            </div>
        </div>

        <div class="main-container">
            <div class="card">
                <form method="post" enctype="multipart/form-data">
                    <div class="form-group">
                        <label>Título da Mudança:</label>
                        <input type="text" name="title" placeholder="Descreva brevemente a mudança" required>
                    </div>

                    <div class="form-group">
                        <label>Descrição Detalhada:</label>
                        <textarea name="description" placeholder="Descreva em detalhes a mudança, objetivos, justificativa e benefícios..." required></textarea>
                    </div>

                    <div class="form-group">
                        <label>Sistemas Afetados:</label>
                        <textarea name="systems_affected" placeholder="Liste todos os sistemas, aplicações ou processos que serão afetados..." required></textarea>
                    </div>

                    <div class="form-grid">
                        <div class="form-group">
                            <label>Prioridade:</label>
                            <select name="priority" required>
                                <option value="Low">🟢 Baixa</option>
                                <option value="Medium" selected>🟡 Média</option>
                                <option value="High">🟠 Alta</option>
                                <option value="Critical">🔴 Crítica</option>
                            </select>
                        </div>

                        <div class="form-group">
                            <label>Impacto:</label>
                            <select name="impact" required>
                                <option value="Low">🟢 Baixo</option>
                                <option value="Medium" selected>🟡 Médio</option>
                                <option value="High">🟠 Alto</option>
                                <option value="Critical">🔴 Crítico</option>
                            </select>
                        </div>
                    </div>

                    <div class="form-grid">
                        <div class="form-group">
                            <label>Data de Implementação Prevista:</label>
                            <input type="date" name="implementation_date">
                        </div>
                        
                        <div class="form-group">
                            <label>Data e Hora da Reunião CAB:</label>
                            <input type="datetime-local" name="meeting_date">
                        </div>
                    </div>

                    <div class="form-grid">
                        <div class="form-group">
                            <label>Início da Execução:</label>
                            <input type="datetime-local" name="start_date">
                        </div>

                        <div class="form-group">
                            <label>Término da Execução:</label>
                            <input type="datetime-local" name="end_date">
                        </div>
                    </div>

                    <div class="attachment-section">
                        <h4>📎 Anexar Documentos (Opcional)</h4>
                        <input type="file" name="documents" multiple accept=".png,.jpg,.jpeg,.gif,.pdf,.doc,.docx,.txt,.xls,.xlsx,.csv">
                        <div style="font-size: 12px; color: #ccc; margin-top: 5px;">
                            Tipos permitidos: PNG, JPG, GIF, PDF, DOC, TXT, XLS (Max: 16MB cada)
                        </div>
                    </div>

                    <button type="submit" class="btn btn-success" style="width: 100%; padding: 15px; font-size: 16px; margin-top: 20px;">
                        💾 Salvar Mudança
                    </button>
                </form>
            </div>
        </div>
    </body>
    </html>
    '''

@app.route('/cab/change/<int:change_id>')
def cab_change_detail(change_id):
    config = get_config()
    u = current_user()
    if not u or (not u.cab_access and u.role not in ['admin', 'analyst'] and not u.manager and not u.senior_manager): 
        flash('Acesso negado!', 'error')
        return redirect(url_for('login'))
    
    change = ChangeRequest.query.get_or_404(change_id)
    creator = User.query.get(change.created_by)
    comments = CABComment.query.filter_by(change_request_id=change_id).order_by(CABComment.created_at).all()
    logs = ChangeLog.query.filter_by(change_request_id=change_id).order_by(ChangeLog.created_at).all()
    documents = CABDocument.query.filter_by(change_request_id=change_id).order_by(CABDocument.uploaded_at).all()
    
    global_styles = apply_global_styles()
    
    detail_html = f'''
    <!DOCTYPE html>
    <html lang="pt-BR">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Mudança {change.number} - CAB</title>
        {global_styles}
        <style>
            * {{ margin: 0; padding: 0; box-sizing: border-box; font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; }}
            body {{ background: linear-gradient(135deg, #0c0c0c 0%, #1a1a2e 50%, #16213e 100%); min-height: 100vh; color: white; }}
            .header {{ background: rgba(255, 255, 255, 0.05); backdrop-filter: blur(20px); border-bottom: 1px solid rgba(255, 255, 255, 0.1); padding: 20px 40px; }}
            .header-content {{ display: flex; justify-content: space-between; align-items: center; max-width: 1200px; margin: 0 auto; }}
            .btn {{ background: #9C27B0; color: white; padding: 10px 20px; border: none; border-radius: 8px; cursor: pointer; text-decoration: none; display: inline-block; }}
            .main-container {{ max-width: 1200px; margin: 0 auto; padding: 40px; }}
            .card {{ background: rgba(255, 255, 255, 0.05); border: 1px solid rgba(255, 255, 255, 0.1); border-radius: 15px; padding: 25px; margin-bottom: 20px; }}
            .change-header {{ display: grid; grid-template-columns: 1fr 1fr; gap: 20px; margin-bottom: 20px; }}
            .change-info div {{ margin-bottom: 10px; }}
            .status-badge {{ padding: 5px 10px; border-radius: 5px; font-weight: bold; }}
            .priority-Low {{ background: #4CAF50; }} .priority-Medium {{ background: #FF9800; }} 
            .priority-High {{ background: #f44336; }} .priority-Critical {{ background: #9C27B0; }}
            .impact-Low {{ background: #4CAF50; }} .impact-Medium {{ background: #FF9800; }} 
            .impact-High {{ background: #f44336; }} .impact-Critical {{ background: #9C27B0; }}
            .comments-section {{ margin-top: 30px; }}
            .comment {{ background: rgba(255,255,255,0.05); padding: 15px; border-radius: 10px; margin-bottom: 15px; }}
            .comment-header {{ display: flex; justify-content: space-between; margin-bottom: 10px; font-size: 14px; color: #ccc; }}
            .comment-form {{ margin-top: 20px; }}
            .form-group {{ margin-bottom: 15px; }}
            .form-group label {{ display: block; margin-bottom: 5px; color: white; }}
            .form-group textarea {{ width: 100%; padding: 10px; background: rgba(255,255,255,0.1); border: 1px solid rgba(255,255,255,0.3); border-radius: 5px; color: white; }}
            .btn-success {{ background: #4CAF50; }} .btn-danger {{ background: #f44336; }} .btn-warning {{ background: #FF9800; }}
            .action-buttons {{ display: flex; gap: 10px; margin-top: 20px; }}
            .documents-section {{ background: rgba(255,255,255,0.1); padding: 15px; border-radius: 10px; margin-top: 15px; }}
            .document-item {{ background: rgba(255,255,255,0.05); padding: 10px; margin: 5px 0; border-radius: 5px; display: flex; justify-content: space-between; align-items: center; }}
            .document-info {{ display: flex; align-items: center; gap: 10px; }}
            .document-icon {{ font-size: 20px; }}
            .timeline-grid {{ display: grid; grid-template-columns: 1fr 1fr; gap: 20px; margin: 20px 0; }}
            .timeline-item {{ background: rgba(255,255,255,0.05); padding: 15px; border-radius: 10px; }}
        </style>
    </head>
    <body>
        <div class="header">
            <div class="header-content">
                <h1>Mudança {change.number}</h1>
                <a href="/cab/dashboard" class="btn">← Voltar</a>
            </div>
        </div>

        <div class="main-container">
            <div class="card">
                <div class="change-header">
                    <div class="change-info">
                        <div><strong>Título:</strong> {change.title}</div>
                        <div><strong>Status:</strong> <span class="status-badge">{change.status.replace('_', ' ').title()}</span></div>
                        <div><strong>Prioridade:</strong> <span class="status-badge priority-{change.priority}">{change.priority}</span></div>
                        <div><strong>Impacto:</strong> <span class="status-badge impact-{change.impact}">{change.impact}</span></div>
                    </div>
                    <div class="change-info">
                        <div><strong>Criado por:</strong> {creator.name if creator else 'N/A'}</div>
                        <div><strong>Data de Criação:</strong> {change.created_at.strftime('%d/%m/%Y %H:%M')}</div>
                        <div><strong>Última Atualização:</strong> {change.updated_at.strftime('%d/%m/%Y %H:%M')}</div>
                        <div><strong>Data de Implementação:</strong> {change.implementation_date.strftime('%d/%m/%Y') if change.implementation_date else 'Não definida'}</div>
                    </div>
                </div>
                
                <div class="timeline-grid">
                    <div class="timeline-item">
                        <strong>📅 Reunião CAB:</strong><br>
                        {change.meeting_date.strftime('%d/%m/%Y %H:%M') if change.meeting_date else 'Não agendada'}
                    </div>
                    <div class="timeline-item">
                        <strong>⏰ Execução:</strong><br>
                        {f"{change.start_date.strftime('%d/%m/%Y %H:%M')} - {change.end_date.strftime('%d/%m/%Y %H:%M')}" if change.start_date and change.end_date else 'Não definida'}
                    </div>
                </div>
                
                <div style="margin-bottom: 20px;">
                    <h3>Descrição:</h3>
                    <p>{change.description}</p>
                </div>

                <div>
                    <h3>Sistemas Afetados:</h3>
                    <p>{change.systems_affected}</p>
                </div>

                {('<div class="action-buttons"><a href="/cab/change/' + str(change.id) + '/submit" class="btn btn-success">📤 Enviar para Aprovação</a><a href="/cab/change/' + str(change.id) + '/edit" class="btn btn-warning">✏️ Editar</a></div>') if change.status == 'draft' and change.created_by == u.id else ''}

                {('<div class="action-buttons"><a href="/cab/change/' + str(change.id) + '/approve" class="btn btn-success">✅ Aprovar</a><a href="/cab/change/' + str(change.id) + '/reject" class="btn btn-danger">❌ Rejeitar</a></div>') if change.status == 'pending_approval' and (u.cab_access or u.role in ['admin', 'analyst'] or u.manager or u.senior_manager) else ''}
            </div>

            {('<div class="card documents-section"><h3>📁 Documentos Anexados</h3>' + 
            ''.join([f'<div class="document-item"><div class="document-info"><span class="document-icon">📄</span><span>{doc.original_filename}</span></div><a href="/download/cab_document/{doc.id}" class="btn">📥 Baixar</a></div>' for doc in documents]) + 
            '</div>') if documents else ''}

            <div class="card comments-section">
                <h3>💬 Comentários e Avaliações de Risco</h3>
    '''
    
    if comments:
        for comment in comments:
            detail_html += f'''
                <div class="comment">
                    <div class="comment-header">
                        <span>{comment.user.name if comment.user else 'N/A'}</span>
                        <span>{comment.created_at.strftime('%d/%m/%Y %H:%M')}</span>
                    </div>
                    <div>{comment.content}</div>
                    {('<div style="margin-top: 10px; padding: 10px; background: rgba(255,152,0,0.1); border-radius: 5px;"><strong>Avaliação de Risco:</strong><br>' + comment.risk_assessment + '</div>') if comment.risk_assessment else ''}
                </div>
            '''
    else:
        detail_html += '<p style="color: #ccc;">Nenhum comentário ainda.</p>'
    
    if change.status == 'pending_approval' and (u.cab_access or u.role in ['admin', 'analyst'] or u.manager or u.senior_manager):
        detail_html += f'''
                <div class="comment-form">
                    <h4>Adicionar Comentário/Avaliação</h4>
                    <form method="post" action="/cab/change/{change.id}/comment">
                        <div class="form-group">
                            <textarea name="content" rows="4" placeholder="Digite seu comentário..." required></textarea>
                        </div>
                        <div class="form-group">
                            <label>Avaliação de Risco (opcional):</label>
                            <textarea name="risk_assessment" rows="3" placeholder="Avalie os riscos associados a esta mudança..."></textarea>
                        </div>
                        <button type="submit" class="btn btn-success">📤 Enviar Comentário</button>
                    </form>
                </div>
        '''
    
    detail_html += '''
            </div>

            <div class="card">
                <h3>📋 Histórico de Atividades</h3>
    '''
    
    if logs:
        for log in logs:
            user = User.query.get(log.user_id)
            detail_html += f'''
                <div class="comment">
                    <div class="comment-header">
                        <span>{user.name if user else 'Sistema'}</span>
                        <span>{log.created_at.strftime('%d/%m/%Y %H:%M')}</span>
                    </div>
                    <div><strong>{log.action.replace('_', ' ').title()}</strong> - {log.details}</div>
                </div>
            '''
    else:
        detail_html += '<p style="color: #ccc;">Nenhuma atividade registrada.</p>'
    
    detail_html += '''
            </div>
        </div>
    </body>
    </html>
    '''
    
    return detail_html

@app.route('/download/cab_document/<int:doc_id>')
def download_cab_document(doc_id):
    u = current_user()
    if not u or (not u.cab_access and u.role not in ['admin', 'analyst'] and not u.manager and not u.senior_manager): 
        flash('Acesso negado!', 'error')
        return redirect(url_for('login'))
    
    document = CABDocument.query.get(doc_id)
    if not document:
        flash('Documento não encontrado!', 'error')
        return redirect(url_for('cab_dashboard'))
    
    file_path = os.path.join(app.config['UPLOAD_FOLDER'], 'documents', document.filename)
    
    if os.path.exists(file_path):
        return send_file(
            file_path,
            as_attachment=True,
            download_name=document.original_filename
        )
    else:
        flash('Arquivo não encontrado!', 'error')
        return redirect(url_for('cab_dashboard'))

# ADICIONAR ROTA PARA EDIÇÃO DE MUDANÇA CAB
@app.route('/cab/change/<int:change_id>/edit', methods=['GET', 'POST'])
def cab_edit_change(change_id):
    config = get_config()
    u = current_user()
    if not u or (not u.cab_access and u.role not in ['admin', 'analyst'] and not u.manager and not u.senior_manager): 
        flash('Acesso negado!', 'error')
        return redirect(url_for('login'))
    
    change = ChangeRequest.query.get_or_404(change_id)
    
    if change.created_by != u.id and u.role not in ['admin']:
        flash('Acesso negado!', 'error')
        return redirect('/cab/dashboard')
    
    if request.method == 'POST':
        change.title = request.form['title']
        change.description = request.form['description']
        change.priority = request.form['priority']
        change.impact = request.form['impact']
        change.systems_affected = request.form['systems_affected']
        change.implementation_date = datetime.strptime(request.form['implementation_date'], '%Y-%m-%d') if request.form['implementation_date'] else None
        change.start_date = datetime.strptime(request.form['start_date'], '%Y-%m-%dT%H:%M') if request.form['start_date'] else None
        change.end_date = datetime.strptime(request.form['end_date'], '%Y-%m-%dT%H:%M') if request.form['end_date'] else None
        change.meeting_date = datetime.strptime(request.form['meeting_date'], '%Y-%m-%dT%H:%M') if request.form['meeting_date'] else None
        
        # Processar novos anexos
        if 'documents' in request.files:
            files = request.files.getlist('documents')
            for file in files:
                if file and file.filename != '' and allowed_file(file.filename):
                    filename = secure_filename(file.filename)
                    unique_filename = f"cab_{change.id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{filename}"
                    file_path = os.path.join(app.config['UPLOAD_FOLDER'], 'documents', unique_filename)
                    file.save(file_path)
                    
                    document = CABDocument(
                        change_request_id=change.id,
                        user_id=u.id,
                        filename=unique_filename,
                        original_filename=filename,
                        file_type=filename.rsplit('.', 1)[1].lower()
                    )
                    db.session.add(document)
        
        # Log da edição
        log = ChangeLog(
            change_request_id=change.id,
            user_id=u.id,
            action='updated',
            details='Mudança atualizada'
        )
        db.session.add(log)
        db.session.commit()
        
        flash('Mudança atualizada com sucesso!', 'success')
        return redirect(f'/cab/change/{change_id}')
    
    global_styles = apply_global_styles()
    
    # Format dates for form inputs
    implementation_date = change.implementation_date.strftime('%Y-%m-%d') if change.implementation_date else ''
    start_date = change.start_date.strftime('%Y-%m-%dT%H:%M') if change.start_date else ''
    end_date = change.end_date.strftime('%Y-%m-%dT%H:%M') if change.end_date else ''
    meeting_date = change.meeting_date.strftime('%Y-%m-%dT%H:%M') if change.meeting_date else ''
    
    documents = CABDocument.query.filter_by(change_request_id=change_id).all()
    
    return f'''
    <!DOCTYPE html>
    <html lang="pt-BR">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Editar Mudança {change.number} - CAB</title>
        {global_styles}
        <style>
            * {{ margin: 0; padding: 0; box-sizing: border-box; font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; }}
            body {{ background: linear-gradient(135deg, #0c0c0c 0%, #1a1a2e 50%, #16213e 100%); min-height: 100vh; color: white; }}
            .header {{ background: rgba(255, 255, 255, 0.05); backdrop-filter: blur(20px); border-bottom: 1px solid rgba(255, 255, 255, 0.1); padding: 20px 40px; }}
            .header-content {{ display: flex; justify-content: space-between; align-items: center; max-width: 1000px; margin: 0 auto; }}
            .btn {{ background: #9C27B0; color: white; padding: 10px 20px; border: none; border-radius: 8px; cursor: pointer; text-decoration: none; display: inline-block; }}
            .main-container {{ max-width: 1000px; margin: 0 auto; padding: 40px; }}
            .card {{ background: rgba(255, 255, 255, 0.05); border: 1px solid rgba(255, 255, 255, 0.1); border-radius: 15px; padding: 25px; }}
            .form-group {{ margin-bottom: 20px; }}
            .form-group label {{ display: block; margin-bottom: 8px; color: white; }}
            .form-group input, .form-group select, .form-group textarea {{ 
                width: 100%; padding: 12px; background: rgba(255, 255, 255, 0.1); 
                border: 1px solid rgba(255, 255, 255, 0.3); border-radius: 8px; 
                color: white; font-size: 16px;
            }}
            .form-group textarea {{ height: 150px; resize: vertical; }}
            .btn-success {{ background: #4CAF50; }}
            .form-grid {{ display: grid; grid-template-columns: 1fr 1fr; gap: 20px; }}
            .attachment-section {{ background: rgba(255,255,255,0.1); padding: 15px; border-radius: 10px; margin-top: 15px; }}
            .document-item {{ background: rgba(255,255,255,0.05); padding: 10px; margin: 5px 0; border-radius: 5px; display: flex; justify-content: space-between; align-items: center; }}
        </style>
    </head>
    <body>
        <div class="header">
            <div class="header-content">
                <h1>✏️ Editar Mudança {change.number}</h1>
                <a href="/cab/change/{change.id}" class="btn">← Voltar</a>
            </div>
        </div>

        <div class="main-container">
            <div class="card">
                <form method="post" enctype="multipart/form-data">
                    <div class="form-group">
                        <label>Título da Mudança:</label>
                        <input type="text" name="title" value="{change.title}" required>
                    </div>

                    <div class="form-group">
                        <label>Descrição Detalhada:</label>
                        <textarea name="description" required>{change.description}</textarea>
                    </div>

                    <div class="form-group">
                        <label>Sistemas Afetados:</label>
                        <textarea name="systems_affected" required>{change.systems_affected}</textarea>
                    </div>

                    <div class="form-grid">
                        <div class="form-group">
                            <label>Prioridade:</label>
                            <select name="priority" required>
                                <option value="Low" {'selected' if change.priority == 'Low' else ''}>🟢 Baixa</option>
                                <option value="Medium" {'selected' if change.priority == 'Medium' else ''}>🟡 Média</option>
                                <option value="High" {'selected' if change.priority == 'High' else ''}>🟠 Alta</option>
                                <option value="Critical" {'selected' if change.priority == 'Critical' else ''}>🔴 Crítica</option>
                            </select>
                        </div>

                        <div class="form-group">
                            <label>Impacto:</label>
                            <select name="impact" required>
                                <option value="Low" {'selected' if change.impact == 'Low' else ''}>🟢 Baixo</option>
                                <option value="Medium" {'selected' if change.impact == 'Medium' else ''}>🟡 Médio</option>
                                <option value="High" {'selected' if change.impact == 'High' else ''}>🟠 Alto</option>
                                <option value="Critical" {'selected' if change.impact == 'Critical' else ''}>🔴 Crítico</option>
                            </select>
                        </div>
                    </div>

                    <div class="form-grid">
                        <div class="form-group">
                            <label>Data de Implementação Prevista:</label>
                            <input type="date" name="implementation_date" value="{implementation_date}">
                        </div>
                        
                        <div class="form-group">
                            <label>Data e Hora da Reunião CAB:</label>
                            <input type="datetime-local" name="meeting_date" value="{meeting_date}">
                        </div>
                    </div>

                    <div class="form-grid">
                        <div class="form-group">
                            <label>Início da Execução:</label>
                            <input type="datetime-local" name="start_date" value="{start_date}">
                        </div>

                        <div class="form-group">
                            <label>Término da Execução:</label>
                            <input type="datetime-local" name="end_date" value="{end_date}">
                        </div>
                    </div>

                    {('<div class="attachment-section"><h4>📎 Documentos Existentes</h4>' + 
                    ''.join([f'<div class="document-item"><span>{doc.original_filename}</span><a href="/download/cab_document/{doc.id}" class="btn">📥 Baixar</a></div>' for doc in documents]) + 
                    '</div>') if documents else ''}

                    <div class="attachment-section">
                        <h4>📎 Adicionar Novos Documentos (Opcional)</h4>
                        <input type="file" name="documents" multiple accept=".png,.jpg,.jpeg,.gif,.pdf,.doc,.docx,.txt,.xls,.xlsx,.csv">
                        <div style="font-size: 12px; color: #ccc; margin-top: 5px;">
                            Tipos permitidos: PNG, JPG, GIF, PDF, DOC, TXT, XLS (Max: 16MB cada)
                        </div>
                    </div>

                    <button type="submit" class="btn btn-success" style="width: 100%; padding: 15px; font-size: 16px; margin-top: 20px;">
                        💾 Atualizar Mudança
                    </button>
                </form>
            </div>
        </div>
    </body>
    </html>
    '''

# ADICIONAR AS ROTAS RESTANTES DO SISTEMA ORIGINAL AQUI...
# [Todas as outras rotas do sistema original permanecem as mesmas]

# PAINEL DO GERENTE APROVADOR - ATUALIZADO
@app.route('/manager/dashboard')
def manager_dashboard():
    config = get_config()
    u = current_user()
    if not u or (not u.manager and not u.senior_manager): 
        flash('Acesso negado!', 'error')
        return redirect(url_for('login'))
    
    if u.manager:
        pending_tickets = Ticket.query.join(User, Ticket.created_by == User.id)\
            .filter(Ticket.status == 'pending_approval', User.manager_id == u.id).all()
    elif u.senior_manager:
        pending_tickets = Ticket.query.join(User, Ticket.created_by == User.id)\
            .filter(Ticket.status == 'pending_approval', User.senior_manager_id == u.id).all()
    else:
        pending_tickets = []
    
    user_tickets = Ticket.query.filter_by(created_by=u.id).order_by(Ticket.created_at.desc()).all()
    open_tickets = [t for t in user_tickets if t.status in ['open', 'in_progress', 'pending_approval']]
    
    # Mudanças CAB pendentes
    pending_changes = ChangeRequest.query.filter_by(status='pending_approval').all()
    
    global_styles = apply_global_styles()
    
    manager_html = f'''
    <!DOCTYPE html>
    <html lang="pt-BR">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>{config.company_name} - Painel do Gerente</title>
        {global_styles}
        <style>
            * {{ margin: 0; padding: 0; box-sizing: border-box; font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; }}
            body {{ background: linear-gradient(135deg, #0c0c0c 0%, #1a1a2e 50%, #16213e 100%); min-height: 100vh; color: white; }}
            .header {{ background: rgba(255, 255, 255, 0.05); backdrop-filter: blur(20px); border-bottom: 1px solid rgba(255, 255, 255, 0.1); padding: 20px 40px; }}
            .header-content {{ display: flex; justify-content: space-between; align-items: center; max-width: 1200px; margin: 0 auto; }}
            .logo-text h1 {{ font-size: 24px; font-weight: 300; }}
            .btn {{ background: {config.primary_color}; color: white; padding: 10px 20px; border: none; border-radius: 8px; cursor: pointer; text-decoration: none; display: inline-block; }}
            .main-container {{ max-width: 1200px; margin: 0 auto; padding: 40px; }}
            .card {{ background: rgba(255, 255, 255, 0.05); border: 1px solid rgba(255, 255, 255, 0.1); border-radius: 15px; padding: 25px; margin-bottom: 20px; }}
            .ticket-list {{ display: grid; gap: 15px; }}
            .ticket-item {{ background: rgba(255, 255, 255, 0.05); border: 1px solid rgba(255, 255, 255, 0.1); border-radius: 10px; padding: 15px; }}
            .ticket-header {{ display: flex; justify-content: space-between; margin-bottom: 10px; }}
            .ticket-number {{ font-weight: bold; color: {config.primary_color}; }}
            .btn-success {{ background: #4CAF50; }} .btn-danger {{ background: #f44336; }}
            .nav-tabs {{ display: flex; gap: 10px; margin-bottom: 20px; }}
            .tab-btn {{ padding: 10px 20px; background: rgba(255,255,255,0.1); border: none; border-radius: 5px; color: white; cursor: pointer; }}
            .tab-btn.active {{ background: {config.primary_color}; }}
            .tab-content {{ display: none; }}
            .tab-content.active {{ display: block; }}
            .stats-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 20px; margin-bottom: 40px; }}
            .stat-card {{ background: rgba(255, 255, 255, 0.05); border: 1px solid rgba(255, 255, 255, 0.1); border-radius: 15px; padding: 20px; text-align: center; }}
            .stat-number {{ font-size: 32px; font-weight: bold; margin: 10px 0; }}
            .ticket-status {{ padding: 4px 8px; border-radius: 4px; font-size: 12px; }}
            .status-open {{ background: #FF9800; }} .status-in_progress {{ background: #2196F3; }} .status-pending_approval {{ background: #9C27B0; }} .status-resolved {{ background: #4CAF50; }}
        </style>
    </head>
    <body>
        <div class="header">
            <div class="header-content">
                <div class="logo-text"><h1>👨‍💼 Painel do Gerente - {config.company_name}</h1></div>
                <div>
                    <a href="/user/chat" class="btn">💬 Chat</a>
                    <a href="/cab/dashboard" class="btn" style="background: #9C27B0;">📋 CAB</a>
                    <a href="/logout" class="btn" style="background: #ff6b6b;">🚪 Sair</a>
                </div>
            </div>
        </div>

        <div class="main-container">
            <div class="stats-grid">
                <div class="stat-card">
                    <div>📋</div>
                    <div class="stat-number">{len(pending_tickets)}</div>
                    <div>Aprovações Pendentes</div>
                </div>
                <div class="stat-card">
                    <div>🎫</div>
                    <div class="stat-number">{len(user_tickets)}</div>
                    <div>Meus Tickets</div>
                </div>
                <div class="stat-card">
                    <div>⏳</div>
                    <div class="stat-number">{len(open_tickets)}</div>
                    <div>Em Aberto</div>
                </div>
                <div class="stat-card">
                    <div>📊</div>
                    <div class="stat-number">{len(pending_changes)}</div>
                    <div>Mudanças CAB</div>
                </div>
            </div>

            <div class="nav-tabs">
                <button class="tab-btn active" onclick="openTab('tab-approvals')">📋 Aprovações Pendentes ({len(pending_tickets)})</button>
                <button class="tab-btn" onclick="openTab('tab-my-tickets')">🎫 Meus Tickets ({len(user_tickets)})</button>
                <button class="tab-btn" onclick="openTab('tab-chat')">💬 Chat</button>
                <button class="tab-btn" onclick="openTab('tab-cab')">📋 CAB ({len(pending_changes)})</button>
            </div>

            <div id="tab-approvals" class="tab-content active">
                <div class="card">
                    <h2>📋 Tickets Aguardando Aprovação ({len(pending_tickets)})</h2>
                    <div class="ticket-list">
    '''
    
    if pending_tickets:
        for ticket in pending_tickets:
            creator = User.query.get(ticket.created_by)
            manager_html += f'''
                        <div class="ticket-item">
                            <div class="ticket-header">
                                <span class="ticket-number">{ticket.number}</span>
                                <span style="color: #FF9800;">⏳ Aguardando Aprovação</span>
                            </div>
                            <div><strong>{ticket.title}</strong></div>
                            <div style="font-size: 14px; color: #ccc; margin-top: 5px;">
                                Criado por: {creator.name if creator else 'N/A'} | 
                                Data: {ticket.created_at.strftime('%d/%m/%Y %H:%M')} | 
                                Categoria: {ticket.category.name if ticket.category else 'N/A'}
                            </div>
                            <div style="margin-top: 10px;">
                                <a href="/manager/ticket/{ticket.id}" class="btn">👁️ Ver Detalhes</a>
                            </div>
                        </div>
            '''
    else:
        manager_html += '<p>Nenhum ticket aguardando aprovação.</p>'
    
    manager_html += f'''
                    </div>
                </div>
            </div>

            <div id="tab-my-tickets" class="tab-content">
                <div class="card">
                    <div class="card-header">
                        <h3>🎫 Meus Tickets</h3>
                        <a href="/user/tickets/new" class="btn btn-success">➕ Novo Ticket</a>
                    </div>
                    <div class="ticket-list">
    '''
    
    if not user_tickets:
        manager_html += '<p style="color: #ccc;">Nenhum ticket encontrado</p>'
    else:
        for ticket in user_tickets:
            status_class = f"status-{ticket.status}"
            manager_html += f'''
                        <div class="ticket-item">
                            <div class="ticket-header">
                                <span class="ticket-number">{ticket.number}</span>
                                <span class="ticket-status {status_class}">{ticket.status.replace('_', ' ').title()}</span>
                            </div>
                            <div><strong>{ticket.title}</strong></div>
                            <div style="font-size: 14px; color: #ccc; margin-top: 5px;">
                                Criado em: {ticket.created_at.strftime('%d/%m/%Y %H:%M')} | 
                                Prioridade: {ticket.priority} |
                                Status: {ticket.status.replace('_', ' ').title()}
                            </div>
                            <div style="margin-top: 10px;">
                                <a href="/ticket/{ticket.id}" class="btn">👁️ Ver Detalhes</a>
                            </div>
                        </div>
            '''
    
    manager_html += f'''
                    </div>
                </div>
            </div>

            <div id="tab-chat" class="tab-content">
                <div class="card">
                    <div class="card-header">
                        <h3>💬 Chat de Atendimento</h3>
                        <a href="/user/chat" class="btn btn-success">💬 Acessar Chat</a>
                    </div>
                    <div class="card-content">
                        <p>Use o sistema de chat para comunicação direta com a equipe de suporte.</p>
                        <p>Clique no botão acima para acessar o chat.</p>
                    </div>
                </div>
            </div>

            <div id="tab-cab" class="tab-content">
                <div class="card">
                    <div class="card-header">
                        <h3>📋 Mudanças CAB Pendentes ({len(pending_changes)})</h3>
                        <a href="/cab/dashboard" class="btn btn-success">📋 Ver Todas</a>
                    </div>
                    <div class="ticket-list">
    '''
    
    if pending_changes:
        for change in pending_changes:
            creator = User.query.get(change.created_by)
            manager_html += f'''
                        <div class="ticket-item">
                            <div class="ticket-header">
                                <span class="ticket-number">{change.number}</span>
                                <span style="color: #FF9800;">⏳ Aguardando Aprovação</span>
                            </div>
                            <div><strong>{change.title}</strong></div>
                            <div style="font-size: 14px; color: #ccc; margin-top: 5px;">
                                Criado por: {creator.name if creator else 'N/A'} | 
                                Data: {change.created_at.strftime('%d/%m/%Y %H:%M')} | 
                                Prioridade: {change.priority}
                            </div>
                            <div style="margin-top: 10px;">
                                <a href="/cab/change/{change.id}" class="btn">👁️ Ver Detalhes</a>
                            </div>
                        </div>
            '''
    else:
        manager_html += '<p style="color: #ccc;">Nenhuma mudança pendente de aprovação.</p>'
    
    manager_html += f'''
                    </div>
                </div>
            </div>
        </div>

        <script>
            function openTab(tabName) {{
                document.querySelectorAll('.tab-content').forEach(tab => {{
                    tab.classList.remove('active');
                }});
                document.querySelectorAll('.tab-btn').forEach(btn => {{
                    btn.classList.remove('active');
                }});
                document.getElementById(tabName).classList.add('active');
                event.currentTarget.classList.add('active');
            }}
        </script>
    </body>
    </html>
    '''
    
    return manager_html
# ROTAS RESTANTES DO SISTEMA COMPLETO

# PAINEL DO ADMIN - ATUALIZADO
@app.route('/admin')
def admin_panel():
    config = get_config()
    u = current_user()
    if not u or u.role != 'admin': 
        flash('Acesso negado!', 'error')
        return redirect(url_for('login'))
    
    online_analysts = User.query.filter_by(role='analyst', online=True).count()
    waiting_count = Session.query.filter_by(status='waiting').count()
    total_users = User.query.count()
    open_tickets = Ticket.query.filter_by(status='open').count()
    in_progress_tickets = Ticket.query.filter_by(status='in_progress').count()
    pending_approval_tickets = Ticket.query.filter_by(status='pending_approval').count()
    total_tickets = Ticket.query.count()
    
    groups = SupportGroup.query.all()
    categories = TicketCategory.query.all()
    rules = RoutingRule.query.all()
    users = User.query.all()
    chat_categories = Category.query.all()
    managers = User.query.filter((User.manager == True) | (User.senior_manager == True)).all()
    
    finished = Session.query.filter_by(status='finished').all()
    total_time = sum((s.finished_at - s.assigned_at).total_seconds() for s in finished if s.assigned_at and s.finished_at)
    avg_time = int(total_time / len(finished)) if finished else 0
    
    waiting = Session.query.filter_by(status='waiting').order_by(Session.created_at).all()
    queue = [(i+1, s) for i, s in enumerate(waiting)]
    
    global_styles = apply_global_styles()
    
    admin_html = f'''
    <!DOCTYPE html>
    <html lang="pt-BR">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>{config.company_name} - Admin</title>
        {global_styles}
        <style>
            * {{ margin: 0; padding: 0; box-sizing: border-box; font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; }}
            body {{ background: linear-gradient(135deg, #0c0c0c 0%, #1a1a2e 50%, #16213e 100%); min-height: 100vh; color: white; position: relative; overflow-x: hidden; }}
            body::before {{ content: ''; position: absolute; top: 0; left: 0; right: 0; bottom: 0; background: radial-gradient(circle at 20% 80%, rgba(4, 103, 250, 0.1) 0%, transparent 50%), radial-gradient(circle at 80% 20%, rgba(33, 150, 243, 0.1) 0%, transparent 50%); }}
            .header {{ background: rgba(255, 255, 255, 0.05); backdrop-filter: blur(20px); border-bottom: 1px solid rgba(255, 255, 255, 0.1); padding: 20px 40px; position: relative; z-index: 10; }}
            .header-content {{ display: flex; justify-content: space-between; align-items: center; max-width: 1400px; margin: 0 auto; }}
            .logo-section {{ display: flex; align-items: center; gap: 15px; }}
            .logo-section img {{ width: 40px; height: 40px; border-radius: 10px; }}
            .logo-text h1 {{ font-size: 24px; font-weight: 300; background: linear-gradient(45deg, #fff, {config.primary_color}); -webkit-background-clip: text; -webkit-text-fill-color: transparent; }}
            .logo-text p {{ font-size: 12px; color: rgba(255, 255, 255, 0.7); }}
            .admin-actions {{ display: flex; gap: 15px; align-items: center; }}
            .admin-btn {{ background: linear-gradient(45deg, {config.primary_color}, {config.secondary_color}); color: white; padding: 10px 20px; border: none; border-radius: 8px; cursor: pointer; transition: all 0.3s ease; text-decoration: none; font-size: 14px; font-weight: 600; }}
            .admin-btn:hover {{ transform: translateY(-2px); box-shadow: 0 5px 15px {config.primary_color}60; }}
            .logout-btn {{ background: linear-gradient(45deg, #ff6b6b, #ee5a52); color: white; padding: 10px 20px; border: none; border-radius: 8px; cursor: pointer; transition: all 0.3s ease; text-decoration: none; font-size: 14px; }}
            .logout-btn:hover {{ transform: translateY(-2px); box-shadow: 0 5px 15px rgba(255, 107, 107, 0.4); }}
            .main-container {{ max-width: 1400px; margin: 0 auto; padding: 40px; position: relative; z-index: 2; }}
            .stats-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 20px; margin-bottom: 40px; }}
            .stat-card {{ background: rgba(255, 255, 255, 0.05); backdrop-filter: blur(20px); border: 1px solid rgba(255, 255, 255, 0.1); border-radius: 20px; padding: 30px; text-align: center; transition: all 0.3s ease; box-shadow: 0 20px 40px rgba(0, 0, 0, 0.3); }}
            .stat-card:hover {{ transform: translateY(-5px); border-color: {config.primary_color}; }}
            .stat-icon {{ font-size: 40px; margin-bottom: 15px; }}
            .stat-number {{ font-size: 32px; font-weight: 700; margin-bottom: 10px; background: linear-gradient(45deg, #fff, {config.primary_color}); -webkit-background-clip: text; -webkit-text-fill-color: transparent; }}
            .stat-label {{ color: rgba(255, 255, 255, 0.7); font-size: 14px; }}
            .dashboard-grid {{ display: grid; grid-template-columns: 2fr 1fr; gap: 30px; margin-bottom: 40px; }}
            .card {{ background: rgba(255, 255, 255, 0.05); backdrop-filter: blur(20px); border: 1px solid rgba(255, 255, 255, 0.1); border-radius: 20px; padding: 30px; box-shadow: 0 20px 40px rgba(0, 0, 0, 0.3); }}
            .card-header {{ display: flex; justify-content: space-between; align-items: center; margin-bottom: 25px; }}
            .card-header h3 {{ font-size: 20px; font-weight: 300; background: linear-gradient(45deg, #fff, {config.secondary_color}); -webkit-background-clip: text; -webkit-text-fill-color: transparent; }}
            .card-content {{ max-height: 400px; overflow-y: auto; }}
            .queue-list {{ display: grid; gap: 15px; }}
            .queue-item {{ background: rgba(255, 255, 255, 0.05); border: 1px solid rgba(255, 255, 255, 0.1); border-radius: 12px; padding: 15px; transition: all 0.3s ease; color: white; }}
            .queue-item:hover {{ border-color: {config.primary_color}; transform: translateX(5px); }}
            .queue-position {{ font-weight: 600; color: {config.primary_color}; margin-bottom: 5px; }}
            .queue-details {{ color: rgba(255, 255, 255, 0.8); font-size: 14px; }}
            table {{ width: 100%; border-collapse: collapse; }}
            th {{ background: rgba(255, 255, 255, 0.1); padding: 15px; text-align: left; font-weight: 600; font-size: 14px; border-bottom: 1px solid rgba(255, 255, 255, 0.1); color: white; }}
            td {{ padding: 15px; border-bottom: 1px solid rgba(255, 255, 255, 0.05); font-size: 14px; color: white; }}
            tr:hover {{ background: rgba(255, 255, 255, 0.02); }}
            .action-buttons {{ display: flex; gap: 5px; }}
            .btn {{ padding: 6px 12px; border: none; border-radius: 6px; cursor: pointer; font-size: 12px; font-weight: 600; transition: all 0.3s ease; color: white; }}
            .btn-danger {{ background: linear-gradient(45deg, #f44336, #E91E63); }}
            .btn-warning {{ background: linear-gradient(45deg, #FF9800, #FFC107); }}
            .btn-primary {{ background: linear-gradient(45deg, {config.primary_color}, {config.secondary_color}); }}
            .btn-success {{ background: linear-gradient(45deg, #4CAF50, #8BC34A); }}
            .btn:hover {{ transform: translateY(-2px); box-shadow: 0 5px 15px rgba(0, 0, 0, 0.3); }}
            .form-group {{ margin-bottom: 20px; }}
            .form-group label {{ display: block; color: rgba(255, 255, 255, 0.8); margin-bottom: 8px; font-size: 14px; }}
            .form-group input, .form-group select, .form-group textarea {{ width: 100%; padding: 12px; background: rgba(255, 255, 255, 0.1); border: 1px solid rgba(255, 255, 255, 0.2); border-radius: 10px; color: white; font-size: 14px; transition: all 0.3s ease; }}
            .form-group input:focus, .form-group select:focus, .form-group textarea:focus {{ outline: none; border-color: {config.primary_color}; box-shadow: 0 0 20px {config.primary_color}40; }}
            .form-group input::placeholder, .form-group textarea::placeholder {{ color: rgba(255, 255, 255, 0.5); }}
            .form-grid {{ display: grid; grid-template-columns: 1fr 1fr; gap: 20px; }}
            .modal {{ display: none; position: fixed; top: 0; left: 0; width: 100%; height: 100%; background: rgba(0,0,0,0.8); z-index: 1000; align-items: center; justify-content: center; }}
            .modal-content {{ background: #1a1a2e; padding: 30px; border-radius: 15px; width: 90%; max-width: 500px; border: 1px solid {config.primary_color}; color: white; }}
            .glow {{ position: fixed; width: 200px; height: 200px; background: {config.primary_color}; border-radius: 50%; filter: blur(100px); opacity: 0.1; animation: pulse 4s infinite ease-in-out; z-index: 1; }}
            .glow-1 {{ top: 10%; left: 10%; }} .glow-2 {{ bottom: 10%; right: 10%; }}
            .nav-tabs {{ display: flex; gap: 10px; margin-bottom: 20px; flex-wrap: wrap; }}
            .tab-btn {{ padding: 12px 20px; background: rgba(255,255,255,0.1); border: none; border-radius: 8px; color: white; cursor: pointer; transition: all 0.3s ease; }}
            .tab-btn.active {{ background: {config.primary_color}; }}
            .tab-content {{ display: none; }}
            .tab-content.active {{ display: block; }}
            @keyframes pulse {{ 0%, 100% {{ opacity: 0.1; transform: scale(1); }} 50% {{ opacity: 0.2; transform: scale(1.1); }} }}
        </style>
    </head>
    <body>
        <div class="glow glow-1"></div><div class="glow glow-2"></div>
        <div class="header">
            <div class="header-content">
                <div class="logo-section">
                    {"<img src='/static/uploads/" + config.logo_path + "' alt='" + config.company_name + "'>" if config.logo_path else ""}
                    <div class="logo-text"><h1>{config.company_name}</h1><p>Admin Control Panel</p></div>
                </div>
                <div class="admin-actions">
                    <a href="/admin/dashboard" class="admin-btn">📊 Dashboard</a>
                    <a href="/admin/chats" class="admin-btn">💬 Conversas</a>
                    <a href="/admin/tickets" class="admin-btn">🎫 Tickets</a>
                    <a href="/cab/dashboard" class="admin-btn" style="background: linear-gradient(45deg, #9C27B0, #E91E63);">📋 CAB</a>
                    <a href="/logout" class="logout-btn">🚪 Sair</a>
                </div>
            </div>
        </div>
        <div class="main-container">
            <div class="nav-tabs">
                <button class="tab-btn active" onclick="openTab('tab-dashboard')">📊 Dashboard</button>
                <button class="tab-btn" onclick="openTab('tab-tickets')">🎫 Tickets</button>
                <button class="tab-btn" onclick="openTab('tab-groups')">👥 Grupos</button>
                <button class="tab-btn" onclick="openTab('tab-routing')">🔄 Roteamento</button>
                <button class="tab-btn" onclick="openTab('tab-users')">👤 Usuários</button>
                <button class="tab-btn" onclick="openTab('tab-subcategories')">📋 Subcategorias</button>
                <button class="tab-btn" onclick="openTab('tab-config')">⚙️ Configurações</button>
                <button class="tab-btn" onclick="openTab('tab-cab')">📊 CAB</button>
            </div>

            <!-- Tab Dashboard -->
            <div id="tab-dashboard" class="tab-content active">
                <div class="stats-grid">
                    <div class="stat-card">
                        <div class="stat-icon">👥</div>
                        <div class="stat-number">{online_analysts}</div>
                        <div class="stat-label">Analistas Online</div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-icon">⏳</div>
                        <div class="stat-number">{waiting_count}</div>
                        <div class="stat-label">Na Fila</div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-icon">🎫</div>
                        <div class="stat-number">{open_tickets}</div>
                        <div class="stat-label">Tickets Abertos</div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-icon">📊</div>
                        <div class="stat-number">{total_users}</div>
                        <div class="stat-label">Total Usuários</div>
                    </div>
                </div>

                <div class="dashboard-grid">
                    <div class="card">
                        <div class="card-header"><h3>📈 Estatísticas do Sistema</h3></div>
                        <div class="card-content">
                            <p>• Tickets em andamento: {in_progress_tickets}</p>
                            <p>• Aguardando aprovação: {pending_approval_tickets}</p>
                            <p>• Total de tickets: {total_tickets}</p>
                            <p>• Taxa de resolução: {round((total_tickets - open_tickets) / total_tickets * 100 if total_tickets > 0 else 0, 1)}%</p>
                        </div>
                    </div>

                    <div class="card">
                        <div class="card-header"><h3>⏳ Fila de Espera</h3></div>
                        <div class="card-content">
                            <div class="queue-list" id="waiting-list">
    '''
    
    for pos, s in queue:
        admin_html += f'''
                                <div class="queue-item">
                                    <div class="queue-position">#{pos}</div>
                                    <div class="queue-details">{s.category} ({s.region}) - {s.created_at.strftime('%d/%m %H:%M')}</div>
                                </div>
        '''
    
    admin_html += f'''
                            </div>
                        </div>
                    </div>
                </div>
            </div>

            <!-- Tab Tickets -->
            <div id="tab-tickets" class="tab-content">
                <div class="card">
                    <div class="card-header">
                        <h3>🎫 Todos os Tickets</h3>
                        <a href="/admin/tickets" class="btn btn-success">📋 Gerenciar Tickets</a>
                    </div>
                    <div class="card-content">
                        <p>Total de tickets no sistema: {total_tickets}</p>
                        <p>Use o link acima para gerenciar todos os tickets do sistema.</p>
                    </div>
                </div>
            </div>

            <!-- Tab Subcategories -->
            <div id="tab-subcategories" class="tab-content">
                <div class="card">
                    <div class="card-header">
                        <h3>📋 Subcategorias</h3>
                        <a href="/admin/subcategories" class="btn btn-success">📋 Gerenciar Subcategorias</a>
                    </div>
                    <div class="card-content">
                        <p>Gerencie as subcategorias de serviços para organizar melhor os tickets.</p>
                        <p>Use o link acima para acessar o gerenciamento completo de subcategorias.</p>
                    </div>
                </div>
            </div>

            <!-- Tab Groups -->
            <div id="tab-groups" class="tab-content">
                <div class="card">
                    <div class="card-header">
                        <h3>👥 Grupos de Suporte</h3>
                        <button class="btn btn-success" onclick="openModal('groupModal')">➕ Novo Grupo</button>
                    </div>
                    <div class="card-content">
                        <table>
                            <thead>
                                <tr>
                                    <th>Nome</th>
                                    <th>Descrição</th>
                                    <th>Analistas</th>
                                    <th>Ações</th>
                                </tr>
                            </thead>
                            <tbody>
    '''
    
    for group in groups:
        analysts_count = User.query.filter_by(group_id=group.id).count()
        admin_html += f'''
                                <tr>
                                    <td>{group.name}</td>
                                    <td>{group.description}</td>
                                    <td>{analysts_count}</td>
                                    <td class="action-buttons">
                                        <button class="btn btn-warning" onclick="editGroup({group.id}, '{group.name}', '{group.description}')">✏️</button>
                                        <button class="btn btn-primary" onclick="assignAnalysts({group.id})">👥</button>
                                    </td>
                                </tr>
        '''
    
    admin_html += f'''
                            </tbody>
                        </table>
                    </div>
                </div>
            </div>

            <!-- Tab Routing -->
            <div id="tab-routing" class="tab-content">
                <div class="card">
                    <div class="card-header">
                        <h3>🔄 Regras de Roteamento</h3>
                        <button class="btn btn-success" onclick="openModal('routingModal')">➕ Nova Regra</button>
                    </div>
                    <div class="card-content">
                        <table>
                            <thead>
                                <tr>
                                    <th>Nome</th>
                                    <th>Tipo</th>
                                    <th>Condição</th>
                                    <th>Grupo Alvo</th>
                                    <th>Status</th>
                                    <th>Ações</th>
                                </tr>
                            </thead>
                            <tbody>
    '''
    
    for rule in rules:
        status = "🟢 Ativa" if rule.active else "🔴 Inativa"
        admin_html += f'''
                                <tr>
                                    <td>{rule.name}</td>
                                    <td>{rule.condition_type}</td>
                                    <td>{rule.condition_value}</td>
                                    <td>{rule.target_group.name}</td>
                                    <td>{status}</td>
                                    <td class="action-buttons">
                                        <button class="btn btn-warning" onclick="editRouting({rule.id}, '{rule.name}', '{rule.condition_type}', '{rule.condition_value}', {rule.target_group_id}, {1 if rule.active else 0})">✏️</button>
                                    </td>
                                </tr>
        '''
    
    admin_html += f'''
                            </tbody>
                        </table>
                    </div>
                </div>
            </div>

            <!-- Tab Users -->
            <div id="tab-users" class="tab-content">
                <div class="card">
                    <div class="card-header">
                        <h3>👤 Gerenciar Usuários</h3>
                        <button class="btn btn-success" onclick="openModal('userModal')">➕ Novo Usuário</button>
                    </div>
                    <div class="card-content">
                        <table>
                            <thead>
                                <tr>
                                    <th>Nome</th>
                                    <th>Usuário</th>
                                    <th>Email</th>
                                    <th>Cargo</th>
                                    <th>Grupo</th>
                                    <th>Status</th>
                                    <th>Ações</th>
                                </tr>
                            </thead>
                            <tbody>
    '''
    
    for user in users:
        status_icon = "🟢 Online" if user.online else "🔴 Offline"
        group_name = user.support_group.name if user.support_group else 'Não atribuído'
        admin_html += f'''
                                <tr>
                                    <td>{user.full_name or user.name}</td>
                                    <td>{user.username}</td>
                                    <td>{user.email or 'N/A'}</td>
                                    <td>{user.position or 'N/A'}</td>
                                    <td>{group_name}</td>
                                    <td>{status_icon}</td>
                                    <td class="action-buttons">
                                        <button class="btn btn-warning" onclick="openEditModal({user.id}, '{user.name}', '{user.username}', '{user.department}', '{user.role}', '{user.region}', '{user.email or ""}', '{user.position or ""}', {1 if user.manager else 0}, {1 if user.senior_manager else 0}, {user.manager_id or 'null'}, {user.senior_manager_id or 'null'}, {1 if user.cab_access else 0})">✏️</button>
                                        <form method="post" action="/admin/reset/{user.id}" style="display: inline;">
                                            <button type="submit" class="btn btn-primary" title="Resetar Senha">🔑</button>
                                        </form>
                                        {"<form method='post' action='/admin/delete/" + str(user.id) + "' style='display: inline;'><button type='submit' class='btn btn-danger' onclick='return confirm(\"Deletar " + user.name + "?\")'>❌</button></form>" if user.username not in ['admin', 'analista'] else ""}
                                    </td>
                                </tr>
        '''
    
    admin_html += f'''
                            </tbody>
                        </table>
                    </div>
                </div>
            </div>

            <!-- Tab Config -->
            <div id="tab-config" class="tab-content">
                <div class="card">
                    <div class="card-header"><h3>⚙️ Configurar Sistema</h3></div>
                    <form method="post" action="/admin/config" enctype="multipart/form-data">
                        <div class="form-group">
                            <label>Nome da Empresa</label>
                            <input type="text" name="company_name" value="{config.company_name}">
                        </div>
                        <div class="form-group">
                            <label>Logo</label>
                            <input type="file" name="logo" accept="image/*">
                            {"<img src='/static/uploads/" + config.logo_path + "' style='width: 50px; margin-top: 10px; border-radius: 5px;'>" if config.logo_path else ""}
                        </div>
                        <div class="form-grid">
                            <div class="form-group">
                                <label>Cor Principal</label>
                                <input type="color" name="primary_color" value="{config.primary_color}">
                            </div>
                            <div class="form-group">
                                <label>Cor Secundária</label>
                                <input type="color" name="secondary_color" value="{config.secondary_color}">
                            </div>
                        </div>
                        <div class="form-grid">
                            <div class="form-group">
                                <label>Cor de Espera</label>
                                <input type="color" name="waiting_color" value="{config.waiting_color}">
                            </div>
                            <div class="form-group">
                                <label>Cor de Progresso</label>
                                <input type="color" name="progress_color" value="{config.progress_color}">
                            </div>
                        </div>
                        <button type="submit" class="btn btn-primary" style="width: 100%; padding: 12px;">💾 SALVAR CONFIGURAÇÕES</button>
                    </form>
                </div>

                <div class="card">
                    <div class="card-header">
                        <h3>📁 Gerenciar Categorias de Chat</h3>
                        <button class="btn btn-success" onclick="openModal('categoryModal')">➕ Nova Categoria</button>
                    </div>
                    <div class="card-content">
                        <table>
                            <thead>
                                <tr>
                                    <th>Área</th>
                                    <th>Nome</th>
                                    <th>Ações</th>
                                </tr>
                            </thead>
                            <tbody>
    '''
    
    for cat in chat_categories:
        admin_html += f'''
                                <tr>
                                    <td>{cat.area}</td>
                                    <td>{cat.name}</td>
                                    <td class="action-buttons">
                                        <form method="post" action="/admin/delete_category/{cat.id}" style="display: inline;">
                                            <button type="submit" class="btn btn-danger" onclick="return confirm('Deletar categoria {cat.name}?')">❌</button>
                                        </form>
                                    </td>
                                </tr>
        '''
    
    admin_html += f'''
                            </tbody>
                        </table>
                    </div>
                </div>

                <div class="card">
                    <div class="card-header">
                        <h3>🌐 Gerenciar Regiões</h3>
                        <button class="btn btn-success" onclick="openModal('regionModal')">➕ Nova Região</button>
                    </div>
                    <div class="card-content">
                        <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 10px;">
    '''
    
    for region in REGIONS:
        admin_html += f'''
                            <div style="background: rgba(255,255,255,0.1); padding: 10px; border-radius: 5px; display: flex; justify-content: space-between; align-items: center;">
                                <span>{region}</span>
                                <form method="post" action="/admin/delete_region" style="display: inline;">
                                    <input type="hidden" name="region" value="{region}">
                                    <button type="submit" class="btn btn-danger" style="padding: 2px 6px; font-size: 10px;" onclick="return confirm('Remover região {region}?')">❌</button>
                                </form>
                            </div>
        '''
    
    admin_html += f'''
                        </div>
                    </div>
                </div>
            </div>

            <!-- Tab CAB -->
            <div id="tab-cab" class="tab-content">
                <div class="card">
                    <div class="card-header">
                        <h3>📊 Change Advisory Board (CAB)</h3>
                        <a href="/cab/dashboard" class="btn btn-success">📋 Acessar CAB</a>
                    </div>
                    <div class="card-content">
                        <p>Gerencie todas as mudanças e solicitações do CAB através do painel dedicado.</p>
                        <p>Clique no botão acima para acessar o sistema completo de gerenciamento de mudanças.</p>
                    </div>
                </div>
            </div>
        </div>

        <!-- Modal Nova Região -->
        <div id="regionModal" class="modal">
            <div class="modal-content">
                <h3 style="margin-bottom: 20px;">🌐 Nova Região</h3>
                <form method="post" action="/admin/add_region">
                    <div class="form-group">
                        <label>Nome da Região:</label>
                        <input type="text" name="region" required>
                    </div>
                    <div style="display: flex; gap: 10px; margin-top: 20px;">
                        <button type="submit" class="btn btn-success" style="flex: 1;">💾 Adicionar</button>
                        <button type="button" class="btn btn-danger" style="flex: 1;" onclick="closeModal('regionModal')">❌ Cancelar</button>
                    </div>
                </form>
            </div>
        </div>

        <!-- Modal Novo Usuário -->
        <div id="userModal" class="modal">
            <div class="modal-content">
                <h3 style="margin-bottom: 20px;">➕ Novo Usuário</h3>
                <form method="post" action="/admin/create_user">
                    <div class="form-grid">
                        <div class="form-group">
                            <label>Nome Completo</label>
                            <input type="text" name="name" required>
                        </div>
                        <div class="form-group">
                            <label>Departamento</label>
                            <input type="text" name="department">
                        </div>
                        <div class="form-group">
                            <label>Usuário</label>
                            <input type="text" name="username" required>
                        </div>
                        <div class="form-group">
                            <label>Email</label>
                            <input type="email" name="email">
                        </div>
                        <div class="form-group">
                            <label>Cargo</label>
                            <input type="text" name="position" placeholder="Cargo/função">
                        </div>
                        <div class="form-group">
                            <label>Senha</label>
                            <input type="password" name="password" required>
                        </div>
                        <div class="form-group">
                            <label>Cargo</label>
                            <select name="role" required>
                                <option value="user">Usuário</option>
                                <option value="analyst">Analista</option>
                                <option value="admin">Administrador</option>
                            </select>
                        </div>
                        <div class="form-group">
                            <label>Região</label>
                            <select name="region" required>
    '''
    
    for r in REGIONS:
        admin_html += f'<option value="{r}">{r}</option>'
    
    admin_html += f'''
                            </select>
                        </div>
                        <div class="form-group">
                            <label>Gerente</label>
                            <input type="checkbox" name="manager" value="1">
                        </div>
                        <div class="form-group">
                            <label>Gerente Sênior</label>
                            <input type="checkbox" name="senior_manager" value="1">
                        </div>
                        <div class="form-group">
                            <label>Acesso CAB</label>
                            <input type="checkbox" name="cab_access" value="1">
                        </div>
                        <div class="form-group">
                            <label>Gerente Responsável</label>
                            <select name="manager_id">
                                <option value="">Nenhum</option>
    '''
    
    for manager in managers:
        admin_html += f'<option value="{manager.id}">{manager.name}</option>'
    
    admin_html += f'''
                            </select>
                        </div>
                        <div class="form-group">
                            <label>Gerente Sênior Responsável</label>
                            <select name="senior_manager_id">
                                <option value="">Nenhum</option>
    '''
    
    for manager in managers:
        admin_html += f'<option value="{manager.id}">{manager.name}</option>'
    
    admin_html += f'''
                            </select>
                        </div>
                    </div>
                    <div style="display: flex; gap: 10px; margin-top: 20px;">
                        <button type="submit" class="btn btn-success" style="flex: 1;">💾 Salvar</button>
                        <button type="button" class="btn btn-danger" style="flex: 1;" onclick="closeModal('userModal')">❌ Cancelar</button>
                    </div>
                </form>
            </div>
        </div>

        <!-- Modal Editar Usuário -->
        <div id="editUserModal" class="modal">
            <div class="modal-content">
                <h3 style="margin-bottom: 20px;">✏️ Editar Usuário</h3>
                <form method="post" action="/admin/update_user" id="editUserForm">
                    <input type="hidden" name="user_id" id="edit_user_id">
                    <div class="form-grid">
                        <div class="form-group">
                            <label>Nome Completo</label>
                            <input type="text" name="name" id="edit_name" required>
                        </div>
                        <div class="form-group">
                            <label>Departamento</label>
                            <input type="text" name="department" id="edit_department">
                        </div>
                        <div class="form-group">
                            <label>Usuário</label>
                            <input type="text" name="username" id="edit_username" required>
                        </div>
                        <div class="form-group">
                            <label>Email</label>
                            <input type="email" name="email" id="edit_email">
                        </div>
                        <div class="form-group">
                            <label>Cargo</label>
                            <input type="text" name="position" id="edit_position" placeholder="Cargo/função">
                        </div>
                        <div class="form-group">
                            <label>Nova Senha (deixe em branco para manter)</label>
                            <input type="password" name="password" id="edit_password">
                        </div>
                        <div class="form-group">
                            <label>Cargo</label>
                            <select name="role" id="edit_role" required>
                                <option value="user">Usuário</option>
                                <option value="analyst">Analista</option>
                                <option value="admin">Administrador</option>
                            </select>
                        </div>
                        <div class="form-group">
                            <label>Região</label>
                            <select name="region" id="edit_region" required>
    '''
    
    for r in REGIONS:
        admin_html += f'<option value="{r}">{r}</option>'
    
    admin_html += f'''
                            </select>
                        </div>
                        <div class="form-group">
                            <label>Gerente</label>
                            <input type="checkbox" name="manager" id="edit_manager" value="1">
                        </div>
                        <div class="form-group">
                            <label>Gerente Sênior</label>
                            <input type="checkbox" name="senior_manager" id="edit_senior_manager" value="1">
                        </div>
                        <div class="form-group">
                            <label>Acesso CAB</label>
                            <input type="checkbox" name="cab_access" id="edit_cab_access" value="1">
                        </div>
                        <div class="form-group">
                            <label>Gerente Responsável</label>
                            <select name="manager_id" id="edit_manager_id">
                                <option value="">Nenhum</option>
    '''
    
    for manager in managers:
        admin_html += f'<option value="{manager.id}">{manager.name}</option>'
    
    admin_html += f'''
                            </select>
                        </div>
                        <div class="form-group">
                            <label>Gerente Sênior Responsável</label>
                            <select name="senior_manager_id" id="edit_senior_manager_id">
                                <option value="">Nenhum</option>
    '''
    
    for manager in managers:
        admin_html += f'<option value="{manager.id}">{manager.name}</option>'
    
    admin_html += f'''
                            </select>
                        </div>
                    </div>
                    <div style="display: flex; gap: 10px; margin-top: 20px;">
                        <button type="submit" class="btn btn-success" style="flex: 1;">💾 Atualizar</button>
                        <button type="button" class="btn btn-danger" style="flex: 1;" onclick="closeModal('editUserModal')">❌ Cancelar</button>
                    </div>
                </form>
            </div>
        </div>

        <!-- Modal Nova Categoria Chat -->
        <div id="categoryModal" class="modal">
            <div class="modal-content">
                <h3 style="margin-bottom: 20px;">📁 Nova Categoria de Chat</h3>
                <form method="post" action="/admin/create_category">
                    <div class="form-group">
                        <label>Área</label>
                        <input type="text" name="area" required placeholder="Ex: TI, RH, FINANCEIRO">
                    </div>
                    <div class="form-group">
                        <label>Nome da Categoria</label>
                        <input type="text" name="name" required placeholder="Ex: Problema com sistema">
                    </div>
                    <div style="display: flex; gap: 10px; margin-top: 20px;">
                        <button type="submit" class="btn btn-success" style="flex: 1;">💾 Criar</button>
                        <button type="button" class="btn btn-danger" style="flex: 1;" onclick="closeModal('categoryModal')">❌ Cancelar</button>
                    </div>
                </form>
            </div>
        </div>

        <!-- Modal Novo Grupo -->
        <div id="groupModal" class="modal">
            <div class="modal-content">
                <h3 style="margin-bottom: 20px;">👥 Novo Grupo de Suporte</h3>
                <form method="post" action="/admin/create_group">
                    <div class="form-group">
                        <label>Nome do Grupo</label>
                        <input type="text" name="name" required>
                    </div>
                    <div class="form-group">
                        <label>Descrição</label>
                        <textarea name="description" required></textarea>
                    </div>
                    <div style="display: flex; gap: 10px; margin-top: 20px;">
                        <button type="submit" class="btn btn-success" style="flex: 1;">💾 Criar</button>
                        <button type="button" class="btn btn-danger" style="flex: 1;" onclick="closeModal('groupModal')">❌ Cancelar</button>
                    </div>
                </form>
            </div>
        </div>

        <!-- Modal Editar Grupo -->
        <div id="editGroupModal" class="modal">
            <div class="modal-content">
                <h3 style="margin-bottom: 20px;">✏️ Editar Grupo</h3>
                <form method="post" action="/admin/update_group" id="editGroupForm">
                    <input type="hidden" name="group_id" id="edit_group_id">
                    <div class="form-group">
                        <label>Nome do Grupo</label>
                        <input type="text" name="name" id="edit_group_name" required>
                    </div>
                    <div class="form-group">
                        <label>Descrição</label>
                        <textarea name="description" id="edit_group_description" required></textarea>
                    </div>
                    <div style="display: flex; gap: 10px; margin-top: 20px;">
                        <button type="submit" class="btn btn-success" style="flex: 1;">💾 Atualizar</button>
                        <button type="button" class="btn btn-danger" style="flex: 1;" onclick="closeModal('editGroupModal')">❌ Cancelar</button>
                    </div>
                </form>
            </div>
        </div>

        <!-- Modal Atribuir Analistas -->
        <div id="assignAnalystsModal" class="modal">
            <div class="modal-content">
                <h3 style="margin-bottom: 20px;">👥 Atribuir Analistas ao Grupo</h3>
                <form method="post" action="/admin/assign_analyst_group">
                    <input type="hidden" name="group_id" id="assign_group_id">
                    <div class="form-group">
                        <label>Selecionar Analista</label>
                        <select name="analyst_id" required>
                            <option value="">Selecione um analista</option>
    '''
    
    analysts = User.query.filter_by(role='analyst').all()
    for analyst in analysts:
        admin_html += f'<option value="{analyst.id}">{analyst.name}</option>'
    
    admin_html += f'''
                        </select>
                    </div>
                    <div style="display: flex; gap: 10px; margin-top: 20px;">
                        <button type="submit" class="btn btn-success" style="flex: 1;">💾 Atribuir</button>
                        <button type="button" class="btn btn-danger" style="flex: 1;" onclick="closeModal('assignAnalystsModal')">❌ Cancelar</button>
                    </div>
                </form>
            </div>
        </div>

        <!-- Modal Nova Regra -->
        <div id="routingModal" class="modal">
            <div class="modal-content">
                <h3 style="margin-bottom: 20px;">🔄 Nova Regra de Roteamento</h3>
                <form method="post" action="/admin/create_rule">
                    <div class="form-group">
                        <label>Nome da Regra</label>
                        <input type="text" name="name" required>
                    </div>
                    <div class="form-group">
                        <label>Tipo de Condição</label>
                        <select name="condition_type" required>
                            <option value="keyword">Palavra-chave</option>
                            <option value="category">Categoria</option>
                        </select>
                    </div>
                    <div class="form-group">
                        <label>Valor da Condição</label>
                        <input type="text" name="condition_value" required placeholder="Ex: reset senha">
                    </div>
                    <div class="form-group">
                        <label>Grupo Alvo</label>
                        <select name="target_group_id" required>
    '''
    
    for group in groups:
        admin_html += f'<option value="{group.id}">{group.name}</option>'
    
    admin_html += f'''
                        </select>
                    </div>
                    <div style="display: flex; gap: 10px; margin-top: 20px;">
                        <button type="submit" class="btn btn-success" style="flex: 1;">💾 Criar</button>
                        <button type="button" class="btn btn-danger" style="flex: 1;" onclick="closeModal('routingModal')">❌ Cancelar</button>
                    </div>
                </form>
            </div>
        </div>

        <!-- Modal Editar Regra -->
        <div id="editRoutingModal" class="modal">
            <div class="modal-content">
                <h3 style="margin-bottom: 20px;">✏️ Editar Regra de Roteamento</h3>
                <form method="post" action="/admin/update_rule" id="editRoutingForm">
                    <input type="hidden" name="rule_id" id="edit_rule_id">
                    <div class="form-group">
                        <label>Nome da Regra</label>
                        <input type="text" name="name" id="edit_rule_name" required>
                    </div>
                    <div class="form-group">
                        <label>Tipo de Condição</label>
                        <select name="condition_type" id="edit_condition_type" required>
                            <option value="keyword">Palavra-chave</option>
                            <option value="category">Categoria</option>
                        </select>
                    </div>
                    <div class="form-group">
                        <label>Valor da Condição</label>
                        <input type="text" name="condition_value" id="edit_condition_value" required>
                    </div>
                    <div class="form-group">
                        <label>Grupo Alvo</label>
                        <select name="target_group_id" id="edit_target_group_id" required>
    '''
    
    for group in groups:
        admin_html += f'<option value="{group.id}">{group.name}</option>'
    
    admin_html += f'''
                        </select>
                    </div>
                    <div class="form-group">
                        <label>Ativa</label>
                        <input type="checkbox" name="active" id="edit_rule_active" value="1">
                    </div>
                    <div style="display: flex; gap: 10px; margin-top: 20px;">
                        <button type="submit" class="btn btn-success" style="flex: 1;">💾 Atualizar</button>
                        <button type="button" class="btn btn-danger" style="flex: 1;" onclick="closeModal('editRoutingModal')">❌ Cancelar</button>
                    </div>
                </form>
            </div>
        </div>

        <script>
            function openTab(tabName) {{
                document.querySelectorAll('.tab-content').forEach(tab => {{
                    tab.classList.remove('active');
                }});
                document.querySelectorAll('.tab-btn').forEach(btn => {{
                    btn.classList.remove('active');
                }});
                document.getElementById(tabName).classList.add('active');
                event.currentTarget.classList.add('active');
            }}

            function openModal(modalId) {{
                document.getElementById(modalId).style.display = 'flex';
            }}

            function closeModal(modalId) {{
                document.getElementById(modalId).style.display = 'none';
            }}

            function openEditModal(id, name, username, department, role, region, email, position, manager, senior_manager, manager_id, senior_manager_id, cab_access) {{
                document.getElementById('edit_user_id').value = id;
                document.getElementById('edit_name').value = name;
                document.getElementById('edit_username').value = username;
                document.getElementById('edit_department').value = department;
                document.getElementById('edit_role').value = role;
                document.getElementById('edit_region').value = region;
                document.getElementById('edit_email').value = email;
                document.getElementById('edit_position').value = position;
                document.getElementById('edit_manager').checked = manager == 1;
                document.getElementById('edit_senior_manager').checked = senior_manager == 1;
                document.getElementById('edit_cab_access').checked = cab_access == 1;
                document.getElementById('edit_manager_id').value = manager_id;
                document.getElementById('edit_senior_manager_id').value = senior_manager_id;
                openModal('editUserModal');
            }}

            function editGroup(id, name, description) {{
                document.getElementById('edit_group_id').value = id;
                document.getElementById('edit_group_name').value = name;
                document.getElementById('edit_group_description').value = description;
                openModal('editGroupModal');
            }}

            function assignAnalysts(group_id) {{
                document.getElementById('assign_group_id').value = group_id;
                openModal('assignAnalystsModal');
            }}

            function editRouting(id, name, condition_type, condition_value, target_group_id, active) {{
                document.getElementById('edit_rule_id').value = id;
                document.getElementById('edit_rule_name').value = name;
                document.getElementById('edit_condition_type').value = condition_type;
                document.getElementById('edit_condition_value').value = condition_value;
                document.getElementById('edit_target_group_id').value = target_group_id;
                document.getElementById('edit_rule_active').checked = active == 1;
                openModal('editRoutingModal');
            }}

            function updateWaitingList() {{
                fetch('/admin/waiting_list').then(r => r.json()).then(data => {{
                    let html = '';
                    data.queue.forEach((s, index) => {{
                        html += `<div class="queue-item">
                            <div class="queue-position">#${{index + 1}}</div>
                            <div class="queue-details">${{s.category}} (${{s.region}}) - ${{s.created_at}}</div>
                        </div>`;
                    }});
                    document.getElementById('waiting-list').innerHTML = html;
                }});
            }}
            setInterval(updateWaitingList, 2000);

            window.onclick = function(event) {{
                if (event.target.classList.contains('modal')) {{
                    event.target.style.display = 'none';
                }}
            }}
        </script>
    </body>
    </html>
    '''
    
    return admin_html

# ROTAS ADMIN PARA GERENCIAMENTO
@app.route('/admin/create_user', methods=['POST'])
def admin_create_user():
    u = current_user()
    if not u or u.role != 'admin': 
        flash('Acesso negado!', 'error')
        return redirect(url_for('login'))
    
    user = User(
        username=request.form['username'], 
        name=request.form['name'],
        department=request.form['department'], 
        region=request.form['region'],
        password_hash=generate_password_hash(request.form['password']),
        role=request.form['role'],
        email=request.form.get('email', ''),
        position=request.form.get('position', ''),
        manager=bool(request.form.get('manager')),
        senior_manager=bool(request.form.get('senior_manager')),
        cab_access=bool(request.form.get('cab_access')),
        manager_id=request.form.get('manager_id') or None,
        senior_manager_id=request.form.get('senior_manager_id') or None
    )
    db.session.add(user)
    db.session.commit()
    flash(f'Usuário {user.name} criado com sucesso!', 'success')
    return redirect(url_for('admin_panel'))

@app.route('/admin/update_user', methods=['POST'])
def admin_update_user():
    u = current_user()
    if not u or u.role != 'admin': 
        flash('Acesso negado!', 'error')
        return redirect(url_for('login'))
    
    user_id = request.form['user_id']
    user = User.query.get(user_id)
    
    if user:
        user.name = request.form['name']
        user.username = request.form['username']
        user.department = request.form['department']
        user.region = request.form['region']
        user.role = request.form['role']
        user.email = request.form.get('email', '')
        user.position = request.form.get('position', '')
        user.manager = bool(request.form.get('manager'))
        user.senior_manager = bool(request.form.get('senior_manager'))
        user.cab_access = bool(request.form.get('cab_access'))
        user.manager_id = request.form.get('manager_id') or None
        user.senior_manager_id = request.form.get('senior_manager_id') or None
        
        if request.form['password']:
            user.password_hash = generate_password_hash(request.form['password'])
        
        db.session.commit()
        flash(f'Usuário {user.name} atualizado com sucesso!', 'success')
    
    return redirect(url_for('admin_panel'))

@app.route('/admin/reset/<int:user_id>', methods=['POST'])
def admin_reset_password(user_id):
    u = current_user()
    if not u or u.role != 'admin': 
        flash('Acesso negado!', 'error')
        return redirect(url_for('login'))
    
    user = User.query.get(user_id)
    if user:
        user.password_hash = generate_password_hash('123456')
        db.session.commit()
        flash(f'Senha de {user.name} resetada para 123456!', 'success')
    
    return redirect(url_for('admin_panel'))

@app.route('/admin/delete/<int:user_id>', methods=['POST'])
def admin_delete_user(user_id):
    u = current_user()
    if not u or u.role != 'admin': 
        flash('Acesso negado!', 'error')
        return redirect(url_for('login'))
    
    user = User.query.get(user_id)
    if user and user.username not in ['admin', 'analista']:
        db.session.delete(user)
        db.session.commit()
        flash(f'Usuário {user.name} deletado com sucesso!', 'success')
    
    return redirect(url_for('admin_panel'))

@app.route('/admin/create_group', methods=['POST'])
def admin_create_group():
    u = current_user()
    if not u or u.role != 'admin': 
        flash('Acesso negado!', 'error')
        return redirect(url_for('login'))
    
    group = SupportGroup(
        name=request.form['name'],
        description=request.form['description']
    )
    db.session.add(group)
    db.session.commit()
    flash(f'Grupo {group.name} criado com sucesso!', 'success')
    return redirect(url_for('admin_panel'))

@app.route('/admin/update_group', methods=['POST'])
def admin_update_group():
    u = current_user()
    if not u or u.role != 'admin': 
        flash('Acesso negado!', 'error')
        return redirect(url_for('login'))
    
    group_id = request.form['group_id']
    group = SupportGroup.query.get(group_id)
    
    if group:
        group.name = request.form['name']
        group.description = request.form['description']
        db.session.commit()
        flash(f'Grupo {group.name} atualizado com sucesso!', 'success')
    
    return redirect(url_for('admin_panel'))

@app.route('/admin/assign_analyst_group', methods=['POST'])
def admin_assign_analyst_group():
    u = current_user()
    if not u or u.role != 'admin': 
        flash('Acesso negado!', 'error')
        return redirect(url_for('login'))
    
    group_id = request.form['group_id']
    analyst_id = request.form['analyst_id']
    
    analyst = User.query.get(analyst_id)
    if analyst and analyst.role == 'analyst':
        analyst.group_id = group_id
        db.session.commit()
        flash(f'Analista {analyst.name} atribuído ao grupo com sucesso!', 'success')
    
    return redirect(url_for('admin_panel'))

@app.route('/admin/create_rule', methods=['POST'])
def admin_create_rule():
    u = current_user()
    if not u or u.role != 'admin': 
        flash('Acesso negado!', 'error')
        return redirect(url_for('login'))
    
    rule = RoutingRule(
        name=request.form['name'],
        condition_type=request.form['condition_type'],
        condition_value=request.form['condition_value'],
        target_group_id=request.form['target_group_id']
    )
    db.session.add(rule)
    db.session.commit()
    flash(f'Regra {rule.name} criada com sucesso!', 'success')
    return redirect(url_for('admin_panel'))

@app.route('/admin/update_rule', methods=['POST'])
def admin_update_rule():
    u = current_user()
    if not u or u.role != 'admin': 
        flash('Acesso negado!', 'error')
        return redirect(url_for('login'))
    
    rule_id = request.form['rule_id']
    rule = RoutingRule.query.get(rule_id)
    
    if rule:
        rule.name = request.form['name']
        rule.condition_type = request.form['condition_type']
        rule.condition_value = request.form['condition_value']
        rule.target_group_id = request.form['target_group_id']
        rule.active = bool(request.form.get('active'))
        db.session.commit()
        flash(f'Regra {rule.name} atualizada com sucesso!', 'success')
    
    return redirect(url_for('admin_panel'))

@app.route('/admin/config', methods=['POST'])
def admin_config():
    u = current_user()
    if not u or u.role != 'admin': 
        flash('Acesso negado!', 'error')
        return redirect(url_for('login'))
    
    config = Config.query.first()
    if not config:
        config = Config()
        db.session.add(config)
    
    config.company_name = request.form['company_name']
    config.primary_color = request.form['primary_color']
    config.secondary_color = request.form['secondary_color']
    config.waiting_color = request.form['waiting_color']
    config.progress_color = request.form['progress_color']
    
    if 'logo' in request.files:
        file = request.files['logo']
        if file and file.filename != '':
            filename = secure_filename(file.filename)
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(file_path)
            config.logo_path = filename
    
    db.session.commit()
    flash('Configurações salvas com sucesso!', 'success')
    return redirect(url_for('admin_panel'))

@app.route('/admin/create_category', methods=['POST'])
def admin_create_category():
    u = current_user()
    if not u or u.role != 'admin': 
        flash('Acesso negado!', 'error')
        return redirect(url_for('login'))
    
    category = Category(
        area=request.form['area'],
        name=request.form['name']
    )
    db.session.add(category)
    db.session.commit()
    flash('Categoria criada com sucesso!', 'success')
    return redirect(url_for('admin_panel'))

@app.route('/admin/delete_category/<int:category_id>', methods=['POST'])
def admin_delete_category(category_id):
    u = current_user()
    if not u or u.role != 'admin': 
        flash('Acesso negado!', 'error')
        return redirect(url_for('login'))
    
    category = Category.query.get(category_id)
    if category:
        db.session.delete(category)
        db.session.commit()
        flash('Categoria deletada com sucesso!', 'success')
    
    return redirect(url_for('admin_panel'))

@app.route('/admin/add_region', methods=['POST'])
def admin_add_region():
    u = current_user()
    if not u or u.role != 'admin': 
        flash('Acesso negado!', 'error')
        return redirect(url_for('login'))
    
    new_region = request.form['region'].strip().upper()
    if new_region and new_region not in REGIONS:
        REGIONS.append(new_region)
        flash(f'Região {new_region} adicionada com sucesso!', 'success')
    else:
        flash('Região já existe ou é inválida!', 'error')
    
    return redirect(url_for('admin_panel'))

@app.route('/admin/delete_region', methods=['POST'])
def admin_delete_region():
    u = current_user()
    if not u or u.role != 'admin': 
        flash('Acesso negado!', 'error')
        return redirect(url_for('login'))
    
    region_to_delete = request.form['region']
    if region_to_delete in REGIONS:
        REGIONS.remove(region_to_delete)
        flash(f'Região {region_to_delete} removida com sucesso!', 'success')
    else:
        flash('Região não encontrada!', 'error')
    
    return redirect(url_for('admin_panel'))

@app.route('/admin/waiting_list')
def admin_waiting_list():
    u = current_user()
    if not u or u.role != 'admin': 
        return jsonify({'error': 'Acesso negado'}), 403
    
    waiting = Session.query.filter_by(status='waiting').order_by(Session.created_at).all()
    queue = [{
        'category': s.category,
        'region': s.region,
        'created_at': s.created_at.strftime('%d/%m %H:%M')
    } for s in waiting]
    
    return jsonify({'queue': queue})

# SISTEMA CAB (Change Advisory Board) - JÁ ATUALIZADO
@app.route('/cab/dashboard')
def cab_dashboard():
    config = get_config()
    u = current_user()
    if not u or (not u.cab_access and u.role not in ['admin', 'analyst'] and not u.manager and not u.senior_manager): 
        flash('Acesso negado! Você não tem permissão para acessar o CAB.', 'error')
        return redirect(url_for('login'))
    
    # Estatísticas
    total_changes = ChangeRequest.query.count()
    pending_changes = ChangeRequest.query.filter_by(status='pending_approval').count()
    approved_changes = ChangeRequest.query.filter_by(status='approved').count()
    rejected_changes = ChangeRequest.query.filter_by(status='rejected').count()
    draft_changes = ChangeRequest.query.filter_by(status='draft').count()
    
    # Mudanças pendentes
    pending_changes_list = ChangeRequest.query.filter_by(status='pending_approval').order_by(ChangeRequest.created_at.desc()).all()
    
    # Minhas mudanças
    my_changes = ChangeRequest.query.filter_by(created_by=u.id).order_by(ChangeRequest.created_at.desc()).all()
    
    global_styles = apply_global_styles()
    
    cab_html = f'''
    <!DOCTYPE html>
    <html lang="pt-BR">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>CAB - {config.company_name}</title>
        {global_styles}
        <style>
            * {{ margin: 0; padding: 0; box-sizing: border-box; font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; }}
            body {{ background: linear-gradient(135deg, #0c0c0c 0%, #1a1a2e 50%, #16213e 100%); min-height: 100vh; color: white; }}
            .header {{ background: rgba(255, 255, 255, 0.05); backdrop-filter: blur(20px); border-bottom: 1px solid rgba(255, 255, 255, 0.1); padding: 20px 40px; }}
            .header-content {{ display: flex; justify-content: space-between; align-items: center; max-width: 1400px; margin: 0 auto; }}
            .logo-text h1 {{ font-size: 24px; font-weight: 300; }}
            .btn {{ background: #9C27B0; color: white; padding: 10px 20px; border: none; border-radius: 8px; cursor: pointer; text-decoration: none; display: inline-block; }}
            .main-container {{ max-width: 1400px; margin: 0 auto; padding: 40px; }}
            .stats-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 20px; margin-bottom: 40px; }}
            .stat-card {{ background: rgba(255, 255, 255, 0.05); border: 1px solid rgba(255, 255, 255, 0.1); border-radius: 15px; padding: 20px; text-align: center; }}
            .stat-number {{ font-size: 32px; font-weight: bold; margin: 10px 0; }}
            .card {{ background: rgba(255, 255, 255, 0.05); border: 1px solid rgba(255, 255, 255, 0.1); border-radius: 15px; padding: 25px; margin-bottom: 20px; }}
            .change-list {{ display: grid; gap: 15px; }}
            .change-item {{ background: rgba(255, 255, 255, 0.05); border: 1px solid rgba(255, 255, 255, 0.1); border-radius: 10px; padding: 15px; }}
            .change-header {{ display: flex; justify-content: space-between; margin-bottom: 10px; }}
            .change-number {{ font-weight: bold; color: #9C27B0; }}
            .btn-success {{ background: #4CAF50; }} .btn-danger {{ background: #f44336; }} .btn-warning {{ background: #FF9800; }}
            .nav-tabs {{ display: flex; gap: 10px; margin-bottom: 20px; }}
            .tab-btn {{ padding: 10px 20px; background: rgba(255,255,255,0.1); border: none; border-radius: 5px; color: white; cursor: pointer; }}
            .tab-btn.active {{ background: #9C27B0; }}
            .tab-content {{ display: none; }}
            .tab-content.active {{ display: block; }}
            .status-badge {{ padding: 4px 8px; border-radius: 4px; font-size: 12px; }}
            .status-draft {{ background: #6c757d; }} .status-pending_approval {{ background: #FF9800; }} .status-approved {{ background: #4CAF50; }} .status-rejected {{ background: #f44336; }}
        </style>
    </head>
    <body>
        <div class="header">
            <div class="header-content">
                <div class="logo-text"><h1>📋 Change Advisory Board - {config.company_name}</h1></div>
                <div>
                    <a href="{'/admin' if u.role == 'admin' else '/analyst' if u.role == 'analyst' else '/manager/dashboard' if u.manager or u.senior_manager else '/user/dashboard'}" class="btn" style="background: {config.primary_color};">← Voltar</a>
                    <a href="/cab/new" class="btn btn-success">➕ Nova Mudança</a>
                    <a href="/logout" class="btn" style="background: #ff6b6b;">🚪 Sair</a>
                </div>
            </div>
        </div>

        <div class="main-container">
            <div class="stats-grid">
                <div class="stat-card">
                    <div>📋</div>
                    <div class="stat-number">{total_changes}</div>
                    <div>Total de Mudanças</div>
                </div>
                <div class="stat-card">
                    <div>⏳</div>
                    <div class="stat-number">{pending_changes}</div>
                    <div>Pendentes</div>
                </div>
                <div class="stat-card">
                    <div>✅</div>
                    <div class="stat-number">{approved_changes}</div>
                    <div>Aprovadas</div>
                </div>
                <div class="stat-card">
                    <div>📝</div>
                    <div class="stat-number">{draft_changes}</div>
                    <div>Rascunhos</div>
                </div>
            </div>

            <div class="nav-tabs">
                <button class="tab-btn active" onclick="openTab('tab-pending')">⏳ Pendentes ({pending_changes})</button>
                <button class="tab-btn" onclick="openTab('tab-my-changes')">📝 Minhas Mudanças ({len(my_changes)})</button>
                <button class="tab-btn" onclick="openTab('tab-all')">📋 Todas as Mudanças ({total_changes})</button>
            </div>

            <div id="tab-pending" class="tab-content active">
                <div class="card">
                    <h3>⏳ Mudanças Pendentes de Aprovação</h3>
                    <div class="change-list">
    '''
    
    if pending_changes_list:
        for change in pending_changes_list:
            creator = User.query.get(change.created_by)
            cab_html += f'''
                        <div class="change-item">
                            <div class="change-header">
                                <span class="change-number">{change.number}</span>
                                <span class="status-badge status-pending_approval">PENDENTE</span>
                            </div>
                            <div><strong>{change.title}</strong></div>
                            <div style="font-size: 14px; color: #ccc; margin-top: 5px;">
                                Criado por: {creator.name if creator else 'N/A'} | 
                                Data: {change.created_at.strftime('%d/%m/%Y %H:%M')} | 
                                Prioridade: {change.priority} | Impacto: {change.impact}
                            </div>
                            <div style="margin-top: 10px;">
                                <a href="/cab/change/{change.id}" class="btn">👁️ Ver Detalhes</a>
                                {'<a href="/cab/change/' + str(change.id) + '/approve" class="btn btn-success">✅ Aprovar</a>' if u.cab_access or u.role in ['admin', 'analyst'] or u.manager or u.senior_manager else ''}
                                {'<a href="/cab/change/' + str(change.id) + '/reject" class="btn btn-danger">❌ Rejeitar</a>' if u.cab_access or u.role in ['admin', 'analyst'] or u.manager or u.senior_manager else ''}
                            </div>
                        </div>
            '''
    else:
        cab_html += '<p style="color: #ccc;">Nenhuma mudança pendente de aprovação.</p>'
    
    cab_html += f'''
                    </div>
                </div>
            </div>

            <div id="tab-my-changes" class="tab-content">
                <div class="card">
                    <div class="card-header">
                        <h3>📝 Minhas Mudanças</h3>
                        <a href="/cab/new" class="btn btn-success">➕ Nova Mudança</a>
                    </div>
                    <div class="change-list">
    '''
    
    if my_changes:
        for change in my_changes:
            status_class = f"status-{change.status}"
            cab_html += f'''
                        <div class="change-item">
                            <div class="change-header">
                                <span class="change-number">{change.number}</span>
                                <span class="status-badge {status_class}">{change.status.replace('_', ' ').upper()}</span>
                            </div>
                            <div><strong>{change.title}</strong></div>
                            <div style="font-size: 14px; color: #ccc; margin-top: 5px;">
                                Data: {change.created_at.strftime('%d/%m/%Y %H:%M')} | 
                                Prioridade: {change.priority} | Impacto: {change.impact}
                            </div>
                            <div style="margin-top: 10px;">
                                <a href="/cab/change/{change.id}" class="btn">👁️ Ver Detalhes</a>
                                {'<a href="/cab/change/' + str(change.id) + '/edit" class="btn btn-warning">✏️ Editar</a>' if change.status == 'draft' else ''}
                            </div>
                        </div>
            '''
    else:
        cab_html += '<p style="color: #ccc;">Nenhuma mudança encontrada.</p>'
    
    cab_html += f'''
                    </div>
                </div>
            </div>

            <div id="tab-all" class="tab-content">
                <div class="card">
                    <h3>📋 Todas as Mudanças</h3>
                    <div class="change-list">
    '''
    
    all_changes = ChangeRequest.query.order_by(ChangeRequest.created_at.desc()).all()
    if all_changes:
        for change in all_changes:
            creator = User.query.get(change.created_by)
            status_class = f"status-{change.status}"
            cab_html += f'''
                        <div class="change-item">
                            <div class="change-header">
                                <span class="change-number">{change.number}</span>
                                <span class="status-badge {status_class}">{change.status.replace('_', ' ').upper()}</span>
                            </div>
                            <div><strong>{change.title}</strong></div>
                            <div style="font-size: 14px; color: #ccc; margin-top: 5px;">
                                Criado por: {creator.name if creator else 'N/A'} | 
                                Data: {change.created_at.strftime('%d/%m/%Y %H:%M')} | 
                                Prioridade: {change.priority} | Impacto: {change.impact}
                            </div>
                            <div style="margin-top: 10px;">
                                <a href="/cab/change/{change.id}" class="btn">👁️ Ver Detalhes</a>
                            </div>
                        </div>
            '''
    else:
        cab_html += '<p style="color: #ccc;">Nenhuma mudança encontrada.</p>'
    
    cab_html += f'''
                    </div>
                </div>
            </div>
        </div>

        <script>
            function openTab(tabName) {{
                document.querySelectorAll('.tab-content').forEach(tab => {{
                    tab.classList.remove('active');
                }});
                document.querySelectorAll('.tab-btn').forEach(btn => {{
                    btn.classList.remove('active');
                }});
                document.getElementById(tabName).classList.add('active');
                event.currentTarget.classList.add('active');
            }}
        </script>
    </body>
    </html>
    '''
    
    return cab_html

# ROTAS CAB JÁ IMPLEMENTADAS ANTERIORMENTE...
@app.route('/cab/change/<int:change_id>/submit')
def cab_submit_change(change_id):
    u = current_user()
    if not u: 
        flash('Acesso negado!', 'error')
        return redirect(url_for('login'))
    
    change = ChangeRequest.query.get_or_404(change_id)
    if change.created_by != u.id:
        flash('Acesso negado!', 'error')
        return redirect('/cab/dashboard')
    
    change.status = 'pending_approval'
    
    log = ChangeLog(
        change_request_id=change.id,
        user_id=u.id,
        action='submitted',
        details='Mudança enviada para aprovação do CAB'
    )
    db.session.add(log)
    db.session.commit()
    
    flash('Mudança enviada para aprovação do CAB!', 'success')
    return redirect(f'/cab/change/{change_id}')

@app.route('/cab/change/<int:change_id>/approve')
def cab_approve_change(change_id):
    u = current_user()
    if not u or (not u.cab_access and u.role not in ['admin', 'analyst'] and not u.manager and not u.senior_manager): 
        flash('Acesso negado!', 'error')
        return redirect(url_for('login'))
    
    change = ChangeRequest.query.get_or_404(change_id)
    change.status = 'approved'
    change.approved_by = u.id
    change.approved_at = now_brasilia()
    
    log = ChangeLog(
        change_request_id=change.id,
        user_id=u.id,
        action='approved',
        details=f'Mudança aprovada por {u.name}'
    )
    db.session.add(log)
    db.session.commit()
    
    flash('Mudança aprovada com sucesso!', 'success')
    return redirect(f'/cab/change/{change_id}')

@app.route('/cab/change/<int:change_id>/reject')
def cab_reject_change(change_id):
    u = current_user()
    if not u or (not u.cab_access and u.role not in ['admin', 'analyst'] and not u.manager and not u.senior_manager): 
        flash('Acesso negado!', 'error')
        return redirect(url_for('login'))
    
    change = ChangeRequest.query.get_or_404(change_id)
    change.status = 'rejected'
    change.approved_by = u.id
    change.approved_at = now_brasilia()
    
    log = ChangeLog(
        change_request_id=change.id,
        user_id=u.id,
        action='rejected',
        details=f'Mudança rejeitada por {u.name}'
    )
    db.session.add(log)
    db.session.commit()
    
    flash('Mudança rejeitada!', 'info')
    return redirect(f'/cab/change/{change_id}')

@app.route('/cab/change/<int:change_id>/comment', methods=['POST'])
def cab_add_comment(change_id):
    u = current_user()
    if not u or (not u.cab_access and u.role not in ['admin', 'analyst'] and not u.manager and not u.senior_manager): 
        flash('Acesso negado!', 'error')
        return redirect(url_for('login'))
    
    change = ChangeRequest.query.get_or_404(change_id)
    content = request.form.get('content', '').strip()
    risk_assessment = request.form.get('risk_assessment', '').strip()
    
    if content:
        comment = CABComment(
            change_request_id=change_id,
            user_id=u.id,
            content=content,
            risk_assessment=risk_assessment
        )
        db.session.add(comment)
        
        log = ChangeLog(
            change_request_id=change.id,
            user_id=u.id,
            action='commented',
            details='Adicionou um comentário/avaliação'
        )
        db.session.add(log)
        db.session.commit()
        
        flash('Comentário adicionado com sucesso!', 'success')
    
    return redirect(f'/cab/change/{change_id}')

# NOVO TICKET COM ANEXO
@app.route('/user/tickets/new', methods=['GET', 'POST'])
def new_ticket():
    config = get_config()
    u = current_user()
    if not u: 
        flash('Acesso negado!', 'error')
        return redirect(url_for('login'))
    
    categories = TicketCategory.query.all()
    
    if request.method == 'POST':
        ticket_type = request.form['type']
        title = request.form['title']
        description = request.form['description']
        priority = request.form['priority']
        category_id = request.form['category_id']
        subcategory_id = request.form.get('subcategory_id')
        
        ticket = Ticket(
            number=generate_ticket_number(),
            type=ticket_type,
            title=title,
            description=description,
            priority=priority,
            created_by=u.id,
            category_id=category_id,
            subcategory_id=subcategory_id,
            requires_approval=False
        )
        
        apply_routing_rules(ticket)
        
        category = TicketCategory.query.get(category_id)
        subcategory = SubCategory.query.get(subcategory_id) if subcategory_id else None
        
        if (category and category.requires_approval) or (subcategory and subcategory.requires_approval):
            ticket.requires_approval = True
            ticket.status = 'pending_approval'
        
        db.session.add(ticket)
        db.session.commit()
        
        if 'attachment' in request.files:
            file = request.files['attachment']
            if file and file.filename != '' and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                unique_filename = f"ticket_{ticket.id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{filename}"
                file_path = os.path.join(app.config['UPLOAD_FOLDER'], 'documents', unique_filename)
                file.save(file_path)
                
                document = Document(
                    session_id=0,
                    user_id=u.id,
                    filename=unique_filename,
                    original_filename=filename,
                    file_type=filename.rsplit('.', 1)[1].lower()
                )
                db.session.add(document)
                
                comment = TicketComment(
                    ticket_id=ticket.id,
                    user_id=u.id,
                    content=f"📎 Arquivo anexado: {filename}",
                    is_internal=False
                )
                db.session.add(comment)
                db.session.commit()
        
        flash('Ticket criado com sucesso!', 'success')
        return redirect(url_for('user_dashboard'))
    
    subcategories_js = '''
    <script>
        function loadSubcategories() {
            const categoryId = document.getElementById('category_id').value;
            const subcategorySelect = document.getElementById('subcategory_id');
            
            subcategorySelect.innerHTML = '<option value="">Selecione uma subcategoria (opcional)</option>';
            
            if (categoryId) {
                fetch('/api/categories/' + categoryId + '/subcategories')
                    .then(response => response.json())
                    .then(data => {
                        data.subcategories.forEach(subcat => {
                            const option = document.createElement('option');
                            option.value = subcat.id;
                            option.textContent = subcat.name;
                            subcategorySelect.appendChild(option);
                        });
                    });
            }
        }
    </script>
    '''
    
    global_styles = apply_global_styles()
    
    new_ticket_html = f'''
    <!DOCTYPE html>
    <html lang="pt-BR">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>{config.company_name} - Novo Ticket</title>
        {global_styles}
        {subcategories_js}
        <style>
            * {{ margin: 0; padding: 0; box-sizing: border-box; font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; }}
            body {{ background: linear-gradient(135deg, #0c0c0c 0%, #1a1a2e 50%, #16213e 100%); min-height: 100vh; color: white; }}
            .header {{ background: rgba(255, 255, 255, 0.05); backdrop-filter: blur(20px); border-bottom: 1px solid rgba(255, 255, 255, 0.1); padding: 20px 40px; }}
            .header-content {{ display: flex; justify-content: space-between; align-items: center; max-width: 800px; margin: 0 auto; }}
            .logo-text h1 {{ font-size: 24px; font-weight: 300; }}
            .btn {{ background: {config.primary_color}; color: white; padding: 10px 20px; border: none; border-radius: 8px; cursor: pointer; text-decoration: none; display: inline-block; }}
            .main-container {{ max-width: 800px; margin: 0 auto; padding: 40px; }}
            .card {{ background: rgba(255, 255, 255, 0.05); border: 1px solid rgba(255, 255, 255, 0.1); border-radius: 15px; padding: 30px; }}
            .form-group {{ margin-bottom: 20px; }}
            .form-group label {{ display: block; margin-bottom: 8px; font-weight: 500; color: white; }}
            .form-group input, .form-group select, .form-group textarea {{ 
                width: 100%; padding: 12px; background: rgba(255, 255, 255, 0.1); 
                border: 1px solid rgba(255, 255, 255, 0.3); border-radius: 8px; 
                color: white; font-size: 16px;
            }}
            .form-group textarea {{ height: 150px; resize: vertical; }}
            .btn-success {{ background: #4CAF50; }}
            .type-selector {{ display: flex; gap: 10px; margin-bottom: 20px; }}
            .type-option {{ flex: 1; text-align: center; padding: 20px; background: rgba(255,255,255,0.1); border-radius: 10px; cursor: pointer; color: white; }}
            .type-option.selected {{ background: {config.primary_color}; }}
            .type-option input {{ display: none; }}
            .attachment-section {{ background: rgba(255,255,255,0.1); padding: 15px; border-radius: 10px; margin-top: 15px; }}
            .file-info {{ font-size: 14px; color: #ccc; margin-top: 5px; }}
        </style>
    </head>
    <body>
        <div class="header">
            <div class="header-content">
                <div class="logo-text"><h1>➕ Novo Ticket</h1></div>
                <a href="/user/dashboard" class="btn">← Voltar</a>
            </div>
        </div>

        <div class="main-container">
            <div class="card">
                <form method="post" enctype="multipart/form-data">
                    <div class="form-group">
                        <label>Tipo de Solicitação:</label>
                        <div class="type-selector">
                            <label class="type-option" onclick="selectType('incident')">
                                <input type="radio" name="type" value="incident" required> 
                                <div>🚨 Estou com Problema</div>
                                <small>Reportar um incidente ou problema</small>
                            </label>
                            <label class="type-option" onclick="selectType('request')">
                                <input type="radio" name="type" value="request" required>
                                <div>📋 Solicitar Algo</div>
                                <small>Fazer uma requisição</small>
                            </label>
                        </div>
                    </div>

                    <div class="form-group">
                        <label>Título:</label>
                        <input type="text" name="title" placeholder="Descreva brevemente o assunto" required>
                    </div>

                    <div class="form-group">
                        <label>Descrição Detalhada:</label>
                        <textarea name="description" placeholder="Descreva em detalhes o problema ou solicitação..." required></textarea>
                    </div>

                    <div class="form-group">
                        <label>Categoria:</label>
                        <select name="category_id" id="category_id" onchange="loadSubcategories()" required>
                            <option value="">Selecione uma categoria</option>
                            {"".join([f'<option value="{c.id}">{c.name}</option>' for c in categories])}
                        </select>
                    </div>

                    <div class="form-group">
                        <label>Subcategoria:</label>
                        <select name="subcategory_id" id="subcategory_id">
                            <option value="">Selecione uma subcategoria (opcional)</option>
                        </select>
                    </div>

                    <div class="form-group">
                        <label>Prioridade:</label>
                        <select name="priority" required>
                            <option value="Low">🟢 Baixa</option>
                            <option value="Medium" selected>🟡 Média</option>
                            <option value="High">🟠 Alta</option>
                            <option value="Critical">🔴 Crítica</option>
                        </select>
                    </div>

                    <div class="attachment-section">
                        <h4>📎 Anexar Arquivo (Opcional)</h4>
                        <input type="file" name="attachment" accept=".png,.jpg,.jpeg,.gif,.pdf,.doc,.docx,.txt,.xls,.xlsx,.csv">
                        <div class="file-info">
                            Tipos permitidos: PNG, JPG, GIF, PDF, DOC, TXT, XLS (Max: 16MB)
                        </div>
                    </div>

                    <button type="submit" class="btn btn-success" style="width: 100%; padding: 15px; font-size: 16px; margin-top: 20px;">
                        🚀 Enviar Ticket
                    </button>
                </form>
            </div>
        </div>

        <script>
            function selectType(type) {{
                document.querySelectorAll('.type-option').forEach(opt => {{
                    opt.classList.remove('selected');
                }});
                event.currentTarget.classList.add('selected');
                event.currentTarget.querySelector('input').checked = true;
            }}
        </script>
    </body>
    </html>
    '''
    
    return new_ticket_html

# PAINEL DO ANALISTA COM PESQUISA
@app.route('/analyst/tickets')
def analyst_all_tickets():
    config = get_config()
    u = current_user()
    if not u or u.role not in ['analyst', 'admin']: 
        flash('Acesso negado!', 'error')
        return redirect(url_for('login'))
    
    status_filter = request.args.get('status', 'all')
    group_filter = request.args.get('group', 'all')
    search_query = request.args.get('search', '')
    ticket_type_filter = request.args.get('type', 'all')
    
    query = Ticket.query
    
    if status_filter != 'all':
        query = query.filter(Ticket.status == status_filter)
    
    if group_filter != 'all' and u.role == 'admin':
        query = query.filter(Ticket.assigned_group == group_filter)
    elif u.role == 'analyst' and u.group_id:
        query = query.filter(Ticket.assigned_group == u.group_id)
    
    if search_query:
        query = query.filter(
            (Ticket.number.contains(search_query)) |
            (Ticket.title.contains(search_query)) |
            (Ticket.description.contains(search_query))
        )
    
    if ticket_type_filter != 'all':
        query = query.filter(Ticket.type == ticket_type_filter)
    
    tickets = query.order_by(Ticket.created_at.desc()).all()
    groups = SupportGroup.query.all()
    
    global_styles = apply_global_styles()
    
    tickets_html = f'''
    <!DOCTYPE html>
    <html lang="pt-BR">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>{config.company_name} - Todos os Tickets</title>
        {global_styles}
        <style>
            * {{ margin: 0; padding: 0; box-sizing: border-box; font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; }}
            body {{ background: linear-gradient(135deg, #0c0c0c 0%, #1a1a2e 50%, #16213e 100%); min-height: 100vh; color: white; }}
            .header {{ background: rgba(255, 255, 255, 0.05); backdrop-filter: blur(20px); border-bottom: 1px solid rgba(255, 255, 255, 0.1); padding: 20px 40px; }}
            .header-content {{ display: flex; justify-content: space-between; align-items: center; max-width: 1400px; margin: 0 auto; }}
            .btn {{ background: {config.primary_color}; color: white; padding: 10px 20px; border: none; border-radius: 8px; cursor: pointer; text-decoration: none; display: inline-block; }}
            .main-container {{ max-width: 1400px; margin: 0 auto; padding: 40px; }}
            .filters {{ background: rgba(255,255,255,0.05); padding: 20px; border-radius: 10px; margin-bottom: 20px; }}
            .filter-group {{ display: inline-block; margin-right: 20px; margin-bottom: 10px; }}
            .filter-group label {{ display: block; margin-bottom: 5px; color: #ccc; font-weight: bold; }}
            .filter-group select, .filter-group input {{ padding: 8px; background: rgba(255,255,255,0.1); border: 1px solid rgba(255,255,255,0.3); border-radius: 5px; color: white; }}
            .filter-group input::placeholder {{ color: rgba(255,255,255,0.5); }}
            .card {{ background: rgba(255, 255, 255, 0.05); border: 1px solid rgba(255, 255, 255, 0.1); border-radius: 15px; padding: 25px; margin-bottom: 20px; }}
            .ticket-list {{ display: grid; gap: 15px; }}
            .ticket-item {{ background: rgba(255, 255, 255, 0.05); border: 1px solid rgba(255, 255, 255, 0.1); border-radius: 10px; padding: 15px; }}
            .ticket-header {{ display: flex; justify-content: space-between; margin-bottom: 10px; }}
            .ticket-number {{ font-weight: bold; color: {config.primary_color}; }}
            .ticket-actions {{ display: flex; gap: 10px; margin-top: 10px; }}
            .btn-warning {{ background: #FF9800; }} .btn-success {{ background: #4CAF50; }} .btn-danger {{ background: #f44336; }}
            .status-badge {{ padding: 4px 8px; border-radius: 4px; font-size: 12px; font-weight: bold; }}
            .status-open {{ background: #FF9800; }} .status-in_progress {{ background: #2196F3; }} 
            .status-pending {{ background: #9C27B0; }} .status-resolved {{ background: #4CAF50; }}
            .status-cancelled {{ background: #f44336; }}
            .type-badge {{ padding: 3px 6px; border-radius: 3px; font-size: 10px; margin-left: 5px; }}
            .type-incident {{ background: #f44336; }} .type-request {{ background: #2196F3; }}
            .search-box {{ width: 300px; padding: 10px; background: rgba(255,255,255,0.1); border: 1px solid rgba(255,255,255,0.3); border-radius: 5px; color: white; }}
        </style>
    </head>
    <body>
        <div class="header">
            <div class="header-content">
                <h1>🎫 Todos os Tickets</h1>
                <a href="{'/admin' if u.role == 'admin' else '/analyst'}" class="btn">← Voltar</a>
            </div>
        </div>

        <div class="main-container">
            <div class="filters">
                <form method="get">
                    <div class="filter-group">
                        <label>🔍 Pesquisar:</label>
                        <input type="text" name="search" value="{search_query}" placeholder="Nº ticket, título ou descrição..." class="search-box">
                    </div>
                    
                    <div class="filter-group">
                        <label>📊 Tipo:</label>
                        <select name="type">
                            <option value="all" {'selected' if ticket_type_filter == 'all' else ''}>Todos</option>
                            <option value="incident" {'selected' if ticket_type_filter == 'incident' else ''}>🚨 Incidente</option>
                            <option value="request" {'selected' if ticket_type_filter == 'request' else ''}>📋 Requisição</option>
                        </select>
                    </div>
                    
                    <div class="filter-group">
                        <label>📋 Status:</label>
                        <select name="status">
                            <option value="all" {'selected' if status_filter == 'all' else ''}>Todos</option>
                            <option value="open" {'selected' if status_filter == 'open' else ''}>Aberto</option>
                            <option value="in_progress" {'selected' if status_filter == 'in_progress' else ''}>Em Andamento</option>
                            <option value="pending" {'selected' if status_filter == 'pending' else ''}>Pendente</option>
                            <option value="pending_approval" {'selected' if status_filter == 'pending_approval' else ''}>Pendente Aprovação</option>
                            <option value="resolved" {'selected' if status_filter == 'resolved' else ''}>Resolvido</option>
                            <option value="cancelled" {'selected' if status_filter == 'cancelled' else ''}>Cancelado</option>
                        </select>
                    </div>
                    
                    {'<div class="filter-group"><label>👥 Grupo:</label><select name="group"><option value="all">Todos</option>' + 
                    ''.join([f'<option value="{g.id}" {"selected" if group_filter == str(g.id) else ""}>{g.name}</option>' for g in groups]) + 
                    '</select></div>' if u.role == 'admin' else ''}
                    
                    <button type="submit" class="btn" style="margin-left: 10px;">🔍 Filtrar</button>
                    <a href="/analyst/tickets" class="btn" style="background: #6c757d; margin-left: 5px;">🔄 Limpar</a>
                </form>
            </div>

            <div class="card">
                <h3>Total de Tickets: {len(tickets)} {f'- Pesquisa: "{search_query}"' if search_query else ''}</h3>
                <div class="ticket-list">
    '''
    
    for ticket in tickets:
        status_class = f"status-{ticket.status}"
        type_class = f"type-{ticket.type}"
        type_text = "🚨" if ticket.type == 'incident' else "📋"
        group_name = ticket.group.name if ticket.group else 'Não atribuído'
        assignee_name = ticket.assignee.name if ticket.assignee else 'Não atribuído'
        
        tickets_html += f'''
                    <div class="ticket-item">
                        <div class="ticket-header">
                            <span class="ticket-number">{ticket.number} <span class="type-badge {type_class}">{type_text} {ticket.type.upper()}</span></span>
                            <span class="status-badge {status_class}">{ticket.status.upper()}</span>
                        </div>
                        <div><strong>{ticket.title}</strong></div>
                        <div style="font-size: 14px; color: #ccc; margin-top: 5px;">
                            Grupo: {group_name} | Analista: {assignee_name} | 
                            Criado: {ticket.created_at.strftime('%d/%m/%Y %H:%M')}
                        </div>
                        <div class="ticket-actions">
                            <a href="/ticket/{ticket.id}/edit" class="btn btn-warning">✏️ Editar</a>
                            <a href="/ticket/{ticket.id}" class="btn">👁️ Ver</a>
                            {'<a href="/ticket/' + str(ticket.id) + '/take" class="btn btn-success">👆 Assumir</a>' if not ticket.assigned_to else ''}
                        </div>
                    </div>
        '''
    
    tickets_html += f'''
                </div>
            </div>
        </div>
    </body>
    </html>
    '''
    
    return tickets_html

# PAINEL DO ANALISTA PRINCIPAL
@app.route('/analyst')
def analyst_panel():
    config = get_config()
    u = current_user()
    if not u or u.role != 'analyst': 
        flash('Acesso negado!', 'error')
        return redirect(url_for('login'))
    
    my_tickets = Ticket.query.filter_by(assigned_to=u.id).filter(Ticket.status.in_(['open', 'in_progress'])).all()
    group_tickets = []
    if u.group_id:
        group_tickets = Ticket.query.filter_by(assigned_group=u.group_id, assigned_to=None)\
            .filter(Ticket.status.in_(['open', 'pending_approval'])).all()
    
    waiting = Session.query.filter_by(status='waiting').order_by(Session.created_at).all()
    in_progress = Session.query.filter_by(status='in_progress', analyst_id=u.id).all()
    
    global_styles = apply_global_styles()
    
    analyst_html = f'''
    <!DOCTYPE html>
    <html lang="pt-BR">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>{config.company_name} - Painel do Analista</title>
        {global_styles}
        <style>
            * {{ margin: 0; padding: 0; box-sizing: border-box; font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; }}
            body {{ background: linear-gradient(135deg, #0c0c0c 0%, #1a1a2e 50%, #16213e 100%); min-height: 100vh; color: white; }}
            .header {{ background: rgba(255, 255, 255, 0.05); backdrop-filter: blur(20px); border-bottom: 1px solid rgba(255, 255, 255, 0.1); padding: 20px 40px; }}
            .header-content {{ display: flex; justify-content: space-between; align-items: center; max-width: 1400px; margin: 0 auto; }}
            .logo-text h1 {{ font-size: 24px; font-weight: 300; }}
            .btn {{ background: {config.primary_color}; color: white; padding: 10px 20px; border: none; border-radius: 8px; cursor: pointer; text-decoration: none; display: inline-block; }}
            .main-container {{ max-width: 1400px; margin: 0 auto; padding: 40px; }}
            .dashboard-grid {{ display: grid; grid-template-columns: 1fr 1fr; gap: 30px; }}
            .card {{ background: rgba(255, 255, 255, 0.05); border: 1px solid rgba(255, 255, 255, 0.1); border-radius: 15px; padding: 25px; }}
            .card-header {{ display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px; }}
            .ticket-list, .session-list {{ display: grid; gap: 15px; }}
            .ticket-item, .session-item {{ background: rgba(255, 255, 255, 0.05); border: 1px solid rgba(255, 255, 255, 0.1); border-radius: 10px; padding: 15px; color: white; }}
            .btn-success {{ background: #4CAF50; }} .btn-warning {{ background: #FF9800; }}
            .nav-tabs {{ display: flex; gap: 10px; margin-bottom: 20px; }}
            .tab-btn {{ padding: 10px 20px; background: rgba(255,255,255,0.1); border: none; border-radius: 5px; color: white; cursor: pointer; }}
            .tab-btn.active {{ background: {config.primary_color}; }}
            .tab-content {{ display: none; }}
            .tab-content.active {{ display: block; }}
            .status-controls {{ display: flex; gap: 10px; margin-bottom: 20px; }}
            .status-btn {{ padding: 10px 15px; border: none; border-radius: 5px; cursor: pointer; color: white; }}
            .online-btn {{ background: #4CAF50; }}
            .offline-btn {{ background: #f44336; }}
            .pause-btn {{ background: #FF9800; }}
        </style>
    </head>
    <body>
        <div class="header">
            <div class="header-content">
                <div class="logo-text"><h1>🛠️ Painel do Analista - {config.company_name}</h1></div>
                <a href="/logout" class="btn" style="background: #ff6b6b;">🚪 Sair</a>
            </div>
        </div>

        <div class="main-container">
            <div class="status-controls">
                <form method="post" action="/analyst/toggle" style="display: inline;">
                    <button type="submit" name="action" value="online" class="status-btn online-btn">🟢 Online</button>
                </form>
                <form method="post" action="/analyst/toggle" style="display: inline;">
                    <button type="submit" name="action" value="offline" class="status-btn offline-btn">🔴 Offline</button>
                </form>
                <form method="post" action="/analyst/toggle" style="display: inline;">
                    <button type="submit" name="action" value="pause" class="status-btn pause-btn">⏸️ Pausa</button>
                </form>
                <span style="margin-left: auto; padding: 10px; background: rgba(255,255,255,0.1); border-radius: 5px; color: white;">
                    Status: {"🟢 ONLINE" if u.online and not u.pause_start else "⏸️ EM PAUSA" if u.pause_start else "🔴 OFFLINE"}
                </span>
            </div>

            <div class="nav-tabs">
                <button class="tab-btn active" onclick="openTab('tab-tickets')">🎫 Tickets ({len(my_tickets) + len(group_tickets)})</button>
                <button class="tab-btn" onclick="openTab('tab-chats')">💬 Chats ({len(waiting) + len(in_progress)})</button>
                <button class="tab-btn" onclick="openTab('tab-all-tickets')">📋 Todos os Tickets</button>
                <button class="tab-btn" onclick="openTab('tab-cab')">📋 CAB</button>
            </div>

            <div id="tab-tickets" class="tab-content active">
                <div class="dashboard-grid">
                    <div class="card">
                        <div class="card-header">
                            <h3 style="color: white;">🎯 Meus Tickets ({len(my_tickets)})</h3>
                        </div>
                        <div class="ticket-list">
    '''
    
    if my_tickets:
        for ticket in my_tickets:
            analyst_html += f'''
                            <div class="ticket-item">
                                <div><strong>{ticket.number}</strong> - {ticket.title}</div>
                                <div style="font-size: 14px; color: #ccc; margin-top: 5px;">
                                    Status: {ticket.status} | Prioridade: {ticket.priority}
                                </div>
                                <div style="margin-top: 10px;">
                                    <a href="/ticket/{ticket.id}" class="btn">👁️ Ver</a>
                                    <a href="/ticket/{ticket.id}/edit" class="btn btn-warning">✏️ Editar</a>
                                </div>
                            </div>
            '''
    else:
        analyst_html += '<p style="color: #ccc;">Nenhum ticket atribuído a você.</p>'
    
    analyst_html += f'''
                        </div>
                    </div>

                    <div class="card">
                        <div class="card-header">
                            <h3 style="color: white;">📋 Fila do Grupo ({len(group_tickets)})</h3>
                        </div>
                        <div class="ticket-list">
    '''
    
    if group_tickets:
        for ticket in group_tickets:
            analyst_html += f'''
                            <div class="ticket-item">
                                <div><strong>{ticket.number}</strong> - {ticket.title}</div>
                                <div style="font-size: 14px; color: #ccc; margin-top: 5px;">
                                    Status: {ticket.status} | Prioridade: {ticket.priority}
                                </div>
                                <div style="margin-top: 10px;">
                                    <a href="/ticket/{ticket.id}/take" class="btn btn-success">👆 Assumir</a>
                                </div>
                            </div>
            '''
    else:
        analyst_html += '<p style="color: #ccc;">Nenhum ticket na fila do grupo.</p>'
    
    analyst_html += f'''
                        </div>
                    </div>
                </div>
            </div>

            <div id="tab-all-tickets" class="tab-content">
                <div class="card">
                    <div class="card-header">
                        <h3 style="color: white;">📋 Todos os Tickets do Grupo</h3>
                    </div>
                    <div class="ticket-list">
                        <p style="text-align: center; margin: 20px 0;">
                            <a href="/analyst/tickets" class="btn btn-success">📋 Ver Todos os Tickets</a>
                        </p>
                        <p style="text-align: center; color: #ccc;">
                            Visualize e gerencie todos os tickets do seu grupo de suporte
                        </p>
                    </div>
                </div>
            </div>

            <div id="tab-cab" class="tab-content">
                <div class="card">
                    <div class="card-header">
                        <h3 style="color: white;">📋 Change Advisory Board</h3>
                    </div>
                    <div class="ticket-list">
                        <p style="text-align: center; margin: 20px 0;">
                            <a href="/cab/dashboard" class="btn btn-success" style="background: #9C27B0;">📋 Acessar CAB</a>
                        </p>
                        <p style="text-align: center; color: #ccc;">
                            Gerencie mudanças e solicitações do Change Advisory Board
                        </p>
                    </div>
                </div>
            </div>

            <div id="tab-chats" class="tab-content">
                <div class="dashboard-grid">
                    <div class="card">
                        <div class="card-header">
                            <h3 style="color: white;">⏳ Fila de Chat ({len(waiting)})</h3>
                        </div>
                        <div class="session-list">
    '''
    
    if waiting:
        for session in waiting:
            analyst_html += f'''
                            <div class="session-item">
                                <div><strong>#{session.id}</strong> - {session.category}</div>
                                <div style="font-size: 14px; color: #ccc;">
                                    {session.region} | {session.created_at.strftime('%d/%m %H:%M')}
                                </div>
                                <div style="margin-top: 10px;">
                                    <form method="post" action="/analyst/pick/{session.id}">
                                        <button type="submit" class="btn">👆 Atender</button>
                                    </form>
                                </div>
                            </div>
            '''
    else:
        analyst_html += '<p style="color: #ccc;">Nenhum usuário na fila de chat.</p>'
    
    analyst_html += f'''
                        </div>
                    </div>

                    <div class="card">
                        <div class="card-header">
                            <h3 style="color: white;">💬 Meus Chats ({len(in_progress)})</h3>
                        </div>
                        <div class="session-list">
    '''
    
    if in_progress:
        for session in in_progress:
            user = User.query.get(session.user_id)
            analyst_html += f'''
                            <div class="session-item">
                                <div><strong>#{session.id}</strong> - {session.category}</div>
                                <div style="font-size: 14px; color: #ccc;">
                                    Usuário: {user.name if user else 'N/A'}
                                </div>
                                <div style="margin-top: 10px;">
                                    <a href="/analyst/chat/{session.id}" class="btn">💬 Conversar</a>
                                    <form method="post" action="/analyst/finish/{session.id}" style="display: inline;">
                                        <button type="submit" class="btn btn-success">✅ Finalizar</button>
                                    </form>
                                </div>
                            </div>
            '''
    else:
        analyst_html += '<p style="color: #ccc;">Nenhum chat em andamento.</p>'
    
    analyst_html += f'''
                        </div>
                    </div>
                </div>
            </div>
        </div>

        <script>
            function openTab(tabName) {{
                document.querySelectorAll('.tab-content').forEach(tab => {{
                    tab.classList.remove('active');
                }});
                document.querySelectorAll('.tab-btn').forEach(btn => {{
                    btn.classList.remove('active');
                }});
                document.getElementById(tabName).classList.add('active');
                event.currentTarget.classList.add('active');
            }}
        </script>
    </body>
    </html>
    '''
    
    return analyst_html

# EDIÇÃO DE TICKET
@app.route('/ticket/<int:ticket_id>/edit', methods=['GET', 'POST'])
def edit_ticket(ticket_id):
    config = get_config()
    u = current_user()
    if not u or u.role not in ['analyst', 'admin']: 
        flash('Acesso negado!', 'error')
        return redirect(url_for('login'))
    
    ticket = Ticket.query.get_or_404(ticket_id)
    groups = SupportGroup.query.all()
    analysts = User.query.filter_by(role='analyst').all()
    categories = TicketCategory.query.all()
    
    if request.method == 'POST':
        ticket.assigned_group = request.form.get('assigned_group') or ticket.assigned_group
        ticket.assigned_to = request.form.get('assigned_to') or ticket.assigned_to
        ticket.priority = request.form.get('priority', ticket.priority)
        ticket.status = request.form.get('status', ticket.status)
        
        if ticket.status == 'pending':
            ticket.pending_reason = request.form.get('pending_reason', '')
        
        if ticket.status == 'pending_approval':
            new_manager_id = request.form.get('manager_id')
            if new_manager_id:
                ticket.current_owner = new_manager_id
        
        db.session.commit()
        flash('Ticket atualizado com sucesso!', 'success')
        return redirect(f'/ticket/{ticket_id}')
    
    managers = User.query.filter((User.manager == True) | (User.senior_manager == True)).all()
    
    global_styles = apply_global_styles()
    
    edit_html = f'''
    <!DOCTYPE html>
    <html lang="pt-BR">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Editar Ticket {ticket.number}</title>
        {global_styles}
        <style>
            * {{ margin: 0; padding: 0; box-sizing: border-box; font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; }}
            body {{ background: linear-gradient(135deg, #0c0c0c 0%, #1a1a2e 50%, #16213e 100%); min-height: 100vh; color: white; }}
            .header {{ background: rgba(255, 255, 255, 0.05); backdrop-filter: blur(20px); border-bottom: 1px solid rgba(255, 255, 255, 0.1); padding: 20px 40px; }}
            .main-container {{ max-width: 800px; margin: 0 auto; padding: 40px; }}
            .card {{ background: rgba(255, 255, 255, 0.05); border: 1px solid rgba(255, 255, 255, 0.1); border-radius: 15px; padding: 25px; }}
            .form-group {{ margin-bottom: 20px; }}
            .form-group label {{ display: block; margin-bottom: 8px; color: white; }}
            .form-group input, .form-group select, .form-group textarea {{ 
                width: 100%; padding: 10px; background: rgba(255,255,255,0.1); 
                border: 1px solid rgba(255,255,255,0.3); border-radius: 5px; color: white;
            }}
            .btn {{ background: {config.primary_color}; color: white; padding: 10px 20px; border: none; border-radius: 5px; cursor: pointer; text-decoration: none; display: inline-block; }}
            .btn-success {{ background: #4CAF50; }}
            .conditional-field {{ display: none; margin-top: 10px; }}
        </style>
        <script>
            function toggleFields() {{
                const status = document.getElementById('status').value;
                const pendingReason = document.getElementById('pendingReasonField');
                const managerField = document.getElementById('managerField');
                
                pendingReason.style.display = status === 'pending' ? 'block' : 'none';
                managerField.style.display = status === 'pending_approval' ? 'block' : 'none';
            }}
        </script>
    </head>
    <body>
        <div class="header">
            <h1 style="text-align: center;">✏️ Editar Ticket {ticket.number}</h1>
        </div>

        <div class="main-container">
            <div class="card">
                <form method="post">
                    <div class="form-group">
                        <label>Grupo de Suporte:</label>
                        <select name="assigned_group">
                            <option value="">Selecione um grupo</option>
                            {"".join([f'<option value="{g.id}" {"selected" if ticket.assigned_group == g.id else ""}>{g.name}</option>' for g in groups])}
                        </select>
                    </div>

                    <div class="form-group">
                        <label>Analista Responsável:</label>
                        <select name="assigned_to">
                            <option value="">Não atribuído</option>
                            {"".join([f'<option value="{a.id}" {"selected" if ticket.assigned_to == a.id else ""}>{a.name}</option>' for a in analysts])}
                        </select>
                    </div>

                    <div class="form-group">
                        <label>Prioridade:</label>
                        <select name="priority">
                            <option value="Low" {'selected' if ticket.priority == 'Low' else ''}>🟢 Baixa</option>
                            <option value="Medium" {'selected' if ticket.priority == 'Medium' else ''}>🟡 Média</option>
                            <option value="High" {'selected' if ticket.priority == 'High' else ''}>🟠 Alta</option>
                            <option value="Critical" {'selected' if ticket.priority == 'Critical' else ''}>🔴 Crítica</option>
                        </select>
                    </div>

                    <div class="form-group">
                        <label>Status:</label>
                        <select name="status" id="status" onchange="toggleFields()" required>
                            <option value="open" {'selected' if ticket.status == 'open' else ''}>🆕 Novo</option>
                            <option value="in_progress" {'selected' if ticket.status == 'in_progress' else ''}>🔄 Em Andamento</option>
                            <option value="pending" {'selected' if ticket.status == 'pending' else ''}>⏳ Pendente</option>
                            <option value="pending_approval" {'selected' if ticket.status == 'pending_approval' else ''}>👨‍💼 Pendente Aprovação</option>
                            <option value="resolved" {'selected' if ticket.status == 'resolved' else ''}>✅ Resolvido</option>
                            <option value="cancelled" {'selected' if ticket.status == 'cancelled' else ''}>❌ Cancelado</option>
                        </select>
                    </div>

                    <div class="form-group conditional-field" id="pendingReasonField">
                        <label>Motivo da Pendência:</label>
                        <textarea name="pending_reason" placeholder="Informe o motivo pelo qual o ticket está pendente...">{ticket.pending_reason or ''}</textarea>
                    </div>

                    <div class="form-group conditional-field" id="managerField">
                        <label>Atribuir para Aprovação do Gerente:</label>
                        <select name="manager_id">
                            <option value="">Selecione um gerente</option>
                            {"".join([f'<option value="{m.id}" {"selected" if ticket.current_owner == m.id else ""}>{m.name}</option>' for m in managers])}
                        </select>
                    </div>

                    <div style="display: flex; gap: 10px; margin-top: 20px;">
                        <button type="submit" class="btn btn-success">💾 Salvar Alterações</button>
                        <a href="/ticket/{ticket.id}" class="btn">❌ Cancelar</a>
                    </div>
                </form>
            </div>
        </div>
        <script>toggleFields();</script>
    </body>
    </html>
    '''
    
    return edit_html

# ASSUMIR TICKET
@app.route('/ticket/<int:ticket_id>/take')
def take_ticket(ticket_id):
    u = current_user()
    if not u or u.role not in ['analyst', 'admin']: 
        flash('Acesso negado!', 'error')
        return redirect(url_for('login'))
    
    ticket = Ticket.query.get_or_404(ticket_id)
    
    if ticket.assigned_to:
        flash('Este ticket já está atribuído a outro analista!', 'error')
    else:
        ticket.assigned_to = u.id
        ticket.status = 'in_progress'
        db.session.commit()
        flash('Ticket assumido com sucesso!', 'success')
    
    return redirect(f'/ticket/{ticket_id}')

# API PARA SUBCATEGORIAS
@app.route('/api/categories/<int:category_id>/subcategories')
def api_subcategories(category_id):
    subcategories = SubCategory.query.filter_by(category_id=category_id).all()
    return jsonify({
        'subcategories': [
            {
                'id': subcat.id,
                'name': subcat.name,
                'description': subcat.description,
                'requires_approval': subcat.requires_approval
            }
            for subcat in subcategories
        ]
    })

# CHAT DO ANALISTA
@app.route('/analyst/chat/<int:sid>')
def analyst_chat(sid):
    config = get_config()
    u = current_user()
    if not u or u.role != 'analyst': 
        flash('Acesso negado!', 'error')
        return redirect(url_for('login'))
    
    session = Session.query.get(sid)
    if not session or session.analyst_id != u.id:
        flash('Sessão não encontrada!', 'error')
        return redirect(url_for('analyst_panel'))
    
    user = User.query.get(session.user_id)
    messages = Message.query.filter_by(session_id=sid).order_by(Message.created_at.asc()).all()
    documents = Document.query.filter_by(session_id=sid).order_by(Document.uploaded_at.asc()).all()
    
    global_styles = apply_global_styles()
    
    chat_html = f'''
    <html>
    <head>
        <title>Chat - {config.company_name}</title>
        {global_styles}
        <style>
            * {{ margin: 0; padding: 0; box-sizing: border-box; font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; }}
            body {{ background: #1a1a2e; color: white; padding: 20px; }}
            .container {{ max-width: 1000px; margin: 0 auto; }}
            .chat-header {{ background: rgba(255,255,255,0.1); padding: 15px; border-radius: 10px; margin-bottom: 20px; }}
            .chat-messages {{ height: 400px; overflow-y: auto; background: rgba(255,255,255,0.05); padding: 15px; border-radius: 10px; margin-bottom: 20px; }}
            .message {{ margin-bottom: 15px; padding: 10px; border-radius: 8px; }}
            .message-user {{ background: rgba(4, 103, 250, 0.2); margin-left: 50px; }}
            .message-analyst {{ background: rgba(76, 175, 80, 0.2); margin-right: 50px; }}
            .message-system {{ background: rgba(255, 152, 0, 0.2); text-align: center; }}
            .message-header {{ font-weight: bold; margin-bottom: 5px; }}
            .message-time {{ font-size: 12px; color: #ccc; }}
            .chat-form {{ display: flex; gap: 10px; }}
            .chat-input {{ flex: 1; padding: 10px; background: rgba(255,255,255,0.1); border: 1px solid rgba(255,255,255,0.3); border-radius: 5px; color: white; }}
            .send-btn {{ background: #0467FA; color: white; padding: 10px 20px; border: none; border-radius: 5px; cursor: pointer; }}
            .back-btn {{ background: #6c757d; color: white; padding: 10px 20px; border: none; border-radius: 5px; cursor: pointer; text-decoration: none; display: inline-block; margin-bottom: 15px; }}
            .documents-section {{ background: rgba(255,255,255,0.1); padding: 15px; border-radius: 10px; margin-top: 20px; }}
            .document-item {{ background: rgba(255,255,255,0.05); padding: 10px; margin: 5px 0; border-radius: 5px; display: flex; justify-content: space-between; align-items: center; }}
            .document-info {{ display: flex; align-items: center; gap: 10px; }}
            .document-icon {{ font-size: 20px; }}
            .document-preview {{ max-width: 300px; max-height: 200px; margin-top: 5px; border-radius: 5px; }}
            .btn {{ background: #0467FA; color: white; padding: 8px 15px; border: none; border-radius: 5px; cursor: pointer; text-decoration: none; display: inline-block; }}
            .btn-success {{ background: #4CAF50; }}
        </style>
    </head>
    <body>
        <div class="container">
            <a href="/analyst" class="back-btn">← Voltar</a>
            
            <div class="chat-header">
                <h2>💬 Chat com {user.name if user else 'Usuário'}</h2>
                <p><strong>Sessão:</strong> #{session.id} - {session.category} | <strong>Status:</strong> {session.status.upper()}</p>
            </div>
            
            <div class="chat-messages" id="chatMessages">
    '''
    
    for msg in messages:
        if msg.sender == 'user':
            chat_html += f'''
                <div class="message message-user">
                    <div class="message-header">👤 {user.name if user else 'Usuário'}</div>
                    <div>{msg.content}</div>
                    <div class="message-time">{msg.created_at.strftime('%d/%m/%Y %H:%M')}</div>
                </div>
            '''
        elif msg.sender == 'analyst':
            chat_html += f'''
                <div class="message message-analyst">
                    <div class="message-header">🛠️ {u.name}</div>
                    <div>{msg.content}</div>
                    <div class="message-time">{msg.created_at.strftime('%d/%m/%Y %H:%M')}</div>
                </div>
            '''
        else:
            chat_html += f'''
                <div class="message message-system">
                    <div>⚡ {msg.content}</div>
                    <div class="message-time">{msg.created_at.strftime('%d/%m/%Y %H:%M')}</div>
                </div>
            '''
    
    chat_html += f'''
            </div>
            
            <form method="post" action="/analyst/send_message/{session.id}" class="chat-form">
                <input type="text" name="message" class="chat-input" placeholder="Digite sua mensagem..." required>
                <button type="submit" class="send-btn">📤 Enviar</button>
            </form>
            
            <div class="documents-section">
                <h3>📁 Arquivos Compartilhados pelo Usuário</h3>
    '''
    
    if documents:
        for doc in documents:
            file_icon = "🖼️" if doc.file_type in ['png', 'jpg', 'jpeg', 'gif', 'bmp'] else "📄"
            file_path = f"/static/uploads/documents/{doc.filename}"
            
            chat_html += f'''
                <div class="document-item">
                    <div class="document-info">
                        <span class="document-icon">{file_icon}</span>
                        <div>
                            <div>{doc.original_filename}</div>
                            {f'<img src="{file_path}" alt="Preview" class="document-preview">' if doc.file_type in ['png', 'jpg', 'jpeg', 'gif', 'bmp'] else ''}
                        </div>
                    </div>
                    <div>
                        <a href="{file_path}" target="_blank" class="btn" style="background: #9C27B0;">👁️ Visualizar</a>
                        <a href="/download/document/{doc.id}" class="btn">📥 Baixar</a>
                    </div>
                </div>
            '''
    else:
        chat_html += '<p style="color: #ccc;">Nenhum arquivo compartilhado ainda</p>'
    
    chat_html += f'''
            </div>
            
            <div style="margin-top: 15px;">
                <form method="post" action="/analyst/finish/{session.id}" style="display: inline;">
                    <button type="submit" class="send-btn" style="background: #4CAF50;">✅ Finalizar Atendimento</button>
                </form>
            </div>
        </div>
        
        <script>
            const chatMessages = document.getElementById('chatMessages');
            chatMessages.scrollTop = chatMessages.scrollHeight;
            
            setInterval(() => {{
                fetch('/analyst/chat_messages/{session.id}')
                    .then(response => response.text())
                    .then(html => {{
                        const tempDiv = document.createElement('div');
                        tempDiv.innerHTML = html;
                        const newMessages = tempDiv.querySelector('#chatMessages');
                        if (newMessages) {{
                            document.getElementById('chatMessages').innerHTML = newMessages.innerHTML;
                            chatMessages.scrollTop = chatMessages.scrollHeight;
                        }}
                    }});
            }}, 3000);
        </script>
    </body>
    </html>
    '''
    
    return chat_html

@app.route('/analyst/chat_messages/<int:sid>')
def analyst_chat_messages(sid):
    u = current_user()
    if not u or u.role != 'analyst': 
        return "Acesso negado", 403
    
    session = Session.query.get(sid)
    if not session or session.analyst_id != u.id:
        return "Sessão não encontrada", 404
    
    user = User.query.get(session.user_id)
    messages = Message.query.filter_by(session_id=sid).order_by(Message.created_at.asc()).all()
    
    messages_html = '<div id="chatMessages">'
    
    for msg in messages:
        if msg.sender == 'user':
            messages_html += f'''
                <div class="message message-user">
                    <div class="message-header">👤 {user.name if user else 'Usuário'}</div>
                    <div>{msg.content}</div>
                    <div class="message-time">{msg.created_at.strftime('%d/%m/%Y %H:%M')}</div>
                </div>
            '''
        elif msg.sender == 'analyst':
            messages_html += f'''
                <div class="message message-analyst">
                    <div class="message-header">🛠️ {u.name}</div>
                    <div>{msg.content}</div>
                    <div class="message-time">{msg.created_at.strftime('%d/%m/%Y %H:%M')}</div>
                </div>
            '''
        else:
            messages_html += f'''
                <div class="message message-system">
                    <div>⚡ {msg.content}</div>
                    <div class="message-time">{msg.created_at.strftime('%d/%m/%Y %H:%M')}</div>
                </div>
            '''
    
    messages_html += '</div>'
    return messages_html

@app.route('/analyst/send_message/<int:sid>', methods=['POST'])
def analyst_send_message(sid):
    u = current_user()
    if not u or u.role != 'analyst': 
        flash('Acesso negado!', 'error')
        return redirect(url_for('login'))
    
    session = Session.query.get(sid)
    if not session or session.analyst_id != u.id:
        flash('Sessão não encontrada!', 'error')
        return redirect(url_for('analyst_panel'))
    
    message_content = request.form.get('message', '').strip()
    if message_content:
        db.session.add(Message(
            session_id=sid,
            sender='analyst',
            content=message_content
        ))
        db.session.commit()
        flash('Mensagem enviada!', 'success')
    
    return redirect(url_for('analyst_chat', sid=sid))

# ANALISTA - CONTROLES DE STATUS
@app.route('/analyst/toggle', methods=['POST'])
def analyst_toggle():
    u = current_user()
    if not u or u.role != 'analyst':
        return redirect(url_for('login'))
    
    action = request.form['action']
    
    if action == 'online': 
        u.online = True
        u.pause_start = None
        flash('🟢 Agora você está ONLINE', 'success')
    elif action == 'offline': 
        u.online = False
        u.pause_start = None
        flash('🔴 Agora você está OFFLINE', 'info')
    elif action == 'pause': 
        u.online = True
        u.pause_start = now_brasilia()
        flash('⏸️ Agora você está EM PAUSA', 'warning')
    
    db.session.commit()
    return redirect(url_for('analyst_panel'))

@app.route('/analyst/pick/<int:sid>', methods=['POST'])
def analyst_pick(sid):
    u = current_user()
    if not u.online or u.pause_start:
        flash('Você precisa estar ONLINE para atender solicitações!', 'error')
        return redirect(url_for('analyst_panel'))
    
    s = Session.query.get(sid)
    if s and s.status == 'waiting':
        s.status = 'in_progress'
        s.analyst_id = u.id
        s.assigned_at = now_brasilia()
        db.session.add(Message(session_id=s.id, sender='system', content=f'Analista {u.name} está te atendendo'))
        db.session.commit()
        flash('Atendimento iniciado com sucesso!', 'success')
        return redirect(url_for('analyst_chat', sid=s.id))
    return redirect(url_for('analyst_panel'))

@app.route('/analyst/finish/<int:sid>', methods=['POST'])
def analyst_finish(sid):
    s = Session.query.get(sid)
    if s:
        s.status = 'finished'
        s.finished_at = now_brasilia()
        u = current_user()
        if u:
            u.total_attended += 1
        db.session.commit()
        flash('Atendimento finalizado com sucesso!', 'success')
    return redirect(url_for('analyst_panel'))

# DASHBOARD ADMIN
@app.route('/admin/dashboard')
def admin_dashboard():
    config = get_config()
    u = current_user()
    if not u or u.role != 'admin': 
        flash('Acesso negado!', 'error')
        return redirect(url_for('login'))
    
    online_analysts = User.query.filter_by(role='analyst', online=True).count()
    waiting_count = Session.query.filter_by(status='waiting').count()
    total_sessions = Session.query.count()
    finished_sessions = Session.query.filter_by(status='finished').count()
    in_progress_sessions = Session.query.filter_by(status='in_progress').count()
    active_users = User.query.filter_by(role='user').count()
    
    open_tickets = Ticket.query.filter_by(status='open').count()
    in_progress_tickets = Ticket.query.filter_by(status='in_progress').count()
    pending_approval_tickets = Ticket.query.filter_by(status='pending_approval').count()
    total_tickets = Ticket.query.count()
    
    analysts_online = User.query.filter_by(role='analyst', online=True).all()
    
    global_styles = apply_global_styles()
    
    return f'''
    <html>
    <head>
        <title>Dashboard - {config.company_name}</title>
        {global_styles}
        <style>
            body {{ background: #1a1a2e; color: white; padding: 40px; font-family: Arial, sans-serif; }}
            .container {{ max-width: 1200px; margin: 0 auto; }}
            .stats {{ display: grid; grid-template-columns: repeat(4, 1fr); gap: 20px; margin: 30px 0; }}
            .stat-card {{ background: rgba(255,255,255,0.1); padding: 20px; border-radius: 10px; text-align: center; }}
            .stat-number {{ font-size: 32px; font-weight: bold; margin: 10px 0; }}
            .nav {{ margin: 20px 0; }}
            .nav a {{ color: #0467FA; margin-right: 15px; text-decoration: none; }}
            .analyst-list {{ background: rgba(255,255,255,0.1); padding: 15px; border-radius: 10px; margin: 10px 0; }}
        </style>
    </head>
    <body>
        <div class="container">
            <h1>📊 Dashboard - {config.company_name}</h1>
            
            <div class="nav">
                <a href="/admin">⚙️ Admin</a>
                <a href="/admin/chats">💬 Conversas</a>
                <a href="/admin/tickets">🎫 Tickets</a>
                <a href="/cab/dashboard">📋 CAB</a>
                <a href="/logout" style="color: #ff6b6b;">🚪 Sair</a>
            </div>
            
            <div class="stats">
                <div class="stat-card">
                    <div>👥</div>
                    <div class="stat-number">{online_analysts}</div>
                    <div>Analistas Online</div>
                </div>
                <div class="stat-card">
                    <div>⏳</div>
                    <div class="stat-number">{waiting_count}</div>
                    <div>Na Fila</div>
                </div>
                <div class="stat-card">
                    <div>🎫</div>
                    <div class="stat-number">{open_tickets}</div>
                    <div>Tickets Abertos</div>
                </div>
                <div class="stat-card">
                    <div>✅</div>
                    <div class="stat-number">{finished_sessions}</div>
                    <div>Chats Concluídos</div>
                </div>
            </div>
            
            <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 20px;">
                <div style="background: rgba(255,255,255,0.1); padding: 20px; border-radius: 10px;">
                    <h3>📈 Estatísticas do Sistema</h3>
                    <p>• Usuários ativos: {active_users}</p>
                    <p>• Atendimentos em andamento: {in_progress_sessions}</p>
                    <p>• Tickets em andamento: {in_progress_tickets}</p>
                    <p>• Aguardando aprovação: {pending_approval_tickets}</p>
                    <p>• Total de tickets: {total_tickets}</p>
                    <p>• Taxa de conclusão: {round((finished_sessions/total_sessions)*100 if total_sessions > 0 else 0, 1)}%</p>
                </div>
                
                <div style="background: rgba(255,255,255,0.1); padding: 20px; border-radius: 10px;">
                    <h3>🟢 Analistas Online</h3>
                    {''.join([f'<div class="analyst-list">🟢 {analyst.name} - {analyst.region}</div>' for analyst in analysts_online]) if analysts_online else '<p>Nenhum analista online</p>'}
                </div>
            </div>
        </div>
    </body>
    </html>
    '''

# CONVERSAS ADMIN
@app.route('/admin/chats', methods=['GET', 'POST'])
def admin_chats():
    config = get_config()
    u = current_user()
    if not u or u.role != 'admin': 
        flash('Acesso negado!', 'error')
        return redirect(url_for('login'))
    
    start_date = request.args.get('start_date', '')
    end_date = request.args.get('end_date', '')
    
    query = Session.query
    
    if start_date:
        try:
            start = datetime.strptime(start_date, '%Y-%m-%d')
            query = query.filter(Session.created_at >= start)
        except ValueError:
            pass
    
    if end_date:
        try:
            end = datetime.strptime(end_date, '%Y-%m-%d')
            end = end.replace(hour=23, minute=59, second=59)
            query = query.filter(Session.created_at <= end)
        except ValueError:
            pass
    
    sessions = query.order_by(Session.created_at.desc()).all()
    
    global_styles = apply_global_styles()
    
    chats_html = f'''
    <html>
    <head>
        <title>Conversas - {config.company_name}</title>
        {global_styles}
        <style>
            body {{ background: #1a1a2e; color: white; padding: 40px; font-family: Arial, sans-serif; }}
            .container {{ max-width: 1200px; margin: 0 auto; }}
            .nav {{ margin: 20px 0; }}
            .nav a {{ color: #0467FA; margin-right: 15px; text-decoration: none; }}
            .session {{ background: rgba(255,255,255,0.1); padding: 15px; margin: 10px 0; border-radius: 8px; }}
            .session-header {{ display: flex; justify-content: space-between; }}
            .status-waiting {{ color: #FF9800; }} 
            .status-progress {{ color: #4CAF50; }} 
            .status-finished {{ color: #2196F3; }}
            .btn {{ background: #0467FA; color: white; padding: 8px 15px; border: none; border-radius: 5px; cursor: pointer; text-decoration: none; display: inline-block; margin: 5px; }}
            .btn-success {{ background: #4CAF50; }}
            .filter-form {{ background: rgba(255,255,255,0.1); padding: 20px; border-radius: 10px; margin: 20px 0; }}
            .form-group {{ margin: 10px 0; }}
            .form-group label {{ display: block; margin-bottom: 5px; color: white; }}
            .form-group input {{ padding: 8px; border-radius: 5px; border: 1px solid #ccc; background: rgba(255,255,255,0.1); color: white; }}
        </style>
    </head>
    <body>
        <div class="container">
            <h1>💬 Conversas - {config.company_name}</h1>
            
            <div class="nav">
                <a href="/admin">⚙️ Admin</a>
                <a href="/admin/dashboard">📊 Dashboard</a>
                <a href="/admin/tickets">🎫 Tickets</a>
                <a href="/cab/dashboard">📋 CAB</a>
                <a href="/logout" style="color: #ff6b6b;">🚪 Sair</a>
            </div>
            
            <div class="filter-form">
                <h3>📅 Filtrar por Período</h3>
                <form method="get">
                    <div class="form-group">
                        <label>Data Inicial:</label>
                        <input type="date" name="start_date" value="{start_date}">
                    </div>
                    <div class="form-group">
                        <label>Data Final:</label>
                        <input type="date" name="end_date" value="{end_date}">
                    </div>
                    <button type="submit" class="btn">🔍 Filtrar</button>
                    <a href="/admin/chats" class="btn" style="background: #FF9800;">🔄 Limpar Filtro</a>
                </form>
                
                <div style="margin-top: 15px;">
                    <form method="post" action="/admin/export/chats_period" style="display: inline;">
                        <input type="hidden" name="start_date" value="{start_date}">
                        <input type="hidden" name="end_date" value="{end_date}">
                        <button type="submit" class="btn btn-success">📥 Exportar Conversas do Período</button>
                    </form>
                    <a href="/admin/export/all_data" class="btn btn-success">📊 Exportar Todos os Dados</a>
                </div>
            </div>
            
            <h3>Total de Conversas: {len(sessions)}</h3>
    '''
    
    for session in sessions:
        user = User.query.get(session.user_id)
        analyst = User.query.get(session.analyst_id) if session.analyst_id else None
        status_class = f"status-{session.status}"
        
        chats_html += f'''
            <div class="session">
                <div class="session-header">
                    <strong>#{session.id} - {session.category}</strong>
                    <span class="{status_class}">{session.status.upper()}</span>
                </div>
                <div>
                    👤 {user.name if user else 'Usuário'} | 📍 {session.region} | 🕒 {session.created_at.strftime('%d/%m/%Y %H:%M')}
                    {f' | 🛠️ {analyst.name}' if analyst else ''}
                </div>
                <div style="margin-top: 10px;">
                    <a href="/admin/export/chat/{session.id}" class="btn">📥 Baixar Conversa</a>
                </div>
            </div>
        '''
    
    chats_html += f'''
        </div>
    </body>
    </html>
    '''
    
    return chats_html

# CHAT DO USUÁRIO
@app.route('/user/chat_session/<int:sid>', methods=['GET', 'POST'])
def user_chat_session(sid):
    config = get_config()
    u = current_user()
    if not u or u.role != 'user': 
        flash('Acesso negado!', 'error')
        return redirect(url_for('login'))
    
    session = Session.query.get(sid)
    if not session or session.user_id != u.id:
        flash('Sessão não encontrada!', 'error')
        return redirect(url_for('user_chat'))
    
    if request.method == 'POST' and 'file' in request.files:
        file = request.files['file']
        if file and file.filename != '' and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            unique_filename = f"{sid}_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{filename}"
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], 'documents', unique_filename)
            file.save(file_path)
            
            document = Document(
                session_id=sid,
                user_id=u.id,
                filename=unique_filename,
                original_filename=filename,
                file_type=filename.rsplit('.', 1)[1].lower()
            )
            db.session.add(document)
            
            message = Message(
                session_id=sid,
                sender='user',
                content=f"📎 Arquivo enviado: {filename}"
            )
            db.session.add(message)
            db.session.commit()
            
            flash('Arquivo enviado com sucesso!', 'success')
            return redirect(url_for('user_chat_session', sid=sid))
        else:
            flash('Tipo de arquivo não permitido ou arquivo vazio!', 'error')
    
    analyst = User.query.get(session.analyst_id) if session.analyst_id else None
    messages = Message.query.filter_by(session_id=sid).order_by(Message.created_at.asc()).all()
    documents = Document.query.filter_by(session_id=sid).order_by(Document.uploaded_at.asc()).all()
    
    global_styles = apply_global_styles()
    
    chat_form_html = ''
    if session.status == 'in_progress':
        chat_form_html = f'''
            <form method="post" action="/user/send_message/{session.id}" class="chat-form">
                <input type="text" name="message" class="chat-input" placeholder="Digite sua mensagem..." required>
                <button type="submit" class="send-btn">📤 Enviar</button>
            </form>
            
            <div style="margin-top: 15px; background: rgba(255,255,255,0.1); padding: 15px; border-radius: 10px;">
                <h4>📎 Compartilhar Arquivo/Print</h4>
                <form method="post" enctype="multipart/form-data" class="upload-form">
                    <input type="file" name="file" accept=".png,.jpg,.jpeg,.gif,.pdf,.doc,.docx,.txt,.xls,.xlsx,.csv" required>
                    <button type="submit" class="btn" style="background: #9C27B0; margin-top: 10px;">📤 Enviar Arquivo</button>
                </form>
                <p style="font-size: 12px; color: #ccc; margin-top: 5px;">
                    Tipos permitidos: PNG, JPG, GIF, PDF, DOC, TXT, XLS (Max: 16MB)
                </p>
            </div>
        '''
    else:
        chat_form_html = '''
            <div style="text-align: center; padding: 20px; background: rgba(255,255,255,0.1); border-radius: 10px;">
                <p>⏳ Aguardando um analista atender sua solicitação...</p>
            </div>
        '''
    
    chat_html = f'''
    <html>
    <head>
        <title>Chat - {config.company_name}</title>
        {global_styles}
        <style>
            body {{ background: #1a1a2e; color: white; padding: 20px; font-family: Arial, sans-serif; }}
            .container {{ max-width: 1000px; margin: 0 auto; }}
            .chat-header {{ background: rgba(255,255,255,0.1); padding: 15px; border-radius: 10px; margin-bottom: 20px; }}
            .chat-messages {{ height: 400px; overflow-y: auto; background: rgba(255,255,255,0.05); padding: 15px; border-radius: 10px; margin-bottom: 20px; }}
            .message {{ margin-bottom: 15px; padding: 10px; border-radius: 8px; }}
            .message-user {{ background: rgba(4, 103, 250, 0.2); margin-right: 50px; }}
            .message-analyst {{ background: rgba(76, 175, 80, 0.2); margin-left: 50px; }}
            .message-system {{ background: rgba(255, 152, 0, 0.2); text-align: center; }}
            .message-header {{ font-weight: bold; margin-bottom: 5px; }}
            .message-time {{ font-size: 12px; color: #ccc; }}
            .chat-form {{ display: flex; gap: 10px; }}
            .chat-input {{ flex: 1; padding: 10px; background: rgba(255,255,255,0.1); border: 1px solid rgba(255,255,255,0.3); border-radius: 5px; color: white; }}
            .send-btn {{ background: #0467FA; color: white; padding: 10px 20px; border: none; border-radius: 5px; cursor: pointer; }}
            .back-btn {{ background: #6c757d; color: white; padding: 10px 20px; border: none; border-radius: 5px; cursor: pointer; text-decoration: none; display: inline-block; margin-bottom: 15px; }}
            .documents-section {{ background: rgba(255,255,255,0.1); padding: 15px; border-radius: 10px; margin-top: 20px; }}
            .document-item {{ background: rgba(255,255,255,0.05); padding: 10px; margin: 5px 0; border-radius: 5px; display: flex; justify-content: space-between; align-items: center; }}
            .document-info {{ display: flex; align-items: center; gap: 10px; }}
            .document-icon {{ font-size: 20px; }}
            .btn {{ background: #0467FA; color: white; padding: 8px 15px; border: none; border-radius: 5px; cursor: pointer; text-decoration: none; display: inline-block; }}
            .btn-success {{ background: #4CAF50; }}
            .upload-form input[type="file"] {{ background: rgba(255,255,255,0.1); color: white; padding: 8px; border-radius: 5px; border: 1px solid rgba(255,255,255,0.3); }}
        </style>
    </head>
    <body>
        <div class="container">
            <a href="/user/chat" class="back-btn">← Voltar</a>
            
            <div class="chat-header">
                <h2>💬 Chat de Atendimento</h2>
                <p><strong>Sessão:</strong> #{session.id} - {session.category} | <strong>Status:</strong> {session.status.upper()}</p>
                {f'<p><strong>Analista:</strong> {analyst.name if analyst else "Aguardando atribuição"}</p>' if analyst else ''}
            </div>
            
            <div class="chat-messages" id="chatMessages">
    '''
    
    for msg in messages:
        if msg.sender == 'user':
            chat_html += f'''
                <div class="message message-user">
                    <div class="message-header">👤 Você</div>
                    <div>{msg.content}</div>
                    <div class="message-time">{msg.created_at.strftime('%d/%m/%Y %H:%M')}</div>
                </div>
            '''
        elif msg.sender == 'analyst':
            chat_html += f'''
                <div class="message message-analyst">
                    <div class="message-header">🛠️ {analyst.name if analyst else 'Analista'}</div>
                    <div>{msg.content}</div>
                    <div class="message-time">{msg.created_at.strftime('%d/%m/%Y %H:%M')}</div>
                </div>
            '''
        else:
            chat_html += f'''
                <div class="message message-system">
                    <div>⚡ {msg.content}</div>
                    <div class="message-time">{msg.created_at.strftime('%d/%m/%Y %H:%M')}</div>
                </div>
            '''
    
    chat_html += f'''
            </div>
            
            {chat_form_html}
            
            <div class="documents-section">
                <h3>📁 Arquivos Compartilhados</h3>
    '''
    
    if documents:
        for doc in documents:
            file_icon = "🖼️" if doc.file_type in ['png', 'jpg', 'jpeg', 'gif', 'bmp'] else "📄"
            chat_html += f'''
                <div class="document-item">
                    <div class="document-info">
                        <span class="document-icon">{file_icon}</span>
                        <span>{doc.original_filename}</span>
                    </div>
                    <a href="/download/document/{doc.id}" class="btn">📥 Baixar</a>
                </div>
            '''
    else:
        chat_html += '<p style="color: #ccc;">Nenhum arquivo compartilhado ainda</p>'
    
    chat_html += f'''
            </div>
        </div>
        
        <script>
            const chatMessages = document.getElementById('chatMessages');
            chatMessages.scrollTop = chatMessages.scrollHeight;
            
            setInterval(() => {{
                fetch('/user/chat_messages/{session.id}')
                    .then(response => response.text())
                    .then(html => {{
                        const tempDiv = document.createElement('div');
                        tempDiv.innerHTML = html;
                        const newMessages = tempDiv.querySelector('#chatMessages');
                        if (newMessages) {{
                            document.getElementById('chatMessages').innerHTML = newMessages.innerHTML;
                            chatMessages.scrollTop = chatMessages.scrollHeight;
                        }}
                    }});
            }}, 3000);
        </script>
    </body>
    </html>
    '''
    
    return chat_html

@app.route('/user/chat_messages/<int:sid>')
def user_chat_messages(sid):
    u = current_user()
    if not u or u.role != 'user': 
        return "Acesso negado", 403
    
    session = Session.query.get(sid)
    if not session or session.user_id != u.id:
        return "Sessão não encontrada", 404
    
    analyst = User.query.get(session.analyst_id) if session.analyst_id else None
    messages = Message.query.filter_by(session_id=sid).order_by(Message.created_at.asc()).all()
    
    messages_html = '<div id="chatMessages">'
    
    for msg in messages:
        if msg.sender == 'user':
            messages_html += f'''
                <div class="message message-user">
                    <div class="message-header">👤 Você</div>
                    <div>{msg.content}</div>
                    <div class="message-time">{msg.created_at.strftime('%d/%m/%Y %H:%M')}</div>
                </div>
            '''
        elif msg.sender == 'analyst':
            messages_html += f'''
                <div class="message message-analyst">
                    <div class="message-header">🛠️ {analyst.name if analyst else 'Analista'}</div>
                    <div>{msg.content}</div>
                    <div class="message-time">{msg.created_at.strftime('%d/%m/%Y %H:%M')}</div>
                </div>
            '''
        else:
            messages_html += f'''
                <div class="message message-system">
                    <div>⚡ {msg.content}</div>
                    <div class="message-time">{msg.created_at.strftime('%d/%m/%Y %H:%M')}</div>
                </div>
            '''
    
    messages_html += '</div>'
    return messages_html

@app.route('/user/send_message/<int:sid>', methods=['POST'])
def user_send_message(sid):
    u = current_user()
    if not u or u.role != 'user': 
        flash('Acesso negado!', 'error')
        return redirect(url_for('login'))
    
    session = Session.query.get(sid)
    if not session or session.user_id != u.id:
        flash('Sessão não encontrada!', 'error')
        return redirect(url_for('user_chat'))
    
    message_content = request.form.get('message', '').strip()
    if message_content:
        db.session.add(Message(
            session_id=sid,
            sender='user',
            content=message_content
        ))
        db.session.commit()
        flash('Mensagem enviada!', 'success')
    
    return redirect(url_for('user_chat_session', sid=sid))

# CHAT PRINCIPAL DO USUÁRIO
@app.route('/user/chat', methods=['GET', 'POST'])
def user_chat():
    config = get_config()
    u = current_user()
    if not u or u.role != 'user': 
        flash('Acesso negado!', 'error')
        return redirect(url_for('login'))
    
    categories = Category.query.all()
    user_sessions = Session.query.filter_by(user_id=u.id).order_by(Session.created_at.desc()).all()
    
    if request.method == 'POST':
        category = request.form['category']
        message = request.form['message']
        
        s = Session(user_id=u.id, category=category, region=u.region)
        db.session.add(s)
        db.session.commit()
        
        db.session.add(Message(session_id=s.id, sender='user', content=message))
        db.session.commit()
        
        flash('Solicitação enviada com sucesso! Aguarde o atendimento.', 'success')
        return redirect(url_for('user_chat'))
    
    global_styles = apply_global_styles()
    
    user_html = f'''
    <html>
    <head>
        <title>Chat do Usuário</title>
        {global_styles}
        <style>
            body {{ background: #1a1a2e; color: white; padding: 40px; font-family: Arial, sans-serif; }}
            .container {{ max-width: 800px; margin: 0 auto; }}
            .form-section {{ background: rgba(255,255,255,0.1); padding: 20px; border-radius: 10px; margin: 20px 0; }}
            .form-group {{ margin: 15px 0; }}
            .form-group label {{ display: block; margin-bottom: 5px; color: white; }}
            .form-group input, .form-group select, .form-group textarea {{ 
                width: 100%; padding: 10px; background: rgba(255,255,255,0.1); 
                border: 1px solid rgba(255,255,255,0.3); border-radius: 5px; color: white; 
            }}
            .btn {{ background: #0467FA; color: white; padding: 12px 25px; border: none; border-radius: 5px; cursor: pointer; }}
            .btn-chat {{ background: #9C27B0; color: white; padding: 8px 15px; border: none; border-radius: 5px; cursor: pointer; text-decoration: none; display: inline-block; margin: 2px; }}
            .session {{ background: rgba(255,255,255,0.05); padding: 15px; margin: 10px 0; border-radius: 8px; }}
            .status-waiting {{ color: #FF9800; }} .status-progress {{ color: #4CAF50; }} .status-finished {{ color: #2196F3; }}
        </style>
    </head>
    <body>
        <div class="container">
            <h1>💬 Chat de Atendimento - {config.company_name}</h1>
            <p>Bem-vindo, <strong>{u.name}</strong>!</p>
            
            <div class="form-section">
                <h3>📝 Nova Solicitação</h3>
                <form method="post">
                    <div class="form-group">
                        <label>Categoria:</label>
                        <select name="category" required>
                            <option value="">Selecione uma categoria</option>
    '''
    
    for cat in categories:
        user_html += f'<option value="{cat.name}">{cat.area} - {cat.name}</option>'
    
    user_html += f'''
                        </select>
                    </div>
                    <div class="form-group">
                        <label>Descreva seu problema:</label>
                        <textarea name="message" rows="4" required placeholder="Descreva detalhadamente o que você precisa..."></textarea>
                    </div>
                    <button type="submit" class="btn">🚀 Enviar Solicitação</button>
                </form>
            </div>
            
            <div class="form-section">
                <h3>📋 Minhas Solicitações ({len(user_sessions)})</h3>
    '''
    
    if not user_sessions:
        user_html += '<p style="color: #ccc;">Nenhuma solicitação encontrada</p>'
    else:
        for session in user_sessions:
            status_class = f"status-{session.status}"
            status_text = {
                'waiting': '⏳ AGUARDANDO',
                'in_progress': '🟢 EM ATENDIMENTO', 
                'finished': '✅ FINALIZADO'
            }.get(session.status, session.status.upper())
            
            user_html += f'''
                <div class="session">
                    <strong>#{session.id} - {session.category}</strong> | 
                    <span class="{status_class}">{status_text}</span><br>
                    🕒 {session.created_at.strftime('%d/%m/%Y %H:%M')}
                    <div style="margin-top: 10px;">
                        <a href="/user/chat_session/{session.id}" class="btn-chat">💬 Ver Chat</a>
                    </div>
                </div>
            '''
    
    user_html += f'''
            </div>
            
            <div style="margin-top: 30px;">
                <a href="/user/dashboard" class="btn">🎫 Meus Tickets</a>
                <a href="/logout" style="color: #ff6b6b; margin-left: 15px;">🚪 Sair</a>
            </div>
        </div>
    </body>
    </html>
    '''
    
    return user_html

# DASHBOARD DO USUÁRIO
@app.route('/user/dashboard')
def user_dashboard():
    config = get_config()
    u = current_user()
    if not u: 
        flash('Acesso negado!', 'error')
        return redirect(url_for('login'))
    
    user_tickets = Ticket.query.filter_by(created_by=u.id).order_by(Ticket.created_at.desc()).all()
    open_tickets = [t for t in user_tickets if t.status in ['open', 'in_progress', 'pending_approval']]
    
    global_styles = apply_global_styles()
    
    user_html = f'''
    <!DOCTYPE html>
    <html lang="pt-BR">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>{config.company_name} - Meus Tickets</title>
        {global_styles}
        <style>
            * {{ margin: 0; padding: 0; box-sizing: border-box; font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; }}
            body {{ background: linear-gradient(135deg, #0c0c0c 0%, #1a1a2e 50%, #16213e 100%); min-height: 100vh; color: white; }}
            .header {{ background: rgba(255, 255, 255, 0.05); backdrop-filter: blur(20px); border-bottom: 1px solid rgba(255, 255, 255, 0.1); padding: 20px 40px; }}
            .header-content {{ display: flex; justify-content: space-between; align-items: center; max-width: 1200px; margin: 0 auto; }}
            .logo-section {{ display: flex; align-items: center; gap: 15px; }}
            .logo-text h1 {{ font-size: 24px; font-weight: 300; }}
            .user-actions {{ display: flex; gap: 15px; align-items: center; }}
            .btn {{ background: {config.primary_color}; color: white; padding: 10px 20px; border: none; border-radius: 8px; cursor: pointer; text-decoration: none; display: inline-block; }}
            .btn-success {{ background: #4CAF50; }}
            .main-container {{ max-width: 1200px; margin: 0 auto; padding: 40px; }}
            .stats-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 20px; margin-bottom: 40px; }}
            .stat-card {{ background: rgba(255, 255, 255, 0.05); border: 1px solid rgba(255, 255, 255, 0.1); border-radius: 15px; padding: 20px; text-align: center; }}
            .stat-number {{ font-size: 32px; font-weight: bold; margin: 10px 0; }}
            .card {{ background: rgba(255, 255, 255, 0.05); border: 1px solid rgba(255, 255, 255, 0.1); border-radius: 15px; padding: 25px; margin-bottom: 20px; }}
            .card-header {{ display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px; }}
            .ticket-list {{ display: grid; gap: 15px; }}
            .ticket-item {{ background: rgba(255, 255, 255, 0.05); border: 1px solid rgba(255, 255, 255, 0.1); border-radius: 10px; padding: 15px; color: white; }}
            .ticket-header {{ display: flex; justify-content: space-between; margin-bottom: 10px; }}
            .ticket-number {{ font-weight: bold; color: {config.primary_color}; }}
            .ticket-status {{ padding: 4px 8px; border-radius: 4px; font-size: 12px; }}
            .status-open {{ background: #FF9800; }} .status-in_progress {{ background: #2196F3; }} .status-pending_approval {{ background: #9C27B0; }} .status-resolved {{ background: #4CAF50; }}
            .nav-tabs {{ display: flex; gap: 10px; margin-bottom: 20px; }}
            .tab-btn {{ padding: 10px 20px; background: rgba(255,255,255,0.1); border: none; border-radius: 5px; color: white; cursor: pointer; }}
            .tab-btn.active {{ background: {config.primary_color}; }}
            .tab-content {{ display: none; }}
            .tab-content.active {{ display: block; }}
        </style>
    </head>
    <body>
        <div class="header">
            <div class="header-content">
                <div class="logo-section">
                    <div class="logo-text"><h1>{config.company_name} - Meus Tickets</h1></div>
                </div>
                <div class="user-actions">
                    <a href="/user/tickets/new" class="btn btn-success">➕ Novo Ticket</a>
                    <a href="/user/chat" class="btn">💬 Chat</a>
                    <a href="/logout" class="btn" style="background: #ff6b6b;">🚪 Sair</a>
                </div>
            </div>
        </div>

        <div class="main-container">
            <div class="stats-grid">
                <div class="stat-card">
                    <div>🎫</div>
                    <div class="stat-number">{len(user_tickets)}</div>
                    <div>Total de Tickets</div>
                </div>
                <div class="stat-card">
                    <div>⏳</div>
                    <div class="stat-number">{len(open_tickets)}</div>
                    <div>Em Aberto</div>
                </div>
                <div class="stat-card">
                    <div>✅</div>
                    <div class="stat-number">{len(user_tickets) - len(open_tickets)}</div>
                    <div>Resolvidos</div>
                </div>
            </div>

            <div class="nav-tabs">
                <button class="tab-btn active" onclick="openTab('tab-open')">⏳ Em Aberto ({len(open_tickets)})</button>
                <button class="tab-btn" onclick="openTab('tab-all')">📋 Todos os Tickets ({len(user_tickets)})</button>
            </div>

            <div id="tab-open" class="tab-content active">
                <div class="card">
                    <div class="card-header">
                        <h3>⏳ Tickets em Aberto</h3>
                    </div>
                    <div class="ticket-list">
    '''
    
    if not open_tickets:
        user_html += '<p style="color: #ccc;">Nenhum ticket em aberto</p>'
    else:
        for ticket in open_tickets:
            status_class = f"status-{ticket.status}"
            user_html += f'''
                        <div class="ticket-item">
                            <div class="ticket-header">
                                <span class="ticket-number">{ticket.number}</span>
                                <span class="ticket-status {status_class}">{ticket.status.replace('_', ' ').title()}</span>
                            </div>
                            <div><strong>{ticket.title}</strong></div>
                            <div style="font-size: 14px; color: #ccc; margin-top: 5px;">
                                Criado em: {ticket.created_at.strftime('%d/%m/%Y %H:%M')} | 
                                Prioridade: {ticket.priority} |
                                Grupo: {ticket.group.name if ticket.group else 'Não atribuído'}
                            </div>
                            <div style="margin-top: 10px;">
                                <a href="/ticket/{ticket.id}" class="btn">👁️ Ver Detalhes</a>
                            </div>
                        </div>
            '''
    
    user_html += f'''
                    </div>
                </div>
            </div>

            <div id="tab-all" class="tab-content">
                <div class="card">
                    <div class="card-header">
                        <h3>📋 Todos os Tickets</h3>
                    </div>
                    <div class="ticket-list">
    '''
    
    if not user_tickets:
        user_html += '<p style="color: #ccc;">Nenhum ticket encontrado</p>'
    else:
        for ticket in user_tickets:
            status_class = f"status-{ticket.status}"
            user_html += f'''
                        <div class="ticket-item">
                            <div class="ticket-header">
                                <span class="ticket-number">{ticket.number}</span>
                                <span class="ticket-status {status_class}">{ticket.status.replace('_', ' ').title()}</span>
                            </div>
                            <div><strong>{ticket.title}</strong></div>
                            <div style="font-size: 14px; color: #ccc; margin-top: 5px;">
                                Criado em: {ticket.created_at.strftime('%d/%m/%Y %H:%M')} | 
                                Prioridade: {ticket.priority} |
                                Status: {ticket.status.replace('_', ' ').title()}
                            </div>
                            <div style="margin-top: 10px;">
                                <a href="/ticket/{ticket.id}" class="btn">👁️ Ver Detalhes</a>
                            </div>
                        </div>
            '''
    
    user_html += f'''
                    </div>
                </div>
            </div>
        </div>

        <script>
            function openTab(tabName) {{
                document.querySelectorAll('.tab-content').forEach(tab => {{
                    tab.classList.remove('active');
                }});
                document.querySelectorAll('.tab-btn').forEach(btn => {{
                    btn.classList.remove('active');
                }});
                document.getElementById(tabName).classList.add('active');
                event.currentTarget.classList.add('active');
            }}
        </script>
    </body>
    </html>
    '''
    
    return user_html

# TICKETS ADMIN
@app.route('/admin/tickets')
def admin_tickets():
    return redirect('/analyst/tickets')

# DOWNLOAD DE DOCUMENTOS
@app.route('/download/document/<int:doc_id>')
def download_document(doc_id):
    u = current_user()
    if not u:
        flash('Acesso negado!', 'error')
        return redirect(url_for('login'))
    
    document = Document.query.get(doc_id)
    if not document:
        flash('Documento não encontrado!', 'error')
        return redirect(url_for('index'))
    
    session = Session.query.get(document.session_id)
    if u.role == 'user' and session.user_id != u.id:
        flash('Acesso negado!', 'error')
        return redirect(url_for('index'))
    elif u.role == 'analyst' and session.analyst_id != u.id:
        flash('Acesso negado!', 'error')
        return redirect(url_for('index'))
    
    file_path = os.path.join(app.config['UPLOAD_FOLDER'], 'documents', document.filename)
    
    if os.path.exists(file_path):
        return send_file(
            file_path,
            as_attachment=True,
            download_name=document.original_filename
        )
    else:
        flash('Arquivo não encontrado!', 'error')
        return redirect(url_for('index'))

# VISUALIZAR IMAGENS
@app.route('/view/image/<int:doc_id>')
def view_image(doc_id):
    u = current_user()
    if not u:
        return "Acesso negado", 403
    
    document = Document.query.get(doc_id)
    if not document or document.file_type not in ['png', 'jpg', 'jpeg', 'gif', 'bmp']:
        return "Arquivo não encontrado ou não é imagem", 404
    
    session = Session.query.get(document.session_id)
    if u.role == 'user' and session.user_id != u.id:
        return "Acesso negado", 403
    elif u.role == 'analyst' and session.analyst_id != u.id:
        return "Acesso negado", 403
    
    file_path = os.path.join(app.config['UPLOAD_FOLDER'], 'documents', document.filename)
    
    if os.path.exists(file_path):
        return f'''
        <html>
        <head>
            <title>{document.original_filename}</title>
            <style>
                body {{ margin: 0; padding: 20px; background: #1a1a2e; display: flex; flex-direction: column; align-items: center; }}
                img {{ max-width: 90vw; max-height: 80vh; border-radius: 10px; }}
                .back-btn {{ background: #0467FA; color: white; padding: 10px 20px; border: none; border-radius: 5px; cursor: pointer; text-decoration: none; margin-bottom: 20px; }}
            </style>
        </head>
        <body>
            <a href="javascript:history.back()" class="back-btn">← Voltar</a>
            <img src="/static/uploads/documents/{document.filename}" alt="{document.original_filename}">
        </body>
        </html>
        '''
    else:
        return "Arquivo não encontrado", 404

# EXPORTAÇÃO DE DADOS
@app.route('/admin/export/chat/<int:sid>')
def export_chat(sid):
    u = current_user()
    if not u or u.role != 'admin': 
        return redirect(url_for('login'))
    
    session = Session.query.get(sid)
    if not session:
        return "Sessão não encontrada", 404
    
    messages = Message.query.filter_by(session_id=sid).order_by(Message.created_at.asc()).all()
    user = User.query.get(session.user_id)
    analyst = User.query.get(session.analyst_id) if session.analyst_id else None
    
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(['Conversa #{}'.format(sid)])
    writer.writerow(['Conversa #{}'.format(sid)])
    writer.writerow(['Usuário:', user.name if user else 'N/A'])
    writer.writerow(['Analista:', analyst.name if analyst else 'N/A'])
    writer.writerow(['Categoria:', session.category])
    writer.writerow(['Região:', session.region])
    writer.writerow(['Status:', session.status])
    writer.writerow(['Data Criação:', session.created_at.strftime('%d/%m/%Y %H:%M')])
    writer.writerow([])
    writer.writerow(['Data/Hora', 'Remetente', 'Mensagem'])
    
    for msg in messages:
        sender_name = ''
        if msg.sender == 'user':
            sender_name = user.name if user else 'Usuário'
        elif msg.sender == 'analyst':
            sender_name = analyst.name if analyst else 'Analista'
        else:
            sender_name = 'Sistema'
        
        writer.writerow([
            msg.created_at.strftime('%d/%m/%Y %H:%M'),
            sender_name,
            msg.content
        ])
    
    output.seek(0)
    return send_file(
        io.BytesIO(output.getvalue().encode('utf-8')),
        as_attachment=True,
        download_name=f'conversa_{sid}_{session.created_at.strftime("%Y%m%d")}.csv',
        mimetype='text/csv'
    )

@app.route('/admin/export/chats_period', methods=['POST'])
def export_chats_period():
    u = current_user()
    if not u or u.role != 'admin': 
        return redirect(url_for('login'))
    
    start_date = request.form.get('start_date', '')
    end_date = request.form.get('end_date', '')
    
    query = Session.query
    
    if start_date:
        try:
            start = datetime.strptime(start_date, '%Y-%m-%d')
            query = query.filter(Session.created_at >= start)
        except ValueError:
            pass
    
    if end_date:
        try:
            end = datetime.strptime(end_date, '%Y-%m-%d')
            end = end.replace(hour=23, minute=59, second=59)
            query = query.filter(Session.created_at <= end)
        except ValueError:
            pass
    
    sessions = query.order_by(Session.created_at.desc()).all()
    
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(['Relatório de Conversas - Período: {} a {}'.format(start_date, end_date)])
    writer.writerow([])
    writer.writerow(['ID', 'Usuário', 'Analista', 'Categoria', 'Região', 'Status', 'Data Criação', 'Data Atendimento', 'Data Término'])
    
    for session in sessions:
        user = User.query.get(session.user_id)
        analyst = User.query.get(session.analyst_id) if session.analyst_id else None
        
        writer.writerow([
            session.id,
            user.name if user else 'N/A',
            analyst.name if analyst else 'N/A',
            session.category,
            session.region,
            session.status,
            session.created_at.strftime('%d/%m/%Y %H:%M'),
            session.assigned_at.strftime('%d/%m/%Y %H:%M') if session.assigned_at else '',
            session.finished_at.strftime('%d/%m/%Y %H:%M') if session.finished_at else ''
        ])
    
    output.seek(0)
    filename = f'conversas_periodo_{start_date}_a_{end_date}.csv'
    return send_file(
        io.BytesIO(output.getvalue().encode('utf-8')),
        as_attachment=True,
        download_name=filename,
        mimetype='text/csv'
    )

@app.route('/admin/export/all_data')
def export_all_data():
    u = current_user()
    if not u or u.role != 'admin': 
        return redirect(url_for('login'))
    
    # Criar arquivo ZIP
    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
        
        # Dados das sessões
        sessions = Session.query.all()
        sessions_output = io.StringIO()
        sessions_writer = csv.writer(sessions_output)
        sessions_writer.writerow(['ID', 'Usuário', 'Analista', 'Categoria', 'Região', 'Status', 'Data Criação', 'Data Atendimento', 'Data Término'])
        
        for session in sessions:
            user = User.query.get(session.user_id)
            analyst = User.query.get(session.analyst_id) if session.analyst_id else None
            
            sessions_writer.writerow([
                session.id,
                user.name if user else 'N/A',
                analyst.name if analyst else 'N/A',
                session.category,
                session.region,
                session.status,
                session.created_at.strftime('%d/%m/%Y %H:%M'),
                session.assigned_at.strftime('%d/%m/%Y %H:%M') if session.assigned_at else '',
                session.finished_at.strftime('%d/%m/%Y %H:%M') if session.finished_at else ''
            ])
        
        zip_file.writestr('sessoes.csv', sessions_output.getvalue())
        
        # Dados dos tickets
        tickets = Ticket.query.all()
        tickets_output = io.StringIO()
        tickets_writer = csv.writer(tickets_output)
        tickets_writer.writerow(['Número', 'Título', 'Tipo', 'Status', 'Prioridade', 'Criado Por', 'Atribuído A', 'Grupo', 'Categoria', 'Data Criação', 'Data Atualização'])
        
        for ticket in tickets:
            creator = User.query.get(ticket.created_by)
            assignee = User.query.get(ticket.assigned_to) if ticket.assigned_to else None
            group = ticket.group.name if ticket.group else ''
            category = ticket.category.name if ticket.category else ''
            
            tickets_writer.writerow([
                ticket.number,
                ticket.title,
                ticket.type,
                ticket.status,
                ticket.priority,
                creator.name if creator else 'N/A',
                assignee.name if assignee else 'N/A',
                group,
                category,
                ticket.created_at.strftime('%d/%m/%Y %H:%M'),
                ticket.updated_at.strftime('%d/%m/%Y %H:%M')
            ])
        
        zip_file.writestr('tickets.csv', tickets_output.getvalue())
        
        # Dados dos usuários
        users = User.query.all()
        users_output = io.StringIO()
        users_writer = csv.writer(users_output)
        users_writer.writerow(['Nome', 'Usuário', 'Email', 'Departamento', 'Cargo', 'Região', 'Função', 'Online', 'Grupo'])
        
        for user in users:
            group_name = user.support_group.name if user.support_group else ''
            
            users_writer.writerow([
                user.name,
                user.username,
                user.email or '',
                user.department or '',
                user.position or '',
                user.region,
                user.role,
                'Sim' if user.online else 'Não',
                group_name
            ])
        
        zip_file.writestr('usuarios.csv', users_output.getvalue())
    
    zip_buffer.seek(0)
    return send_file(
        zip_buffer,
        as_attachment=True,
        download_name=f'dados_completos_{datetime.now().strftime("%Y%m%d_%H%M")}.zip',
        mimetype='application/zip'
    )

# ROTA PARA ADICIONAR COMENTÁRIO AO TICKET
@app.route('/ticket/<int:ticket_id>/comment', methods=['POST'])
def add_ticket_comment(ticket_id):
    u = current_user()
    if not u or u.role not in ['analyst', 'admin']: 
        flash('Acesso negado!', 'error')
        return redirect(url_for('login'))
    
    ticket = Ticket.query.get_or_404(ticket_id)
    content = request.form.get('content', '').strip()
    is_internal = bool(request.form.get('is_internal'))
    mark_resolved = bool(request.form.get('mark_resolved'))
    resolution_notes = request.form.get('resolution_notes', '').strip()
    
    if content:
        comment = TicketComment(
            ticket_id=ticket_id,
            user_id=u.id,
            content=content,
            is_internal=is_internal
        )
        db.session.add(comment)
        
        # Processar anexo se houver
        if 'attachment' in request.files:
            file = request.files['attachment']
            if file and file.filename != '' and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                unique_filename = f"ticket_{ticket.id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{filename}"
                file_path = os.path.join(app.config['UPLOAD_FOLDER'], 'documents', unique_filename)
                file.save(file_path)
                
                document = Document(
                    session_id=0,
                    user_id=u.id,
                    filename=unique_filename,
                    original_filename=filename,
                    file_type=filename.rsplit('.', 1)[1].lower()
                )
                db.session.add(document)
                
                # Adicionar comentário sobre o arquivo
                file_comment = TicketComment(
                    ticket_id=ticket_id,
                    user_id=u.id,
                    content=f"📎 Arquivo anexado: {filename}",
                    is_internal=is_internal
                )
                db.session.add(file_comment)
        
        # Marcar como resolvido se solicitado
        if mark_resolved and resolution_notes:
            ticket.status = 'resolved'
            ticket.resolution_notes = resolution_notes
            ticket.resolved_at = now_brasilia()
            
            # Adicionar comentário de resolução
            resolution_comment = TicketComment(
                ticket_id=ticket_id,
                user_id=u.id,
                content=f"✅ SOLUÇÃO APLICADA: {resolution_notes}",
                is_internal=False
            )
            db.session.add(resolution_comment)
        
        db.session.commit()
        flash('Comentário adicionado com sucesso!', 'success')
    
    return redirect(f'/ticket/{ticket_id}')

# ROTA DO GERENTE PARA APROVAR TICKET
@app.route('/manager/ticket/<int:ticket_id>', methods=['GET', 'POST'])
def manager_ticket_detail(ticket_id):
    config = get_config()
    u = current_user()
    if not u or (not u.manager and not u.senior_manager): 
        flash('Acesso negado!', 'error')
        return redirect(url_for('login'))
    
    ticket = Ticket.query.get_or_404(ticket_id)
    creator = User.query.get(ticket.created_by)
    
    # Verificar se o gerente tem permissão para aprovar este ticket
    if u.manager and creator.manager_id != u.id:
        flash('Acesso negado! Você não é o gerente responsável por este colaborador.', 'error')
        return redirect('/manager/dashboard')
    
    if u.senior_manager and creator.senior_manager_id != u.id:
        flash('Acesso negado! Você não é o gerente sênior responsável por este colaborador.', 'error')
        return redirect('/manager/dashboard')
    
    if request.method == 'POST':
        action = request.form.get('action')
        
        if action == 'approve':
            ticket.status = 'in_progress'
            ticket.current_owner = None
            db.session.commit()
            flash('Ticket aprovado com sucesso!', 'success')
        elif action == 'reject':
            ticket.status = 'open'
            ticket.current_owner = None
            ticket.pending_reason = request.form.get('rejection_reason', '')
            db.session.commit()
            flash('Ticket rejeitado!', 'warning')
        
        return redirect(f'/manager/ticket/{ticket_id}')
    
    comments = TicketComment.query.filter_by(ticket_id=ticket_id).order_by(TicketComment.created_at).all()
    
    global_styles = apply_global_styles()
    
    manager_ticket_html = f'''
    <!DOCTYPE html>
    <html lang="pt-BR">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Aprovar Ticket {ticket.number}</title>
        {global_styles}
        <style>
            * {{ margin: 0; padding: 0; box-sizing: border-box; font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; }}
            body {{ background: linear-gradient(135deg, #0c0c0c 0%, #1a1a2e 50%, #16213e 100%); min-height: 100vh; color: white; }}
            .header {{ background: rgba(255, 255, 255, 0.05); backdrop-filter: blur(20px); border-bottom: 1px solid rgba(255, 255, 255, 0.1); padding: 20px 40px; }}
            .header-content {{ display: flex; justify-content: space-between; align-items: center; max-width: 1000px; margin: 0 auto; }}
            .btn {{ background: {config.primary_color}; color: white; padding: 10px 20px; border: none; border-radius: 8px; cursor: pointer; text-decoration: none; display: inline-block; }}
            .main-container {{ max-width: 1000px; margin: 0 auto; padding: 40px; }}
            .card {{ background: rgba(255, 255, 255, 0.05); border: 1px solid rgba(255, 255, 255, 0.1); border-radius: 15px; padding: 25px; margin-bottom: 20px; }}
            .ticket-header {{ display: grid; grid-template-columns: 1fr 1fr; gap: 20px; margin-bottom: 20px; }}
            .ticket-info div {{ margin-bottom: 10px; }}
            .status-badge {{ padding: 5px 10px; border-radius: 5px; font-weight: bold; }}
            .priority-Low {{ background: #4CAF50; }} .priority-Medium {{ background: #FF9800; }} 
            .priority-High {{ background: #f44336; }} .priority-Critical {{ background: #9C27B0; }}
            .comments-section {{ margin-top: 30px; }}
            .comment {{ background: rgba(255,255,255,0.05); padding: 15px; border-radius: 10px; margin-bottom: 15px; }}
            .comment-header {{ display: flex; justify-content: space-between; margin-bottom: 10px; font-size: 14px; color: #ccc; }}
            .comment-internal {{ border-left: 3px solid #FF9800; background: rgba(255,152,0,0.1); }}
            .approval-actions {{ background: rgba(255,255,255,0.1); padding: 20px; border-radius: 10px; margin-top: 20px; }}
            .form-group {{ margin-bottom: 15px; }}
            .form-group label {{ display: block; margin-bottom: 5px; color: white; }}
            .form-group textarea {{ width: 100%; padding: 10px; background: rgba(255,255,255,0.1); border: 1px solid rgba(255,255,255,0.3); border-radius: 5px; color: white; }}
            .btn-success {{ background: #4CAF50; }} .btn-danger {{ background: #f44336; }}
        </style>
    </head>
    <body>
        <div class="header">
            <div class="header-content">
                <h1>👨‍💼 Aprovar Ticket {ticket.number}</h1>
                <a href="/manager/dashboard" class="btn">← Voltar</a>
            </div>
        </div>

        <div class="main-container">
            <div class="card">
                <div class="ticket-header">
                    <div class="ticket-info">
                        <div><strong>Título:</strong> {ticket.title}</div>
                        <div><strong>Status:</strong> <span class="status-badge" style="background: #9C27B0;">AGUARDANDO APROVAÇÃO</span></div>
                        <div><strong>Prioridade:</strong> <span class="status-badge priority-{ticket.priority}">{ticket.priority}</span></div>
                        <div><strong>Tipo:</strong> {'🚨 Incidente' if ticket.type == 'incident' else '📋 Solicitação'}</div>
                    </div>
                    <div class="ticket-info">
                        <div><strong>Criado por:</strong> {creator.name}</div>
                        <div><strong>Departamento:</strong> {creator.department}</div>
                        <div><strong>Data:</strong> {ticket.created_at.strftime('%d/%m/%Y %H:%M')}</div>
                        <div><strong>Categoria:</strong> {ticket.category.name if ticket.category else 'N/A'}</div>
                        <div><strong>Subcategoria:</strong> {ticket.subcategory.name if ticket.subcategory else 'N/A'}</div>
                    </div>
                </div>
                
                <div>
                    <h3>Descrição:</h3>
                    <p>{ticket.description}</p>
                </div>

                <div class="approval-actions">
                    <h3>✅ Ação de Aprovação</h3>
                    <form method="post">
                        <div class="form-group">
                            <label for="rejection_reason">Motivo da rejeição (se aplicável):</label>
                            <textarea name="rejection_reason" rows="3" placeholder="Explique por que está rejeitando esta solicitação..."></textarea>
                        </div>
                        <div style="display: flex; gap: 10px; margin-top: 15px;">
                            <button type="submit" name="action" value="approve" class="btn btn-success">✅ Aprovar Solicitação</button>
                            <button type="submit" name="action" value="reject" class="btn btn-danger">❌ Rejeitar Solicitação</button>
                        </div>
                    </form>
                </div>
            </div>

            <div class="card comments-section">
                <h3>💬 Histórico do Ticket</h3>
    '''
    
    if comments:
        for comment in comments:
            internal_class = 'comment-internal' if comment.is_internal else ''
            internal_badge = ' 🔒 Interno' if comment.is_internal else ''
            manager_ticket_html += f'''
                <div class="comment {internal_class}">
                    <div class="comment-header">
                        <span>{comment.user.name if comment.user else 'Sistema'}{internal_badge}</span>
                        <span>{comment.created_at.strftime('%d/%m/%Y %H:%M')}</span>
                    </div>
                    <div>{comment.content}</div>
                </div>
            '''
    else:
        manager_ticket_html += '<p style="color: #ccc;">Nenhum comentário ainda.</p>'
    
    manager_ticket_html += '''
            </div>
        </div>
    </body>
    </html>
    '''
    
    return manager_ticket_html

# ROTA PARA GERENCIAR SUBCATEGORIAS
@app.route('/admin/subcategories')
def admin_subcategories():
    config = get_config()
    u = current_user()
    if not u or u.role != 'admin': 
        flash('Acesso negado!', 'error')
        return redirect(url_for('login'))
    
    categories = TicketCategory.query.all()
    subcategories = SubCategory.query.all()
    
    global_styles = apply_global_styles()
    
    subcategories_html = f'''
    <!DOCTYPE html>
    <html lang="pt-BR">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Subcategorias - {config.company_name}</title>
        {global_styles}
        <style>
            * {{ margin: 0; padding: 0; box-sizing: border-box; font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; }}
            body {{ background: linear-gradient(135deg, #0c0c0c 0%, #1a1a2e 50%, #16213e 100%); min-height: 100vh; color: white; }}
            .header {{ background: rgba(255, 255, 255, 0.05); backdrop-filter: blur(20px); border-bottom: 1px solid rgba(255, 255, 255, 0.1); padding: 20px 40px; }}
            .header-content {{ display: flex; justify-content: space-between; align-items: center; max-width: 1400px; margin: 0 auto; }}
            .btn {{ background: {config.primary_color}; color: white; padding: 10px 20px; border: none; border-radius: 8px; cursor: pointer; text-decoration: none; display: inline-block; }}
            .main-container {{ max-width: 1400px; margin: 0 auto; padding: 40px; }}
            .card {{ background: rgba(255, 255, 255, 0.05); border: 1px solid rgba(255, 255, 255, 0.1); border-radius: 15px; padding: 25px; margin-bottom: 20px; }}
            .form-group {{ margin-bottom: 20px; }}
            .form-group label {{ display: block; margin-bottom: 8px; color: white; }}
            .form-group input, .form-group select, .form-group textarea {{ 
                width: 100%; padding: 12px; background: rgba(255, 255, 255, 0.1); 
                border: 1px solid rgba(255, 255, 255, 0.3); border-radius: 8px; 
                color: white; font-size: 16px;
            }}
            .form-group textarea {{ height: 100px; resize: vertical; }}
            .btn-success {{ background: #4CAF50; }} .btn-danger {{ background: #f44336; }}
            table {{ width: 100%; border-collapse: collapse; margin-top: 20px; }}
            th {{ background: rgba(255, 255, 255, 0.1); padding: 15px; text-align: left; font-weight: 600; }}
            td {{ padding: 15px; border-bottom: 1px solid rgba(255, 255, 255, 0.05); }}
            tr:hover {{ background: rgba(255, 255, 255, 0.02); }}
            .action-buttons {{ display: flex; gap: 5px; }}
            .requires-approval {{ color: #FF9800; font-weight: bold; }}
        </style>
    </head>
    <body>
        <div class="header">
            <div class="header-content">
                <h1>📋 Gerenciar Subcategorias</h1>
                <a href="/admin" class="btn">← Voltar ao Admin</a>
            </div>
        </div>

        <div class="main-container">
            <div class="card">
                <h3>➕ Nova Subcategoria</h3>
                <form method="post" action="/admin/create_subcategory">
                    <div class="form-group">
                        <label>Nome:</label>
                        <input type="text" name="name" required>
                    </div>
                    <div class="form-group">
                        <label>Descrição:</label>
                        <textarea name="description" required></textarea>
                    </div>
                    <div class="form-group">
                        <label>Categoria Pai:</label>
                        <select name="category_id" required>
                            <option value="">Selecione uma categoria</option>
                            {"".join([f'<option value="{cat.id}">{cat.name}</option>' for cat in categories])}
                        </select>
                    </div>
                    <div class="form-group">
                        <label>
                            <input type="checkbox" name="requires_approval" value="1">
                            Requer aprovação do gerente
                        </label>
                    </div>
                    <button type="submit" class="btn btn-success">💾 Criar Subcategoria</button>
                </form>
            </div>

            <div class="card">
                <h3>📋 Subcategorias Existentes</h3>
                <table>
                    <thead>
                        <tr>
                            <th>Nome</th>
                            <th>Descrição</th>
                            <th>Categoria</th>
                            <th>Aprovação</th>
                            <th>Ações</th>
                        </tr>
                    </thead>
                    <tbody>
    '''
    
    for subcat in subcategories:
        category = TicketCategory.query.get(subcat.category_id)
        requires_approval = "✅ Sim" if subcat.requires_approval else "❌ Não"
        approval_class = "requires-approval" if subcat.requires_approval else ""
        
        subcategories_html += f'''
                        <tr>
                            <td>{subcat.name}</td>
                            <td>{subcat.description}</td>
                            <td>{category.name if category else 'N/A'}</td>
                            <td class="{approval_class}">{requires_approval}</td>
                            <td class="action-buttons">
                                <form method="post" action="/admin/delete_subcategory/{subcat.id}" style="display: inline;">
                                    <button type="submit" class="btn btn-danger" onclick="return confirm('Deletar subcategoria {subcat.name}?')">❌</button>
                                </form>
                            </td>
                        </tr>
        '''
    
    subcategories_html += f'''
                    </tbody>
                </table>
            </div>
        </div>
    </body>
    </html>
    '''
    
    return subcategories_html

@app.route('/admin/create_subcategory', methods=['POST'])
def admin_create_subcategory():
    u = current_user()
    if not u or u.role != 'admin': 
        flash('Acesso negado!', 'error')
        return redirect(url_for('login'))
    
    subcategory = SubCategory(
        name=request.form['name'],
        description=request.form['description'],
        category_id=request.form['category_id'],
        requires_approval=bool(request.form.get('requires_approval'))
    )
    db.session.add(subcategory)
    db.session.commit()
    flash('Subcategoria criada com sucesso!', 'success')
    return redirect('/admin/subcategories')

@app.route('/admin/delete_subcategory/<int:subcategory_id>', methods=['POST'])
def admin_delete_subcategory(subcategory_id):
    u = current_user()
    if not u or u.role != 'admin': 
        flash('Acesso negado!', 'error')
        return redirect(url_for('login'))
    
    subcategory = SubCategory.query.get(subcategory_id)
    if subcategory:
        # Verificar se há tickets usando esta subcategoria
        tickets_count = Ticket.query.filter_by(subcategory_id=subcategory_id).count()
        if tickets_count > 0:
            flash(f'Não é possível deletar esta subcategoria pois existem {tickets_count} tickets vinculados a ela!', 'error')
        else:
            db.session.delete(subcategory)
            db.session.commit()
            flash('Subcategoria deletada com sucesso!', 'success')
    
    return redirect('/admin/subcategories')

# INICIALIZAR O BANCO DE DADOS
# FUNÇÕES PARA URLS DE REDE - ADICIONAR ANTES DO if __name__
def get_local_ip():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except:
        return "127.0.0.1"

def get_network_urls():
    """Obtém todas as URLs possíveis para acesso na rede"""
    local_ip = get_local_ip()
    urls = [
        f"http://localhost:5000",
        f"http://127.0.0.1:5000", 
        f"http://{local_ip}:5000"
    ]
    
    # Tentar descobrir o nome da máquina na rede
    try:
        hostname = socket.gethostname()
        urls.append(f"http://{hostname}.local:5000")
        urls.append(f"http://{hostname}:5000")
    except:
        pass
        
    return urls

# SUBSTITUIR O BLOCO if __name__ == '__main__' ORIGINAL POR ESTE:
if __name__ == '__main__':
    # Verificar licença no startup
    license_status = license_manager.check_license_status()
    
    # Tentar inicializar o banco
    db_initialized = init_db()
    
    if not db_initialized and license_status['status'] in ['expired', 'invalid']:
        print("❌ SISTEMA BLOQUEADO - LICENÇA INVÁLIDA")
        print("💡 Acesse http://localhost:5000/license para ativar uma licença válida")
    
    # Obter URLs de acesso
    urls = get_network_urls()
    
    print("=" * 70)
    print("🎯 HELP DESK HUB - SISTEMA LICENCIADO")
    print("=" * 70)
    print("📍 URLs DE ACESSO:")
    for url in urls:
        print(f"   🌐 {url}")
    print("=" * 70)
    print("📋 STATUS DA LICENÇA:")
    print(f"   {license_status['message']}")
    print("=" * 70)
    
    if license_status['status'] == 'trial':
        print("🚀 MODO TRIAL ATIVO - " + str(license_status['days_left']) + " DIAS RESTANTES")
    elif license_status['status'] == 'licensed':
        print("✅ SISTEMA LICENCIADO - " + str(license_status['days_left']) + " DIAS RESTANTES")
    
    print("=" * 70)
    print("👑 ADMIN: usuario: admin | senha: Hubdesk.1988")
    print("🛠️ ANALISTA: usuario: analista | senha: analista") 
    print("=" * 70)
    
    # Iniciar servidor
    app.run(debug=False, host='0.0.0.0', port=5000)
