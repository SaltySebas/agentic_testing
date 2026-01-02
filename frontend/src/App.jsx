import React, { useState, useEffect, useRef } from 'react'
import InputForm from './components/InputForm'
import ProgressDisplay from './components/ProgressDisplay'
import ResultsDisplay from './components/ResultsDisplay'
import AgentWorkflow from './components/AgentWorkflow'
import axios from 'axios'

function App() {
  const [mode, setMode] = useState('generate')
  const [input, setInput] = useState('')
  const [maxIterations, setMaxIterations] = useState(5)
  const [status, setStatus] = useState('idle')
  const [progress, setProgress] = useState([])
  const [results, setResults] = useState(null)
  const [currentStep, setCurrentStep] = useState('')
  const [wsConnection, setWsConnection] = useState(null)
  const clientIdRef = useRef(null)

  // Generate unique client ID on mount
  useEffect(() => {
    if (!clientIdRef.current) {
      clientIdRef.current = Math.random().toString(36).substr(2, 9)
    }
  }, [])

  // WebSocket connection
  useEffect(() => {
    if (!clientIdRef.current) return

    const ws = new WebSocket(`ws://localhost:8000/ws/${clientIdRef.current}`)
    
    ws.onopen = () => {
      console.log('WebSocket connected')
      setWsConnection(ws)
    }

    ws.onmessage = (event) => {
      const data = JSON.parse(event.data)
      
      if (data.type === 'progress') {
        setProgress(prev => [...prev, {
          step: data.step,
          message: data.message,
          timestamp: new Date()
        }])
        setCurrentStep(data.step)
      } else if (data.type === 'result') {
        setResults(data.data)
        setStatus('success')
        setCurrentStep('COMPLETE')
      } else if (data.type === 'error') {
        setStatus('error')
        setProgress(prev => [...prev, {
          step: 'ERROR',
          message: data.message,
          timestamp: new Date()
        }])
      } else if (data.type === 'status') {
        console.log('WebSocket status:', data.message)
      }
    }

    ws.onerror = (error) => {
      console.error('WebSocket error:', error)
    }

    ws.onclose = () => {
      console.log('WebSocket disconnected')
      setWsConnection(null)
    }

    return () => {
      if (ws.readyState === WebSocket.OPEN) {
        ws.close()
      }
    }
  }, [])

  const handleSubmit = async (inputValue, iterations) => {
    if (!inputValue.trim()) {
      alert('Please enter some input')
      return
    }

    setInput(inputValue)
    setMaxIterations(iterations)
    setStatus('running')
    setProgress([])
    setResults(null)
    setCurrentStep('START')

    try {
      const endpoint = mode === 'generate' ? '/api/generate' : '/api/test'
      const payload = mode === 'generate' 
        ? { requirements: inputValue, max_iterations: iterations }
        : { code: inputValue, max_iterations: iterations }

      const response = await axios.post(endpoint, payload, {
        params: { client_id: clientIdRef.current }
      })

      setResults(response.data)
      if (response.data.status === 'SUCCESS') {
        setStatus('success')
      } else {
        setStatus('success') // Still success, but with results showing status
      }
    } catch (error) {
      console.error('API error:', error)
      setStatus('error')
      setProgress(prev => [...prev, {
        step: 'ERROR',
        message: error.response?.data?.detail || error.message || 'An error occurred',
        timestamp: new Date()
      }])
    }
  }

  const handleResume = async (resumeState) => {
    setStatus('running')
    setProgress([])
    setCurrentStep('RESUME')

    try {
      const response = await axios.post('/api/resume', {
        resume_state: resumeState,
        code: input
      }, {
        params: { client_id: clientIdRef.current }
      })

      setResults(response.data)
      setStatus('success')
    } catch (error) {
      console.error('Resume error:', error)
      setStatus('error')
    }
  }

  const handleDownload = () => {
    if (!results?.tests) return

    const blob = new Blob([results.tests], { type: 'text/plain' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `generated_tests_${Date.now()}.py`
    document.body.appendChild(a)
    a.click()
    document.body.removeChild(a)
    URL.revokeObjectURL(url)
  }

  return (
    <div className="min-h-screen gradient-bg-dark">
      {/* Header */}
      <header className="bg-slate-900/80 backdrop-blur-sm border-b border-slate-700 sticky top-0 z-50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-3">
              <div className="w-10 h-10 bg-gradient-to-br from-cyan-400 to-blue-500 rounded-lg flex items-center justify-center">
                <span className="text-white font-bold text-xl">AT</span>
              </div>
              <div>
                <h1 className="text-2xl font-bold text-white">Agentic Test Generator</h1>
                <p className="text-sm text-slate-400">AI-powered test generation</p>
              </div>
            </div>
            <div className="flex items-center space-x-2">
              <div className={`px-3 py-1 rounded-full text-xs font-medium ${
                wsConnection ? 'bg-green-500/20 text-green-400' : 'bg-red-500/20 text-red-400'
              }`}>
                {wsConnection ? '● Connected' : '○ Disconnected'}
              </div>
            </div>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Agent Workflow Visualization */}
        <div className="mb-8">
          <AgentWorkflow currentStep={currentStep} status={status} />
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Left Column: Input */}
          <div className="space-y-6">
            <div className="bg-slate-800/50 backdrop-blur-sm rounded-xl border border-slate-700 p-6">
              <InputForm
                mode={mode}
                onModeChange={setMode}
                onSubmit={handleSubmit}
                isRunning={status === 'running'}
              />
            </div>

            {/* Progress Display */}
            {status === 'running' && (
              <div className="bg-slate-800/50 backdrop-blur-sm rounded-xl border border-slate-700 p-6">
                <ProgressDisplay progress={progress} status={status} />
              </div>
            )}
          </div>

          {/* Right Column: Results */}
          <div className="space-y-6">
            {results && (
              <div className="bg-slate-800/50 backdrop-blur-sm rounded-xl border border-slate-700 p-6">
                <ResultsDisplay
                  results={results}
                  onDownload={handleDownload}
                  onResume={results.status === 'CODE_BUG' ? () => handleResume(results.resume_state) : null}
                />
              </div>
            )}

            {status === 'idle' && !results && (
              <div className="bg-slate-800/50 backdrop-blur-sm rounded-xl border border-slate-700 p-12 text-center">
                <div className="text-slate-400">
                  <svg className="mx-auto h-12 w-12 mb-4 opacity-50" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                  </svg>
                  <p className="text-lg">Ready to generate tests</p>
                  <p className="text-sm mt-2">Enter your requirements or code above to get started</p>
                </div>
              </div>
            )}
          </div>
        </div>
      </main>
    </div>
  )
}

export default App
