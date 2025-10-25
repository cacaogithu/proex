import { useState } from 'react'
import axios from 'axios'
import LetterFeedback from '../components/LetterFeedback'

export default function StatusPage() {
  const [submissionId, setSubmissionId] = useState('')
  const [loading, setLoading] = useState(false)
  const [submission, setSubmission] = useState<any>(null)
  const [error, setError] = useState<string>('')
  const [showFeedback, setShowFeedback] = useState(false)

  const checkStatus = async () => {
    if (!submissionId.trim()) {
      setError('Por favor, insira um ID de submissão')
      return
    }

    setLoading(true)
    setError('')
    setSubmission(null)

    try {
      const response = await axios.get(`/api/submissions/${submissionId}`)
      setSubmission(response.data)
      
      if (response.data.status === 'completed') {
        const processedData = JSON.parse(response.data.processed_data || '{}')
        response.data.letters = processedData.letters || []
      }
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Erro ao consultar status')
    } finally {
      setLoading(false)
    }
  }

  const handleRegenerateComplete = () => {
    setShowFeedback(false)
    setTimeout(() => {
      checkStatus()
    }, 2000)
  }

  const downloadResults = () => {
    window.open(`/api/submissions/${submissionId}/download`, '_blank')
  }

  const getStatusColor = (status: string) => {
    const colors: any = {
      received: 'bg-blue-100 text-blue-800',
      extracting: 'bg-yellow-100 text-yellow-800',
      organizing: 'bg-yellow-100 text-yellow-800',
      designing: 'bg-yellow-100 text-yellow-800',
      generating: 'bg-yellow-100 text-yellow-800',
      completed: 'bg-green-100 text-green-800',
      error: 'bg-red-100 text-red-800'
    }
    return colors[status] || 'bg-gray-100 text-gray-800'
  }

  const getStatusLabel = (status: string) => {
    const labels: any = {
      received: 'Recebido',
      extracting: 'Extraindo PDFs',
      organizing: 'Organizando Dados',
      designing: 'Gerando Designs',
      generating: 'Gerando Cartas',
      completed: 'Concluído',
      error: 'Erro'
    }
    return labels[status] || status
  }

  return (
    <div className="max-w-4xl mx-auto py-8 px-4">
      <h2 className="text-3xl font-bold text-gray-900 mb-8">
        Consultar Status da Submissão
      </h2>

      <div className="bg-white shadow-md rounded-lg p-6 mb-6">
        <div className="flex gap-4">
          <input
            type="text"
            value={submissionId}
            onChange={(e) => setSubmissionId(e.target.value)}
            placeholder="Cole o ID da submissão aqui"
            className="flex-1 px-4 py-2 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500"
          />
          <button
            onClick={checkStatus}
            disabled={loading}
            className="bg-blue-600 text-white px-6 py-2 rounded-md hover:bg-blue-700 disabled:bg-gray-400 disabled:cursor-not-allowed font-semibold"
          >
            {loading ? 'Consultando...' : 'Consultar'}
          </button>
        </div>
      </div>

      {error && (
        <div className="bg-red-50 border border-red-200 rounded-lg p-4 mb-6">
          <p className="text-red-800">✗ {error}</p>
        </div>
      )}

      {submission && (
        <div className="bg-white shadow-md rounded-lg p-6 space-y-4">
          <div className="flex items-center justify-between border-b pb-4">
            <h3 className="text-xl font-bold text-gray-900">
              Submissão: {submission.id}
            </h3>
            <span className={`px-4 py-2 rounded-full text-sm font-semibold ${getStatusColor(submission.status)}`}>
              {getStatusLabel(submission.status)}
            </span>
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div>
              <p className="text-sm text-gray-500">Email</p>
              <p className="font-medium">{submission.user_email}</p>
            </div>
            <div>
              <p className="text-sm text-gray-500">Número de Testemunhos</p>
              <p className="font-medium">{submission.number_of_testimonials}</p>
            </div>
            <div>
              <p className="text-sm text-gray-500">Criado em</p>
              <p className="font-medium">{new Date(submission.created_at).toLocaleString('pt-BR')}</p>
            </div>
            <div>
              <p className="text-sm text-gray-500">Atualizado em</p>
              <p className="font-medium">{new Date(submission.updated_at).toLocaleString('pt-BR')}</p>
            </div>
          </div>

          {submission.error_message && (
            <div className="bg-red-50 border border-red-200 rounded-lg p-4">
              <p className="text-sm text-gray-500 mb-1">Mensagem de Erro</p>
              <p className="text-red-800">{submission.error_message}</p>
            </div>
          )}

          {submission.status === 'completed' && (
            <div className="space-y-4">
              <div className="bg-gray-50 rounded-lg p-4">
                <h4 className="font-semibold text-gray-900 mb-3">Cartas Geradas:</h4>
                <div className="space-y-2">
                  {submission.files?.map((file: string, index: number) => (
                    <a
                      key={index}
                      href={`/api/files/${submission.id}/${file}`}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="flex items-center justify-between p-3 bg-white border border-gray-200 rounded-md hover:bg-gray-50 hover:border-blue-300 transition-colors"
                    >
                      <div className="flex items-center gap-3">
                        <svg className="w-5 h-5 text-red-600" fill="currentColor" viewBox="0 0 20 20">
                          <path d="M4 4a2 2 0 012-2h4.586A2 2 0 0112 2.586L15.414 6A2 2 0 0116 7.414V16a2 2 0 01-2 2H6a2 2 0 01-2-2V4z" />
                        </svg>
                        <span className="text-sm font-medium text-gray-900">{file}</span>
                      </div>
                      <svg className="w-5 h-5 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14" />
                      </svg>
                    </a>
                  )) || Array.from({ length: submission.number_of_testimonials }).map((_, i) => (
                    <a
                      key={i}
                      href={`/api/files/${submission.id}/letter_${i + 1}.pdf`}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="flex items-center justify-between p-3 bg-white border border-gray-200 rounded-md hover:bg-gray-50 hover:border-blue-300 transition-colors"
                    >
                      <div className="flex items-center gap-3">
                        <svg className="w-5 h-5 text-red-600" fill="currentColor" viewBox="0 0 20 20">
                          <path d="M4 4a2 2 0 012-2h4.586A2 2 0 0112 2.586L15.414 6A2 2 0 0116 7.414V16a2 2 0 01-2 2H6a2 2 0 01-2-2V4z" />
                        </svg>
                        <span className="text-sm font-medium text-gray-900">Carta {i + 1}</span>
                      </div>
                      <svg className="w-5 h-5 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14" />
                      </svg>
                    </a>
                  ))}
                </div>
              </div>
              
              <div className="flex gap-3">
                <button
                  onClick={downloadResults}
                  className="flex-1 bg-green-600 text-white py-3 px-6 rounded-md hover:bg-green-700 font-semibold flex items-center justify-center gap-2"
                >
                  <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
                  </svg>
                  Download ZIP
                </button>
                <button
                  onClick={() => setShowFeedback(!showFeedback)}
                  className="flex-1 bg-blue-600 text-white py-3 px-6 rounded-md hover:bg-blue-700 font-semibold flex items-center justify-center gap-2"
                >
                  <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M11.049 2.927c.3-.921 1.603-.921 1.902 0l1.519 4.674a1 1 0 00.95.69h4.915c.969 0 1.371 1.24.588 1.81l-3.976 2.888a1 1 0 00-.363 1.118l1.518 4.674c.3.922-.755 1.688-1.538 1.118l-3.976-2.888a1 1 0 00-1.176 0l-3.976 2.888c-.783.57-1.838-.197-1.538-1.118l1.518-4.674a1 1 0 00-.363-1.118l-3.976-2.888c-.784-.57-.38-1.81.588-1.81h4.914a1 1 0 00.951-.69l1.519-4.674z" />
                  </svg>
                  {showFeedback ? 'Ocultar Feedback' : 'Avaliar e Editar'}
                </button>
              </div>
            </div>
          )}

          {submission.status === 'completed' && showFeedback && submission.letters && (
            <div className="bg-gray-50 rounded-lg p-4 space-y-3">
              <div className="flex items-center justify-between mb-2">
                <h4 className="font-semibold text-gray-900">Feedback e Edição Seletiva</h4>
                <span className="text-xs text-gray-500">
                  Avalie cada carta e regenere as que precisam de ajustes
                </span>
              </div>
              {submission.letters.map((letter: any, index: number) => (
                <LetterFeedback
                  key={index}
                  submissionId={submission.id}
                  letter={letter}
                  letterIndex={index}
                  onRegenerateComplete={handleRegenerateComplete}
                />
              ))}
            </div>
          )}

          {['extracting', 'organizing', 'designing', 'generating'].includes(submission.status) && (
            <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
              <div className="flex items-center gap-3">
                <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-blue-600"></div>
                <p className="text-blue-800">
                  Processamento em andamento. Atualize esta página periodicamente para verificar o progresso.
                </p>
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  )
}
