"use client"

import { useState, useCallback, useRef } from "react"

export interface StreamMessage {
  id: string
  agent: string
  content: string
  type: "message" | "thinking" | "tool" | "result" | "error" | "decision" | "query"
  timestamp: Date
  status?: "running" | "completed" | "error"
  metadata?: Record<string, unknown>
  // Query details for expandable cards
  queryDetails?: {
    source: string
    query: string
    result_count?: number
    duration_ms?: number
    raw_result?: unknown
    error?: string
  }
}

export interface ExecutedQuery {
  id: string
  source: string
  query: string
  result_count?: number
  duration_ms?: number
  raw_result?: unknown
  error?: string
  executed_at: Date
}

export interface TimelineEvent {
  id: string
  agent: string
  action: string
  timestamp: Date
  duration_ms?: number
  result_summary?: string
  status: string
}

export interface Hypothesis {
  id: string
  description: string
  category: string
  confidence: number
  evidence_for: Array<{ source: string; finding: string; weight: number }>
  evidence_against: Array<{ source: string; finding: string; weight: number }>
}

export interface DataSourceResult {
  source: string
  exists?: boolean
  error?: string
  skipped?: boolean
  timeout?: boolean
  data: Record<string, unknown>
  receivedAt: Date
}

export interface HeartbeatInfo {
  timestamp: Date
  heartbeat_count: number
  phase: string
  progress_percent: number
  current_activity: string
  agents_running: string[]
  data_sources_queried: number
  data_sources_total: number
}

export interface AgentDiscussion {
  agent: string
  message: string
  type: "observation" | "proposal" | "agreement" | "disagreement" | "question" | "decision"
  timestamp: string
}

export interface CollaborativeDecision {
  agent: string
  action: string
  target: string
  reasoning: string
  rationale: string
  votes: Record<string, boolean>
}

export interface InvestigationState {
  investigation_id: string
  status: "idle" | "running" | "complete" | "error"
  mode: "standard" | "collaborative"
  streamMessages: StreamMessage[]
  executedQueries: ExecutedQuery[]
  timelineEvents: TimelineEvent[]
  hypotheses: Hypothesis[]
  dataSources: Record<string, DataSourceResult>
  // For AgentDiscussionPanel - human-level conversation
  discussions: AgentDiscussion[]
  decisions: CollaborativeDecision[]
  rootCause: {
    category: string
    description: string
    confidence: number
    recommended_actions?: Array<{
      description: string
      priority: string
      category: string
      details?: string
    }>
  } | null
  needsHuman: boolean
  humanQuestion?: string
  error?: string
  currentAgent?: string
  iteration: number
  maxIterations: number
  phase: string
  // Heartbeat info for progress visualization
  heartbeat: HeartbeatInfo | null
  lastHeartbeat: Date | null
}

