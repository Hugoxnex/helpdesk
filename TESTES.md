# Guia de Testes - Help Desk SaaS Multi-Tenant

## 🎯 Objetivo

Este guia descreve como testar todas as funcionalidades do sistema multi-tenant.

## 📋 Pré-requisitos

1. Python 3.8+ instalado
2. Dependências instaladas: `pip install flask flask-sqlalchemy sqlalchemy pytz matplotlib`
3. Diretório limpo (recomendado para testes)

## 🚀 Setup de Teste

### Passo 1: Executar Setup

```bash
python setup_test.py
```

Isso irá:
- Criar banco master
- Criar tenant "teste" (http://teste.localhost:5000)
- Criar tenant "empresa1" (http://empresa1.localhost:5000)

### Passo 2: Iniciar Servidor

```bash
python app_multi_tenant.py
```

## 🧪 Casos de Teste

### 1. Teste do Painel Master

#### 1.1 Login no Master
- **URL:** http://localhost:5000
- **Senha:** `Master@2024`
- **Resultado esperado:** Redirecionamento para dashboard

#### 1.2 Dashboard do Master
- **Verificar:**
  - Total de tenants = 2
  - Tenants ativos = 2
  - Cards de estatísticas preenchidos

#### 1.3 Criar Novo Tenant
1. Acessar: http://localhost:5000/master/tenants/create
2. Preencher formulário:
   - Nome: "Empresa Teste 3"
   - Subdomínio: "empresa3"
   - Plano: HUB3M
   - Admin username: admin
   - Admin senha: teste123
3. **Resultado esperado:** 
   - Tenant criado
   - Banco criado em `/databases/empresa3/helpdesk.db`
   - Redirecionamento para lista de tenants

#### 1.4 Editar Tenant
1. Acessar: http://localhost:5000/master/tenants/1/edit
2. Alterar nome da empresa
3. Marcar/desmarcar "Tenant Ativo"
4. **Resultado esperado:** Alterações salvas

#### 1.5 Renovar Tenant
1. Acessar: http://localhost:5000/master/tenants/1/renew
2. Selecionar plano "HUB6M"
3. **Resultado esperado:** Nova data de expiração = data atual + 180 dias

#### 1.6 Listar Tenants com Filtros
- Testar filtros:
  - Todos: `/master/tenants?filtro=todos`
  - Ativos: `/master/tenants?filtro=ativos`
  - Expirados: `/master/tenants?filtro=expirados`

### 2. Teste de Tenants

#### 2.1 Login no Tenant 1
- **URL:** http://teste.localhost:5000
- **Credenciais:** admin / admin
- **Resultado esperado:** Login bem-sucedido, redirecionamento para admin panel

#### 2.2 Login no Tenant 2
- **URL:** http://empresa1.localhost:5000
- **Credenciais:** admin / admin123
- **Resultado esperado:** Login bem-sucedido

#### 2.3 Isolamento de Dados
1. Logar no Tenant 1
2. Criar usuário: "usuario_teste"
3. Logout
4. Logar no Tenant 2
5. **Resultado esperado:** Usuário "usuario_teste" NÃO existe no Tenant 2

### 3. Teste de Expiração

#### 3.1 Simular Expiração
```python
# No Python shell:
from multi_tenant import Tenant, master_db
from datetime import datetime, timedelta

tenant = Tenant.query.get(1)
tenant.data_expiracao = datetime.utcnow() - timedelta(days=1)
master_db.session.commit()
```

#### 3.2 Acessar Tenant Expirado
- **URL:** http://teste.localhost:5000
- **Resultado esperado:** Redirecionamento para página de expiração
- **Mensagem:** "Contrato Expirado"

#### 3.3 Renovar Tenant Expirado
1. Acessar painel master
2. Renovar tenant expirado
3. Tentar acessar tenant novamente
- **Resultado esperado:** Acesso normalizado

### 4. Teste de Migração

#### 4.1 Backup do Banco Original
```bash
# Verificar se backup foi criado
ls instance/helpdesk_backup_*.db
```

#### 4.2 Executar Migração
```bash
python migrate_to_multi_tenant.py
```
- Seguir prompts interativos
- **Resultado esperado:** Tenant criado com dados migrados

### 5. Teste de Performance

#### 5.1 Tempo de Resposta
```bash
# Usar curl para medir tempo
curl -w "@curl-format.txt" -o /dev/null -s http://localhost:5000
```

#### 5.2 Múltiplos Acessos Simultâneos
```bash
# Usar ab (Apache Benchmark)
ab -n 100 -c 10 http://localhost:5000/
```

## 📊 Critérios de Aceite

### Funcionalidades Críticas

| Funcionalidade | Status Esperado |
|----------------|-----------------|
| Login no Master | ✅ Sucesso |
| Criar Tenant | ✅ Banco criado |
| Login no Tenant | ✅ Sucesso |
| Isolamento de Dados | ✅ Dados separados |
| Expiração de Tenant | ✅ Bloqueio funciona |
| Renovação | ✅ Acesso restaurado |
| Dashboard Master | ✅ Estatísticas corretas |

### Performance

| Métrica | Meta |
|---------|------|
| Detecção de Tenant | < 10ms |
| Login | < 500ms |
| Criação de Tenant | < 5s |

## 🐛 Debug de Problemas

### Logs do Sistema

Habilite debug no app:
```python
app.run(debug=True)
```

### Verificar Estrutura de Bancos

```bash
# Listar bancos criados
ls -la databases/*/helpdesk.db

# Verificar tabelas
sqlite3 databases/teste/helpdesk.db ".tables"
```

### Verificar Sessões

No código, adicione:
```python
print(f"Tenant: {g.current_tenant}")
print(f"Session: {g.tenant_session}")
```

## 📝 Checklist de Teste

### Antes de Produção

- [ ] Todos os testes passaram
- [ ] Senha mestra alterada
- [ ] Backup configurado
- [ ] Logs habilitados
- [ ] HTTPS configurado
- [ ] Domínios configurados
- [ ] Monitoramento ativo

### Após Deploy

- [ ] Login no master funciona
- [ ] Criação de tenants funciona
- [ ] Tenants acessam seus bancos
- [ ] Expiração bloqueia acesso
- [ ] Renovação restaura acesso
- [ ] Isolamento de dados confirmado

## 🎯 Próximos Passos

Após testes concluídos:

1. Revisar código original (app.py)
2. Migrar rotas específicas para app_multi_tenant.py
3. Testar cada rota migrada
4. Atualizar documentação
5. Planejar deploy em produção

---

**Versão:** 1.0  
**Data:** Março 2026
