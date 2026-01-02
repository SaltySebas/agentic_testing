import React, { useState } from 'react'
import { PlayIcon, CodeBracketIcon, DocumentTextIcon } from '@heroicons/react/24/outline'

function InputForm({ mode, onModeChange, onSubmit, isRunning }) {
  const [input, setInput] = useState('')
  const [maxIterations, setMaxIterations] = useState(5)
  const [error, setError] = useState('')

  const handleSubmit = (e) => {
    e.preventDefault()
    setError('')

    if (!input.trim()) {
      setError('Please enter some input')
      return
    }

    onSubmit(input, maxIterations)
  }

  const placeholder = mode === 'generate'
    ? 'Enter requirements for code generation...\n\nExample:\nCreate a function that calculates discount based on customer type and quantity.\n- Regular: 5% if quantity >= 10\n- Premium: 15% always\n- VIP: 20% base, +5% if quantity >= 20'
    : 'Paste your function code here...\n\nExample:\ndef calculate_discount(price, customer_type, quantity):\n    """Calculate discount based on customer type and quantity."""\n    # Your code here\n    pass'

  return (
    <div className="space-y-6">
      {/* Mode Selector */}
      <div className="flex space-x-2">
        <button
          type="button"
          onClick={() => onModeChange('generate')}
          className={`flex-1 flex items-center justify-center space-x-2 px-4 py-3 rounded-lg font-medium transition-all ${
            mode === 'generate'
              ? 'bg-gradient-to-r from-cyan-500 to-blue-500 text-white shadow-lg shadow-cyan-500/50'
              : 'bg-slate-700 text-slate-300 hover:bg-slate-600'
          }`}
        >
          <DocumentTextIcon className="w-5 h-5" />
          <span>Generate</span>
        </button>
        <button
          type="button"
          onClick={() => onModeChange('test')}
          className={`flex-1 flex items-center justify-center space-x-2 px-4 py-3 rounded-lg font-medium transition-all ${
            mode === 'test'
              ? 'bg-gradient-to-r from-cyan-500 to-blue-500 text-white shadow-lg shadow-cyan-500/50'
              : 'bg-slate-700 text-slate-300 hover:bg-slate-600'
          }`}
        >
          <CodeBracketIcon className="w-5 h-5" />
          <span>Test</span>
        </button>
      </div>

      <form onSubmit={handleSubmit} className="space-y-4">
        {/* Textarea */}
        <div>
          <label className="block text-sm font-medium text-slate-300 mb-2">
            {mode === 'generate' ? 'Requirements' : 'Function Code'}
          </label>
          <textarea
            value={input}
            onChange={(e) => {
              setInput(e.target.value)
              setError('')
            }}
            placeholder={placeholder}
            rows={12}
            className={`w-full px-4 py-3 bg-slate-900 border rounded-lg text-slate-100 placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-cyan-500 focus:border-transparent transition-all font-mono text-sm ${
              error ? 'border-red-500' : 'border-slate-600'
            }`}
            disabled={isRunning}
          />
          {error && (
            <p className="mt-2 text-sm text-red-400">{error}</p>
          )}
        </div>

        {/* Max Iterations Slider */}
        <div>
          <label className="block text-sm font-medium text-slate-300 mb-2">
            Max Iterations: {maxIterations}
          </label>
          <input
            type="range"
            min="1"
            max="10"
            value={maxIterations}
            onChange={(e) => setMaxIterations(parseInt(e.target.value))}
            className="w-full h-2 bg-slate-700 rounded-lg appearance-none cursor-pointer accent-cyan-500"
            disabled={isRunning}
          />
          <div className="flex justify-between text-xs text-slate-400 mt-1">
            <span>1</span>
            <span>5</span>
            <span>10</span>
          </div>
        </div>

        {/* Submit Button */}
        <button
          type="submit"
          disabled={isRunning || !input.trim()}
          className={`w-full flex items-center justify-center space-x-2 px-6 py-3 rounded-lg font-semibold text-white transition-all ${
            isRunning || !input.trim()
              ? 'bg-slate-700 cursor-not-allowed'
              : 'bg-gradient-to-r from-cyan-500 to-blue-500 hover:from-cyan-600 hover:to-blue-600 shadow-lg shadow-cyan-500/50 hover:shadow-xl hover:shadow-cyan-500/50 transform hover:scale-[1.02]'
          }`}
        >
          {isRunning ? (
            <>
              <div className="loading-spinner w-5 h-5 border-2"></div>
              <span>Running...</span>
            </>
          ) : (
            <>
              <PlayIcon className="w-5 h-5" />
              <span>{mode === 'generate' ? 'Generate Tests' : 'Test Code'}</span>
            </>
          )}
        </button>
      </form>
    </div>
  )
}

export default InputForm
