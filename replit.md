# ProEx Platform - Processamento de Cartas EB-2 NIW

## Visão Geral
Plataforma web standalone 100% funcional para processar cartas de recomendação para vistos EB-2 NIW. Replica completamente a lógica dos workflows n8n em código Python/TypeScript.

## Status do Projeto
✅ **MVP Completo e Funcional** (23 de Outubro de 2025)

### Funcionalidades Implementadas
- ✅ Upload de múltiplos PDFs (Quadro, CV, Estratégia, OneNote, Testemunhos)
- ✅ Extração automática de texto dos PDFs usando pdfplumber
- ✅ Processamento via LLM (Gemini/OpenAI) para organizar dados
- ✅ Heterogeneity Architect - gera estilos únicos para cada testemunho
- ✅ Geração dos 5 blocos (BLOCO3-7) por carta
- ✅ Montagem e geração de PDFs finais com WeasyPrint
- ✅ Sistema de tracking de status em tempo real
- ✅ Download de resultados em formato ZIP
- ✅ Interface web responsiva com React + Tailwind CSS

## Arquitetura

### Stack Tecnológica
**Backend:**
- FastAPI (Python 3.11) - API REST
- SQLite - Banco de dados local
- pdfplumber - Extração de PDFs
- OpenAI SDK - Integração com Gemini/OpenAI
- WeasyPrint - Geração de PDFs
- Markdown - Processamento de texto

**Frontend:**
- React 18 + TypeScript
- Vite - Build tool
- Tailwind CSS - Estilização
- React Router - Navegação
- Axios - Chamadas HTTP

### Estrutura de Diretórios
```
proex-platform/
├── backend/
│   ├── app/
│   │   ├── api/              # Rotas FastAPI
│   │   │   └── submissions.py
│   │   ├── core/             # Lógica de processamento
│   │   │   ├── pdf_extractor.py    # Extração de PDFs
│   │   │   ├── llm_processor.py    # Clean & Organize
│   │   │   ├── heterogeneity.py    # Design structures
│   │   │   ├── block_generator.py  # BLOCO3-7
│   │   │   ├── pdf_generator.py    # Assembly & PDF
│   │   │   └── processor.py        # Orquestrador principal
│   │   ├── db/               # Banco de dados
│   │   │   └── database.py
│   │   └── main.py           # App FastAPI
│   └── storage/
│       ├── uploads/          # PDFs enviados
│       └── outputs/          # PDFs gerados
│
├── frontend/
│   ├── src/
│   │   ├── pages/
│   │   │   ├── SubmitPage.tsx    # Formulário de upload
│   │   │   └── StatusPage.tsx    # Consulta de status
│   │   ├── App.tsx
│   │   └── main.tsx
│   └── package.json
│
├── start-backend.sh
└── README.md
```

## Fluxo de Processamento

### Fase 1: Recebimento e Extração
- Usuário envia PDFs via formulário web
- Sistema salva arquivos em `storage/uploads/{submission_id}/`
- PDFExtractor extrai texto de todos os documentos

### Fase 2: Clean and Organize (LLM)
- LLMProcessor estrutura dados extraídos em JSON
- Cria objeto com: petitioner, strategy, onet, testimonies
- Valida e organiza informações

### Fase 3: Heterogeneity Architect
- Gera N design structures (uma por testemunho)
- Cada design tem: tone, narrative framework, paragraph structure, etc.
- Garante heterogeneidade entre as cartas

### Fase 4: Geração de Blocos
- Para cada testemunho, gera 5 blocos:
  - BLOCO3: Validação Empírica de Resultados
  - BLOCO4: Diferenciação Técnica
  - BLOCO5: Impacto Setorial
  - BLOCO6: Qualificação do Recomendador
  - BLOCO7: Conclusão

### Fase 5: Assembly e PDF
- Combina os 5 blocos em carta completa
- Converte Markdown para HTML com CSS
- Gera PDF final com WeasyPrint
- Salva em `storage/outputs/{submission_id}/`

## API Endpoints

### POST /api/submissions
Cria nova submissão e inicia processamento
- **Params**: email, numberOfTestimonials, quadro, cv, testimonials[], estrategia?, onenote?
- **Response**: `{submission_id, status, message}`

### GET /api/submissions/{id}
Consulta status da submissão
- **Response**: Objeto submission com status atual

### GET /api/submissions/{id}/download
Download dos PDFs gerados
- **Response**: Arquivo ZIP com todas as cartas

## Configuração

### Secrets Necessários
- `OPENAI_API_KEY` - Chave da API Gemini/OpenAI ✅ Configurado

### Workflows Ativos
1. **Backend API** - Porta 8000 (console)
2. **Frontend** - Porta 5000 (webview) ✅ Porta principal

## Status dos Componentes

### Backend ✅
- FastAPI rodando na porta 8000
- SQLite database inicializado
- Todos os módulos de processamento implementados
- Sistema de background tasks funcionando

### Frontend ✅
- React app rodando na porta 5000
- Formulário de upload completo
- Sistema de tracking de status
- Download de resultados

### Integrações ✅
- OpenAI SDK configurado com Gemini
- PDF extraction funcionando
- WeasyPrint instalado e configurado

## Próximos Passos (Opcionais)
- [ ] Sistema de autenticação JWT
- [ ] Notificações por email
- [ ] Preview de PDFs antes do download
- [ ] Dashboard administrativo
- [ ] Métricas e analytics
- [ ] Testes automatizados

## Notas Importantes

### Modelos LLM
- Usando `gemini-2.0-flash-exp` para Clean & Organize (rápido)
- Usando `gemini-2.0-flash-exp` para todos os blocos (balanceado)
- Base URL configurada para Gemini: `https://generativelanguage.googleapis.com/v1beta/openai/`

### Limitações
- PDFs devem estar em formato legível (não escaneados sem OCR)
- Processamento é assíncrono (pode levar alguns minutos)
- Storage local (arquivos ficam no servidor Replit)

### Segurança
- API key armazenada em Replit Secrets
- Arquivos salvos com IDs únicos (UUID)
- SQLite com acesso local apenas

## Comandos Úteis

### Backend
```bash
./start-backend.sh
# ou
cd backend && python -m uvicorn app.main:app --host 0.0.0.0 --port 8000
```

### Frontend
```bash
cd frontend && npm run dev
```

### Logs
- Backend: Console workflow "Backend API"
- Frontend: Console workflow "Frontend"

## Autor
Desenvolvido para ProEx Venture
Data: Outubro 2025
