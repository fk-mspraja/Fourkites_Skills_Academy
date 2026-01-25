"use client"

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Progress } from "@/components/ui/progress"
import type { Hypothesis } from "@/lib/types"
import { ChevronDown, ChevronRight, ThumbsUp, ThumbsDown } from "lucide-react"
import { useState } from "react"

interface HypothesisTrackerProps {
  hypotheses: Hypothesis[]
}

function getCategoryLabel(category: string): string {
  const labels: Record<string, string> = {
    load_creation_failure: "Load Creation Failure",
    configuration_issue: "Configuration Issue",
    jt_issue: "JT Issue",
    carrier_issue: "Carrier Issue",
    network_relationship: "Network Relationship",
    callback_failure: "Callback Failure",
    data_quality: "Data Quality",
    system_error: "System Error",
    unknown: "Unknown",
  }
  return labels[category] || category
}

function HypothesisCard({ hypothesis }: { hypothesis: Hypothesis }) {
  const [expanded, setExpanded] = useState(false)
  const confidencePercent = Math.round(hypothesis.confidence * 100)

  return (
    <div className="border rounded-lg p-4 bg-white">
      <div className="flex items-start justify-between mb-2">
        <div className="flex-1">
          <div className="font-medium text-sm mb-1">
            {hypothesis.description}
          </div>
          <Badge variant="outline" className="text-xs">
            {getCategoryLabel(hypothesis.category)}
          </Badge>
        </div>
        <div className="flex items-center gap-2">
          <Badge
            variant={confidencePercent >= 70 ? "default" : "secondary"}
            className="text-sm font-semibold"
          >
            {confidencePercent}%
          </Badge>
        </div>
      </div>

      <Progress value={confidencePercent} className="mb-3 h-2" />

      <button
        onClick={() => setExpanded(!expanded)}
        className="flex items-center gap-1 text-sm text-muted-foreground hover:text-foreground transition-colors"
      >
        {expanded ? (
          <ChevronDown className="w-4 h-4" />
        ) : (
          <ChevronRight className="w-4 h-4" />
        )}
        View Evidence ({hypothesis.evidence_for.length} for, {hypothesis.evidence_against.length} against)
      </button>

      {expanded && (
        <div className="mt-3 space-y-3 pl-5 border-l-2 border-gray-200">
          {hypothesis.evidence_for.length > 0 && (
            <div>
              <div className="flex items-center gap-2 text-sm font-medium text-green-700 mb-2">
                <ThumbsUp className="w-4 h-4" />
                Evidence For ({hypothesis.evidence_for.length})
              </div>
              {hypothesis.evidence_for.map((evidence, idx) => (
                <div key={idx} className="text-sm pl-6 mb-2">
                  <span className="font-medium text-gray-700">
                    {evidence.source}:
                  </span>{" "}
                  <span className="text-gray-600">{evidence.finding}</span>
                  <Badge variant="secondary" className="ml-2 text-xs">
                    weight: {evidence.weight.toFixed(2)}
                  </Badge>
                </div>
              ))}
            </div>
          )}

          {hypothesis.evidence_against.length > 0 && (
            <div>
              <div className="flex items-center gap-2 text-sm font-medium text-red-700 mb-2">
                <ThumbsDown className="w-4 h-4" />
                Evidence Against ({hypothesis.evidence_against.length})
              </div>
              {hypothesis.evidence_against.map((evidence, idx) => (
                <div key={idx} className="text-sm pl-6 mb-2">
                  <span className="font-medium text-gray-700">
                    {evidence.source}:
                  </span>{" "}
                  <span className="text-gray-600">{evidence.finding}</span>
                  <Badge variant="secondary" className="ml-2 text-xs">
                    weight: {evidence.weight.toFixed(2)}
                  </Badge>
                </div>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  )
}

export function HypothesisTracker({ hypotheses }: HypothesisTrackerProps) {
  if (hypotheses.length === 0) {
    return null
  }

  return (
    <Card>
      <CardHeader className="bg-purple-50 border-b">
        <CardTitle className="flex items-center gap-2">
          Hypotheses
          <Badge variant="secondary" className="ml-auto">
            {hypotheses.length} formed
          </Badge>
        </CardTitle>
      </CardHeader>
      <CardContent className="p-4 space-y-3">
        {hypotheses.map((hypothesis) => (
          <HypothesisCard key={hypothesis.id} hypothesis={hypothesis} />
        ))}
      </CardContent>
    </Card>
  )
}
