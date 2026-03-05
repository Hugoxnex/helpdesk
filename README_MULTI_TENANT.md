# Help Desk SaaS - Sistema Multi-Tenant

## 📋 Visão Geral

Este sistema foi transformado de uma arquitetura single-tenant para **multi-tenant com banco de dados isolado**. Cada empresa (tenant) possui seu próprio banco de dados SQLite, garantindo isolamento total dos dados.

## 🏗️ Arquitetura

### Estrutura de Diretórios

```
/databases/
├── master.db              # Banco master (gestão de tenants)
├── empresa1/
│   └── helpdesk.db        # Banco da empresa 1
├── empresa2/
│   └── helpdesk.db        # Banco da empresa 2
└── ...

/instance/
└── helpdesk.db            # Banco original (após migração)
```

### Roteamento por Subdomínio

| Domínio | Acesso |
|---------|--------|
| `localhost:5000` ou `master.helpdeskhub.com` | Painel Master |
| `empresa1.localhost:5000` | Sistema da Empresa 1 |
| `empresa2.localhost:5000` | Sistema da Empresa 2 |

## 🚀 Instalação e Uso

### 1. Instalação das Dependências

```bash
pip install flask flask-sqlalchemy sqlalchemy pytz matplotlib werkzeug
```

### 2. Migração (se houver dados existentes)

```bash
python migrate_to_multi_tenant.py
```

### 3. Inicialização do Sistema

```bash
python app_multi_tenant.py
```

### 4. Acessos

#### Painel Master
- **URL:** http://localhost:5000
- **Senha Mestra:** `Master@2024` (altere via variável de ambiente `MASTER_PASSWORD`)

#### Tenant de Exemplo
- **URL:** http://principal.localhost:5000
- **Admin:** admin
- **Senha:** admin (ou a definida na migração)

## 🎛️ Painel Master

### Funcionalidades

1. **Dashboard**
   - Total de tenants
   - Tenants ativos/expirados
   - Alertas de expiração (15, 7, 1 dia)
   - Tenants recentes

2. **Gerenciamento de Tenants**
   - Criar novo tenant
   - Editar tenant
   - Renovar contrato
   - Excluir/desativar tenant
   - Listar todos os tenants

3. **Relatórios**
   - Visão geral de todos os tenants
   - Status de expiração
   - Último acesso

### Rotas do Painel Master

| Rota | Descrição |
|------|-----------|
| `/master/login` | Login do painel master |
| `/master/logout` | Logout |
| `/master/dashboard` | Dashboard principal |
| `/master/tenants` | Lista de tenants |
| `/master/tenants/create` | Criar novo tenant |
| `/master/tenants/<id>/edit` | Editar tenant |
| `/master/tenants/<id>/renew` | Renovar contrato |
| `/master/tenants/<id>/delete` | Desativar tenant |
| `/master/reports` | Relatórios |

## 🏢 Ciclo de Vida de um Tenant

### 1. Criação

Ao criar um novo tenant no painel master:

1. Registro no banco master com:
   - Nome da empresa
   - Subdomínio
   - Plano contratado (3M, 6M, 1Y, 2Y)
   - Data de expiração
   - Admin username/email

2. Criação automática do banco de dados:
   - Diretório: `/databases/<subdominio>/`
   - Banco: `helpdesk.db`
   - Todas as tabelas são criadas
   - Usuário admin é registrado

3. Configurações padrão:
   - Grupos de suporte (Helpdesk, Field Support, Systems Team)
   - Configurações de cores e empresa

### 2. Acesso

O tenant acessa via subdomínio:
```
http://<subdominio>.localhost:5000
```

O sistema detecta automaticamente o tenant baseado no host e conecta ao banco correto.

### 3. Expiração

- **15, 7 e 1 dia antes:** Alerta no painel master
- **Na expiração:** Tenant é redirecionado para página de expiração
- **Página de expiração:** Mostra dados de contato para renovação

### 4. Renovação

Pelo painel master:
1. Acessar `/master/tenants/<id>/renew`
2. Selecionar novo plano ou dias adicionais
3. Nova data de expiração é calculada automaticamente

## 📊 Planos Disponíveis

| Plano | Duração | Código |
|-------|---------|--------|
| 3 Meses | 90 dias | HUB3M |
| 6 Meses | 180 dias | HUB6M |
| 1 Ano | 365 dias | HUB1Y |
| 2 Anos | 730 dias | HUB2Y |

