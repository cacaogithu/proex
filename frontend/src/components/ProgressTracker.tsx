import { useState, useEffect, useRef } from 'react'

interface ProgressEvent {
  type: string
  timestamp: string
  data: {
    phase?: string
    message?: string
    current_step?: number
    total_steps?: number
    percentage?: number
    letter_index?: number
    recommender_name?: string
    step?: string
    company_name?: string
    status?: string
    source?: string
    success?: boolean
    total_letters?: number
    successful_letters?: number
    details?: any
  }
}

interface ProgressTrackerProps {
  submissionId: string
  onComplete?: (success: boolean) => void
}

const phaseLabels: Record<string, string> = {
  extracting: 'Extraindo Documentos',
  organizing: 'Organizando Dados',
  designing: 'Criando Designs',
  generating: 'Gerando Cartas',
  email: 'Enviando Email'
}

const phaseIcons: Record<string, string> = {
  extracting: '📄',
  organizing: '🧹',
  designing: '🎨',
  generating: '✍️',
  email: '📧'
}


export default function ProgressTracker({ submissionId, onComplete }: ProgressTrackerProps) {
  const [events, setEvents] = useState<ProgressEvent[]>([])
  const [currentPhase, setCurrentPhase] = useState<string>('')
  const [currentMessage, setCurrentMessage] = useState<string>('')
  const [isCompleted, setIsCompleted] = useState(false)
  const [completedPhases, setCompletedPhases] = useState<Set<string>>(new Set())
  const [letters, setLetters] = useState<Record<number, { name: string; step: string; completed: boolean }>>({})
  const [logoSearches, setLogoSearches] = useState<Record<string, string>>({})
  const [connectionError, setConnectionError] = useState(false)
  const eventSourceRef = useRef<EventSource | null>(null)
  const scrollRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    const token = localStorage.getItem('token')
    if (!token) {
      setConnectionError(true)
      return
    }
    
    const eventSource = new EventSource(`/api/progress/${submissionId}/stream?token=${encodeURIComponent(token)}`)
    eventSourceRef.current = eventSource

    eventSource.onmessage = (event) => {
      try {
        const progressEvent: ProgressEvent = JSON.parse(event.data)
        setEvents(prev => [...prev, progressEvent])

        const { type, data } = progressEvent

        switch (type) {
          case 'phase_start':
            setCurrentPhase(data.phase || '')
            setCurrentMessage(data.message || '')
            break

          case 'phase_progress':
            setCurrentPhase(data.phase || '')
            setCurrentMessage(data.message || '')
            break

          case 'phase_complete':
            if (data.phase) {
              setCompletedPhases(prev => new Set([...prev, data.phase!]))
            }
            break

          case 'letter_start':
            if (data.letter_index !== undefined) {
              setLetters(prev => ({
                ...prev,
                [data.letter_index!]: {
                  name: data.recommender_name || 'Desconhecido',
                  step: 'Iniciando...',
                  completed: false
                }
              }))
            }
            break

          case 'letter_step':
            if (data.letter_index !== undefined) {
              setLetters(prev => ({
                ...prev,
                [data.letter_index!]: {
                  ...prev[data.letter_index!],
                  step: data.message || data.step || ''
                }
              }))
            }
            break

          case 'letter_complete':
            if (data.letter_index !== undefined) {
              setLetters(prev => ({
                ...prev,
                [data.letter_index!]: {
                  ...prev[data.letter_index!],
                  completed: true,
                  step: 'Concluído'
                }
              }))
            }
            break

          case 'logo_search':
            if (data.company_name) {
              setLogoSearches(prev => ({
                ...prev,
                [data.company_name!]: data.status || ''
              }))
            }
            break

          case 'completion':
            setIsCompleted(true)
            setCurrentMessage(data.message || 'Processamento concluído')
            onComplete?.(data.success || false)
            eventSource.close()
            break

          case 'error':
            setCurrentMessage(`Erro: ${data.message}`)
            break
        }

        if (scrollRef.current) {
          scrollRef.current.scrollTop = scrollRef.current.scrollHeight
        }
      } catch (e) {
        console.error('Failed to parse progress event:', e)
      }
    }

    eventSource.onerror = () => {
      console.log('SSE connection closed or error')
      setConnectionError(true)
    }

    return () => {
      eventSource.close()
    }
  }, [submissionId, onComplete])

  const phases = ['extracting', 'organizing', 'designing', 'generating', 'email']

  const getPhaseStatus = (phase: string) => {
    if (completedPhases.has(phase)) return 'completed'
    if (currentPhase === phase) return 'active'
    return 'pending'
  }

  if (connectionError && events.length === 0) {
    return (
      <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4">
        <p className="text-yellow-800">Aguardando atualizações de progresso...</p>
        <p className="text-sm text-yellow-600 mt-1">Recarregue a página para ver o status atualizado.</p>
      </div>
    )
  }

  return (
    <div className="bg-white rounded-lg shadow-lg p-6 space-y-6">
      <div className="flex items-center justify-between">
        <h3 className="text-xl font-bold text-gray-900">
          {isCompleted ? '✅ Processamento Concluído' : '⏳ Processando...'}
        </h3>
        {!isCompleted && (
          <div className="flex items-center gap-2">
            <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-blue-600"></div>
            <span className="text-sm text-gray-500">Em andamento</span>
          </div>
        )}
      </div>

      <div className="space-y-3">
        {phases.map((phase, index) => {
          const status = getPhaseStatus(phase)
          return (
            <div
              key={phase}
              className={`flex items-center gap-3 p-3 rounded-lg transition-all duration-300 ${
                status === 'completed'
                  ? 'bg-green-50 border border-green-200'
                  : status === 'active'
                  ? 'bg-blue-50 border border-blue-200 animate-pulse'
                  : 'bg-gray-50 border border-gray-200'
              }`}
            >
              <div
                className={`w-8 h-8 rounded-full flex items-center justify-center text-lg ${
                  status === 'completed'
                    ? 'bg-green-500 text-white'
                    : status === 'active'
                    ? 'bg-blue-500 text-white'
                    : 'bg-gray-300 text-gray-500'
                }`}
              >
                {status === 'completed' ? '✓' : phaseIcons[phase] || (index + 1)}
              </div>
              <div className="flex-1">
                <div className={`font-medium ${
                  status === 'completed'
                    ? 'text-green-700'
                    : status === 'active'
                    ? 'text-blue-700'
                    : 'text-gray-500'
                }`}>
                  {phaseLabels[phase] || phase}
                </div>
                {status === 'active' && currentPhase === phase && (
                  <div className="text-sm text-blue-600 mt-1">{currentMessage}</div>
                )}
              </div>
              {status === 'active' && (
                <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-blue-600"></div>
              )}
            </div>
          )
        })}
      </div>

      {Object.keys(letters).length > 0 && (
        <div className="border-t pt-4">
          <h4 className="font-semibold text-gray-700 mb-3 flex items-center gap-2">
            <span>📝</span> Cartas em Geração
          </h4>
          <div className="space-y-2">
            {Object.entries(letters).map(([index, letter]) => (
              <div
                key={index}
                className={`flex items-center gap-3 p-2 rounded-lg text-sm ${
                  letter.completed
                    ? 'bg-green-50 border border-green-200'
                    : 'bg-yellow-50 border border-yellow-200'
                }`}
              >
                <div
                  className={`w-6 h-6 rounded-full flex items-center justify-center text-xs font-bold ${
                    letter.completed
                      ? 'bg-green-500 text-white'
                      : 'bg-yellow-500 text-white'
                  }`}
                >
                  {letter.completed ? '✓' : parseInt(index) + 1}
                </div>
                <div className="flex-1">
                  <div className="font-medium text-gray-800">{letter.name}</div>
                  <div className={`text-xs ${letter.completed ? 'text-green-600' : 'text-yellow-700'}`}>
                    {letter.step}
                  </div>
                </div>
                {!letter.completed && (
                  <div className="flex items-center gap-1">
                    <div className="w-2 h-2 bg-yellow-500 rounded-full animate-pulse"></div>
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>
      )}

      {Object.keys(logoSearches).length > 0 && (
        <div className="border-t pt-4">
          <h4 className="font-semibold text-gray-700 mb-3 flex items-center gap-2">
            <span>🔍</span> Busca de Logos
          </h4>
          <div className="flex flex-wrap gap-2">
            {Object.entries(logoSearches).map(([company, status]) => (
              <div
                key={company}
                className={`px-3 py-1 rounded-full text-xs font-medium ${
                  status === 'found'
                    ? 'bg-green-100 text-green-700'
                    : status === 'not_found'
                    ? 'bg-red-100 text-red-700'
                    : 'bg-blue-100 text-blue-700'
                }`}
              >
                {status === 'found' ? '✓' : status === 'not_found' ? '✗' : '⏳'} {company}
              </div>
            ))}
          </div>
        </div>
      )}

      <div className="border-t pt-4">
        <details className="text-sm">
          <summary className="cursor-pointer text-gray-600 hover:text-gray-800 font-medium">
            📋 Ver log detalhado ({events.length} eventos)
          </summary>
          <div
            ref={scrollRef}
            className="mt-2 max-h-48 overflow-y-auto bg-gray-50 rounded-lg p-3 space-y-1 font-mono text-xs"
          >
            {events.map((event, i) => (
              <div key={i} className="text-gray-600">
                <span className="text-gray-400">
                  {new Date(event.timestamp).toLocaleTimeString('pt-BR')}
                </span>{' '}
                <span className="text-blue-600">[{event.type}]</span>{' '}
                {event.data.message || JSON.stringify(event.data)}
              </div>
            ))}
          </div>
        </details>
      </div>
    </div>
  )
}
