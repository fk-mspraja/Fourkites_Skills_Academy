"use client"

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import type { RedshiftDataSource } from "@/lib/types"

interface ValidationErrorsTableProps {
  data: RedshiftDataSource
}

export function ValidationErrorsTable({ data }: ValidationErrorsTableProps) {
  if (!data || data.total_attempts === 0) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>🔍 Load Validation</CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-sm text-gray-500">No validation records found</p>
        </CardContent>
      </Card>
    )
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center justify-between">
          <span>🔍 Load Validation ({data.total_attempts} attempts)</span>
          <div className="flex gap-2 text-sm">
            <Badge variant="outline" className="bg-green-50">
              ✓ {data.total_attempts - data.failed_attempts} Success
            </Badge>
            <Badge variant="outline" className="bg-red-50">
              ✗ {data.failed_attempts} Failed
            </Badge>
          </div>
        </CardTitle>
      </CardHeader>
      <CardContent>
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead className="bg-gray-50 border-b">
              <tr>
                <th className="px-4 py-2 text-left font-medium">Load Number</th>
                <th className="px-4 py-2 text-left font-medium">Company</th>
                <th className="px-4 py-2 text-left font-medium">Carrier</th>
                <th className="px-4 py-2 text-left font-medium">Status</th>
                <th className="px-4 py-2 text-left font-medium">Error</th>
                <th className="px-4 py-2 text-left font-medium">Processed At</th>
                <th className="px-4 py-2 text-left font-medium">File</th>
              </tr>
            </thead>
            <tbody>
              {data.validation_attempts.slice(0, 20).map((attempt, idx) => (
                <tr key={idx} className="border-b hover:bg-gray-50">
                  <td className="px-4 py-2 font-mono text-xs">
                    {attempt.load_number}
                  </td>
                  <td className="px-4 py-2 text-xs">
                    {attempt.company_name}
                  </td>
                  <td className="px-4 py-2 text-xs">
                    {attempt.carrier_name}
                  </td>
                  <td className="px-4 py-2">
                    <Badge
                      variant={
                        attempt.status.toLowerCase().includes("success") ||
                        attempt.status.toLowerCase() === "valid"
                          ? "default"
                          : "destructive"
                      }
                    >
                      {attempt.status}
                    </Badge>
                  </td>
                  <td className="px-4 py-2 text-xs max-w-xs truncate">
                    {attempt.error || "—"}
                  </td>
                  <td className="px-4 py-2 text-xs">
                    {new Date(attempt.processed_at).toLocaleString()}
                  </td>
                  <td className="px-4 py-2 text-xs truncate max-w-xs">
                    {attempt.file_name}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
          {data.total_attempts > 20 && (
            <p className="text-xs text-gray-500 mt-2 text-center">
              Showing first 20 of {data.total_attempts} attempts
            </p>
          )}
        </div>

        {data.latest_error && (
          <div className="mt-4 p-3 bg-red-50 border border-red-200 rounded">
            <p className="text-sm font-medium text-red-900">Latest Error:</p>
            <p className="text-xs text-red-800 mt-1">{data.latest_error}</p>
          </div>
        )}
      </CardContent>
    </Card>
  )
}
