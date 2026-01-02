import React, { useEffect, useRef } from 'react'
import { CheckCircleIcon, XCircleIcon, ClockIcon } from '@heroicons/react/24/outline'
import { CheckCircleIcon as CheckCircleIconSolid } from '@heroicons/react/24/solid'

function ProgressDisplay({ progress, status }) {
  const scrollRef = useRef(null)

  // Auto-scroll to bottom on new messages
  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight
    }
  }, [progress])

  const getStepColor = (step) => {
    if (step.includes('STEP 1') || step.includes('STEP 2')) {
      return 'bg-blue-500/20 text-blue-400 border-blue-500/50'
    }
    if (step.includes('STEP 3')) {
      return 'bg-green-500/20 text-green-400 border-green-500/50'
    }
    if (step.includes('STEP 5') || step.includes('STEP 6')) {
      return 'bg-yellow-500/20 text-yellow-400 border-yellow-500/50'
    }
    if (step === 'SUCCESS' || step === 'COMPLETE') {
      return 'bg-green-500/20 text-green-400 border-green-500/50'
    }
    if (step === 'ERROR') {
      return 'bg-red-500/20 text-red-400 border-red-500/50'
    }
    if (step.includes('RESUME') || step.includes('START')) {
      return 'bg-cyan-500/20 text-cyan-400 border-cyan-500/50'
    }
    return 'bg-slate-700/50 text-slate-300 border-slate-600'
  }

  const formatTime = (date) => {
    return date.toLocaleTimeString('en-US', { 
      hour12: false,
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit'
    })
  }

  const isComplete = (step, index) => {
    if (step === 'ERROR') return false
    if (index < progress.length - 1) return true
    if (status === 'success' && index === progress.length - 1) return true
    return false
  }

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h3 className="text-lg font-semibold text-white">Progress</h3>
        {status === 'running' && (
          <div className="flex items-center space-x-2 text-sm text-slate-400">
            <div className="loading-spinner w-4 h-4 border-2"></div>
            <span>Running...</span>
          </div>
        )}
      </div>

      <div
        ref={scrollRef}
        className="custom-scrollbar max-h-96 overflow-y-auto space-y-2 bg-slate-900/50 rounded-lg p-4"
      >
        {progress.length === 0 ? (
          <div className="text-center text-slate-400 py-8">
            <ClockIcon className="w-8 h-8 mx-auto mb-2 opacity-50" />
            <p>Waiting for progress updates...</p>
          </div>
        ) : (
          progress.map((item, index) => {
            const isCompleted = isComplete(item.step, index)
            const isLast = index === progress.length - 1

            return (
              <div
                key={index}
                className={`flex items-start space-x-3 p-3 rounded-lg border transition-all animate-fade-in ${
                  isLast && status === 'running' ? 'bg-slate-800/50' : 'bg-slate-900/30'
                } ${getStepColor(item.step)}`}
              >
                {/* Icon */}
                <div className="flex-shrink-0 mt-0.5">
                  {isCompleted ? (
                    <CheckCircleIconSolid className="w-5 h-5 text-green-400" />
                  ) : isLast && status === 'running' ? (
                    <div className="loading-spinner w-5 h-5 border-2 border-cyan-400"></div>
                  ) : item.step === 'ERROR' ? (
                    <XCircleIcon className="w-5 h-5 text-red-400" />
                  ) : (
                    <ClockIcon className="w-5 h-5 opacity-50" />
                  )}
                </div>

                {/* Content */}
                <div className="flex-1 min-w-0">
                  <div className="flex items-center space-x-2 mb-1">
                    <span className="px-2 py-0.5 text-xs font-semibold rounded border">
                      {item.step}
                    </span>
                    <span className="text-xs text-slate-400 font-mono">
                      {formatTime(item.timestamp)}
                    </span>
                  </div>
                  <p className="text-sm text-slate-200 font-mono whitespace-pre-wrap break-words">
                    {item.message}
                  </p>
                </div>
              </div>
            )
          })
        )}
      </div>
    </div>
  )
}

export default ProgressDisplay
