# ProEx Platform - Processamento de Cartas EB-2 NIW

## Visão Geral
Plataforma web standalone 100% funcional para processar cartas de recomendação para vistos EB-2 NIW. Replica completamente a lógica dos workflows n8n em código Python/TypeScript.

## Status do Projeto
✅ **MVP Completo e Funcional** (23 de Outubro de 2025)

### Funcionalidades Implementadas
- ✅ Upload de múltiplos PDFs (Quadro, CV, Estratégia, OneNote, Testemunhos)
- ✅ Extração automática de texto dos PDFs usando pdfplumber
- ✅ Processamento via LLM (OpenRouter: Gemini + Claude) para organizar dados
- ✅ Heterogeneity Architect - gera estilos únicos para cada testemunho
- ✅ Geração dos 5 blocos (BLOCO3-7) por carta
- ✅ **Logo Scraping** - Busca automática de logos das empresas (Clearbit API + scraping)
- ✅ **Geração de DOCX editáveis** - Documentos Word ao invés de PDFs (python-docx)
- ✅ **Logos nos documentos** - Logos das empresas adicionados ao cabeçalho
- ✅ Sistema de tracking de status em tempo real
- ✅ Download de resultados em formato ZIP
- ✅ Interface web responsiva com React + Tailwind CSS

## Arquitetura

### Stack Tecnológica
**Backend:**
- FastAPI (Python 3.11) - API REST
- SQLite - Banco de dados local
- pdfplumber - Extração de PDFs
- OpenAI SDK - Integração com OpenRouter (Gemini + Claude)
- python-docx - Geração de DOCX editáveis
- requests + BeautifulSoup - Logo scraping
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
│   │   │   ├── llm_processor.py    # Clean & Organize (LLM tier strategy)
│   │   │   ├── heterogeneity.py    # Design structures
│   │   │   ├── block_generator.py  # BLOCO3-7
│   │   │   ├── logo_scraper.py     # Logo scraping com cache
│   │   │   ├── docx_generator.py   # Assembly & DOCX generation
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

### Fase 5: Logo Scraping e Assembly
- **Logo Scraping** (com cache e retry):
  - Tenta Clearbit API (melhor qualidade)
  - Fallback para scraping direto do website
  - Cache interno para evitar re-fetches
  - Timeouts e retry logic robustos
- **Assembly e DOCX**:
  - Combina os 5 blocos em carta completa via LLM
  - Converte Markdown para HTML (com parser completo)
  - Gera DOCX editável com python-docx
  - Suporte completo para: listas aninhadas, hyperlinks, formatação inline, tabelas
  - Logos adicionados ao cabeçalho dos documentos
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
Download dos documentos DOCX gerados
- **Response**: Arquivo ZIP com todas as cartas em formato Word editável

## Configuração

### Integração LLM
- ✅ **OpenRouter.ai** - API unificada para 400+ modelos LLM (muito mais barato que Replit AI)
- ✅ Usa sua própria chave API OpenRouter (cobrado na sua conta OpenRouter)
- ✅ **Estratégia de Modelos em Tiers** para otimizar custo/qualidade:
  - **Gemini 2.5 Flash** (`google/gemini-2.5-flash`) - Extração rápida de dados ($0.30/$2.50 por 1M tokens)
  - **Gemini 2.5 Pro** (`google/gemini-2.5-pro-preview-05-06`) - Geração de blocos de alta qualidade ($1.25/$10 por 1M tokens)
  - **Claude 3.7 Sonnet** (`anthropic/claude-sonnet-3.7`) - Assembly premium de documentos ($3/$15 por 1M tokens)
- ✅ Retry logic com exponential backoff para lidar com rate limiting
- ✅ Variável configurada: `OPENROUTER_API_KEY`

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
- OpenAI SDK configurado com OpenRouter (multi-model strategy)
- PDF extraction funcionando (pdfplumber)
- Logo scraping com Clearbit API + website scraping
- DOCX generation com python-docx + markdown parser
- Retry logic e cache em todas as integrações externas

## Próximos Passos (Opcionais)
- [ ] Sistema de autenticação JWT
- [ ] Notificações por email
- [ ] Preview de PDFs antes do download
- [ ] Dashboard administrativo
- [ ] Métricas e analytics
- [ ] Testes automatizados

## Notas Importantes

### Modelos LLM (Estratégia de Tiers)
- **Tier 1 - Fast** (`google/gemini-2.5-flash`):
  - Clean & Organize - Extração e estruturação de dados dos PDFs
  - Rápido e econômico para processamento inicial
  
- **Tier 2 - Quality** (`google/gemini-2.5-pro-preview-05-06`):
  - Heterogeneity Architect - Geração de design structures únicas
  - Blocos 3-7 - Geração de conteúdo de alta qualidade
  - Melhor capacidade de raciocínio e escrita criativa
  
- **Tier 3 - Premium** (`anthropic/claude-sonnet-3.7`):
  - Assembly final dos documentos
  - Maior qualidade de escrita e coerência narrativa
  - Usado apenas na etapa final para maximizar qualidade

- Todas as chamadas via OpenRouter.ai com retry logic
- Exponential backoff para lidar com rate limiting (429 errors)

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
