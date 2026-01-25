"use client"

import { useState, useMemo } from "react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import {
  Terminal,
  Clock,
  Hash,
  ChevronDown,
  ChevronRight,
  Copy,
  Check,
  Search,
  Filter,
  X,
  Database,
  Radio,
  Settings,
  Wrench,
  Waves,
  Ship,
  BookOpen,
  MessageSquare,
  Ticket,
  AlertCircle,
  CheckCircle2,
  Code,
  FileJson,
} from "lucide-react"

interface ExecutedQuery {
  id: string
  source: string
  query: string
  result_count?: number
  duration_ms?: number
  raw_result?: unknown
  error?: string
  executed_at: Date
}

interface LogsPanelProps {
  queries: ExecutedQuery[]
  isOpen: boolean
  onClose: () => void
}

const sourceIcons: Record<string, React.ReactNode> = {
  "tracking": <Radio className="w-4 h-4" />,
  "redshift": <Database className="w-4 h-4" />,
  "super": <Settings className="w-4 h-4" />,
  "jt": <Wrench className="w-4 h-4" />,
  "ocean": <Waves className="w-4 h-4" />,
  "confluence": <BookOpen className="w-4 h-4" />,
  "slack": <MessageSquare className="w-4 h-4" />,
  "jira": <Ticket className="w-4 h-4" />,
}

const sourceColors: Record<string, string> = {
  "tracking": "text-green-400 bg-green-500/10 border-green-500/20",
  "redshift": "text-orange-400 bg-orange-500/10 border-orange-500/20",
  "super": "text-cyan-400 bg-cyan-500/10 border-cyan-500/20",
  "jt": "text-amber-400 bg-amber-500/10 border-amber-500/20",
  "ocean": "text-teal-400 bg-teal-500/10 border-teal-500/20",
  "confluence": "text-blue-400 bg-blue-500/10 border-blue-500/20",
  "slack": "text-pink-400 bg-pink-500/10 border-pink-500/20",
  "jira": "text-blue-400 bg-blue-500/10 border-blue-500/20",
}

function getSourceIcon(source: string) {
  const key = source.toLowerCase()
  for (const [k, icon] of Object.entries(sourceIcons)) {
    if (key.includes(k)) return icon
  }
  return <Terminal className="w-4 h-4" />
}

function getSourceColor(source: string) {
  const key = source.toLowerCase()
  for (const [k, color] of Object.entries(sourceColors)) {
    if (key.includes(k)) return color
  }
  return "text-gray-400 bg-gray-500/10 border-gray-500/20"
}

function JsonViewer({ data, maxHeight = "400px" }: { data: unknown; maxHeight?: string }) {
  const [copied, setCopied] = useState(false)
  const jsonString = JSON.stringify(data, null, 2)

  const copyToClipboard = (e: React.MouseEvent) => {
    e.stopPropagation()
    navigator.clipboard.writeText(jsonString)
    setCopied(true)
    setTimeout(() => setCopied(false), 2000)
  }

  return (
    <div className="relative group">
      <button
        onClick={copyToClipboard}
        className="absolute top-2 right-2 p-1.5 rounded bg-gray-800 hover:bg-gray-700 opacity-0 group-hover:opacity-100 transition-opacity z-10"
        title="Copy JSON"
      >
        {copied ? (
          <Check className="w-3 h-3 text-emerald-400" />
        ) : (
          <Copy className="w-3 h-3 text-gray-400" />
        )}
      </button>
      <pre
        className="text-xs text-gray-300 bg-[#050505] p-3 rounded-lg overflow-auto font-mono border border-[#1a1a1a]"
        style={{ maxHeight }}
      >
        {jsonString}
      </pre>
    </div>
  )
}

