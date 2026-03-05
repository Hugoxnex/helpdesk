# 🚀 Guia Completo de Deploy - Help Desk SaaS Multi-Tenant

## 📋 Visão Geral

Este guia cobre o deploy do sistema em produção usando **Render.com** (gratuito) ou **Railway.app**.

---

## 🎯 Opção 1: Deploy no Render.com (Recomendado)

### Passo 1: Criar Conta no Render

1. Acesse: https://render.com
2. Clique em **Get Started for Free**
3. Faça login com GitHub

### Passo 2: Preparar Repositório GitHub

1. Crie um repositório no GitHub
2. Faça upload dos seguintes arquivos:
   ```
   app_cloud.py
   wsgi.py
   Procfile
   runtime.txt
   requirements.txt
   .gitignore
   multi_tenant/
   ├── __init__.py
   ├── master_routes.py
   └── tenant_db.py
   static/
   └── uploads/
   ```

3. **NÃO suba** estes arquivos (estão no .gitignore):
   - `.env`
   - `databases/`
   - `instance/`
   - `*.db`

### Passo 3: Criar Web Service no Render

1. No dashboard do Render, clique em **New +**
2. Selecione **Web Service**
3. Conecte seu repositório GitHub
4. Configure:

```
Name: helpdesk-saaS
Region: Brazil (São Paulo)
Branch: main
Root Directory: (deixe em branco)
Runtime: Python 3
Start Command: gunicorn wsgi:app --bind 0.0.0.0:$PORT
```

5. Clique em **Advanced** e adicione variáveis de ambiente:

```
ENVIRONMENT=production
SECRET_KEY=sua_chave_secreta_aqui_32_caracteres
MASTER_PASSWORD=SuaSenhaMestra123!
DATABASE_URL=postgresql://user:pass@host:5432/dbname
```

6. Clique em **Create Web Service**

### Passo 4: Banco de Dados PostgreSQL

**Opção A: Render PostgreSQL (Recomendado)**

1. No dashboard, clique em **New +** → **PostgreSQL**
2. Configure:
   ```
   Name: helpdesk-db
   Region: Brazil (São Paulo)
   Database: helpdesk_db
   ```
3. Escolha plano **Free** (90 dias)
4. Após criar, copie a **Internal Database URL**
5. No Web Service, adicione esta URL na variável `DATABASE_URL`

**Opção B: Neon (Gratuito)**

1. Acesse: https://neon.tech
2. Crie conta gratuita
3. Crie novo projeto
4. Copie connection string
5. Adicione no Render como `DATABASE_URL`

### Passo 5: Configurar Domínio

1. No Web Service, vá em **Settings**
2. Em **Custom Domains**, adicione:
   - Domínio principal: `helpdeskhub.com`
   - Wildcard: `*.helpdeskhub.com`

3. Configure DNS no seu registrador de domínio:
   ```
   Tipo: CNAME
   Nome: @
   Valor: helpdesk-saaS.onrender.com
   
   Tipo: CNAME
   Nome: *
   Valor: helpdesk-saaS.onrender.com
   ```

### Passo 6: Acessar o Sistema

Após deploy (5-10 minutos):

- **Painel Master:** https://helpdeskhub.com
- **Tenant 1:** https://empresa1.helpdeskhub.com
- **Tenant 2:** https://empresa2.helpdeskhub.com

---

## 🎯 Opção 2: Deploy no Railway.app

### Passo 1: Criar Conta

1. Acesse: https://railway.app
2. Login com GitHub

### Passo 2: Criar Projeto

1. Clique em **New Project**
2. Selecione **Deploy from GitHub repo**
3. Escolha seu repositório

### Passo 3: Configurar Variáveis

Em **Variables**, adicione:
```
ENVIRONMENT=production
SECRET_KEY=sua_chave_secreta
MASTER_PASSWORD=SuaSenhaMestra
DATABASE_URL=postgresql://...
```

### Passo 4: Adicionar PostgreSQL

1. Clique em **New** → **Database** → **Add PostgreSQL**
2. Railway cria banco automaticamente
3. `DATABASE_URL` é preenchido automaticamente

### Passo 5: Deploy

Railway faz deploy automático. Aguarde 3-5 minutos.

---

## 🎯 Opção 3: PythonAnywhere (Mais Simples)

### Passo 1: Criar Conta

1. Acesse: https://www.pythonanywhere.com
2. Crie conta **Free**

### Passo 2: Upload de Código

1. No dashboard, vá em **Files**
2. Faça upload de todos os arquivos
3. Crie diretório `multi_tenant/`

### Passo 3: Configurar Web App

