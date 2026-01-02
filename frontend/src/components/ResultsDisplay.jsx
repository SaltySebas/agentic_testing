import React, { useState } from 'react'
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter'
import { vscDarkPlus } from 'react-syntax-highlighter/dist/esm/styles/prism'
import {
  CheckCircleIcon,
  XCircleIcon,
  ExclamationTriangleIcon,
  ArrowDownTrayIcon,
  ArrowPathIcon,
  ClipboardIcon,
  ChevronDownIcon,
  ChevronUpIcon
} from '@heroicons/react/24/outline'

function ResultsDisplay({ results, onDownload, onResume }) {
  const [copied, setCopied] = useState(false)
  const [expandedSections, setExpandedSections] = useState({
    code: true,
    tests: true,
    analysis: false
  })

  const copyToClipboard = () => {
    if (results?.tests) {
      navigator.clipboard.writeText(results.tests)
      setCopied(true)
      setTimeout(() => setCopied(false), 2000)
    }
  }

  const toggleSection = (section) => {
    setExpandedSections(prev => ({
      ...prev,
      [section]: !prev[section]
    }))
  }

  const getStatusColor = () => {
    switch (results?.status) {
      case 'SUCCESS':
        return 'bg-green-500/20 text-green-400 border-green-500/50'
      case 'CODE_BUG':
      case 'TEST_BUG':
      case 'REQUIREMENTS_AMBIGUITY':
        return 'bg-yellow-500/20 text-yellow-400 border-yellow-500/50'
      case 'ERROR':
        return 'bg-red-500/20 text-red-400 border-red-500/50'
      default:
        return 'bg-slate-700/50 text-slate-300 border-slate-600'
    }
  }

  const getStatusIcon = () => {
    switch (results?.status) {
      case 'SUCCESS':
        return <CheckCircleIcon className="w-6 h-6 text-green-400" />
      case 'CODE_BUG':
      case 'TEST_BUG':
      case 'REQUIREMENTS_AMBIGUITY':
        return <ExclamationTriangleIcon className="w-6 h-6 text-yellow-400" />
      case 'ERROR':
        return <XCircleIcon className="w-6 h-6 text-red-400" />
      default:
        return null
    }
  }

  const testResults = results?.test_results || {}
  const passed = testResults.passed || 0
  const failed = testResults.failed || 0
  const total = passed + failed
  const passPercentage = total > 0 ? (passed / total) * 100 : 0

  return (
    <div className="space-y-6">
      {/* Status Banner */}
      <div className={`flex items-center space-x-3 p-4 rounded-lg border ${getStatusColor()}`}>
        {getStatusIcon()}
        <div className="flex-1">
          <h3 className="font-semibold">{results?.status || 'Unknown'}</h3>
          <p className="text-sm opacity-90">{results?.message || ''}</p>
        </div>
      </div>

      {/* Summary Stats */}
      <div className="grid grid-cols-3 gap-4">
        <div className="bg-slate-900/50 rounded-lg p-4 border border-slate-700">
          <div className="text-2xl font-bold text-cyan-400">{results?.iterations || 0}</div>
          <div className="text-sm text-slate-400">Iterations</div>
        </div>
        <div className="bg-slate-900/50 rounded-lg p-4 border border-slate-700">
          <div className="text-2xl font-bold text-green-400">{passed}</div>
          <div className="text-sm text-slate-400">Passed</div>
        </div>
        <div className="bg-slate-900/50 rounded-lg p-4 border border-slate-700">
          <div className="text-2xl font-bold text-red-400">{failed}</div>
          <div className="text-sm text-slate-400">Failed</div>
        </div>
      </div>

      {/* Test Results Progress */}
      {total > 0 && (
        <div className="bg-slate-900/50 rounded-lg p-4 border border-slate-700">
          <div className="flex items-center justify-between mb-2">
            <span className="text-sm font-medium text-slate-300">Test Results</span>
            <span className="text-sm text-slate-400">{passed}/{total} passed</span>
          </div>
          <div className="w-full bg-slate-800 rounded-full h-2">
            <div
              className="bg-gradient-to-r from-green-500 to-green-400 h-2 rounded-full transition-all duration-500"
              style={{ width: `${passPercentage}%` }}
            />
          </div>
          {testResults.failing_tests && testResults.failing_tests.length > 0 && (
            <div className="mt-3">
              <p className="text-sm text-red-400 mb-1">Failing tests:</p>
              <div className="flex flex-wrap gap-2">
                {testResults.failing_tests.map((test, idx) => (
                  <span key={idx} className="px-2 py-1 bg-red-500/20 text-red-400 rounded text-xs font-mono">
                    {test}
                  </span>
                ))}
              </div>
            </div>
          )}
        </div>
      )}

      {/* Generated Code */}
      {results?.tests && (
        <div className="bg-slate-900/50 rounded-lg border border-slate-700 overflow-hidden">
          <div className="flex items-center justify-between p-4 border-b border-slate-700">
            <h3 className="font-semibold text-white">Generated Code</h3>
            <div className="flex items-center space-x-2">
              <button
                onClick={copyToClipboard}
                className="p-2 hover:bg-slate-800 rounded-lg transition-colors"
                title="Copy to clipboard"
              >
                <ClipboardIcon className={`w-5 h-5 ${copied ? 'text-green-400' : 'text-slate-400'}`} />
              </button>
              <button
                onClick={onDownload}
                className="p-2 hover:bg-slate-800 rounded-lg transition-colors"
                title="Download"
              >
                <ArrowDownTrayIcon className="w-5 h-5 text-slate-400" />
              </button>
              <button
                onClick={() => toggleSection('code')}
                className="p-2 hover:bg-slate-800 rounded-lg transition-colors"
              >
                {expandedSections.code ? (
                  <ChevronUpIcon className="w-5 h-5 text-slate-400" />
                ) : (
                  <ChevronDownIcon className="w-5 h-5 text-slate-400" />
                )}
              </button>
            </div>
          </div>
          {expandedSections.code && (
            <div className="code-block">
              <SyntaxHighlighter
                language="python"
                style={vscDarkPlus}
                customStyle={{ margin: 0, background: 'transparent' }}
                showLineNumbers
              >
                {results.tests}
              </SyntaxHighlighter>
            </div>
          )}
        </div>
      )}

      {/* Analysis Section */}
      {results?.analysis && (
        <div className="bg-slate-900/50 rounded-lg border border-slate-700 overflow-hidden">
          <div className="flex items-center justify-between p-4 border-b border-slate-700">
            <h3 className="font-semibold text-white">Analysis</h3>
            <button
              onClick={() => toggleSection('analysis')}
              className="p-2 hover:bg-slate-800 rounded-lg transition-colors"
            >
              {expandedSections.analysis ? (
                <ChevronUpIcon className="w-5 h-5 text-slate-400" />
              ) : (
                <ChevronDownIcon className="w-5 h-5 text-slate-400" />
              )}
            </button>
          </div>
          {expandedSections.analysis && (
            <div className="p-4 space-y-4">
              <div>
                <span className="text-sm text-slate-400">Failure Type:</span>
                <span className="ml-2 text-sm font-semibold text-yellow-400">
                  {results.analysis.failure_type}
                </span>
              </div>
              {results.analysis.confidence && (
                <div>
                  <span className="text-sm text-slate-400">Confidence:</span>
                  <span className="ml-2 text-sm font-semibold text-cyan-400">
                    {results.analysis.confidence}%
                  </span>
                </div>
              )}
              {results.analysis.analysis && (
                <div>
                  <p className="text-sm text-slate-400 mb-1">Analysis:</p>
                  <p className="text-sm text-slate-200 whitespace-pre-wrap">
                    {results.analysis.analysis}
                  </p>
                </div>
              )}
              {results.analysis.suggested_fix && (
                <div>
                  <p className="text-sm text-slate-400 mb-1">Suggested Fix:</p>
                  <div className="code-block">
                    <SyntaxHighlighter
                      language="python"
                      style={vscDarkPlus}
                      customStyle={{ margin: 0, background: 'transparent' }}
                    >
                      {results.analysis.suggested_fix}
                    </SyntaxHighlighter>
                  </div>
                </div>
              )}
            </div>
          )}
        </div>
      )}

      {/* Resume Button */}
      {onResume && results?.status === 'CODE_BUG' && (
        <button
          onClick={onResume}
          className="w-full flex items-center justify-center space-x-2 px-6 py-3 bg-gradient-to-r from-yellow-500 to-orange-500 hover:from-yellow-600 hover:to-orange-600 text-white rounded-lg font-semibold transition-all shadow-lg hover:shadow-xl transform hover:scale-[1.02]"
        >
          <ArrowPathIcon className="w-5 h-5" />
          <span>Resume After Fix</span>
        </button>
      )}
    </div>
  )
}

export default ResultsDisplay
