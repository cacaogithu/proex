import { useState } from 'react'
import axios from 'axios'

interface Letter {
  testimony_id: string
  recommender: string
  pdf_path: string
  template_id: string
  has_logo: boolean
  regenerated?: boolean
}

interface Props {
  submissionId: string
  letter: Letter
  letterIndex: number
  onRegenerateComplete: () => void
}

export default function LetterFeedback({ submissionId, letter, letterIndex, onRegenerateComplete }: Props) {
  const [score, setScore] = useState<number>(50)
  const [comment, setComment] = useState('')
  const [showFeedback, setShowFeedback] = useState(false)
  const [submitLoading, setSubmitLoading] = useState(false)
  const [submitSuccess, setSubmitSuccess] = useState(false)
  const [showRegenerateModal, setShowRegenerateModal] = useState(false)
  const [regenerateInstructions, setRegenerateInstructions] = useState('')
  const [regenerating, setRegenerating] = useState(false)

  const submitScore = async () => {
    setSubmitLoading(true)
    try {
      await axios.post(
        `/api/submissions/${submissionId}/letters/${letterIndex}/score`,
        { score, comment: comment || undefined }
      )
      setSubmitSuccess(true)
      setTimeout(() => setSubmitSuccess(false), 3000)
    } catch (err) {
      alert('Erro ao salvar avaliação')
    } finally {
      setSubmitLoading(false)
    }
  }

  const handleRegenerate = async () => {
    setRegenerating(true)
    try {
      await axios.post(`/api/submissions/${submissionId}/regenerate`, {
        letter_indices: [letterIndex],
        instructions: regenerateInstructions || undefined
      })
      setShowRegenerateModal(false)
      setRegenerateInstructions('')
      alert('Regeneração iniciada! Você receberá um email quando estiver pronta.')
      onRegenerateComplete()
    } catch (err: any) {
      alert(err.response?.data?.detail || 'Erro ao iniciar regeneração')
    } finally {
      setRegenerating(false)
    }
  }

  const getScoreColor = (value: number) => {
    if (value >= 80) return 'bg-green-500'
    if (value >= 60) return 'bg-blue-500'
    if (value >= 40) return 'bg-yellow-500'
    return 'bg-red-500'
  }

  return (
    <div className="bg-white border border-gray-200 rounded-lg p-4 space-y-3">
      <div className="flex items-center justify-between">
        <div>
          <h4 className="font-semibold text-gray-900">
            Carta {letterIndex + 1}: {letter.recommender}
          </h4>
          <p className="text-xs text-gray-500 mt-1">
            Template: {letter.template_id} {letter.has_logo && '• Logo incluído'}
            {letter.regenerated && ' • Regenerada'}
          </p>
        </div>
        <a
          href={letter.pdf_path ? `/api/files/${submissionId}/${letter.pdf_path.split('/').pop()}` : '#'}
          target="_blank"
          rel="noopener noreferrer"
          className="text-blue-600 hover:text-blue-700 text-sm font-medium flex items-center gap-1"
        >
          Ver PDF
          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14" />
          </svg>
        </a>
      </div>

      {!submitSuccess ? (
        <div className="space-y-3">
          <button
            onClick={() => setShowFeedback(!showFeedback)}
            className="text-sm text-blue-600 hover:text-blue-700 font-medium"
          >
            {showFeedback ? '▼ Ocultar Avaliação' : '▶ Avaliar Esta Carta'}
          </button>

          {showFeedback && (
            <div className="space-y-3 border-t pt-3">
              <div>
                <div className="flex items-center justify-between mb-2">
                  <span className="text-sm font-medium text-gray-700">Avaliação (0-100):</span>
                  <span className={`px-3 py-1 rounded-full text-white text-sm font-bold ${getScoreColor(score)}`}>
                    {score}
                  </span>
                </div>
                <input
                  type="range"
                  min="0"
                  max="100"
                  value={score}
                  onChange={(e) => setScore(Number(e.target.value))}
                  className="w-full h-2 rounded-lg appearance-none cursor-pointer"
                  style={{
                    background: `linear-gradient(to right, ${
                      score >= 80 ? '#10b981' : 
                      score >= 60 ? '#3b82f6' : 
                      score >= 40 ? '#eab308' : '#ef4444'
                    } 0%, ${
                      score >= 80 ? '#10b981' : 
                      score >= 60 ? '#3b82f6' : 
                      score >= 40 ? '#eab308' : '#ef4444'
                    } ${score}%, #e5e7eb ${score}%, #e5e7eb 100%)`
                  }}
                />
                <div className="flex justify-between text-xs text-gray-500 mt-1">
                  <span>0 - Ruim</span>
                  <span>50 - Médio</span>
                  <span>100 - Excelente</span>
                </div>
              </div>

              <textarea
                value={comment}
                onChange={(e) => setComment(e.target.value)}
                placeholder="Comentários (opcional) - O que você gostou ou o que poderia melhorar?"
                className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm resize-none focus:ring-blue-500 focus:border-blue-500"
                rows={3}
              />

              <div className="flex gap-2">
                <button
                  onClick={submitScore}
                  disabled={submitLoading}
                  className="px-4 py-2 bg-blue-600 text-white text-sm rounded-md hover:bg-blue-700 disabled:bg-gray-400 disabled:cursor-not-allowed font-medium"
                >
                  {submitLoading ? 'Salvando...' : 'Salvar Avaliação'}
                </button>
                <button
                  onClick={() => setShowRegenerateModal(true)}
                  className="px-4 py-2 bg-orange-500 text-white text-sm rounded-md hover:bg-orange-600 font-medium"
                >
                  Regenerar Esta Carta
                </button>
              </div>
            </div>
          )}
        </div>
      ) : (
        <div className="bg-green-50 border border-green-200 rounded-md p-3">
          <p className="text-green-800 text-sm font-medium">✓ Avaliação salva com sucesso! (Score: {score}/100)</p>
        </div>
      )}

      {showRegenerateModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg shadow-xl max-w-md w-full mx-4 p-6">
            <h3 className="text-lg font-bold text-gray-900 mb-4">
              Regenerar Carta {letterIndex + 1}
            </h3>
            <p className="text-sm text-gray-600 mb-4">
              A carta será regenerada com um novo template e conteúdo. Você pode adicionar instruções
              específicas para personalizar o resultado.
            </p>
            <textarea
              value={regenerateInstructions}
              onChange={(e) => setRegenerateInstructions(e.target.value)}
              placeholder="Instruções personalizadas (opcional)&#10;Ex: Adicionar mais detalhes técnicos, usar tom mais formal, etc."
              className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm resize-none focus:ring-blue-500 focus:border-blue-500 mb-4"
              rows={4}
            />
            <div className="flex gap-3 justify-end">
              <button
                onClick={() => setShowRegenerateModal(false)}
                disabled={regenerating}
                className="px-4 py-2 border border-gray-300 text-gray-700 rounded-md hover:bg-gray-50 disabled:opacity-50"
              >
                Cancelar
              </button>
              <button
                onClick={handleRegenerate}
                disabled={regenerating}
                className="px-4 py-2 bg-orange-500 text-white rounded-md hover:bg-orange-600 disabled:bg-gray-400 disabled:cursor-not-allowed"
              >
                {regenerating ? 'Regenerando...' : 'Regenerar'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
