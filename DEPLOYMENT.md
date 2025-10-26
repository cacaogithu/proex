# ProEx Platform - Guia de Deployment

## 🚀 Configuração de Deployment

O ProEx Platform está configurado para deployment em **Reserved VM** no Replit, que é ideal para aplicações multi-serviço que precisam estar sempre ligadas.

### Arquitetura de Deployment

A aplicação consiste em **3 serviços** que rodam simultaneamente:

1. **Backend API (FastAPI)** - Porta 8000 (principal)
   - Endpoint principal: `/`
   - Health check: `/health`
   - Processamento de cartas, LLM, ML, etc.

2. **Frontend (React)** - Porta 5000
   - Interface web do usuário
   - Faz proxy para o backend

3. **Email Service (Node.js)** - Porta 3001
   - Envia emails com links do Google Drive
   - Notificações de conclusão

### Comando de Inicialização

O deployment usa o script `start-production.sh` que inicia todos os 3 serviços em paralelo:

```bash
bash start-production.sh
```

Este script:
- ✅ Inicia o Backend API na porta 8000
- ✅ Inicia o Email Service na porta 3001
- ✅ Inicia o Frontend na porta 5000
- ✅ Mantém todos rodando simultaneamente

### Configuração no .replit

```toml
[deployment]
deploymentTarget = "vm"
run = ["bash", "start-production.sh"]
```

### Health Checks

O Replit monitora automaticamente o endpoint `/` do backend na porta 8000:

**GET /** → Retorna:
```json
{
  "message": "ProEx Platform API",
  "version": "1.0.0",
  "status": "running"
}
```

**GET /health** → Retorna:
```json
{
  "status": "healthy"
}
```

### Por que Reserved VM?

Segundo a [documentação do Replit](https://docs.replit.com/):

- ✅ **Suporta múltiplos serviços** rodando simultaneamente
- ✅ **Sempre ligado** - ideal para apps que precisam de conexões persistentes
- ✅ **Recursos dedicados** - performance previsível
- ✅ **Melhor para apps long-running** como o nosso email service

**Autoscale NÃO seria adequado porque:**
- ❌ Escala para zero quando idle (interromperia email service)
- ❌ Não mantém estado em memória
- ❌ Múltiplos restarts poderiam afetar ML training

### Portas

Durante o deployment:
- **Porta 8000** é exposta externamente (backend API)
- Portas 3001 e 5000 são internas (comunicação entre serviços)

### Testando Localmente

Para testar o script de produção localmente:

```bash
# Parar workflows atuais
# Executar:
./start-production.sh
```

### Variáveis de Ambiente Necessárias

Certifique-se de que estes secrets estão configurados:
- ✅ `OPENROUTER_API_KEY` - Para LLMs
- ✅ Credenciais Google (via integração Replit)

### Monitoramento

Após deployment, você pode:
1. Verificar logs na interface do Replit
2. Testar health check: `curl https://seu-app.repl.co/health`
3. Acessar frontend: `https://seu-app.repl.co`

### Troubleshooting

**Problema:** Health checks falhando
- ✅ **Solução:** Verificar se backend iniciou na porta 8000
- ✅ **Solução:** Checar logs para erros de startup

**Problema:** Email service não responde
- ✅ **Solução:** Verificar credenciais Google Drive/Gmail
- ✅ **Solução:** Checar logs do Node.js service

**Problema:** Frontend não carrega
- ✅ **Solução:** Verificar se `npm run dev` completou build
- ✅ **Solução:** Checar configuração de proxy no Vite

---

## 📊 Status Atual

- ✅ Deployment configurado como Reserved VM
- ✅ Health checks implementados e testados
- ✅ Script de inicialização multi-serviço criado
- ✅ Configuração `.replit` atualizada
- ✅ Pronto para deploy!

Para fazer deployment:
1. Clique no botão "Deploy" no Replit
2. Selecione "Reserved VM" (já configurado)
3. Aguarde inicialização (~2-3 minutos)
4. Teste o endpoint de health check
