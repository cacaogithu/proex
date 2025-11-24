import { useState } from 'react'
import axios from 'axios'

export default function SubmitPage() {
  const [email, setEmail] = useState('')
  const [numberOfTestimonials, setNumberOfTestimonials] = useState('') // Changed from 0 to '' to handle initial empty string
  const [quadro, setQuadro] = useState<File | null>(null)
  const [cv, setCv] = useState<File | null>(null)
  const [estrategia, setEstrategia] = useState<File | null>(null)
  const [onenote, setOnenote] = useState<File | null>(null)
  const [otherDocs, setOtherDocs] = useState<File[]>([])
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
      const formDataToSend = new FormData() // Renamed to avoid confusion with state variable
      formDataToSend.append('email', email)
      formDataToSend.append('numberOfTestimonials', String(numberOfTestimonials || 0)); // Corrected to handle empty string and convert to string

      if (quadro) formDataToSend.append('quadro', quadro)
      if (cv) formDataToSend.append('cv', cv)
      if (estrategia) formDataToSend.append('estrategia', estrategia)
      if (onenote) formDataToSend.append('onenote', onenote)

      testimonials.forEach((file) => {
        formDataToSend.append('testimonials', file)
      })

      otherDocs.forEach((file) => {
        formDataToSend.append('other_documents', file)
      })

      const response = await axios.post('/api/submissions', formDataToSend, {
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
      <h2 className="text-3xl font-bold text-gray-900 mb-2">
        Nova Submissão - Geração de Cartas de Recomendação EB-2 NIW
      </h2>
      <p className="text-gray-600 mb-8">
        Envie os documentos necessários para gerar cartas de recomendação profissionais baseadas nos CVs dos seus recomendadores.
      </p>

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
            Número de Cartas de Recomendação a Gerar *
          </label>
          <p className="text-xs text-gray-500 mb-2">
            Informe quantas cartas de recomendação você deseja gerar (1-10)
          </p>
          <input
            type="number"
            min="1"
            max="10"
            required
            value={numberOfTestimonials}
            onChange={(e) => {
              const val = e.target.value
              setNumberOfTestimonials(val)
            }}
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
          <h3 className="text-lg font-semibold mb-2">CVs dos Recomendadores *</h3>
          <p className="text-sm text-gray-600 mb-4">
            Envie os CVs ou perfis LinkedIn (em PDF) dos profissionais que farão as recomendações.
            O sistema gerará automaticamente cartas de recomendação únicas baseadas nestes documentos.
          </p>
          <div className="space-y-3">
            {Array.from({ length: parseInt(numberOfTestimonials) || 0 }).map((_, index) => (
              <div key={index}>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  CV do Recomendador {index + 1}
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

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Outros Documentos (Opcional)
              </label>
              <p className="text-xs text-gray-500 mb-2">
                Adicione outros documentos relevantes (ex: Prêmios, Artigos, Mídia)
              </p>
              <input
                type="file"
                accept=".pdf"
                multiple
                onChange={(e) => setOtherDocs(Array.from(e.target.files || []))}
                className="w-full text-sm text-gray-500 file:mr-4 file:py-2 file:px-4 file:rounded-md file:border-0 file:text-sm file:font-semibold file:bg-gray-50 file:text-gray-700 hover:file:bg-gray-100"
              />
              {otherDocs.length > 0 && (
                <ul className="mt-2 text-sm text-gray-600">
                  {otherDocs.map((file, index) => (
                    <li key={index}>• {file.name}</li>
                  ))}
                </ul>
              )}
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