import React from 'react'
import {
  DocumentTextIcon,
  CodeBracketIcon,
  ServerIcon,
  MagnifyingGlassIcon,
  CheckCircleIcon
} from '@heroicons/react/24/outline'
import { CheckCircleIcon as CheckCircleIconSolid } from '@heroicons/react/24/solid'

function AgentWorkflow({ currentStep, status }) {
  const agents = [
    {
      id: 'agent1',
      name: 'Requirements Analysis',
      icon: DocumentTextIcon,
      step: 'STEP 1',
      color: 'blue'
    },
    {
      id: 'agent2',
      name: 'Test Generation',
      icon: CodeBracketIcon,
      step: 'STEP 2',
      color: 'cyan'
    },
    {
      id: 'agent3',
      name: 'Docker Execution',
      icon: ServerIcon,
      step: 'STEP 3',
      color: 'green'
    },
    {
      id: 'agent4',
      name: 'Failure Analysis',
      icon: MagnifyingGlassIcon,
      step: 'STEP 5',
      color: 'yellow'
    }
  ]

  const getAgentStatus = (agent) => {
    if (status === 'idle') return 'idle'
    if (currentStep === agent.step && status === 'running') return 'active'
    if (currentStep === 'COMPLETE' || currentStep === 'SUCCESS') return 'complete'
    // Check if this step has been completed
    const stepNumber = parseInt(agent.step.split(' ')[1])
    const currentStepNumber = currentStep.includes('STEP') 
      ? parseInt(currentStep.split(' ')[1]) 
      : 0
    if (currentStepNumber > stepNumber) return 'complete'
    return 'pending'
  }

  const getColorClasses = (agent, agentStatus) => {
    const colors = {
      blue: {
        idle: 'bg-slate-700 text-slate-400 border-slate-600',
        pending: 'bg-blue-500/10 text-blue-400 border-blue-500/30',
        active: 'bg-blue-500/20 text-blue-400 border-blue-500 animate-pulse',
        complete: 'bg-blue-500/20 text-blue-400 border-blue-500'
      },
      cyan: {
        idle: 'bg-slate-700 text-slate-400 border-slate-600',
        pending: 'bg-cyan-500/10 text-cyan-400 border-cyan-500/30',
        active: 'bg-cyan-500/20 text-cyan-400 border-cyan-500 animate-pulse',
        complete: 'bg-cyan-500/20 text-cyan-400 border-cyan-500'
      },
      green: {
        idle: 'bg-slate-700 text-slate-400 border-slate-600',
        pending: 'bg-green-500/10 text-green-400 border-green-500/30',
        active: 'bg-green-500/20 text-green-400 border-green-500 animate-pulse',
        complete: 'bg-green-500/20 text-green-400 border-green-500'
      },
      yellow: {
        idle: 'bg-slate-700 text-slate-400 border-slate-600',
        pending: 'bg-yellow-500/10 text-yellow-400 border-yellow-500/30',
        active: 'bg-yellow-500/20 text-yellow-400 border-yellow-500 animate-pulse',
        complete: 'bg-yellow-500/20 text-yellow-400 border-yellow-500'
      }
    }
    return colors[agent.color][agentStatus]
  }

  return (
    <div className="bg-slate-800/50 backdrop-blur-sm rounded-xl border border-slate-700 p-6">
      <h2 className="text-lg font-semibold text-white mb-6">Agent Pipeline</h2>
      
      {/* Desktop: Horizontal Layout */}
      <div className="hidden md:flex items-center justify-between">
        {agents.map((agent, index) => {
          const agentStatus = getAgentStatus(agent)
          const Icon = agent.icon
          const colorClasses = getColorClasses(agent, agentStatus)
          const isLast = index === agents.length - 1

          return (
            <React.Fragment key={agent.id}>
              <div className="flex flex-col items-center flex-1">
                <div
                  className={`w-20 h-20 rounded-xl border-2 flex items-center justify-center transition-all ${colorClasses}`}
                >
                  {agentStatus === 'complete' ? (
                    <CheckCircleIconSolid className="w-10 h-10" />
                  ) : agentStatus === 'active' ? (
                    <div className="loading-spinner w-8 h-8 border-2"></div>
                  ) : (
                    <Icon className="w-10 h-10" />
                  )}
                </div>
                <div className="mt-3 text-center">
                  <p className="text-xs font-semibold text-slate-300">{agent.step}</p>
                  <p className="text-xs text-slate-400 mt-1">{agent.name}</p>
                </div>
              </div>
              {!isLast && (
                <div className="flex-1 mx-4 h-0.5 bg-slate-700 relative">
                  <div
                    className={`h-full transition-all ${
                      agentStatus === 'complete' || agentStatus === 'active'
                        ? 'bg-gradient-to-r from-cyan-400 to-blue-500'
                        : 'bg-slate-700'
                    }`}
                    style={{
                      width: agentStatus === 'complete' ? '100%' : agentStatus === 'active' ? '50%' : '0%'
                    }}
                  />
                </div>
              )}
            </React.Fragment>
          )
        })}
      </div>

      {/* Mobile: Vertical Layout */}
      <div className="md:hidden space-y-4">
        {agents.map((agent, index) => {
          const agentStatus = getAgentStatus(agent)
          const Icon = agent.icon
          const colorClasses = getColorClasses(agent, agentStatus)

          return (
            <React.Fragment key={agent.id}>
              <div className="flex items-center space-x-4">
                <div
                  className={`w-16 h-16 rounded-xl border-2 flex items-center justify-center flex-shrink-0 transition-all ${colorClasses}`}
                >
                  {agentStatus === 'complete' ? (
                    <CheckCircleIconSolid className="w-8 h-8" />
                  ) : agentStatus === 'active' ? (
                    <div className="loading-spinner w-6 h-6 border-2"></div>
                  ) : (
                    <Icon className="w-8 h-8" />
                  )}
                </div>
                <div className="flex-1">
                  <p className="text-sm font-semibold text-slate-300">{agent.step}</p>
                  <p className="text-xs text-slate-400">{agent.name}</p>
                </div>
              </div>
              {index < agents.length - 1 && (
                <div className="ml-8 w-0.5 h-6 bg-slate-700 relative">
                  <div
                    className={`w-full transition-all ${
                      agentStatus === 'complete' || agentStatus === 'active'
                        ? 'bg-gradient-to-b from-cyan-400 to-blue-500'
                        : 'bg-slate-700'
                    }`}
                    style={{
                      height: agentStatus === 'complete' ? '100%' : agentStatus === 'active' ? '50%' : '0%'
                    }}
                  />
                </div>
              )}
            </React.Fragment>
          )
        })}
      </div>
    </div>
  )
}

export default AgentWorkflow