function QueryCard({ query, index }: { query: ExecutedQuery; index: number }) {
  const [expanded, setExpanded] = useState(false)
  const colorClass = getSourceColor(query.source)

  return (
    <div
      className={`rounded-lg border transition-all ${colorClass} ${
        expanded ? "ring-1 ring-gray-700" : ""
      }`}
    >
      <div
        className="p-4 cursor-pointer"
        onClick={() => setExpanded(!expanded)}
      >
        <div className="flex items-start gap-3">
          <div className="flex-shrink-0 mt-0.5">
            {getSourceIcon(query.source)}
          </div>
          <div className="flex-1 min-w-0">
            <div className="flex items-center gap-2 mb-1">
              <span className="text-sm font-semibold">{query.source}</span>
              <span className="text-xs text-gray-600">#{index + 1}</span>
              {query.error ? (
                <AlertCircle className="w-3.5 h-3.5 text-red-500" />
              ) : (
                <CheckCircle2 className="w-3.5 h-3.5 text-emerald-500" />
              )}
            </div>

            <div className="text-xs text-gray-400 font-mono break-all mb-2">
              {query.query}
            </div>

            <div className="flex items-center gap-4 text-xs text-gray-500">
              {query.duration_ms !== undefined && (
                <span className="flex items-center gap-1">
                  <Clock className="w-3 h-3" />
                  {query.duration_ms}ms
                </span>
              )}
              {query.result_count !== undefined && (
                <span className="flex items-center gap-1">
                  <Hash className="w-3 h-3" />
                  {query.result_count} results
                </span>
              )}
              <span className="flex items-center gap-1 text-gray-600">
                {query.executed_at.toLocaleTimeString()}
              </span>
              {query.raw_result !== null && query.raw_result !== undefined && (
                <span className="flex items-center gap-1 text-gray-600 ml-auto">
                  {expanded ? <ChevronDown className="w-3 h-3" /> : <ChevronRight className="w-3 h-3" />}
                  {expanded ? "Hide" : "View"} response
                </span>
              )}
            </div>

            {query.error && (
              <div className="mt-2 p-2 rounded bg-red-500/10 border border-red-500/20 text-xs text-red-400">
                {query.error}
              </div>
            )}
          </div>
        </div>
      </div>

      {expanded && query.raw_result !== null && query.raw_result !== undefined && (
        <div className="px-4 pb-4 border-t border-[#1a1a1a]">
          <div className="mt-3">
            <div className="flex items-center gap-2 mb-2">
              <FileJson className="w-3 h-3 text-gray-500" />
              <span className="text-xs text-gray-500 font-medium">Response Data</span>
            </div>
            <JsonViewer data={query.raw_result} />
          </div>
        </div>
      )}
    </div>
  )
}

