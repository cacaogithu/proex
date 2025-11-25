import { useState } from 'react'
import axios from 'axios'
import LetterFeedback from '../components/LetterFeedback'
import OverallFeedback from '../components/OverallFeedback'

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
      const submissionData = response.data

      if (submissionData.status === 'completed' && submissionData.processed_data) {
        try {
          const processedData = JSON.parse(submissionData.processed_data)
          submissionData.letters = processedData.letters || []
        } catch (e) {
          console.error('Failed to parse processed_data:', e)
          submissionData.letters = []
        }
      }

      setSubmission(submissionData)
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Erro ao consultar status')
    } finally {
      setLoading(false)
    }
  }

  const retrySubmission = async () => {
    setLoading(true)
    try {
      const response = await axios.post(`/api/submissions/${submission.id}/retry`)
      setSubmission(response.data)
      setError('')
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Erro ao tentar novamente')
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

  const handleDownload = async (url: string, filename: string) => {
    try {
      const response = await axios.get(url, {
        responseType: 'blob',
      });
      const blob = new Blob([response.data], { type: response.headers['content-type'] });
      const link = document.createElement('a');
      link.href = window.URL.createObjectURL(blob);
      link.download = filename;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
    } catch (error) {
      console.error("Download failed", error);
      alert("Erro ao baixar arquivo. Verifique se você está logado.");
    }
  };

  const downloadResults = () => {
    handleDownload(`/api/submissions/${submissionId}/download`, `cartas_${submissionId}.zip`);
  }

  // Helper functions for status display (assuming they exist elsewhere or need to be added)
  const getStatusColor = (status: string) => {
    switch (status) {
      case 'completed': return 'bg-green-100 text-green-800';
      case 'failed': return 'bg-red-100 text-red-800';
      case 'pending': return 'bg-yellow-100 text-yellow-800';
      default: return 'bg-blue-100 text-blue-800';
    }
  };

  const getStatusLabel = (status: string) => {
    switch (status) {
      case 'pending': return 'Pendente';
      case 'extracting': return 'Extraindo Dados';
      case 'organizing': return 'Organizando Dados';
      case 'designing': return 'Gerando Design';
      case 'generating': return 'Gerando Cartas';
      case 'completed': return 'Concluído';
      case 'failed': return 'Falhou';
      default: return status;
    }
  };

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
              <p className="text-sm text-gray-500">Número de Cartas Geradas</p>
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
            <div className="bg-red-50 border border-red-200 rounded-lg p-4 space-y-3">
              <div>
                <p className="text-sm text-gray-500 mb-1">Mensagem de Erro</p>
                <p className="text-red-800">{submission.error_message}</p>
              </div>
              <button
                onClick={retrySubmission}
                disabled={loading}
                className="bg-orange-600 text-white px-6 py-2 rounded-md hover:bg-orange-700 disabled:bg-gray-400 disabled:cursor-not-allowed font-semibold"
              >
                {loading ? 'Tentando novamente...' : 'Tentar Novamente'}
              </button>
            </div>
          )}

          {submission.status === 'completed' && (
            <div className="space-y-4">
              <div className="bg-gray-50 rounded-lg p-4">
                <h4 className="font-semibold text-gray-900 mb-3">Cartas de Recomendação Geradas:</h4>
                <div className="space-y-2">
                  {submission.letters?.map((letter: any, index: number) => {
                    const pdfFileName = letter.pdf_path ? letter.pdf_path.split('/').pop() : null
                    const docxFileName = letter.docx_path ? letter.docx_path.split('/').pop() : null
                    
                    return (
                      <div key={index} className="bg-white border border-gray-200 rounded-md p-3">
                        <div className="font-medium text-gray-900 mb-2">
                          Carta {index + 1}: {letter.recommender || 'Unknown'}
                        </div>
                        <div className="flex gap-2">
                          {pdfFileName && (
                            <button
                              onClick={() => handleDownload(`/api/files/${submission.id}/${pdfFileName}`, pdfFileName)}
                              className="flex-1 flex items-center justify-center gap-2 px-3 py-2 bg-red-50 border border-red-200 rounded hover:bg-red-100 transition-colors text-sm"
                            >
                              <svg className="w-4 h-4 text-red-600" fill="currentColor" viewBox="0 0 20 20">
                                <path d="M4 4a2 2 0 012-2h4.586A2 2 0 0112 2.586L15.414 6A2 2 0 0116 7.414V16a2 2 0 01-2 2H6a2 2 0 01-2-2V4z" />
                              </svg>
                              <span className="font-medium text-red-600">PDF</span>
                            </button>
                          )}
                          {docxFileName && (
                            <button
                              onClick={() => handleDownload(`/api/files/${submission.id}/${docxFileName}`, docxFileName)}
                              className="flex-1 flex items-center justify-center gap-2 px-3 py-2 bg-blue-50 border border-blue-200 rounded hover:bg-blue-100 transition-colors text-sm"
                            >
                              <svg className="w-4 h-4 text-blue-600" fill="currentColor" viewBox="0 0 20 20">
                                <path d="M4 4a2 2 0 012-2h4.586A2 2 0 0112 2.586L15.414 6A2 2 0 0116 7.414V16a2 2 0 01-2 2H6a2 2 0 01-2-2V4z" />
                              </svg>
                              <span className="font-medium text-blue-600">DOCX</span>
                            </button>
                          )}
                        </div>
                      </div>
                    )
                  })}
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
            <div className="bg-gray-50 rounded-lg p-4 space-y-4">
              <div className="flex items-center justify-between mb-2">
                <h4 className="font-semibold text-gray-900">Feedback e Edição Seletiva</h4>
                <span className="text-xs text-gray-500">
                  Avalie o conjunto de cartas e cada carta individualmente
                </span>
              </div>

              <OverallFeedback submissionId={submission.id} />

              <div className="border-t pt-4">
                <h5 className="font-semibold text-gray-800 mb-3">Avaliação Individual de Cartas</h5>
                <p className="text-sm text-gray-600 mb-3">
                  Avalie cada carta separadamente e regenere as que precisam de ajustes
                </p>
                <div className="space-y-3">
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
              </div>
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
