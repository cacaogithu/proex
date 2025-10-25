import { useState, useEffect } from 'react'
import axios from 'axios'

interface Props {
  submissionId: string
}

export default function OverallFeedback({ submissionId }: Props) {
  const [overallScore, setOverallScore] = useState<number>(50)
  const [feedbackText, setFeedbackText] = useState('')
  const [submitLoading, setSubmitLoading] = useState(false)
  const [submitSuccess, setSubmitSuccess] = useState(false)
  const [existingFeedback, setExistingFeedback] = useState<any>(null)

  useEffect(() => {
    loadExistingFeedback()
  }, [submissionId])

  const loadExistingFeedback = async () => {
    try {
      const response = await axios.get(`/api/submissions/${submissionId}/feedback`)
      if (response.data.feedback) {
        setExistingFeedback(response.data.feedback)
        setOverallScore(response.data.feedback.overall_score)
        setFeedbackText(response.data.feedback.feedback_text || '')
      }
    } catch (err) {
      console.log('Sem feedback anterior')
    }
  }

  const submitFeedback = async () => {
    setSubmitLoading(true)
    try {
      await axios.post(`/api/submissions/${submissionId}/feedback`, {
        overall_score: overallScore,
        feedback_text: feedbackText || undefined
      })
      setSubmitSuccess(true)
      setTimeout(() => {
        setSubmitSuccess(false)
        loadExistingFeedback()
      }, 3000)
    } catch (err) {
      alert('Erro ao salvar feedback geral')
    } finally {
      setSubmitLoading(false)
    }
  }

  const getScoreColor = (value: number) => {
    if (value >= 80) return 'bg-green-500'
    if (value >= 60) return 'bg-blue-500'
    if (value >= 40) return 'bg-yellow-500'
    return 'bg-red-500'
  }

  return (
    <div className="bg-gradient-to-br from-blue-50 to-indigo-50 border-2 border-blue-200 rounded-lg p-5 mb-4">
      <h4 className="font-bold text-lg text-gray-900 mb-3 flex items-center gap-2">
        <svg className="w-6 h-6 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
        </svg>
        Avaliação Geral da Submissão
      </h4>
      <p className="text-sm text-gray-600 mb-4">
        Como você avalia o conjunto completo de cartas de recomendação geradas?
      </p>

      {!submitSuccess ? (
        <div className="space-y-4">
          <div>
            <div className="flex items-center justify-between mb-2">
              <span className="text-sm font-semibold text-gray-700">Avaliação Geral (0-100):</span>
              <span className={`px-4 py-1.5 rounded-full text-white text-base font-bold ${getScoreColor(overallScore)}`}>
                {overallScore}
              </span>
            </div>
            <input
              type="range"
              min="0"
              max="100"
              value={overallScore}
              onChange={(e) => setOverallScore(Number(e.target.value))}
              className="w-full h-3 rounded-lg appearance-none cursor-pointer"
              style={{
                background: `linear-gradient(to right, ${
                  overallScore >= 80 ? '#10b981' : 
                  overallScore >= 60 ? '#3b82f6' : 
                  overallScore >= 40 ? '#eab308' : '#ef4444'
                } 0%, ${
                  overallScore >= 80 ? '#10b981' : 
                  overallScore >= 60 ? '#3b82f6' : 
                  overallScore >= 40 ? '#eab308' : '#ef4444'
                } ${overallScore}%, #e5e7eb ${overallScore}%, #e5e7eb 100%)`
              }}
            />
            <div className="flex justify-between text-xs text-gray-600 mt-1">
              <span>0 - Insatisfeito</span>
              <span>50 - Razoável</span>
              <span>100 - Excelente</span>
            </div>
          </div>

          <textarea
            value={feedbackText}
            onChange={(e) => setFeedbackText(e.target.value)}
            placeholder="Feedback geral (opcional) - Compartilhe sua experiência e sugestões gerais sobre o conjunto de cartas..."
            className="w-full px-4 py-3 border-2 border-gray-300 rounded-md text-sm resize-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
            rows={4}
          />

          <button
            onClick={submitFeedback}
            disabled={submitLoading}
            className="w-full px-6 py-3 bg-blue-600 text-white text-base rounded-md hover:bg-blue-700 disabled:bg-gray-400 disabled:cursor-not-allowed font-semibold shadow-md"
          >
            {submitLoading ? 'Salvando Feedback...' : existingFeedback ? 'Atualizar Feedback Geral' : 'Salvar Feedback Geral'}
          </button>
        </div>
      ) : (
        <div className="bg-green-50 border-2 border-green-300 rounded-md p-4">
          <p className="text-green-800 text-base font-semibold flex items-center gap-2">
            <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 20 20">
              <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
            </svg>
            Feedback geral salvo com sucesso! (Score: {overallScore}/100)
          </p>
        </div>
      )}

      {existingFeedback && !submitSuccess && (
        <div className="mt-3 pt-3 border-t border-blue-200">
          <p className="text-xs text-gray-500">
            Feedback anterior: {existingFeedback.overall_score}/100 em {new Date(existingFeedback.created_at).toLocaleString('pt-BR')}
          </p>
        </div>
      )}
    </div>
  )
}
