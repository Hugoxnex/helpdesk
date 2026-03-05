"""
Script de Migração - Single Tenant para Multi-Tenant
Este script migra os dados do banco original para um tenant inicial

Uso: python migrate_to_multi_tenant.py
"""

import os
import sys
import shutil
from datetime import datetime, timedelta

# Configurar paths
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ORIGINAL_DB = os.path.join(BASE_DIR, 'instance', 'helpdesk.db')
DATABASES_DIR = os.path.join(BASE_DIR, 'databases')

def backup_original_db():
    """Cria backup do banco original"""
    if not os.path.exists(ORIGINAL_DB):
        print("❌ Banco original não encontrado!")
        return False
    
    backup_path = os.path.join(BASE_DIR, 'instance', f'helpdesk_backup_{datetime.now().strftime("%Y%m%d_%H%M%S")}.db')
    shutil.copy2(ORIGINAL_DB, backup_path)
    print(f"✅ Backup criado: {backup_path}")
    return True


def create_first_tenant():
    """Cria o primeiro tenant com os dados existentes"""
    import sqlite3
    
    # Importar módulo multi-tenant
    sys.path.insert(0, BASE_DIR)
    from multi_tenant import Tenant, master_db, init_master_db, create_tenant_database
    from flask import Flask
    
    # Criar app Flask para inicializar o banco master
    app = Flask(__name__)
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    init_master_db(app)
    
    with app.app_context():
        # Verificar se já existe tenant
        if Tenant.query.count() > 0:
            print("⚠️ Já existem tenants cadastrados!")
            print("Deseja continuar e criar um novo tenant? (s/n)")
            if input().lower() != 's':
                return False
        
        # Criar tenant para empresa existente
        print("\n📝 Cadastro do Tenant")
        print("=" * 50)
        
        nome = input("Nome da empresa: ") or "Empresa Principal"
        subdominio = input("Subdomínio (ex: empresa1): ") or "principal"
        admin_username = input("Username do admin (ex: admin): ") or "admin"
        admin_email = input("Email do admin: ") or "admin@empresa.com"
        
        print("\nPlanos disponíveis:")
        print("  1 - HUB3M (3 meses / 90 dias)")
        print("  2 - HUB6M (6 meses / 180 dias)")
        print("  3 - HUB1Y (1 ano / 365 dias)")
        print("  4 - HUB2Y (2 anos / 730 dias)")
        plano_opcao = input("Escolha o plano (1-4): ") or "1"
        
        planos = {
            '1': ('HUB3M', 90),
            '2': ('HUB6M', 180),
            '3': ('HUB1Y', 365),
            '4': ('HUB2Y', 730)
        }
        plano, dias = planos.get(plano_opcao, ('HUB3M', 90))
        
        # Criar registro do tenant
        tenant = Tenant(
            nome=nome,
            subdominio=subdominio,
            admin_username=admin_username,
            admin_email=admin_email,
            plano=plano,
            dias_contrato=dias,
            data_expiracao=datetime.utcnow() + timedelta(days=dias),
            banco_path=os.path.join(DATABASES_DIR, subdominio, 'helpdesk.db')
        )
        
        master_db.session.add(tenant)
        master_db.session.commit()
        
        print(f"\n✅ Tenant '{nome}' registrado!")
        print(f"   Subdomínio: {subdominio}")
        print(f"   Plano: {plano} ({dias} dias)")
        print(f"   Expiração: {tenant.data_expiracao.strftime('%d/%m/%Y')}")
        
        # Migrar dados do banco original
        if os.path.exists(ORIGINAL_DB):
            print(f"\n📦 Migrando dados do banco original...")
            migrate_data(ORIGINAL_DB, tenant.banco_path)
        else:
            # Criar banco vazio
            print(f"\n📦 Criando banco de dados do tenant...")
            create_tenant_database(tenant, admin_password='admin')
        
        print(f"\n🎉 Migração concluída!")
        print(f"   URL de acesso: http://{subdominio}.localhost:5000")
        print(f"   Admin: {admin_username}")
        print(f"   Senha: admin (ou a mesma do banco original)")
        
        return True


def migrate_data(original_db_path, new_db_path):
    """Migra dados do banco original para o novo"""
    import sqlite3
    
    # Criar diretório
    os.makedirs(os.path.dirname(new_db_path), exist_ok=True)
    
    # Copiar estrutura e dados
    conn_orig = sqlite3.connect(original_db_path)
    conn_new = sqlite3.connect(new_db_path)
    
    # Usar backup do SQLite para copiar tudo
    backup_cmd = f"BACKUP TO '{new_db_path}'"
    conn_orig.execute(backup_cmd)
    conn_orig.close()
    
    # Alternativa: copiar manualmente tabela por tabela
    # Isso é necessário se quiser transformar dados durante a migração
    
    print(f"   ✅ Dados copiados para: {new_db_path}")


def main():
    print("=" * 60)
    print("🔄 Migração Single-Tenant para Multi-Tenant")
    print("=" * 60)
    print()
    
    # 1. Backup
    print("1️⃣ Criando backup do banco original...")
    if not backup_original_db():
        print("❌ Erro ao criar backup. Verifique se o banco original existe.")
        return
    
    # 2. Criar tenant
    print("\n2️⃣ Criando primeiro tenant...")
    if not create_first_tenant():
        print("❌ Erro ao criar tenant.")
        return
    
    # 3. Instruções finais
    print("\n" + "=" * 60)
    print("✅ MIGRAÇÃO CONCLUÍDA!")
    print("=" * 60)
    print()
    print("📋 Próximos passos:")
    print("   1. Execute: python app_multi_tenant.py")
    print("   2. Acesse o painel master: http://localhost:5000")
    print("   3. Senha mestra: Master@2024")
    print("   4. Acesse o tenant: http://principal.localhost:5000")
    print()
    print("⚠️ IMPORTANTE:")
    print("   - O banco original foi movido para backup")
    print("   - Todas as rotas agora são multi-tenant")
    print("   - Use o painel master para gerenciar tenants")
    print()


if __name__ == '__main__':
    main()
