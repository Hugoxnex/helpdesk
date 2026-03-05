# 🔧 Como Acessar o Sistema Multi-Tenant

## ✅ Sistema Funcionando!

O sistema multi-tenant está instalado e configurado. Siga estas instruções para acessar.

---

## 🚀 Passo a Passo

### 1. Iniciar o Servidor

```bash
cd "c:\Users\user\Desktop\Nova pasta (2)"
python app_multi_tenant.py
```

O servidor iniciará em: **http://localhost:5000**

---

### 2. Acessar o Painel Master (Gestão)

**URL:** http://localhost:5000

**Senha:** `Master@2024`

**O que você pode fazer:**
- Criar novos tenants
- Editar tenants existentes
- Renovar contratos
- Ver estatísticas
- Gerenciar expirações

---

### 3. Acessar Tenants Criados

Após o setup, estes tenants foram criados automaticamente:

#### Tenant "Teste"
- **URL:** http://teste.localhost:5000
- **Username:** `admin`
- **Senha:** `admin`
- **Acesso:** Após login, redireciona para `/admin`

#### Tenant "Empresa 1"
- **URL:** http://empresa1.localhost:5000
- **Username:** `admin`
- **Senha:** `admin123`
- **Acesso:** Após login, redireciona para `/admin`

---

## 🔍 Fluxo de Acesso do Tenant

1. **Acesse:** http://teste.localhost:5000
2. **Login:** Digite `admin` e senha `admin`
3. **Redirecionamento:** Sistema detecta que é admin → vai para `/admin`
4. **Dashboard:** Você verá:
   - Estatísticas do tenant
   - Informações da empresa
   - Dias restantes do contrato
   - Status do tenant

---

## ⚠️ Problemas Comuns

### Erro: "Não foi possível acessar o site"

**Causa:** Servidor não está rodando

**Solução:**
```bash
python app_multi_tenant.py
```

---

### Erro: "Página não encontrada" ao acessar tenant

**Causa:** DNS do Windows não resolve subdomínios .localhost

**Solução 1 - Usar hosts file:**
1. Abra `C:\Windows\System32\drivers\etc\hosts` como Administrador
2. Adicione:
   ```
   127.0.0.1  teste.localhost
   127.0.0.1  empresa1.localhost
   ```
3. Salve e tente acessar novamente

**Solução 2 - Usar URL direta:**
- http://localhost:5000 (master)
- Para tenants, será necessário configurar o hosts file acima

---

### Erro: "Usuário não encontrado"

**Causa:** Usuário não existe no banco do tenant

**Solução:** Verifique se está usando as credenciais corretas:
- Tenant Teste: `admin` / `admin`
- Tenant Empresa1: `admin` / `admin123`

---

### Erro: "Acesso negado"

**Causa:** Usuário não tem permissão para o painel

**Solução:** Verifique o role do usuário no banco de dados

---

## 📋 URLs Disponíveis

| URL | Descrição | Autenticação |
|-----|-----------|--------------|
| http://localhost:5000 | Painel Master | Senha: Master@2024 |
| http://teste.localhost:5000 | Tenant Teste | admin/admin |
| http://empresa1.localhost:5000 | Tenant Empresa 1 | admin/admin123 |
| http://localhost:5000/master/login | Login Master | - |
| http://localhost:5000/master/dashboard | Dashboard Master | Master authenticated |
| http://localhost:5000/master/tenants | Lista de Tenants | Master authenticated |
| http://localhost:5000/master/tenants/create | Criar Tenant | Master authenticated |

---

## 🎯 Teste Rápido

### No Navegador:

1. **Abra:** http://localhost:5000
2. **Digite a senha:** `Master@2024`
3. **Clique em:** "➕ Novo Tenant"
4. **Preencha:**
   - Nome: Minha Empresa
   - Subdomínio: minhaempresa
   - Plano: HUB3M
   - Admin username: admin
   - Admin senha: senha123
5. **Salve**
6. **Acesse:** http://minhaempresa.localhost:5000
7. **Login:** admin / senha123

---

## 🔐 Papéis de Usuário (Roles)

| Role | Redirecionamento após Login |
|------|----------------------------|
| admin | /admin (Painel Admin) |
| analyst | /analyst (Painel Analista) |
| manager | /manager/dashboard |
| senior_manager | /manager/dashboard |
| user | /user/dashboard |

---

## 📊 O Que Cada Tenant Vê

Ao acessar o painel admin de um tenant:

```
┌─────────────────────────────────────────┐
│  ⚡ Nome da Empresa - Admin             │
├─────────────────────────────────────────┤
│  ✅ Sistema Multi-Tenant Funcionando!   │
├─────────────────────────────────────────┤
│  📊 Estatísticas:                       │
│  • Total de Usuários: X                 │
│  • Total de Tickets: Y                  │
│  • Usuário Logado: admin                │
├─────────────────────────────────────────┤
│  📋 Informações do Tenant:              │
│  • Empresa: Nome                        │
│  • Subdomínio: xxx                      │
│  • Plano: HUB3M                         │
│  • Expiração: dd/mm/aaaa                │
│  • Dias Restantes: N                    │
│  • Status: Ativo                        │
└─────────────────────────────────────────┘
```

---

## 🛠️ Comandos Úteis

### Ver tenants cadastrados
```bash
python -c "from multi_tenant import Tenant, master_db; from app_multi_tenant import app; ctx = app.app_context(); ctx.push(); tenants = Tenant.query.all(); print('\n'.join([f'{t.nome} - {t.subdominio}' for t in tenants])); ctx.pop()"
```

### Criar novo tenant via código
```bash
python -c "
from multi_tenant import Tenant, master_db, create_tenant_database
from app_multi_tenant import app
from datetime import datetime, timedelta

app.app_context().push()

tenant = Tenant(
    nome='Nova Empresa',
    subdominio='novaempresa',
    admin_username='admin',
    admin_email='admin@nova.com',
    plano='HUB3M',
    dias_contrato=90,
    data_expiracao=datetime.utcnow() + timedelta(days=90),
    banco_path='databases/novaempresa/helpdesk.db'
)

master_db.session.add(tenant)
master_db.session.commit()
create_tenant_database(tenant, 'admin123')
print('Tenant criado!')
"
```

---

## 📞 Suporte

Se ainda tiver problemas:

1. Verifique se o servidor está rodando
2. Confira se o hosts file está configurado
3. Teste primeiro o painel master
4. Verifique logs de erro no terminal

---

**Versão:** 2.0.0 Multi-Tenant  
**Status:** ✅ Funcional