## 🔐 Segurança e Isolamento

### Isolamento de Dados

- Cada tenant tem seu próprio arquivo SQLite
- Sessões são isoladas por thread
- Middleware detecta tenant antes de cada requisição
- Usuários de um tenant não acessam dados de outro

### Verificações

1. **Tenant Ativo:** `tenant.ativo == True`
2. **Não Expirado:** `tenant.data_expiracao > datetime.utcnow()`
3. **Redirecionamento:** Se expirado/inativo, redireciona para página informativa

## 🛠️ Desenvolvimento

### Estrutura de Módulos

```
multi_tenant/
├── __init__.py           # Núcleo do sistema multi-tenant
├── master_routes.py      # Rotas do painel master
└── tenant_db.py          # Criação de tabelas do tenant
```

### Arquivos Principais

| Arquivo | Descrição |
|---------|-----------|
| `app_multi_tenant.py` | Aplicação principal (substitui app.py) |
| `migrate_to_multi_tenant.py` | Script de migração |
| `multi_tenant/__init__.py` | Módulo multi-tenant |

### Adicionando Novas Funcionalidades

Para adicionar novas rotas/funcionalidades:

1. **Use os modelos do tenant:**
```python
@app.route('/exemplo')
def exemplo():
    tenant = g.current_tenant
    User = g.tenant_models['User']
    
    # Query usando sessão do tenant
    usuarios = g.tenant_session.query(User).all()
```

2. **Acesse dados do tenant:**
```python
tenant = g.current_tenant
print(f"Empresa: {tenant.nome}")
print(f"Banco: {tenant.banco_path}")
```

## 🔄 Migração de Dados

### Processo Automático

Execute o script de migração:
```bash
python migrate_to_multi_tenant.py
```

O script:
1. Cria backup do banco original
2. Cria primeiro tenant
3. Copia dados para o novo banco
4. Mantém estrutura original intacta

### Migração Manual

1. Copie o banco original:
```bash
cp instance/helpdesk.db databases/principal/helpdesk.db
```

2. Crie registro no master:
```python
tenant = Tenant(
    nome="Empresa Principal",
    subdominio="principal",
    banco_path="databases/principal/helpdesk.db",
    data_expiracao=datetime.utcnow() + timedelta(days=90)
)
```

## ⚙️ Configuração

### Variáveis de Ambiente

```bash
# Senha do painel master
MASTER_PASSWORD=Master@2024

# Chave secreta do Flask
SECRET_KEY=sua_chave_secreta_aqui
```

### Configuração de Produção

1. **Use servidor WSGI:**
```bash
gunicorn -w 4 -b 0.0.0.0:5000 app_multi_tenant:app
```

2. **Configure reverse proxy (Nginx):**
```nginx
server {
    listen 80;
    server_name *.helpdeskhub.com;
    
    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

3. **Altere senha mestra:**
```bash
export MASTER_PASSWORD=NovaSenhaForte123!
```

## 📝 Notas Importantes

### Restrições

- **SQLite:** Mantido por compatibilidade, mas cada tenant tem arquivo separado
- **Performance:** Overhead mínimo na detecção de tenant (~5ms)
- **Concorrência:** SQLite tem limitações de escrita concorrente

### Melhorias Futuras

- [ ] Suporte a PostgreSQL/MySQL por tenant
- [ ] Pool de conexões mais eficiente
- [ ] Cache de sessões de tenant
- [ ] Backup automático de tenants
- [ ] API para gestão de tenants
- [ ] Dashboard de métricas por tenant

## 🐛 Troubleshooting

### Erro: "Tenant não encontrado"

Verifique se:
1. O subdomínio está correto
2. O tenant foi criado no painel master
3. O arquivo do banco existe em `/databases/<subdominio>/helpdesk.db`

### Erro: "Tabela não existe"

Execute:
```python
from multi_tenant import create_tenant_tables
create_tenant_tables('databases/empresa/helpdesk.db')
```

### Erro: "Acesso negado" no login

Verifique:
1. Está acessando o subdomínio correto
2. O usuário foi criado no banco do tenant (não no master)
3. A senha está correta (padrão: admin/admin)

## 📞 Suporte

Para dúvidas ou problemas:
- 📧 suporte@helpdeskhub.com
- 📞 0800 123 4567

---

**Versão:** 2.0.0 Multi-Tenant  
**Última atualização:** Março 2026
