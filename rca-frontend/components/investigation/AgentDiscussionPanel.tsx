"use client"

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import type { AgentDiscussion, CollaborativeDecision } from "@/lib/types"

interface AgentDiscussionPanelProps {
  discussions: AgentDiscussion[]
  decisions: CollaborativeDecision[]
  iterations?: number
}

const agentColors: Record<string, string> = {
  "Coordinator": "bg-purple-100 text-purple-800 border-purple-300",
  "Hypothesis Agent": "bg-blue-100 text-blue-800 border-blue-300",
  "Tracking API Agent": "bg-green-100 text-green-800 border-green-300",
  "Redshift Agent": "bg-orange-100 text-orange-800 border-orange-300",
  "Callbacks Agent": "bg-yellow-100 text-yellow-800 border-yellow-300",
  "Ocean Events Agent": "bg-cyan-100 text-cyan-800 border-cyan-300",
  "Ocean Trace Agent": "bg-teal-100 text-teal-800 border-teal-300",
  "JT Agent": "bg-pink-100 text-pink-800 border-pink-300",
  "Super API Agent": "bg-indigo-100 text-indigo-800 border-indigo-300",
  "Synthesis Agent": "bg-red-100 text-red-800 border-red-300",
}

const messageTypeIcons: Record<string, string> = {
  observation: "🔍",
  proposal: "💡",
  agreement: "✓",
  disagreement: "✗",
  question: "?",
  decision: "⚡",
}

const messageTypeColors: Record<string, string> = {
  observation: "border-l-gray-400",
  proposal: "border-l-blue-400",
  agreement: "border-l-green-400",
  disagreement: "border-l-red-400",
  question: "border-l-yellow-400",
  decision: "border-l-purple-400",
}

export function AgentDiscussionPanel({ discussions, decisions, iterations }: AgentDiscussionPanelProps) {
  // Interleave discussions and decisions by timestamp
  const timeline = [
    ...discussions.map(d => ({ type: 'discussion' as const, data: d, timestamp: d.timestamp })),
    ...decisions.map(d => ({ type: 'decision' as const, data: d, timestamp: new Date().toISOString() })),
  ].sort((a, b) => new Date(a.timestamp).getTime() - new Date(b.timestamp).getTime())

  if (discussions.length === 0 && decisions.length === 0) {
    return (
      <Card className="h-full">
        <CardHeader className="pb-3">
          <CardTitle className="text-lg flex items-center gap-2">
            Agent Collaboration
            {iterations !== undefined && (
              <Badge variant="outline" className="ml-2">
                Iteration {iterations}
              </Badge>
            )}
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="text-center text-muted-foreground py-8">
            <p>No collaborative discussion yet.</p>
            <p className="text-sm mt-2">Start an investigation in collaborative mode to see agents discuss.</p>
          </div>
        </CardContent>
      </Card>
    )
  }

  return (
    <Card className="h-full flex flex-col">
      <CardHeader className="pb-3 flex-shrink-0">
        <CardTitle className="text-lg flex items-center gap-2">
          Agent Collaboration
          {iterations !== undefined && (
            <Badge variant="outline" className="ml-2">
              Iteration {iterations}
            </Badge>
          )}
          <Badge variant="secondary" className="ml-auto">
            {discussions.length} messages
          </Badge>
        </CardTitle>
      </CardHeader>
      <CardContent className="flex-1 overflow-hidden p-0">
        <div className="h-[400px] overflow-y-auto px-4">
          <div className="space-y-3 py-2">
            {timeline.map((item, idx) => {
              if (item.type === 'discussion') {
                const discussion = item.data as AgentDiscussion
                const agentColor = agentColors[discussion.agent] || "bg-gray-100 text-gray-800 border-gray-300"
                const typeColor = messageTypeColors[discussion.type] || "border-l-gray-400"
                const typeIcon = messageTypeIcons[discussion.type] || ""

                return (
                  <div
                    key={`discussion-${idx}`}
                    className={`border-l-4 ${typeColor} pl-3 py-2 bg-white rounded-r shadow-sm`}
                  >
                    <div className="flex items-center gap-2 mb-1">
                      <Badge variant="outline" className={`text-xs ${agentColor}`}>
                        {discussion.agent}
                      </Badge>
                      <span className="text-xs text-muted-foreground capitalize">
                        {typeIcon} {discussion.type}
                      </span>
                      <span className="text-xs text-muted-foreground ml-auto">
                        {new Date(discussion.timestamp).toLocaleTimeString()}
                      </span>
                    </div>
                    <p className="text-sm text-gray-700">{discussion.message}</p>
                  </div>
                )
              } else {
                const decision = item.data as CollaborativeDecision
                const votes = Object.entries(decision.votes || {})
                const approvals = votes.filter(([_, v]) => v).length
                const total = votes.length

                return (
                  <div
                    key={`decision-${idx}`}
                    className="border-l-4 border-l-purple-500 pl-3 py-3 bg-purple-50 rounded-r shadow-sm"
                  >
                    <div className="flex items-center gap-2 mb-2">
                      <Badge className="bg-purple-600">Decision Made</Badge>
                      {total > 0 && (
                        <span className="text-xs text-muted-foreground">
                          {approvals}/{total} agents approved
                        </span>
                      )}
                    </div>
                    <div className="space-y-1">
                      <p className="text-sm font-medium">
                        <span className="text-purple-700">{decision.agent}</span> will {decision.action} on{" "}
                        <span className="font-mono text-xs bg-gray-100 px-1 rounded">{decision.target}</span>
                      </p>
                      <p className="text-sm text-gray-600">
                        <span className="font-medium">Reasoning:</span> {decision.reasoning}
                      </p>
                      {decision.rationale && (
                        <p className="text-xs text-gray-500 italic">
                          {decision.rationale}
                        </p>
                      )}
                    </div>
                  </div>
                )
              }
            })}
          </div>
        </div>
      </CardContent>
    </Card>
  )
}
