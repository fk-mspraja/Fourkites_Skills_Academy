"use client"

import { useEffect, useRef } from "react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { formatTimestamp } from "@/lib/utils"
import type { AgentMessage } from "@/lib/types"
import { CheckCircle2, Loader2, XCircle, Circle } from "lucide-react"

interface AgentConversationProps {
  messages: AgentMessage[]
}

function getStatusIcon(status?: string) {
  switch (status) {
    case "completed":
      return <CheckCircle2 className="w-4 h-4 text-green-500" />
    case "running":
      return <Loader2 className="w-4 h-4 text-blue-500 animate-spin" />
    case "failed":
      return <XCircle className="w-4 h-4 text-red-500" />
    default:
      return <Circle className="w-4 h-4 text-gray-400" />
  }
}

function getAgentColor(agent: string): string {
  const colors: Record<string, string> = {
    "Identifier Agent": "bg-purple-100 text-purple-800 border-purple-200",
    "Tracking API Agent": "bg-blue-100 text-blue-800 border-blue-200",
    "JT Agent": "bg-green-100 text-green-800 border-green-200",
    "Super API Agent": "bg-yellow-100 text-yellow-800 border-yellow-200",
    "Network Agent": "bg-orange-100 text-orange-800 border-orange-200",
    "Hypothesis Agent": "bg-pink-100 text-pink-800 border-pink-200",
    "Synthesis Agent": "bg-indigo-100 text-indigo-800 border-indigo-200",
  }
  return colors[agent] || "bg-gray-100 text-gray-800 border-gray-200"
}

export function AgentConversation({ messages }: AgentConversationProps) {
  const scrollRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight
    }
  }, [messages])

  return (
    <Card className="h-full flex flex-col">
      <CardHeader className="bg-blue-50 border-b">
        <CardTitle className="flex items-center gap-2">
          <Circle className="w-5 h-5 text-blue-500 fill-blue-500" />
          Agent Activity
          <Badge variant="secondary" className="ml-auto">
            {messages.length} messages
          </Badge>
        </CardTitle>
      </CardHeader>
      <CardContent
        ref={scrollRef}
        className="flex-1 overflow-y-auto p-4 space-y-3 max-h-[600px]"
      >
        {messages.length === 0 ? (
          <div className="text-center text-muted-foreground py-8">
            Waiting for investigation to start...
          </div>
        ) : (
          messages.map((msg, idx) => (
            <div key={idx} className="flex items-start gap-3 group">
              <div className="flex-shrink-0 mt-1">
                {getStatusIcon(msg.status)}
              </div>
              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-2 mb-1">
                  <span
                    className={`text-xs font-medium px-2 py-0.5 rounded-full border ${getAgentColor(msg.agent)}`}
                  >
                    {msg.agent}
                  </span>
                  <span className="text-xs text-muted-foreground">
                    {formatTimestamp(msg.timestamp)}
                  </span>
                </div>
                <div className="text-sm text-gray-700">
                  {msg.message}
                </div>
              </div>
            </div>
          ))
        )}
      </CardContent>
    </Card>
  )
}
