# 🚀 Guia Rápido de Início

## Passo 1: Instalar Dependências

```bash
pip install flask flask-sqlalchemy sqlalchemy pytz matplotlib werkzeug python-dotenv
```

## Passo 2: Configurar Ambiente

O arquivo `.env` já está configurado com valores padrão.

## Passo 3: Criar Tenants de Teste

```bash
python setup_test.py
```

Isso cria:
- **Tenant "teste"**: http://teste.localhost:5000 (admin/admin)
- **Tenant "empresa1"**: http://empresa1.localhost:5000 (admin/admin123)

## Passo 4: Iniciar Servidor

```bash
python app_multi_tenant.py
```

## Passo 5: Acessar

### Painel Master (Gestão de Tenants)
- **URL:** http://localhost:5000
- **Senha:** `Master@2024`

### Tenants Criados
- **Teste:** http://teste.localhost:5000
  - User: `admin`
  - Senha: `admin`

- **Empresa 1:** http://empresa1.localhost:5000
  - User: `admin`
  - Senha: `admin123`

---

## 📋 Comandos Úteis

### Verificar estrutura de bancos
```bash
dir databases
```

### Verificar tenants no master
```bash
python -c "from multi_tenant import Tenant, master_db; from app_multi_tenant import app; app.app_context().push(); print([(t.nome, t.subdominio) for t in Tenant.query.all()])"
```

### Limpar e recriar
```bash
# Remove bancos de teste
rmdir /s /q databases

# Recria tenants
python setup_test.py
```

---

## ⚠️ Problemas Comuns

### Erro: "module not found"
```bash
pip install -r requirements.txt
```

### Erro: "database locked"
Feche o servidor e tente novamente.

### Erro: "tenant not found"
Verifique se o subdomínio está correto e se o tenant foi criado.

---

## 🔗 URLs de Acesso

| Serviço | URL | Credenciais |
|---------|-----|-------------|
| Painel Master | http://localhost:5000 | Senha: Master@2024 |
| Tenant Teste | http://teste.localhost:5000 | admin/admin |
| Tenant Empresa1 | http://empresa1.localhost:5000 | admin/admin123 |

---

**Versão:** 2.0.0 Multi-Tenant  
**Data:** Março 2026
