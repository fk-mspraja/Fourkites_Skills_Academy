"use client"

import { useState } from "react"
import { useInvestigation } from "@/hooks/useInvestigation"
import { StreamingChat } from "@/components/investigation/StreamingChat"
import { LogsPanel } from "@/components/investigation/LogsPanel"
import { AgentDiscussionPanel } from "@/components/investigation/AgentDiscussionPanel"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Textarea } from "@/components/ui/textarea"
import { Badge } from "@/components/ui/badge"
import {
  Microscope,
  Send,
  RotateCcw,
  Lightbulb,
  AlertTriangle,
  CheckCircle,
  Users,
  Loader2,
  Sparkles,
  Terminal,
  Database,
  Radio,
  Settings,
  Wrench,
  Waves,
  Ship,
  BookOpen,
  MessageSquare,
  Ticket,
  ChevronDown,
  ChevronRight,
  ExternalLink,
  Activity,
  Layers,
  Zap,
} from "lucide-react"
import { Progress } from "@/components/ui/progress"

const sourceIcons: Record<string, React.ReactNode> = {
  "tracking": <Radio className="w-4 h-4" />,
  "redshift": <Database className="w-4 h-4" />,
  "callbacks": <Activity className="w-4 h-4" />,
  "super": <Settings className="w-4 h-4" />,
  "jt": <Wrench className="w-4 h-4" />,
  "ocean_events": <Waves className="w-4 h-4" />,
  "ocean_trace": <Ship className="w-4 h-4" />,
  "confluence": <BookOpen className="w-4 h-4" />,
  "slack": <MessageSquare className="w-4 h-4" />,
  "jira": <Ticket className="w-4 h-4" />,
}

