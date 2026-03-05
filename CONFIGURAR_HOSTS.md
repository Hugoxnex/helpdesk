# ⚙️ Configurar Acesso aos Tenants (Windows)

## 🚨 IMPORTANTE: Como Acessar os Tenants

O sistema está **funcionando corretamente**! O problema é que o Windows não resolve automaticamente subdomínios como `teste.localhost`.

---

## ✅ Solução: Editar Arquivo Hosts

### Passo 1: Abrir Bloco de Notas como Administrador

1. Pressione `Windows + S`
2. Digite: `bloco de notas`
3. Clique com botão direito → **Executar como administrador**

### Passo 2: Abrir Arquivo Hosts

1. No Bloco de Notas: `Arquivo` → `Abrir`
2. Navegue até: `C:\Windows\System32\drivers\etc\`
3. Mude filtro para **Todos os arquivos**
4. Selecione: `hosts`
5. Clique em `Abrir`

### Passo 3: Adicionar Entradas

Adicione estas linhas no **final** do arquivo:

```
# Help Desk Multi-Tenant
127.0.0.1  teste.localhost
127.0.0.1  empresa1.localhost
127.0.0.1  xnexhelp.localhost
```

### Passo 4: Salvar

1. `Arquivo` → `Salvar` (ou Ctrl+S)
2. Feche o Bloco de Notas

### Passo 5: Limpar Cache DNS

Abra o Prompt de Comando (CMD) e execute:

```bash
ipconfig /flushdns
```

---

## 🎯 Agora Sim - Acessar os Tenants

### 1. Iniciar Servidor

```bash
cd "c:\Users\user\Desktop\Nova pasta (2)"
python app_multi_tenant.py
```

### 2. Acessar no Navegador

| Tenant | URL | Login | Senha |
|--------|-----|-------|-------|
| Master | http://localhost:5000 | - | Master@2024 |
| Teste | http://teste.localhost:5000 | admin | admin |
| Empresa1 | http://empresa1.localhost:5000 | admin | admin123 |
| Xnexhelp | http://xnexhelp.localhost:5000 | admin | (veja no master) |

---

## 🧪 Teste de Acesso

### Teste 1: Ping

No CMD:
```bash
ping teste.localhost
```

**Resultado esperado:**
```
Disparando teste.localhost [127.0.0.1] com 32 bytes de dados:
```

### Teste 2: Navegador

1. Abra: http://teste.localhost:5000
2. Deve aparecer tela de login
3. Digite: `admin` / `admin`
4. Deve ir para painel admin

---

## ⚠️ Problemas Comuns

### "Acesso negado" ao salvar hosts

**Solução:**
- Certifique-se de abrir Bloco de Notas como **Administrador**

### "Não foi possível acessar o site"

**Soluções:**
1. Verifique se servidor está rodando: `python app_multi_tenant.py`
2. Verifique se hosts foi salvo corretamente
3. Execute: `ipconfig /flushdns`
4. Reinicie o navegador

### "Página em branco"

**Solução:**
- Pressione F12 no navegador
- Verifique console por erros
- Pode ser necessário limpar cache do navegador (Ctrl+Shift+Del)

---

## 🔄 Alternativa: Usar Navegador Diferente

Alguns navegadores podem ter problemas com localhost. Tente:

1. Chrome
2. Firefox
3. Edge

---

## 📋 Verificação Rápida

Execute este comando para verificar se está tudo OK:

```bash
cd "c:\Users\user\Desktop\Nova pasta (2)"
python test_system.py
```

**Saída esperada:**
```
✅ Testes concluídos!
```

---

## 🎯 Resumo

```
┌─────────────────────────────────────────────────┐
│  1. Editar hosts (como admin)                   │
│  2. Adicionar entradas de tenants               │
│  3. Salvar arquivo                               │
│  4. Executar: ipconfig /flushdns                │
│  5. Iniciar servidor: python app_multi_tenant.py│
│  6. Acessar: http://teste.localhost:5000        │
│  7. Login: admin / admin                        │
│  8. ✅ Sucesso!                                 │
└─────────────────────────────────────────────────┘
```

---

## 📞 Ainda com Problemas?

1. Execute: `python test_system.py`
2. Verifique saída
3. Tire screenshot do erro
4. Verifique logs do servidor

---

**Versão:** 2.0.0 Multi-Tenant  
**Status:** ✅ Funcional - Requer configuração de hosts
