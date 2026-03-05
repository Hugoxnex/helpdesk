"""
Script de Inicialização Rápida - Help Desk SaaS Multi-Tenant
Cria um tenant de exemplo e inicia o servidor para testes
"""

import os
import sys
from datetime import datetime, timedelta

# Configurar encoding para Windows
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

# Adicionar diretório atual ao path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from multi_tenant import Tenant, master_db, init_master_db, create_tenant_database
from flask import Flask

def setup_test_environment():
    """Configura ambiente de teste com tenant de exemplo"""
    
    print("=" * 60)
    print("🚀 Configuração do Ambiente de Teste")
    print("=" * 60)
    
    # Criar app Flask
    app = Flask(__name__)
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    init_master_db(app)
    
    with app.app_context():
        # Verificar se já existe tenant de teste
        tenant = Tenant.query.filter_by(subdominio='teste').first()
        
        if tenant:
            print(f"⚠️ Tenant 'teste' já existe!")
            print(f"   URL: http://teste.localhost:5000")
            print(f"   Admin: {tenant.admin_username}")
        else:
            print("\n📦 Criando tenant de exemplo...")
            
            # Criar tenant de teste
            tenant = Tenant(
                nome="Empresa de Teste",
                subdominio="teste",
                admin_username="admin",
                admin_email="admin@teste.com",
                plano="HUB3M",
                dias_contrato=90,
                data_expiracao=datetime.utcnow() + timedelta(days=90),
                banco_path=os.path.join(os.path.dirname(__file__), 'databases', 'teste', 'helpdesk.db')
            )
            
            master_db.session.add(tenant)
            master_db.session.commit()
            
            # Criar banco de dados do tenant
            create_tenant_database(tenant, admin_password='admin')
            
            print(f"✅ Tenant criado com sucesso!")
            print(f"   Nome: {tenant.nome}")
            print(f"   Subdomínio: {tenant.subdominio}")
            print(f"   Admin: {tenant.admin_username}")
            print(f"   Senha: admin")
            print(f"   Expiração: {tenant.data_expiracao.strftime('%d/%m/%Y')}")
        
        # Criar segundo tenant de exemplo
        tenant2 = Tenant.query.filter_by(subdominio='empresa1').first()
        
        if not tenant2:
            print("\n📦 Criando segundo tenant de exemplo...")
            
            tenant2 = Tenant(
                nome="Empresa 1 Ltda",
                subdominio="empresa1",
                admin_username="admin",
                admin_email="admin@empresa1.com",
                plano="HUB6M",
                dias_contrato=180,
                data_expiracao=datetime.utcnow() + timedelta(days=180),
                banco_path=os.path.join(os.path.dirname(__file__), 'databases', 'empresa1', 'helpdesk.db')
            )
            
            master_db.session.add(tenant2)
            master_db.session.commit()
            
            create_tenant_database(tenant2, admin_password='admin123')
            
            print(f"✅ Segundo tenant criado!")
            print(f"   Nome: {tenant2.nome}")
            print(f"   Subdomínio: {tenant2.subdominio}")
            print(f"   Admin: {tenant2.admin_username}")
            print(f"   Senha: admin123")
        
        print("\n" + "=" * 60)
        print("🎉 Ambiente configurado!")
        print("=" * 60)
        print("\n📋 URLs de acesso:")
        print("   🎛️ Painel Master: http://localhost:5000")
        print("      Senha mestra: Master@2024")
        print()
        print("   🏢 Tenant 1 (Teste): http://teste.localhost:5000")
        print("      Admin: admin / Senha: admin")
        print()
        print("   🏢 Tenant 2 (Empresa1): http://empresa1.localhost:5000")
        print("      Admin: admin / Senha: admin123")
        print()
        print("🚀 Para iniciar o servidor, execute:")
        print("   python app_multi_tenant.py")
        print()
    
    return app


if __name__ == '__main__':
    setup_test_environment()