export default function HomePage() {
  const { state, startInvestigation } = useInvestigation()
  const [issueText, setIssueText] = useState("")
  const [collaborative, setCollaborative] = useState(true)
  const [showLogs, setShowLogs] = useState(false)
  const [expandedSources, setExpandedSources] = useState<Set<string>>(new Set())
  const [expandedHypotheses, setExpandedHypotheses] = useState<Set<string>>(new Set())

  const isRunning = state.status === "running"
  const isComplete = state.status === "complete"

  const handleSubmit = () => {
    if (issueText.trim() && !isRunning) {
      startInvestigation(issueText.trim(), collaborative)
    }
  }

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && (e.metaKey || e.ctrlKey)) {
      handleSubmit()
    }
  }

  const toggleSourceExpanded = (source: string) => {
    setExpandedSources((prev) => {
      const next = new Set(prev)
      if (next.has(source)) {
        next.delete(source)
      } else {
        next.add(source)
      }
      return next
    })
  }

  const toggleHypothesisExpanded = (id: string) => {
    setExpandedHypotheses((prev) => {
      const next = new Set(prev)
      if (next.has(id)) {
        next.delete(id)
      } else {
        next.add(id)
      }
      return next
    })
  }

  const dataSourceCount = Object.keys(state.dataSources).length

  return (
    <div className="min-h-screen bg-[#000000]">
      {/* Header */}
      <header className="border-b border-[#1a1a1a] bg-[#050505]">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-lg bg-gradient-to-br from-emerald-500 to-teal-600 flex items-center justify-center">
                <Microscope className="w-5 h-5 text-white" />
              </div>
              <div>
                <h1 className="text-lg font-semibold text-white tracking-tight">
                  RCA Platform
                </h1>
                <p className="text-xs text-gray-500">
                  Multi-Agent Root Cause Analysis
                </p>
              </div>
            </div>
            <div className="flex items-center gap-3">
              {state.investigation_id && (
                <div className="text-xs text-gray-600 font-mono bg-[#0a0a0a] px-3 py-1.5 rounded border border-[#1a1a1a]">
                  {state.investigation_id.slice(0, 8)}
                </div>
              )}
              {state.iteration > 0 && (
                <div className="text-xs text-gray-500 font-mono">
                  Iteration {state.iteration}/{state.maxIterations}
                </div>
              )}
              {isRunning && (
                <Badge className="bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 gap-1.5">
                  <Loader2 className="w-3 h-3 animate-spin" />
                  Running
                </Badge>
              )}
              {isComplete && (
                <Badge className="bg-blue-500/10 text-blue-400 border border-blue-500/20 gap-1.5">
                  <CheckCircle className="w-3 h-3" />
                  Complete
                </Badge>
              )}
            </div>
          </div>

          {/* Progress Bar - Shows during investigation */}
          {isRunning && state.heartbeat && (
            <div className="mt-4 space-y-2">
              <div className="flex items-center justify-between text-xs">
                <div className="flex items-center gap-2 text-gray-400">
                  <Zap className="w-3 h-3 text-emerald-500" />
                  <span>{state.heartbeat.current_activity}</span>
                </div>
                <div className="flex items-center gap-3 text-gray-500">
                  <span className="font-mono">{state.heartbeat.progress_percent}%</span>
                  <span>|</span>
                  <span>{state.heartbeat.data_sources_queried}/{state.heartbeat.data_sources_total} sources</span>
                </div>
              </div>
              <Progress value={state.heartbeat.progress_percent} className="h-1.5 bg-[#1a1a1a]" />
              {state.heartbeat.agents_running.length > 0 && (
                <div className="flex items-center gap-2 text-[10px] text-gray-600">
                  <span>Active:</span>
                  {state.heartbeat.agents_running.map((agent, idx) => (
                    <Badge key={idx} variant="outline" className="text-[10px] border-emerald-500/30 text-emerald-400 py-0 px-1.5">
                      {agent}
                    </Badge>
                  ))}
                </div>
              )}
            </div>
          )}
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Left Column - Input & Controls */}
          <div className="space-y-4">
            {/* Input Card */}
            <Card className="bg-[#0a0a0a] border-[#1a1a1a]">
              <CardHeader className="pb-3">
                <CardTitle className="text-white text-sm font-medium flex items-center gap-2">
                  <Sparkles className="w-4 h-4 text-emerald-500" />
                  New Investigation
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <Textarea
                  placeholder="Enter tracking ID, load number, or describe the issue..."
                  value={issueText}
                  onChange={(e) => setIssueText(e.target.value)}
                  onKeyDown={handleKeyDown}
                  className="min-h-[120px] bg-[#050505] border-[#1a1a1a] text-gray-200 placeholder:text-gray-600 focus:border-emerald-500/50 focus:ring-emerald-500/20 resize-none"
                  disabled={isRunning}
                />

                {/* Mode Toggle */}
                <div className="flex items-center justify-between p-3 rounded-lg bg-[#050505] border border-[#1a1a1a]">
                  <div className="flex items-center gap-2">
                    <Users className="w-4 h-4 text-gray-500" />
                    <div>
                      <div className="text-sm font-medium text-gray-300">Collaborative</div>
                      <div className="text-xs text-gray-600">Agents discuss together</div>
                    </div>
                  </div>
                  <button
                    onClick={() => setCollaborative(!collaborative)}
                    className={`relative w-11 h-6 rounded-full transition-colors ${
                      collaborative ? "bg-emerald-500" : "bg-[#1a1a1a]"
                    }`}
                    disabled={isRunning}
                  >
                    <div
                      className={`absolute top-1 w-4 h-4 rounded-full bg-white transition-transform shadow-sm ${
                        collaborative ? "translate-x-6" : "translate-x-1"
                      }`}
                    />
                  </button>
                </div>

                <div className="flex gap-2">
                  <Button
                    onClick={handleSubmit}
                    disabled={!issueText.trim() || isRunning}
                    className="flex-1 bg-emerald-600 hover:bg-emerald-700 text-white border-0"
                  >
                    {isRunning ? (
                      <>
                        <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                        Investigating...
                      </>
                    ) : (
                      <>
                        <Send className="w-4 h-4 mr-2" />
                        Investigate
                      </>
                    )}
                  </Button>
                  <Button
                    variant="outline"
                    onClick={() => {
                      setIssueText("")
                      window.location.reload()
                    }}
                    className="bg-transparent border-[#1a1a1a] text-gray-400 hover:bg-[#1a1a1a] hover:text-gray-300"
                  >
                    <RotateCcw className="w-4 h-4" />
                  </Button>
                </div>

                <div className="text-[10px] text-gray-600 text-center">
                  <kbd className="px-1.5 py-0.5 bg-[#1a1a1a] rounded text-gray-500 font-mono">⌘</kbd>
                  <span className="mx-1">+</span>
                  <kbd className="px-1.5 py-0.5 bg-[#1a1a1a] rounded text-gray-500 font-mono">↵</kbd>
                  <span className="ml-1.5">to submit</span>
                </div>
              </CardContent>
            </Card>

            {/* Logs Button */}
            {state.executedQueries.length > 0 && (
              <Button
                variant="outline"
                onClick={() => setShowLogs(true)}
                className="w-full bg-[#0a0a0a] border-[#1a1a1a] text-gray-300 hover:bg-[#1a1a1a] hover:text-white gap-2"
              >
                <Terminal className="w-4 h-4 text-blue-400" />
                View All Queries & Logs ({state.executedQueries.length})
                <ExternalLink className="w-3 h-3 ml-auto text-gray-500" />
              </Button>
            )}

            {/* Data Sources Card */}
            {dataSourceCount > 0 && (
              <Card className="bg-[#0a0a0a] border-[#1a1a1a]">
                <CardHeader className="pb-3">
                  <CardTitle className="text-white text-sm font-medium flex items-center gap-2">
                    <Layers className="w-4 h-4 text-blue-500" />
                    Data Sources
                    <Badge variant="outline" className="ml-auto border-gray-700 text-gray-500 text-xs">
                      {dataSourceCount}
                    </Badge>
                  </CardTitle>
                </CardHeader>
                <CardContent className="space-y-2">
                  {Object.entries(state.dataSources).map(([key, source]) => {
                    const isExpanded = expandedSources.has(key)
                    const icon = sourceIcons[key.replace("_data", "")] || <Database className="w-4 h-4" />
                    const hasError = source.error || source.timeout

                    return (
                      <div
                        key={key}
                        className={`rounded-lg border transition-colors ${
                          hasError
                            ? "bg-red-500/5 border-red-500/20"
                            : source.exists === false
                            ? "bg-gray-500/5 border-gray-500/20"
                            : "bg-emerald-500/5 border-emerald-500/20"
                        }`}
                      >
                        <button
                          onClick={() => toggleSourceExpanded(key)}
                          className="w-full p-3 flex items-center gap-3 text-left"
                        >
                          <div className={hasError ? "text-red-400" : source.exists === false ? "text-gray-500" : "text-emerald-400"}>
                            {icon}
                          </div>
                          <div className="flex-1 min-w-0">
                            <div className={`text-sm font-medium ${hasError ? "text-red-400" : source.exists === false ? "text-gray-400" : "text-gray-300"}`}>
                              {source.source}
                            </div>
                            <div className="text-xs text-gray-600">
                              {hasError ? "Error" : source.exists === false ? "Not found" : "Data available"}
                            </div>
                          </div>
                          {isExpanded ? (
                            <ChevronDown className="w-4 h-4 text-gray-500" />
                          ) : (
                            <ChevronRight className="w-4 h-4 text-gray-500" />
                          )}
                        </button>

                        {isExpanded && (
                          <div className="px-3 pb-3 border-t border-[#1a1a1a]">
                            <pre className="mt-2 p-2 text-xs text-gray-400 bg-[#050505] rounded overflow-auto max-h-48 font-mono">
                              {JSON.stringify(source.data, null, 2)}
                            </pre>
                          </div>
                        )}
                      </div>
                    )
                  })}
                </CardContent>
              </Card>
            )}

            {/* Hypotheses Card */}
            {state.hypotheses.length > 0 && (
              <Card className="bg-[#0a0a0a] border-[#1a1a1a]">
                <CardHeader className="pb-3">
                  <CardTitle className="text-white text-sm font-medium flex items-center gap-2">
                    <Lightbulb className="w-4 h-4 text-yellow-500" />
                    Hypotheses
                    <span className="text-xs text-gray-600 font-normal ml-auto">Click to expand</span>
                  </CardTitle>
                </CardHeader>
                <CardContent className="space-y-3">
                  {state.hypotheses.map((hyp, idx) => {
                    const isExpanded = expandedHypotheses.has(hyp.id)
                    const hasEvidence = hyp.evidence_for.length > 0 || hyp.evidence_against.length > 0
                    return (
                      <div
                        key={hyp.id}
                        className={`rounded-lg bg-[#050505] border transition-all cursor-pointer hover:border-opacity-60 ${
                          hyp.confidence > 0.7
                            ? "border-emerald-500/30 hover:border-emerald-500/50"
                            : hyp.confidence > 0.4
                            ? "border-yellow-500/30 hover:border-yellow-500/50"
                            : "border-red-500/30 hover:border-red-500/50"
                        }`}
                      >
                        <button
                          onClick={() => toggleHypothesisExpanded(hyp.id)}
                          className="w-full p-3 text-left"
                        >
                          <div className="flex items-center justify-between mb-2">
                            <div className="flex items-center gap-2">
                              <span className="text-xs font-medium text-gray-500">H{idx + 1}</span>
                              <Badge variant="outline" className={`text-[10px] px-1.5 py-0 h-4 ${
                                hyp.confidence > 0.7
                                  ? "border-emerald-500/30 text-emerald-400"
                                  : hyp.confidence > 0.4
                                  ? "border-yellow-500/30 text-yellow-400"
                                  : "border-red-500/30 text-red-400"
                              }`}>
                                {hyp.category}
                              </Badge>
                            </div>
                            <div className="flex items-center gap-2">
                              <span
                                className={`text-xs font-mono ${
                                  hyp.confidence > 0.7
                                    ? "text-emerald-400"
                                    : hyp.confidence > 0.4
                                    ? "text-yellow-400"
                                    : "text-red-400"
                                }`}
                              >
                                {(hyp.confidence * 100).toFixed(0)}%
                              </span>
                              {hasEvidence && (
                                isExpanded ? (
                                  <ChevronDown className="w-4 h-4 text-gray-500" />
                                ) : (
                                  <ChevronRight className="w-4 h-4 text-gray-500" />
                                )
                              )}
                            </div>
                          </div>
                          <p className="text-sm text-gray-300 mb-2">{hyp.description}</p>
                          <div className="h-1 bg-[#1a1a1a] rounded-full overflow-hidden">
                            <div
                              className={`h-full transition-all duration-500 ${
                                hyp.confidence > 0.7
                                  ? "bg-emerald-500"
                                  : hyp.confidence > 0.4
                                  ? "bg-yellow-500"
                                  : "bg-red-500"
                              }`}
                              style={{ width: `${hyp.confidence * 100}%` }}
                            />
                          </div>
                          {/* Collapsed evidence preview */}
                          {!isExpanded && hasEvidence && (
                            <div className="mt-2 flex items-center gap-3 text-[10px] text-gray-600">
                              {hyp.evidence_for.length > 0 && (
                                <span className="flex items-center gap-1">
                                  <span className="text-emerald-500">+</span>
                                  {hyp.evidence_for.length} supporting
                                </span>
                              )}
                              {hyp.evidence_against.length > 0 && (
                                <span className="flex items-center gap-1">
                                  <span className="text-red-500">-</span>
                                  {hyp.evidence_against.length} contradicting
                                </span>
                              )}
                            </div>
                          )}
                        </button>

                        {/* Expanded evidence details */}
                        {isExpanded && hasEvidence && (
                          <div className="px-3 pb-3 border-t border-[#1a1a1a]">
                            <div className="mt-3 space-y-3">
                              {/* Supporting Evidence */}
                              {hyp.evidence_for.length > 0 && (
                                <div>
                                  <div className="text-[10px] uppercase tracking-wider text-emerald-500 mb-2 flex items-center gap-1">
                                    <CheckCircle className="w-3 h-3" />
                                    Supporting Evidence ({hyp.evidence_for.length})
                                  </div>
                                  <div className="space-y-2">
                                    {hyp.evidence_for.map((e, i) => (
                                      <div key={i} className="p-2 rounded bg-emerald-500/5 border border-emerald-500/10">
                                        <div className="flex items-center gap-2 mb-1">
                                          <Badge variant="outline" className="text-[9px] px-1 py-0 h-3.5 border-emerald-500/30 text-emerald-400">
                                            {e.source}
                                          </Badge>
                                          <span className="text-[10px] text-emerald-400/60 font-mono">
                                            weight: {(e.weight * 100).toFixed(0)}%
                                          </span>
                                        </div>
                                        <p className="text-xs text-gray-400">{e.finding}</p>
                                      </div>
                                    ))}
                                  </div>
                                </div>
                              )}

                              {/* Contradicting Evidence */}
                              {hyp.evidence_against.length > 0 && (
                                <div>
                                  <div className="text-[10px] uppercase tracking-wider text-red-500 mb-2 flex items-center gap-1">
                                    <AlertTriangle className="w-3 h-3" />
                                    Contradicting Evidence ({hyp.evidence_against.length})
                                  </div>
                                  <div className="space-y-2">
                                    {hyp.evidence_against.map((e, i) => (
                                      <div key={i} className="p-2 rounded bg-red-500/5 border border-red-500/10">
                                        <div className="flex items-center gap-2 mb-1">
                                          <Badge variant="outline" className="text-[9px] px-1 py-0 h-3.5 border-red-500/30 text-red-400">
                                            {e.source}
                                          </Badge>
                                          <span className="text-[10px] text-red-400/60 font-mono">
                                            weight: {(e.weight * 100).toFixed(0)}%
                                          </span>
                                        </div>
                                        <p className="text-xs text-gray-400">{e.finding}</p>
                                      </div>
                                    ))}
                                  </div>
                                </div>
                              )}
                            </div>
                          </div>
                        )}
                      </div>
                    )
                  })}
                </CardContent>
              </Card>
            )}

            {/* Human Input Card */}
            {state.needsHuman && (
              <Card className="bg-[#0a0a0a] border-yellow-500/20">
                <CardHeader className="pb-3">
                  <CardTitle className="text-yellow-400 text-sm font-medium flex items-center gap-2">
                    <AlertTriangle className="w-4 h-4" />
                    Human Input Required
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <p className="text-sm text-gray-300 whitespace-pre-wrap leading-relaxed">
                    {state.humanQuestion}
                  </p>
                </CardContent>
              </Card>
            )}

            {/* Root Cause Card */}
            {state.rootCause && (
              <Card className="bg-[#0a0a0a] border-emerald-500/20">
                <CardHeader className="pb-3">
                  <CardTitle className="text-emerald-400 text-sm font-medium flex items-center gap-2">
                    <CheckCircle className="w-4 h-4" />
                    Root Cause Identified
                  </CardTitle>
                </CardHeader>
                <CardContent className="space-y-3">
                  <div>
                    <div className="text-[10px] uppercase tracking-wider text-gray-600 mb-1">Category</div>
                    <Badge variant="outline" className="border-emerald-500/30 text-emerald-400 bg-emerald-500/5">
                      {state.rootCause.category}
                    </Badge>
                  </div>
                  <div>
                    <div className="text-[10px] uppercase tracking-wider text-gray-600 mb-1">Description</div>
                    <p className="text-sm text-gray-300">{state.rootCause.description}</p>
                  </div>
                  <div>
                    <div className="text-[10px] uppercase tracking-wider text-gray-600 mb-1">Confidence</div>
                    <div className="flex items-center gap-3">
                      <div className="flex-1 h-1.5 bg-[#1a1a1a] rounded-full overflow-hidden">
                        <div
                          className="h-full bg-emerald-500 transition-all duration-500"
                          style={{ width: `${state.rootCause.confidence * 100}%` }}
                        />
                      </div>
                      <span className="text-sm font-mono text-emerald-400">
                        {(state.rootCause.confidence * 100).toFixed(0)}%
                      </span>
                    </div>
                  </div>
                  {state.rootCause.recommended_actions && state.rootCause.recommended_actions.length > 0 && (
                    <div>
                      <div className="text-[10px] uppercase tracking-wider text-gray-600 mb-2">Recommended Actions</div>
                      <div className="space-y-2">
                        {state.rootCause.recommended_actions.map((action, idx) => (
                          <div key={idx} className="p-2 rounded bg-[#050505] border border-[#1a1a1a]">
                            <div className="flex items-center gap-2 mb-1">
                              <Badge
                                variant="outline"
                                className={`text-[10px] ${
                                  action.priority === "high"
                                    ? "border-red-500/30 text-red-400"
                                    : action.priority === "medium"
                                    ? "border-yellow-500/30 text-yellow-400"
                                    : "border-gray-500/30 text-gray-400"
                                }`}
                              >
                                {action.priority}
                              </Badge>
                              <span className="text-xs text-gray-500">{action.category}</span>
                            </div>
                            <p className="text-sm text-gray-300">{action.description}</p>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}
                </CardContent>
              </Card>
            )}
          </div>

          {/* Right Column - Agent Activity (spans 2 columns) */}
          <div className="lg:col-span-2 space-y-4">
            {/* Agent Discussion Panel - Human-level collaboration view */}
            {collaborative && (state.discussions.length > 0 || state.decisions.length > 0) && (
              <AgentDiscussionPanel
                discussions={state.discussions}
                decisions={state.decisions}
                iterations={state.iteration}
              />
            )}

            {/* Streaming Chat - Technical activity feed */}
            <StreamingChat
              messages={state.streamMessages}
              isStreaming={isRunning}
              currentAgent={state.currentAgent}
            />
          </div>
        </div>
      </main>

      {/* Footer */}
      <footer className="mt-8 py-4 border-t border-[#1a1a1a]">
        <div className="max-w-7xl mx-auto px-4 text-center text-[10px] text-gray-700">
          RCA Platform v2.0 — Multi-Agent Orchestration
        </div>
      </footer>

      {/* Logs Panel Modal */}
      <LogsPanel
        queries={state.executedQueries}
        isOpen={showLogs}
        onClose={() => setShowLogs(false)}
      />
    </div>
  )
}
