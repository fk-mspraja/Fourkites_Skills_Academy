export type AgentStatus = "pending" | "running" | "completed" | "failed"

export type RootCauseCategory =
  | "load_creation_failure"
  | "configuration_issue"
  | "jt_issue"
  | "carrier_issue"
  | "network_relationship"
  | "callback_failure"
  | "data_quality"
  | "system_error"
  | "unknown"

export interface AgentMessage {
  agent: string
  message: string
  timestamp: string
  status?: AgentStatus
  metadata?: Record<string, any>
}

export interface TimelineEvent {
  timestamp: string
  agent: string
  action: string
  duration_ms?: number
  result_summary?: string
  status: AgentStatus
}

export interface Evidence {
  source: string
  finding: string
  weight: number
}

export interface Hypothesis {
  id: string
  description: string
  category: RootCauseCategory
  confidence: number
  evidence_for: Evidence[]
  evidence_against: Evidence[]
}

export interface Action {
  description: string
  priority: "high" | "medium" | "low"
  category: string
  details?: string
}

export interface RootCause {
  category: RootCauseCategory
  description: string
  confidence: number
  recommended_actions: Action[]
}

export interface Query {
  source: string
  query: string
  result_count?: number
  duration_ms?: number
  error?: string
}

export interface CallbackData {
  uuid: string
  config_id: number
  tracking_id: string
  callback_event_timestamp: string
  http_response_code?: string
  http_response_timestamp?: string
  message_type: string
  transformed_data_exists?: boolean
  error_message?: string
  destination_url?: string
}

export interface CallbacksDataSource {
  total_callbacks: number
  successful: number
  failed: number
  callbacks: CallbackData[]
  summary: {
    total: number
    success: number
    failed: number
  }
}

export interface TrackingDataSource {
  exists: boolean
  tracking_id?: string
  loadNumber?: string
  status?: string
  mode?: string
  carrier?: string
  shipper?: string
  shipperCompanyId?: string
  stops?: any[]
  raw?: any
}

export interface ValidationAttempt {
  load_id: string
  company_id: string
  company_name: string
  load_number: string
  status: string
  error?: string
  processed_at: string
  carrier_id: string
  carrier_name: string
  file_name: string
  stop_count: number
}

export interface RedshiftDataSource {
  validation_attempts: ValidationAttempt[]
  total_attempts: number
  failed_attempts: number
  latest_error?: string
  latest_file?: string
  latest_status?: string
}

export interface OceanEvent {
  timestamp: string
  correlation_id: string
  body: string
}

export interface OceanEventsDataSource {
  total_events: number
  events: OceanEvent[]
  date_range: {
    start: string
    end: string
  }
}

export interface OceanUpdate {
  status: string
  event_code: string
  location: string
  event_time: string
  created_at: string
  source: string
}

export interface OceanTraceDataSource {
  subscription_id: string
  total_updates: number
  successful: number
  rejected: number
  updates: OceanUpdate[]
}

export interface AgentDiscussion {
  agent: string
  message: string
  type: "observation" | "proposal" | "agreement" | "disagreement" | "question" | "decision"
  timestamp: string
}

export interface CollaborativeDecision {
  action: string
  target: string
  agent: string
  reasoning: string
  rationale: string
  votes: Record<string, boolean>
}

export interface InvestigationState {
  investigation_id: string
  status: "idle" | "running" | "complete" | "error"
  mode?: "standard" | "collaborative"
  messages: AgentMessage[]
  discussions: AgentDiscussion[]
  decisions: CollaborativeDecision[]
  timeline: TimelineEvent[]
  hypotheses: Hypothesis[]
  queries: Query[]
  rootCause: RootCause | null
  needsHuman: boolean
  humanQuestion?: string
  error?: string
  iterations?: number
  // Data source results
  callbacksData?: CallbacksDataSource
  trackingData?: TrackingDataSource
  redshiftData?: RedshiftDataSource
  oceanEventsData?: OceanEventsDataSource
  oceanTraceData?: OceanTraceDataSource
  confluenceData?: ConfluenceDataSource
  slackData?: SlackDataSource
  jiraData?: JiraDataSource
}

export interface ConfluenceDataSource {
  found: boolean
  count: number
  pages?: Array<{
    title: string
    url: string
    excerpt?: string
    space?: string
  }>
  search_keywords?: string[]
  error?: string
  skipped?: boolean
}

export interface SlackDataSource {
  found: boolean
  count: number
  threads?: Array<{
    text: string
    user?: string
    channel?: string
    timestamp?: string
    permalink?: string
    reactions?: Array<{ name: string; count: number }>
  }>
  search_query?: string
  error?: string
  skipped?: boolean
}

export interface JiraDataSource {
  found: boolean
  count: number
  issues?: Array<{
    key: string
    summary: string
    status: string
    priority?: string
    assignee?: string
    created?: string
    url?: string
    search_type?: string
  }>
  analysis?: {
    status_breakdown?: Record<string, number>
    priority_breakdown?: Record<string, number>
    has_open_issues?: boolean
    total_found?: number
  }
  error?: string
  skipped?: boolean
}