1. Vá em **Web**
2. Clique em **Add a new web app**
3. Escolha **Manual configuration**
4. Selecione **Python 3.10**

### Passo 4: Configurar WSGI

1. Em **WSGI configuration file**, edite:
```python
import sys
path = '/home/seuusuario'
if path not in sys.path:
    sys.path.append(path)

from app_cloud import app as application
```

### Passo 5: Variáveis de Ambiente

Em **Virtualenv**, configure:
```bash
export ENVIRONMENT=production
export SECRET_KEY=sua_chave
export MASTER_PASSWORD=SuaSenha
```

---

## 🔐 Variáveis de Ambiente Obrigatórias

| Variável | Descrição | Exemplo |
|----------|-----------|---------|
| `ENVIRONMENT` | Ambiente (production/development) | `production` |
| `SECRET_KEY` | Chave secreta do Flask | `abc123...` (32 chars) |
| `MASTER_PASSWORD` | Senha do painel master | `SenhaForte123!` |
| `DATABASE_URL` | URL do PostgreSQL | `postgresql://...` |

### Gerar SECRET_KEY

```python
import secrets
print(secrets.token_hex(32))
```

---

## 📊 Estrutura de Bancos em Produção

### PostgreSQL Schema

```sql
-- Tabela de Tenants (banco master)
CREATE TABLE tenants (
    id SERIAL PRIMARY KEY,
    nome VARCHAR(120),
    subdominio VARCHAR(100) UNIQUE,
    banco_schema VARCHAR(100),
    data_expiracao TIMESTAMP,
    ativo BOOLEAN DEFAULT true
);

-- Cada tenant tem seu schema
CREATE SCHEMA empresa1;
CREATE SCHEMA empresa2;
```

### Migração para PostgreSQL

O sistema automaticamente:
1. Usa PostgreSQL para o banco master
2. Cria schemas separados para cada tenant
3. Isola dados por schema

---

## 🔄 Deploy Contínuo (CI/CD)

### GitHub Actions

Crie `.github/workflows/deploy.yml`:

```yaml
name: Deploy to Render

on:
  push:
    branches: [ main ]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      
      - name: Deploy to Render
        env:
          RENDER_API_KEY: ${{ secrets.RENDER_API_KEY }}
        run: |
          curl -X POST https://api.render.com/deploy/svc-xxx
```

---

## 🧪 Testes Pós-Deploy

### Checklist

- [ ] Painel Master acessível
- [ ] Login no master funciona
- [ ] Criar novo tenant funciona
- [ ] Tenant acessa via subdomínio
- [ ] Login no tenant funciona
- [ ] Dados estão isolados
- [ ] HTTPS está ativo
- [ ] Logs estão funcionando

### Comandos de Teste

```bash
# Testar endpoint
curl https://helpdeskhub.com/master/login

# Ver logs
render logs -f helpdesk-saaS

# Testar tenant
curl https://teste.helpdeskhub.com/login
```

---

## ⚠️ Problemas Comuns

### Erro: "DATABASE_URL not set"

**Solução:** Adicione variável no painel do provedor

### Erro: "Module not found"

**Solução:** Verifique se `requirements.txt` está correto

### Erro: "Port not available"

**Solução:** Use `$PORT` do ambiente, não porte fixo

### Erro: "CORS error"

**Solução:** Adicione cabeçalhos CORS no app

---

## 📈 Monitoramento

### Render Dashboard

- **Logs:** Tempo real
- **Metrics:** CPU, Memória
- **Alerts:** Configure notificações

### Logs no Código

```python
import logging
logging.basicConfig(level=logging.INFO)
logging.info("Tenant criado: %s", tenant.nome)
```

---

## 💰 Custos Estimados

| Serviço | Plano | Custo |
|---------|-------|-------|
| Render Web Service | Free | $0/mês |
| Render PostgreSQL | Free (90 dias) | $0/mês → $7/mês |
| Domínio | .com | $12/ano |
| **Total** | | **~$19/mês** |

### Alternativas Gratuitas

- **Neon:** PostgreSQL free tier
- **Railway:** $5 crédito grátis
- **Fly.io:** Free tier limitado

---

## 🎯 Próximos Passos

1. ✅ Fazer deploy
2. ✅ Configurar domínio
3. ✅ Criar primeiro tenant
4. ✅ Testar todas as funcionalidades
5. ✅ Configurar backup automático
6. ✅ Monitorar uso

---

## 📞 Suporte

- **Docs:** https://render.com/docs
- **Community:** Discord do Render
- **Status:** https://status.render.com

---

**Versão:** 2.0.0 Cloud  
**Última atualização:** Março 2026