export function useInvestigation() {
  const [state, setState] = useState<InvestigationState>({
    investigation_id: "",
    status: "idle",
    mode: "standard",
    streamMessages: [],
    executedQueries: [],
    timelineEvents: [],
    hypotheses: [],
    dataSources: {},
    discussions: [],
    decisions: [],
    rootCause: null,
    needsHuman: false,
    iteration: 0,
    maxIterations: 10,
    phase: "gathering",
    heartbeat: null,
    lastHeartbeat: null,
  })

  const messageIdRef = useRef(0)
  const queryIdRef = useRef(0)
  const timelineIdRef = useRef(0)

  const addMessage = useCallback((
    agent: string,
    content: string,
    type: StreamMessage["type"] = "message",
    status: StreamMessage["status"] = "completed",
    metadata?: Record<string, unknown>,
    queryDetails?: StreamMessage["queryDetails"]
  ) => {
    const newMessage: StreamMessage = {
      id: `msg-${++messageIdRef.current}`,
      agent,
      content,
      type,
      timestamp: new Date(),
      status,
      metadata,
      queryDetails,
    }
    setState((prev) => ({
      ...prev,
      streamMessages: [...prev.streamMessages, newMessage],
      currentAgent: status === "running" ? agent : prev.currentAgent,
    }))
  }, [])

  const addQuery = useCallback((query: Omit<ExecutedQuery, "id">) => {
    const newQuery: ExecutedQuery = {
      id: `query-${++queryIdRef.current}`,
      ...query,
    }
    setState((prev) => ({
      ...prev,
      executedQueries: [...prev.executedQueries, newQuery],
    }))
    return newQuery
  }, [])

  const addTimelineEvent = useCallback((event: Omit<TimelineEvent, "id">) => {
    const newEvent: TimelineEvent = {
      id: `timeline-${++timelineIdRef.current}`,
      ...event,
    }
    setState((prev) => ({
      ...prev,
      timelineEvents: [...prev.timelineEvents, newEvent],
    }))
  }, [])

  const startInvestigation = useCallback(async (issueText: string, collaborative: boolean = false) => {
    // Reset state
    messageIdRef.current = 0
    queryIdRef.current = 0
    timelineIdRef.current = 0
    setState({
      investigation_id: "",
      status: "running",
      mode: collaborative ? "collaborative" : "standard",
      streamMessages: [],
      executedQueries: [],
      timelineEvents: [],
      hypotheses: [],
      dataSources: {},
      discussions: [],
      decisions: [],
      rootCause: null,
      needsHuman: false,
      currentAgent: "System",
      iteration: 0,
      maxIterations: 10,
      phase: "gathering",
      heartbeat: null,
      lastHeartbeat: null,
    })

    // Add initial message
    addMessage("System", `Starting ${collaborative ? "collaborative " : ""}investigation for: "${issueText}"`, "message", "completed")

    const endpoint = collaborative
      ? "/api/rca/investigate/collaborative"
      : "/api/rca/investigate/stream"

    try {
      const response = await fetch(endpoint, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ issue_text: issueText }),
      })

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`)
      }

      const reader = response.body?.getReader()
      const decoder = new TextDecoder()

      if (!reader) {
        throw new Error("No response body")
      }

      let buffer = ""

      while (true) {
        const { done, value } = await reader.read()

        if (done) {
          break
        }

        // Decode the chunk and add to buffer
        buffer += decoder.decode(value, { stream: true })

        // Process complete SSE messages (separated by double newlines)
        let eventEnd: number
        while ((eventEnd = buffer.indexOf("\n\n")) !== -1) {
          const eventBlock = buffer.slice(0, eventEnd)
          buffer = buffer.slice(eventEnd + 2)

          if (!eventBlock.trim()) continue

          // Parse the event block
          const lines = eventBlock.split("\n")
          let eventType = ""
          let eventData = ""

          for (const line of lines) {
            if (line.startsWith("event: ")) {
              eventType = line.slice(7).trim()
            } else if (line.startsWith("data: ")) {
              eventData = line.slice(6)
            }
          }

          if (!eventType || !eventData) continue

          try {
            const data = JSON.parse(eventData)
            processEvent(eventType, data)
          } catch (parseError) {
            console.error("Failed to parse SSE data:", parseError, eventData)
          }
        }
      }

      // Mark as complete if not already
      setState((prev) => {
        if (prev.status === "running") {
          return { ...prev, status: "complete", currentAgent: undefined }
        }
        return prev
      })

    } catch (error) {
      console.error("Investigation error:", error)
      const errorMessage = error instanceof Error ? error.message : "Unknown error"
      addMessage("System", `Error: ${errorMessage}`, "error", "error")
      setState((prev) => ({
        ...prev,
        status: "error",
        error: errorMessage,
        currentAgent: undefined,
      }))
    }

    function processEvent(eventType: string, data: Record<string, unknown>) {
      switch (eventType) {
        case "started":
          setState((prev) => ({
            ...prev,
            investigation_id: data.investigation_id as string,
          }))
          addMessage("System", `Investigation started (ID: ${(data.investigation_id as string).slice(0, 8)}...)`, "message", "completed")
          break

        case "heartbeat": {
          // Update heartbeat state for progress visualization
          const heartbeatInfo: HeartbeatInfo = {
            timestamp: new Date(data.timestamp as string || Date.now()),
            heartbeat_count: data.heartbeat_count as number || 0,
            phase: data.phase as string || "processing",
            progress_percent: data.progress_percent as number || 0,
            current_activity: data.current_activity as string || "Processing...",
            agents_running: data.agents_running as string[] || [],
            data_sources_queried: data.data_sources_queried as number || 0,
            data_sources_total: data.data_sources_total as number || 9,
          }
          setState((prev) => ({
            ...prev,
            heartbeat: heartbeatInfo,
            lastHeartbeat: new Date(),
            phase: heartbeatInfo.phase,
          }))
          // Don't add a message for every heartbeat - it would flood the chat
          // Only log if in debug mode or if agents_running changed
          break
        }

        case "iteration":
          setState((prev) => ({
            ...prev,
            iteration: data.count as number,
            maxIterations: data.max as number,
            phase: data.phase as string,
          }))
          addMessage("System", `Iteration ${data.count}/${data.max} - Phase: ${data.phase}`, "thinking", "completed", { type: "iteration" })
          break

        case "agent_message": {
          const agent = data.agent as string
          const message = data.message as string
          const status = data.status as string
          const metadata = data.metadata as Record<string, unknown> | undefined
          addMessage(agent, message, "message", status === "completed" ? "completed" : "running", metadata)
          break
        }

        case "agent_discussion": {
          const agent = data.agent as string
          const message = data.message as string
          const rawType = data.type as string
          const timestamp = data.timestamp as string || new Date().toISOString()

          // Map backend type to valid discussion type
          const validTypes = ["observation", "proposal", "agreement", "disagreement", "question", "decision"] as const
          const discussionType = validTypes.includes(rawType as any) ? rawType as AgentDiscussion["type"] : "observation"

          // Add to discussions array for AgentDiscussionPanel
          setState((prev) => ({
            ...prev,
            discussions: [...prev.discussions, {
              agent,
              message,
              type: discussionType,
              timestamp,
            }],
          }))

          // Also add as stream message for StreamingChat
          addMessage(agent, message, "thinking", "completed", { type: discussionType })
          break
        }

        case "decision": {
          const action = data.action as string
          const target = data.target as string
          const reasoning = data.reasoning as string
          const agent = data.agent as string
          const rationale = data.rationale as string | undefined
          const votes = data.votes as Record<string, boolean> | undefined

          // Add to decisions array for AgentDiscussionPanel
          setState((prev) => ({
            ...prev,
            decisions: [...prev.decisions, {
              agent,
              action,
              target,
              reasoning,
              rationale: rationale || "",
              votes: votes || {},
            }],
          }))

          // Also add as stream message for StreamingChat
          addMessage("Decision", `${agent} → ${action} on ${target}\nReason: ${reasoning}`, "decision", "completed", {
            type: "decision",
            votes,
            rationale
          })
          break
        }

        case "query_executed": {
          const query = addQuery({
            source: data.source as string,
            query: data.query as string,
            result_count: data.result_count as number | undefined,
            duration_ms: data.duration_ms as number | undefined,
            raw_result: data.raw_result,
            error: data.error as string | undefined,
            executed_at: new Date(data.executed_at as string || Date.now()),
          })

          // Also add as a message with query details for expandable view
          const sourceName = data.source as string
          const queryStr = data.query as string
          const duration = data.duration_ms ? `${data.duration_ms}ms` : ""
          const resultCount = data.result_count !== undefined ? `${data.result_count} results` : ""
          const statusText = data.error ? `Error: ${data.error}` : [resultCount, duration].filter(Boolean).join(" | ")

          addMessage(
            `${sourceName} Agent`,
            `Query: ${queryStr}\n${statusText}`,
            "query",
            data.error ? "error" : "completed",
            { type: "query" },
            {
              source: data.source as string,
              query: data.query as string,
              result_count: data.result_count as number | undefined,
              duration_ms: data.duration_ms as number | undefined,
              raw_result: data.raw_result,
              error: data.error as string | undefined,
            }
          )
          break
        }

        case "timeline_event": {
          addTimelineEvent({
            agent: data.agent as string,
            action: data.action as string,
            timestamp: new Date(data.timestamp as string || Date.now()),
            duration_ms: data.duration_ms as number | undefined,
            result_summary: data.result_summary as string | undefined,
            status: data.status as string,
          })
          break
        }

        case "hypothesis_update":
          setState((prev) => ({
            ...prev,
            hypotheses: data as unknown as Hypothesis[],
          }))
          if (Array.isArray(data) && data.length > 0) {
            const topHyp = data[0] as Hypothesis
            addMessage("Hypothesis Agent", `Top hypothesis: ${topHyp.description} (${(topHyp.confidence * 100).toFixed(0)}% confidence)`, "result", "completed")
          }
          break

        case "root_cause":
          setState((prev) => ({
            ...prev,
            rootCause: data as InvestigationState["rootCause"],
          }))
          addMessage("Synthesis Agent", `Root Cause Found: ${(data as { description?: string }).description || "Unknown"}`, "result", "completed", { type: "root_cause" })
          break

        case "needs_human":
          setState((prev) => ({
            ...prev,
            needsHuman: true,
            humanQuestion: data.question as string,
          }))
          addMessage("System", `Human input needed: ${data.question as string}`, "message", "completed", { type: "hitl" })
          break

        // Data source events - store them for the data panel
        case "tracking_data":
        case "redshift_data":
        case "callbacks_data":
        case "super_api_data":
        case "jt_data":
        case "ocean_events_data":
        case "ocean_trace_data":
        case "confluence_data":
        case "slack_data":
        case "jira_data": {
          const sourceName = eventType.replace("_data", "").replace(/_/g, " ")
          setState((prev) => ({
            ...prev,
            dataSources: {
              ...prev.dataSources,
              [eventType]: {
                source: sourceName,
                exists: (data as { exists?: boolean }).exists,
                error: (data as { error?: string }).error,
                skipped: (data as { skipped?: boolean }).skipped,
                timeout: (data as { timeout?: boolean }).timeout,
                data: data as Record<string, unknown>,
                receivedAt: new Date(),
              },
            },
          }))

          // Add a message about the data received
          const isError = (data as { error?: string }).error || (data as { timeout?: boolean }).timeout
          const isSkipped = (data as { skipped?: boolean }).skipped
          if (!isSkipped) {
            if (isError) {
              addMessage(`${sourceName} Agent`, `Error: ${(data as { error?: string }).error || "Timeout"}`, "tool", "error")
            } else {
              const exists = (data as { exists?: boolean }).exists
              if (exists !== undefined) {
                addMessage(`${sourceName} Agent`, exists ? "Data retrieved successfully" : "No data found", "tool", "completed")
              } else {
                addMessage(`${sourceName} Agent`, "Data received", "tool", "completed")
              }
            }
          }
          break
        }

        case "complete":
          setState((prev) => ({
            ...prev,
            status: "complete",
            currentAgent: undefined,
          }))
          const stats = data as { iterations?: number; total_queries?: number; total_messages?: number }
          addMessage("System", `Investigation completed | ${stats.iterations || 0} iterations | ${stats.total_queries || 0} queries`, "message", "completed")
          break

        case "error":
          setState((prev) => ({
            ...prev,
            status: "error",
            error: data.error as string,
          }))
          addMessage("System", `Error: ${data.error as string}`, "error", "error")
          break

        default:
          // Handle any other data events
          if (eventType.endsWith("_data")) {
            const sourceName = eventType.replace("_data", "").replace(/_/g, " ")
            addMessage(sourceName, `Data received from ${sourceName}`, "tool", "completed")
          }
      }
    }
  }, [addMessage, addQuery, addTimelineEvent])

  return { state, startInvestigation }
}
