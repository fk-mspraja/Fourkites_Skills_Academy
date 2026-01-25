"use client"

import { useEffect, useRef, useState } from "react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import {
  Search,
  Target,
  Radio,
  Database,
  Settings,
  Wrench,
  Waves,
  Ship,
  BookOpen,
  MessageSquare,
  Ticket,
  Lightbulb,
  Brain,
  Bot,
  CheckCircle2,
  Loader2,
  AlertCircle,
  ArrowDown,
  Zap,
  Activity,
  ChevronDown,
  ChevronRight,
  Code,
  Clock,
  Hash,
  Terminal,
  GitBranch,
  Eye,
  Copy,
  Check,
} from "lucide-react"

interface StreamMessage {
  id: string
  agent: string
  content: string
  type: "message" | "thinking" | "tool" | "result" | "error" | "decision" | "query"
  timestamp: Date
  status?: "running" | "completed" | "error"
  metadata?: Record<string, unknown>
  queryDetails?: {
    source: string
    query: string
    result_count?: number
    duration_ms?: number
    raw_result?: unknown
    error?: string
  }
}

interface StreamingChatProps {
  messages: StreamMessage[]
  isStreaming: boolean
  currentAgent?: string
}

const agentConfig: Record<string, { icon: React.ReactNode; color: string; bgColor: string; borderColor: string }> = {
  "System": {
    icon: <Zap className="w-4 h-4" />,
    color: "text-emerald-400",
    bgColor: "bg-emerald-500/10",
    borderColor: "border-emerald-500/20"
  },
  "Identifier Agent": {
    icon: <Search className="w-4 h-4" />,
    color: "text-blue-400",
    bgColor: "bg-blue-500/10",
    borderColor: "border-blue-500/20"
  },
  "Coordinator": {
    icon: <Target className="w-4 h-4" />,
    color: "text-purple-400",
    bgColor: "bg-purple-500/10",
    borderColor: "border-purple-500/20"
  },
  "Coordinator Agent": {
    icon: <Target className="w-4 h-4" />,
    color: "text-purple-400",
    bgColor: "bg-purple-500/10",
    borderColor: "border-purple-500/20"
  },
  "Tracking API Agent": {
    icon: <Radio className="w-4 h-4" />,
    color: "text-green-400",
    bgColor: "bg-green-500/10",
    borderColor: "border-green-500/20"
  },
  "Redshift Agent": {
    icon: <Database className="w-4 h-4" />,
    color: "text-orange-400",
    bgColor: "bg-orange-500/10",
    borderColor: "border-orange-500/20"
  },
  "Super API Agent": {
    icon: <Settings className="w-4 h-4" />,
    color: "text-cyan-400",
    bgColor: "bg-cyan-500/10",
    borderColor: "border-cyan-500/20"
  },
  "JT Agent": {
    icon: <Wrench className="w-4 h-4" />,
    color: "text-amber-400",
    bgColor: "bg-amber-500/10",
    borderColor: "border-amber-500/20"
  },
  "Ocean Events Agent": {
    icon: <Waves className="w-4 h-4" />,
    color: "text-teal-400",
    bgColor: "bg-teal-500/10",
    borderColor: "border-teal-500/20"
  },
  "Ocean Trace Agent": {
    icon: <Ship className="w-4 h-4" />,
    color: "text-indigo-400",
    bgColor: "bg-indigo-500/10",
    borderColor: "border-indigo-500/20"
  },
  "Confluence Agent": {
    icon: <BookOpen className="w-4 h-4" />,
    color: "text-blue-400",
    bgColor: "bg-blue-500/10",
    borderColor: "border-blue-500/20"
  },
  "Slack Agent": {
    icon: <MessageSquare className="w-4 h-4" />,
    color: "text-pink-400",
    bgColor: "bg-pink-500/10",
    borderColor: "border-pink-500/20"
  },
  "JIRA Agent": {
    icon: <Ticket className="w-4 h-4" />,
    color: "text-blue-400",
    bgColor: "bg-blue-500/10",
    borderColor: "border-blue-500/20"
  },
  "Hypothesis Agent": {
    icon: <Lightbulb className="w-4 h-4" />,
    color: "text-yellow-400",
    bgColor: "bg-yellow-500/10",
    borderColor: "border-yellow-500/20"
  },
  "Synthesis Agent": {
    icon: <Brain className="w-4 h-4" />,
    color: "text-violet-400",
    bgColor: "bg-violet-500/10",
    borderColor: "border-violet-500/20"
  },
  "Decision": {
    icon: <GitBranch className="w-4 h-4" />,
    color: "text-rose-400",
    bgColor: "bg-rose-500/10",
    borderColor: "border-rose-500/20"
  },
  "default": {
    icon: <Bot className="w-4 h-4" />,
    color: "text-gray-400",
    bgColor: "bg-gray-500/10",
    borderColor: "border-gray-500/20"
  },
}

