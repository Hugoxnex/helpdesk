# ☁️ Help Desk SaaS - Versão Cloud

## 🚀 Deploy Rápido em 5 Minutos

### 1. Preparar Código

```bash
# Certifique-se de ter estes arquivos:
ls app_cloud.py wsgi.py Procfile requirements.txt
```

### 2. Criar Conta no Render

1. Acesse: https://render.com
2. Login com GitHub

### 3. Deploy

```bash
# Suba o código para o GitHub
git init
git add .
git commit -m "Initial commit"
git branch -M main
git remote add origin https://github.com/seuusuario/seurepo.git
git push -u origin main
```

### 4. Configurar no Render

1. **New +** → **Web Service**
2. Conecte repositório
3. Configure:
   - **Name:** helpdesk-saaS
   - **Start Command:** `gunicorn wsgi:app --bind 0.0.0.0:$PORT`
4. **Environment Variables:**
   ```
   ENVIRONMENT=production
   SECRET_KEY=gerar_chave_32_caracteres
   MASTER_PASSWORD=SuaSenhaMestra
   ```
5. **Create Web Service**

### 5. Adicionar Banco de Dados

1. **New +** → **PostgreSQL**
2. **Free** tier
3. Copie **Internal Database URL**
4. Adicione como `DATABASE_URL` no Web Service

### 6. Acessar

Após 5-10 minutos:
- **URL:** https://helpdesk-saaS.onrender.com
- **Master:** Senha configurada

---

## 📁 Arquivos para Deploy

```
✅ Obrigatórios:
├── app_cloud.py           # Aplicação principal
├── wsgi.py                # Entry point
├── Procfile               # Comando de start
├── runtime.txt            # Versão Python
├── requirements.txt       # Dependências
├── multi_tenant/          # Módulo multi-tenant
│   ├── __init__.py
│   ├── master_routes.py
│   └── tenant_db.py
└── static/
    └── uploads/

❌ NÃO subir (.gitignore):
├── .env
├── databases/
├── instance/
└── *.db
```

---

## 🔐 Variáveis de Ambiente

### Obrigatórias

```bash
ENVIRONMENT=production
SECRET_KEY=sua_chave_secreta_32_caracteres
MASTER_PASSWORD=SuaSenhaMestra123!
DATABASE_URL=postgresql://user:pass@host:port/db
```

### Opcionais

```bash
LOG_LEVEL=INFO
GUNICORN_WORKERS=4
MAX_UPLOAD_SIZE=16777216
```

---

## 🎯 URLs de Acesso

### Desenvolvimento Local

```bash
python app_cloud.py
```

- **Master:** http://localhost:5000
- **Tenant:** http://teste.localhost:5000

### Produção (Render)

- **Master:** https://helpdesk-saaS.onrender.com
- **Tenant 1:** https://empresa1.helpdeskhub.com
- **Tenant 2:** https://empresa2.helpdeskhub.com

---

## 📊 Estrutura Multi-Tenant na Nuvem

```
PostgreSQL (Render)
├── Schema: public (master)
│   └── tenants
├── Schema: tenant_1
│   ├── users
│   ├── tickets
│   └── ...
└── Schema: tenant_2
    ├── users
    ├── tickets
    └── ...
```

---

## 🧪 Testes

### Local

```bash
python test_system.py
```

### Produção

```bash
# Testar endpoint
curl https://helpdesk-saaS.onrender.com/master/login

# Ver logs
render logs -f helpdesk-saaS
```

---

## ⚠️ Importante

### Diferenças Local vs Produção

| Local | Produção |
|-------|----------|
| SQLite | PostgreSQL |
| 1 tenant = 1 arquivo | 1 tenant = 1 schema |
| Sem HTTPS | HTTPS obrigatório |
| localhost | Domínio real |

### Adaptações Necessárias

O `app_cloud.py` já faz isso automaticamente:
- Detecta ambiente
- Configura banco correto
- Ajusta paths de upload

---

## 💰 Custos

### Render Free Tier

- **Web Service:** 750 horas/mês (grátis)
- **PostgreSQL:** 90 dias grátis, depois $7/mês
- **Total:** ~$7-19/mês

### Reduzir Custos

- Use **Neon** para PostgreSQL (free)
- Use **Railway** ($5 crédito grátis)

---

## 🔧 Troubleshooting

### "Application error"

Verifique logs no Render dashboard

### "DATABASE_URL not set"

Adicione variável de ambiente

### "Module not found"

Verifique `requirements.txt`

### "Port not available"

Use `$PORT` do ambiente

---

## 📞 Suporte

- **Render Docs:** https://render.com/docs
- **Status:** https://status.render.com
- **Discord:** https://discord.gg/render

---

**Versão:** 2.0.0 Cloud  
**Status:** ✅ Pronto para produção
