import { useState } from 'react'
import axios from 'axios'

export default function SubmitPage() {
  const [email, setEmail] = useState('')
  const [numberOfTestimonials, setNumberOfTestimonials] = useState(3)
  const [quadro, setQuadro] = useState<File | null>(null)
  const [cv, setCv] = useState<File | null>(null)
  const [estrategia, setEstrategia] = useState<File | null>(null)
  const [onenote, setOnenote] = useState<File | null>(null)
  const [testimonials, setTestimonials] = useState<File[]>([])
  const [submitting, setSubmitting] = useState(false)
  const [result, setResult] = useState<any>(null)
  const [error, setError] = useState<string>('')

  const handleTestimonialChange = (index: number, file: File | null) => {
    const newTestimonials = [...testimonials]
    if (file) {
      newTestimonials[index] = file
    } else {
      newTestimonials.splice(index, 1)
    }
    setTestimonials(newTestimonials)
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setSubmitting(true)
    setError('')
    setResult(null)

    try {
      const formData = new FormData()
      formData.append('email', email)
      formData.append('numberOfTestimonials', numberOfTestimonials.toString())
      
      if (quadro) formData.append('quadro', quadro)
      if (cv) formData.append('cv', cv)
      if (estrategia) formData.append('estrategia', estrategia)
      if (onenote) formData.append('onenote', onenote)
      
      testimonials.forEach((file) => {
        formData.append('testimonials', file)
      })

      const response = await axios.post('/api/submissions', formData, {
        headers: {
          'Content-Type': 'multipart/form-data'
        }
      })

      setResult(response.data)
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Erro ao enviar submissão')
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <div className="max-w-4xl mx-auto py-8 px-4">
      <h2 className="text-3xl font-bold text-gray-900 mb-8">
        Nova Submissão de Documentos
      </h2>

      {result && (
        <div className="mb-6 bg-green-50 border border-green-200 rounded-lg p-4">
          <h3 className="text-green-800 font-semibold mb-2">✓ Submissão Recebida!</h3>
          <p className="text-green-700">ID: {result.submission_id}</p>
          <p className="text-green-700">{result.message}</p>
          <a 
            href={`/status?id=${result.submission_id}`}
            className="inline-block mt-3 text-blue-600 hover:text-blue-800 underline"
          >
            Acompanhar Status →
          </a>
        </div>
      )}

      {error && (
        <div className="mb-6 bg-red-50 border border-red-200 rounded-lg p-4">
          <p className="text-red-800">✗ {error}</p>
        </div>
      )}

      <form onSubmit={handleSubmit} className="space-y-6 bg-white shadow-md rounded-lg p-6">
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Email *
          </label>
          <input
            type="email"
            required
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500"
            placeholder="seu@email.com"
          />
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Número de Testemunhos
          </label>
          <input
            type="number"
            min="1"
            max="10"
            value={numberOfTestimonials}
            onChange={(e) => setNumberOfTestimonials(parseInt(e.target.value))}
            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500"
          />
        </div>

        <div className="border-t pt-6">
          <h3 className="text-lg font-semibold mb-4">Documentos Obrigatórios</h3>
          
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Quadro Preenchido por Cliente *
              </label>
              <input
                type="file"
                accept=".pdf"
                required
                onChange={(e) => setQuadro(e.target.files?.[0] || null)}
                className="w-full text-sm text-gray-500 file:mr-4 file:py-2 file:px-4 file:rounded-md file:border-0 file:text-sm file:font-semibold file:bg-blue-50 file:text-blue-700 hover:file:bg-blue-100"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Background (CV) Peticionário *
              </label>
              <input
                type="file"
                accept=".pdf"
                required
                onChange={(e) => setCv(e.target.files?.[0] || null)}
                className="w-full text-sm text-gray-500 file:mr-4 file:py-2 file:px-4 file:rounded-md file:border-0 file:text-sm file:font-semibold file:bg-blue-50 file:text-blue-700 hover:file:bg-blue-100"
              />
            </div>
          </div>
        </div>

        <div className="border-t pt-6">
          <h3 className="text-lg font-semibold mb-4">Testemunhos (CVs/LinkedIn) *</h3>
          <div className="space-y-3">
            {Array.from({ length: numberOfTestimonials }).map((_, index) => (
              <div key={index}>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Testemunho {index + 1}
                </label>
                <input
                  type="file"
                  accept=".pdf"
                  required
                  onChange={(e) => handleTestimonialChange(index, e.target.files?.[0] || null)}
                  className="w-full text-sm text-gray-500 file:mr-4 file:py-2 file:px-4 file:rounded-md file:border-0 file:text-sm file:font-semibold file:bg-blue-50 file:text-blue-700 hover:file:bg-blue-100"
                />
              </div>
            ))}
          </div>
        </div>

        <div className="border-t pt-6">
          <h3 className="text-lg font-semibold mb-4">Documentos Opcionais</h3>
          
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Estratégia Base
              </label>
              <input
                type="file"
                accept=".pdf"
                onChange={(e) => setEstrategia(e.target.files?.[0] || null)}
                className="w-full text-sm text-gray-500 file:mr-4 file:py-2 file:px-4 file:rounded-md file:border-0 file:text-sm file:font-semibold file:bg-gray-50 file:text-gray-700 hover:file:bg-gray-100"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                PDF do OneNote
              </label>
              <input
                type="file"
                accept=".pdf"
                onChange={(e) => setOnenote(e.target.files?.[0] || null)}
                className="w-full text-sm text-gray-500 file:mr-4 file:py-2 file:px-4 file:rounded-md file:border-0 file:text-sm file:font-semibold file:bg-gray-50 file:text-gray-700 hover:file:bg-gray-100"
              />
            </div>
          </div>
        </div>

        <button
          type="submit"
          disabled={submitting}
          className="w-full bg-blue-600 text-white py-3 px-6 rounded-md hover:bg-blue-700 disabled:bg-gray-400 disabled:cursor-not-allowed font-semibold"
        >
          {submitting ? 'Enviando...' : 'Enviar Documentos'}
        </button>
      </form>
    </div>
  )
}