function getAgentConfig(agent: string) {
  // Check for partial matches
  for (const [key, config] of Object.entries(agentConfig)) {
    if (agent.toLowerCase().includes(key.toLowerCase().replace(" agent", ""))) {
      return config
    }
  }
  return agentConfig[agent] || agentConfig["default"]
}

function ThinkingIndicator({ agent }: { agent: string }) {
  const config = getAgentConfig(agent)
  return (
    <div className={`flex items-center gap-3 p-4 rounded-lg border ${config.bgColor} ${config.borderColor}`}>
      <div className={`flex-shrink-0 ${config.color}`}>
        {config.icon}
      </div>
      <div className="flex-1">
        <div className={`text-sm font-medium ${config.color}`}>{agent}</div>
        <div className="flex items-center gap-2 mt-1.5">
          <Loader2 className="w-3 h-3 animate-spin text-gray-500" />
          <span className="text-xs text-gray-500">Processing...</span>
        </div>
      </div>
    </div>
  )
}

function JsonViewer({ data, maxHeight = "300px" }: { data: unknown; maxHeight?: string }) {
  const [copied, setCopied] = useState(false)
  const jsonString = JSON.stringify(data, null, 2)

  const copyToClipboard = () => {
    navigator.clipboard.writeText(jsonString)
    setCopied(true)
    setTimeout(() => setCopied(false), 2000)
  }

  return (
    <div className="relative group">
      <button
        onClick={copyToClipboard}
        className="absolute top-2 right-2 p-1.5 rounded bg-gray-800 hover:bg-gray-700 opacity-0 group-hover:opacity-100 transition-opacity"
        title="Copy JSON"
      >
        {copied ? (
          <Check className="w-3 h-3 text-emerald-400" />
        ) : (
          <Copy className="w-3 h-3 text-gray-400" />
        )}
      </button>
      <pre
        className="text-xs text-gray-300 bg-[#0d0d0d] p-3 rounded-lg overflow-auto font-mono border border-[#1a1a1a]"
        style={{ maxHeight }}
      >
        {jsonString}
      </pre>
    </div>
  )
}

