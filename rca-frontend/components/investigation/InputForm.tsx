"use client"

import { useState } from "react"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Textarea } from "@/components/ui/textarea"
import { Label } from "@/components/ui/label"
import { Switch } from "@/components/ui/switch"

interface InputFormProps {
  onSubmit: (issueText: string, collaborative: boolean) => void
  isLoading: boolean
}

export function InputForm({ onSubmit, isLoading }: InputFormProps) {
  const [issueText, setIssueText] = useState("")
  const [collaborative, setCollaborative] = useState(true)

  const handleSubmit = () => {
    if (issueText.trim()) {
      onSubmit(issueText, collaborative)
    }
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle>Start Investigation</CardTitle>
        <CardDescription>
          Describe the issue you're investigating. Include tracking IDs, load numbers, or container numbers if known.
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-4">
        <Textarea
          placeholder="Example: Load U110123982 is not tracking, customer reports no updates. Shipper: ABC Corp, Carrier: XYZ Logistics"
          value={issueText}
          onChange={(e) => setIssueText(e.target.value)}
          rows={6}
          disabled={isLoading}
          className="resize-none"
        />

        <div className="flex items-center justify-between gap-4">
          <div className="flex items-center space-x-2">
            <Switch
              id="collaborative-mode"
              checked={collaborative}
              onCheckedChange={setCollaborative}
              disabled={isLoading}
            />
            <Label htmlFor="collaborative-mode" className="text-sm">
              Collaborative Mode
              <span className="block text-xs text-muted-foreground">
                Agents discuss and decide together
              </span>
            </Label>
          </div>

          <div className="flex gap-2">
            <Button
              onClick={handleSubmit}
              disabled={isLoading || !issueText.trim()}
            >
              {isLoading ? "Investigating..." : "Start Investigation"}
            </Button>

            {isLoading && (
              <Button
                variant="outline"
                onClick={() => setIssueText("")}
              >
                Clear
              </Button>
            )}
          </div>
        </div>

        {!isLoading && issueText && (
          <div className="text-xs text-muted-foreground">
            The system will extract identifiers, query data sources in parallel, form hypotheses, and determine the root cause.
          </div>
        )}
      </CardContent>
    </Card>
  )
}
