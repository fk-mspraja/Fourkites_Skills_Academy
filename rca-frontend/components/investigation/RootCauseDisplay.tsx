"use client"

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import type { RootCause } from "@/lib/types"
import { CheckCircle2, AlertTriangle, AlertCircle } from "lucide-react"

interface RootCauseDisplayProps {
  rootCause: RootCause | null
  needsHuman: boolean
  humanQuestion?: string
}

function getPriorityIcon(priority: string) {
  switch (priority) {
    case "high":
      return <AlertCircle className="w-4 h-4 text-red-500" />
    case "medium":
      return <AlertTriangle className="w-4 h-4 text-yellow-500" />
    case "low":
      return <CheckCircle2 className="w-4 h-4 text-green-500" />
    default:
      return null
  }
}

function getPriorityColor(priority: string): string {
  switch (priority) {
    case "high":
      return "bg-red-100 text-red-800 border-red-200"
    case "medium":
      return "bg-yellow-100 text-yellow-800 border-yellow-200"
    case "low":
      return "bg-green-100 text-green-800 border-green-200"
    default:
      return "bg-gray-100 text-gray-800 border-gray-200"
  }
}

export function RootCauseDisplay({
  rootCause,
  needsHuman,
  humanQuestion,
}: RootCauseDisplayProps) {
  if (needsHuman) {
    return (
      <Card className="border-yellow-300 bg-yellow-50">
        <CardHeader>
          <CardTitle className="flex items-center gap-2 text-yellow-800">
            <AlertTriangle className="w-5 h-5" />
            Human Input Required
          </CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-sm text-yellow-900 whitespace-pre-wrap">
            {humanQuestion || "The system needs your input to proceed with the investigation."}
          </p>
        </CardContent>
      </Card>
    )
  }

  if (!rootCause) {
    return null
  }

  const confidencePercent = Math.round(rootCause.confidence * 100)

  return (
    <Card className="border-green-300 bg-green-50">
      <CardHeader>
        <CardTitle className="flex items-center gap-2 text-green-800">
          <CheckCircle2 className="w-5 h-5" />
          Root Cause Determined
          <Badge className="ml-auto bg-green-600">{confidencePercent}% confidence</Badge>
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        <div>
          <div className="text-sm font-medium text-green-900 mb-1">
            Description:
          </div>
          <div className="text-sm text-green-800">
            {rootCause.description}
          </div>
        </div>

        <div>
          <div className="text-sm font-medium text-green-900 mb-1">
            Category:
          </div>
          <Badge variant="outline" className="text-green-800">
            {rootCause.category.replace(/_/g, " ").toUpperCase()}
          </Badge>
        </div>

        {rootCause.recommended_actions.length > 0 && (
          <div>
            <div className="text-sm font-medium text-green-900 mb-2">
              Recommended Actions:
            </div>
            <div className="space-y-2">
              {rootCause.recommended_actions.map((action, idx) => (
                <div
                  key={idx}
                  className="flex items-start gap-2 p-3 bg-white rounded-lg border"
                >
                  <div className="flex-shrink-0 mt-0.5">
                    {getPriorityIcon(action.priority)}
                  </div>
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2 mb-1">
                      <span
                        className={`text-xs font-medium px-2 py-0.5 rounded-full border ${getPriorityColor(action.priority)}`}
                      >
                        {action.priority.toUpperCase()}
                      </span>
                      <Badge variant="outline" className="text-xs">
                        {action.category}
                      </Badge>
                    </div>
                    <div className="text-sm font-medium text-gray-900">
                      {action.description}
                    </div>
                    {action.details && (
                      <div className="text-xs text-gray-600 mt-1">
                        → {action.details}
                      </div>
                    )}
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  )
}