function MessageBubble({ message }: { message: StreamMessage }) {
  const config = getAgentConfig(message.agent)
  const [expanded, setExpanded] = useState(false)
  const hasExpandableContent = Boolean(message.queryDetails?.raw_result) || message.type === "query"

  const getTypeIcon = () => {
    switch (message.type) {
      case "query":
        return <Terminal className="w-3 h-3" />
      case "decision":
        return <GitBranch className="w-3 h-3" />
      case "thinking":
        return <Brain className="w-3 h-3" />
      case "tool":
        return <Wrench className="w-3 h-3" />
      case "result":
        return <CheckCircle2 className="w-3 h-3" />
      case "error":
        return <AlertCircle className="w-3 h-3" />
      default:
        return null
    }
  }

  return (
    <div
      className={`flex flex-col rounded-lg border transition-all duration-300 ${config.bgColor} ${config.borderColor} ${
        hasExpandableContent ? "cursor-pointer hover:border-opacity-60" : ""
      }`}
      onClick={() => { if (hasExpandableContent) setExpanded(!expanded) }}
    >
      {/* Header */}
      <div className="flex items-start gap-3 p-4">
        <div className={`flex-shrink-0 mt-0.5 ${config.color}`}>
          {config.icon}
        </div>
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 mb-1.5 flex-wrap">
            <span className={`text-sm font-semibold ${config.color}`}>{message.agent}</span>
            {message.status === "completed" && (
              <CheckCircle2 className="w-3.5 h-3.5 text-emerald-500" />
            )}
            {message.status === "running" && (
              <Loader2 className="w-3.5 h-3.5 text-blue-400 animate-spin" />
            )}
            {message.status === "error" && (
              <AlertCircle className="w-3.5 h-3.5 text-red-500" />
            )}
            {message.type && message.type !== "message" && (
              <Badge variant="outline" className="text-[10px] px-1.5 py-0 h-4 border-gray-700 text-gray-500 gap-1">
                {getTypeIcon()}
                {message.type}
              </Badge>
            )}
            {message.metadata?.type !== undefined && message.metadata?.type !== null && (
              <Badge variant="outline" className="text-[10px] px-1.5 py-0 h-4 border-gray-700 text-gray-500">
                {String(message.metadata.type)}
              </Badge>
            )}
          </div>
          <div className="text-sm text-gray-300 whitespace-pre-wrap break-words leading-relaxed">
            {message.content}
          </div>

          {/* Query metadata inline */}
          {message.queryDetails !== undefined && message.queryDetails !== null && (
            <div className="flex items-center gap-3 mt-2 text-xs text-gray-500">
              {message.queryDetails.duration_ms && (
                <span className="flex items-center gap-1">
                  <Clock className="w-3 h-3" />
                  {message.queryDetails.duration_ms}ms
                </span>
              )}
              {message.queryDetails.result_count !== undefined && (
                <span className="flex items-center gap-1">
                  <Hash className="w-3 h-3" />
                  {message.queryDetails.result_count} results
                </span>
              )}
              {hasExpandableContent && (
                <span className="flex items-center gap-1 text-gray-600">
                  {expanded ? <ChevronDown className="w-3 h-3" /> : <ChevronRight className="w-3 h-3" />}
                  {expanded ? "Hide" : "View"} response
                </span>
              )}
            </div>
          )}

          <div className="text-[10px] text-gray-600 mt-2 font-mono">
            {message.timestamp.toLocaleTimeString()}
          </div>
        </div>
      </div>

      {/* Expanded content */}
      {expanded && message.queryDetails?.raw_result !== undefined && message.queryDetails?.raw_result !== null && (
        <div className="px-4 pb-4 border-t border-[#1a1a1a]">
          <div className="mt-3">
            <div className="flex items-center gap-2 mb-2">
              <Code className="w-3 h-3 text-gray-500" />
              <span className="text-xs text-gray-500 font-medium">Raw Response</span>
            </div>
            <JsonViewer data={message.queryDetails.raw_result} />
          </div>
        </div>
      )}
    </div>
  )
}

