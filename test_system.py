"""
Script de Teste Rápido - Verifica se o sistema está funcionando
"""

import os
import sys

# Configurar encoding para Windows
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

print("=" * 60)
print("🧪 Teste do Sistema Multi-Tenant")
print("=" * 60)

# Teste 1: Importar módulos
print("\n1️⃣ Testando imports...")
try:
    from multi_tenant import Tenant, master_db, init_master_db
    from app_multi_tenant import app
    print("   ✅ Imports OK")
except Exception as e:
    print(f"   ❌ Erro nos imports: {e}")
    sys.exit(1)

# Teste 2: Verificar banco master
print("\n2️⃣ Verificando banco master...")
try:
    with app.app_context():
        tenant_count = Tenant.query.count()
        print(f"   ✅ Banco master OK ({tenant_count} tenants)")
except Exception as e:
    print(f"   ❌ Erro no banco master: {e}")

# Teste 3: Listar tenants
print("\n3️⃣ Tenants cadastrados:")
try:
    with app.app_context():
        tenants = Tenant.query.all()
        if tenants:
            for t in tenants:
                print(f"   - {t.nome} ({t.subdominio}) - {t.status}")
        else:
            print("   Nenhum tenant encontrado. Execute: python setup_test.py")
except Exception as e:
    print(f"   ❌ Erro ao listar tenants: {e}")

# Teste 4: Verificar arquivos de banco
print("\n4️⃣ Verificando arquivos de banco...")
databases_dir = os.path.join(os.path.dirname(__file__), 'databases')
if os.path.exists(databases_dir):
    for root, dirs, files in os.walk(databases_dir):
        for file in files:
            if file.endswith('.db'):
                db_path = os.path.join(root, file)
                size = os.path.getsize(db_path)
                print(f"   ✅ {os.path.relpath(db_path)} ({size} bytes)")
else:
    print(f"   ⚠️ Diretório databases não encontrado")

# Teste 5: Testar contexto do app
print("\n5️⃣ Testando contexto do app...")
try:
    with app.test_client() as client:
        # Testar acesso ao master
        rv = client.get('/master/login')
        if rv.status_code == 200:
            print("   ✅ Rota /master/login OK")
        else:
            print(f"   ⚠️ Rota /master/login retornou {rv.status_code}")
        
        # Testar acesso à home
        rv = client.get('/')
        if rv.status_code in [200, 302]:
            print("   ✅ Rota / OK")
        else:
            print(f"   ⚠️ Rota / retornou {rv.status_code}")
except Exception as e:
    print(f"   ❌ Erro ao testar rotas: {e}")

print("\n" + "=" * 60)
print("✅ Testes concluídos!")
print("=" * 60)

print("\n📋 Para iniciar o servidor:")
print("   python app_multi_tenant.py")
print()
print("📋 URLs de acesso:")
print("   Painel Master: http://localhost:5000")
print("   Tenant Teste: http://teste.localhost:5000")
print("   Tenant Empresa1: http://empresa1.localhost:5000")
print()