export function LogsPanel({ queries, isOpen, onClose }: LogsPanelProps) {
  const [searchTerm, setSearchTerm] = useState("")
  const [sourceFilter, setSourceFilter] = useState<string>("all")
  const [statusFilter, setStatusFilter] = useState<"all" | "success" | "error">("all")

  const sources = useMemo(() => {
    const uniqueSources = new Set(queries.map((q) => q.source))
    return Array.from(uniqueSources)
  }, [queries])

  const filteredQueries = useMemo(() => {
    return queries.filter((q) => {
      // Search filter
      if (searchTerm) {
        const term = searchTerm.toLowerCase()
        const matchesQuery = q.query.toLowerCase().includes(term)
        const matchesSource = q.source.toLowerCase().includes(term)
        const matchesResult = q.raw_result
          ? JSON.stringify(q.raw_result).toLowerCase().includes(term)
          : false
        if (!matchesQuery && !matchesSource && !matchesResult) return false
      }

      // Source filter
      if (sourceFilter !== "all" && q.source !== sourceFilter) return false

      // Status filter
      if (statusFilter === "success" && q.error) return false
      if (statusFilter === "error" && !q.error) return false

      return true
    })
  }, [queries, searchTerm, sourceFilter, statusFilter])

  const stats = useMemo(() => ({
    total: queries.length,
    success: queries.filter((q) => !q.error).length,
    error: queries.filter((q) => q.error).length,
    avgDuration: queries.length > 0
      ? Math.round(queries.reduce((acc, q) => acc + (q.duration_ms || 0), 0) / queries.length)
      : 0,
  }), [queries])

  if (!isOpen) return null

  return (
    <div className="fixed inset-0 z-50 bg-black/80 backdrop-blur-sm">
      <div className="absolute inset-4 lg:inset-8 bg-[#0a0a0a] rounded-xl border border-[#1a1a1a] flex flex-col overflow-hidden">
        {/* Header */}
        <div className="flex-shrink-0 p-4 border-b border-[#1a1a1a] bg-[#0d0d0d]">
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center gap-3">
              <Terminal className="w-5 h-5 text-emerald-500" />
              <h2 className="text-lg font-semibold text-gray-200">Queries & Logs</h2>
              <Badge variant="outline" className="border-gray-700 text-gray-500">
                {queries.length} total
              </Badge>
            </div>
            <button
              onClick={onClose}
              className="p-2 rounded-lg hover:bg-gray-800 text-gray-400 hover:text-gray-200 transition-colors"
            >
              <X className="w-5 h-5" />
            </button>
          </div>

          {/* Stats */}
          <div className="flex items-center gap-4 mb-4">
            <div className="flex items-center gap-2 text-sm">
              <CheckCircle2 className="w-4 h-4 text-emerald-500" />
              <span className="text-gray-400">{stats.success} success</span>
            </div>
            <div className="flex items-center gap-2 text-sm">
              <AlertCircle className="w-4 h-4 text-red-500" />
              <span className="text-gray-400">{stats.error} errors</span>
            </div>
            <div className="flex items-center gap-2 text-sm">
              <Clock className="w-4 h-4 text-blue-400" />
              <span className="text-gray-400">{stats.avgDuration}ms avg</span>
            </div>
          </div>

          {/* Filters */}
          <div className="flex items-center gap-3 flex-wrap">
            {/* Search */}
            <div className="relative flex-1 min-w-[200px] max-w-md">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-500" />
              <input
                type="text"
                placeholder="Search queries, sources, or results..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="w-full pl-9 pr-4 py-2 bg-[#050505] border border-[#1a1a1a] rounded-lg text-sm text-gray-300 placeholder:text-gray-600 focus:outline-none focus:border-emerald-500/50"
              />
            </div>

            {/* Source filter */}
            <div className="flex items-center gap-2">
              <Filter className="w-4 h-4 text-gray-500" />
              <select
                value={sourceFilter}
                onChange={(e) => setSourceFilter(e.target.value)}
                className="bg-[#050505] border border-[#1a1a1a] rounded-lg text-sm text-gray-300 px-3 py-2 focus:outline-none focus:border-emerald-500/50"
              >
                <option value="all">All Sources</option>
                {sources.map((source) => (
                  <option key={source} value={source}>
                    {source}
                  </option>
                ))}
              </select>
            </div>

            {/* Status filter */}
            <div className="flex items-center gap-1">
              <button
                onClick={() => setStatusFilter("all")}
                className={`px-3 py-1.5 text-xs rounded-md transition-colors ${
                  statusFilter === "all"
                    ? "bg-gray-800 text-gray-200"
                    : "text-gray-500 hover:text-gray-300 hover:bg-gray-800/50"
                }`}
              >
                All
              </button>
              <button
                onClick={() => setStatusFilter("success")}
                className={`px-3 py-1.5 text-xs rounded-md transition-colors flex items-center gap-1 ${
                  statusFilter === "success"
                    ? "bg-emerald-500/20 text-emerald-400"
                    : "text-gray-500 hover:text-gray-300 hover:bg-gray-800/50"
                }`}
              >
                <CheckCircle2 className="w-3 h-3" />
                Success
              </button>
              <button
                onClick={() => setStatusFilter("error")}
                className={`px-3 py-1.5 text-xs rounded-md transition-colors flex items-center gap-1 ${
                  statusFilter === "error"
                    ? "bg-red-500/20 text-red-400"
                    : "text-gray-500 hover:text-gray-300 hover:bg-gray-800/50"
                }`}
              >
                <AlertCircle className="w-3 h-3" />
                Errors
              </button>
            </div>
          </div>
        </div>

        {/* Query list */}
        <div className="flex-1 overflow-y-auto p-4">
          {filteredQueries.length === 0 ? (
            <div className="flex items-center justify-center h-full text-gray-600">
              <div className="text-center">
                <Terminal className="w-12 h-12 mx-auto mb-3 text-gray-700" />
                <p className="text-sm">No queries match your filters</p>
              </div>
            </div>
          ) : (
            <div className="space-y-3">
              {filteredQueries.map((query, index) => (
                <QueryCard key={query.id} query={query} index={index} />
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