export function StreamingChat({ messages, isStreaming, currentAgent }: StreamingChatProps) {
  const scrollRef = useRef<HTMLDivElement>(null)
  const containerRef = useRef<HTMLDivElement>(null)
  const [autoScroll, setAutoScroll] = useState(true)
  const [filter, setFilter] = useState<string>("all")

  useEffect(() => {
    if (autoScroll && scrollRef.current) {
      scrollRef.current.scrollIntoView({ behavior: "smooth" })
    }
  }, [messages, autoScroll, currentAgent])

  const handleScroll = () => {
    if (containerRef.current) {
      const { scrollTop, scrollHeight, clientHeight } = containerRef.current
      const isAtBottom = scrollHeight - scrollTop - clientHeight < 100
      setAutoScroll(isAtBottom)
    }
  }

  const filteredMessages = filter === "all"
    ? messages
    : messages.filter((msg) => {
        if (filter === "queries") return msg.type === "query"
        if (filter === "decisions") return msg.type === "decision"
        if (filter === "errors") return msg.status === "error" || msg.type === "error"
        return true
      })

  const queryCount = messages.filter((m) => m.type === "query").length
  const errorCount = messages.filter((m) => m.status === "error" || m.type === "error").length

  return (
    <Card className="h-[700px] flex flex-col bg-[#0a0a0a] border-[#1a1a1a]">
      <CardHeader className="flex-shrink-0 pb-3 border-b border-[#1a1a1a] bg-[#0d0d0d]">
        <div className="flex items-center justify-between">
          <CardTitle className="text-base flex items-center gap-2 text-gray-200">
            <Activity className="w-5 h-5 text-emerald-500" />
            Agent Activity
          </CardTitle>
          <div className="flex items-center gap-2">
            {isStreaming && (
              <div className="flex items-center gap-1.5 px-2 py-1 rounded-full bg-emerald-500/10 border border-emerald-500/20">
                <span className="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse" />
                <span className="text-xs text-emerald-400 font-medium">Live</span>
              </div>
            )}
            {messages.length > 0 && (
              <span className="text-xs text-gray-600 font-mono">
                {messages.length} events
              </span>
            )}
          </div>
        </div>

        {/* Filter tabs */}
        {messages.length > 0 && (
          <div className="flex items-center gap-1 mt-3">
            <button
              onClick={() => setFilter("all")}
              className={`px-2.5 py-1 text-xs rounded-md transition-colors ${
                filter === "all"
                  ? "bg-gray-800 text-gray-200"
                  : "text-gray-500 hover:text-gray-300 hover:bg-gray-800/50"
              }`}
            >
              All ({messages.length})
            </button>
            <button
              onClick={() => setFilter("queries")}
              className={`px-2.5 py-1 text-xs rounded-md transition-colors flex items-center gap-1 ${
                filter === "queries"
                  ? "bg-blue-500/20 text-blue-400"
                  : "text-gray-500 hover:text-gray-300 hover:bg-gray-800/50"
              }`}
            >
              <Terminal className="w-3 h-3" />
              Queries ({queryCount})
            </button>
            <button
              onClick={() => setFilter("decisions")}
              className={`px-2.5 py-1 text-xs rounded-md transition-colors flex items-center gap-1 ${
                filter === "decisions"
                  ? "bg-rose-500/20 text-rose-400"
                  : "text-gray-500 hover:text-gray-300 hover:bg-gray-800/50"
              }`}
            >
              <GitBranch className="w-3 h-3" />
              Decisions
            </button>
            {errorCount > 0 && (
              <button
                onClick={() => setFilter("errors")}
                className={`px-2.5 py-1 text-xs rounded-md transition-colors flex items-center gap-1 ${
                  filter === "errors"
                    ? "bg-red-500/20 text-red-400"
                    : "text-gray-500 hover:text-gray-300 hover:bg-gray-800/50"
                }`}
              >
                <AlertCircle className="w-3 h-3" />
                Errors ({errorCount})
              </button>
            )}
          </div>
        )}
      </CardHeader>

      <CardContent
        ref={containerRef}
        onScroll={handleScroll}
        className="flex-1 overflow-y-auto p-4 space-y-2 bg-[#0a0a0a]"
      >
        {messages.length === 0 && !isStreaming && (
          <div className="flex items-center justify-center h-full text-gray-600">
            <div className="text-center">
              <Bot className="w-12 h-12 mx-auto mb-3 text-gray-700" />
              <p className="text-sm">Waiting for investigation to start...</p>
              <p className="text-xs text-gray-700 mt-1">Queries and logs will appear here</p>
            </div>
          </div>
        )}

        {filteredMessages.map((msg) => (
          <MessageBubble key={msg.id} message={msg} />
        ))}

        {isStreaming && currentAgent && (
          <ThinkingIndicator agent={currentAgent} />
        )}

        <div ref={scrollRef} />
      </CardContent>

      {!autoScroll && messages.length > 0 && (
        <button
          onClick={() => {
            setAutoScroll(true)
            scrollRef.current?.scrollIntoView({ behavior: "smooth" })
          }}
          className="absolute bottom-6 right-6 flex items-center gap-1.5 bg-[#1a1a1a] text-gray-400 px-3 py-1.5 rounded-full text-xs border border-[#2a2a2a] hover:bg-[#2a2a2a] hover:text-gray-300 transition-colors shadow-lg"
        >
          <ArrowDown className="w-3 h-3" />
          Scroll to bottom
        </button>
      )}
    </Card>
  )
}
