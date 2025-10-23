import { BrowserRouter, Routes, Route, Link } from 'react-router-dom'
import SubmitPage from './pages/SubmitPage'
import StatusPage from './pages/StatusPage'

function App() {
  return (
    <BrowserRouter>
      <div className="min-h-screen bg-gray-50">
        <nav className="bg-white shadow-sm">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
            <div className="flex justify-between h-16 items-center">
              <div className="flex-shrink-0 flex items-center">
                <h1 className="text-2xl font-bold text-blue-600">ProEx Platform</h1>
              </div>
              <div className="flex space-x-4">
                <Link 
                  to="/" 
                  className="text-gray-700 hover:text-blue-600 px-3 py-2 rounded-md text-sm font-medium"
                >
                  Nova Submissão
                </Link>
                <Link 
                  to="/status" 
                  className="text-gray-700 hover:text-blue-600 px-3 py-2 rounded-md text-sm font-medium"
                >
                  Consultar Status
                </Link>
              </div>
            </div>
          </div>
        </nav>

        <main>
          <Routes>
            <Route path="/" element={<SubmitPage />} />
            <Route path="/status" element={<StatusPage />} />
          </Routes>
        </main>

        <footer className="bg-white border-t mt-12">
          <div className="max-w-7xl mx-auto py-6 px-4 sm:px-6 lg:px-8">
            <p className="text-center text-gray-500 text-sm">
              © 2025 ProEx Venture. Plataforma de Processamento de Cartas EB-2 NIW.
            </p>
          </div>
        </footer>
      </div>
    </BrowserRouter>
  )
}

export default App
