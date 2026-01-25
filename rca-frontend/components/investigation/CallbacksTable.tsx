"use client"

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import type { CallbacksDataSource } from "@/lib/types"

interface CallbacksTableProps {
  data: CallbacksDataSource
}

export function CallbacksTable({ data }: CallbacksTableProps) {
  if (!data || data.total_callbacks === 0) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>📞 Callbacks</CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-sm text-gray-500">No callbacks found</p>
        </CardContent>
      </Card>
    )
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center justify-between">
          <span>📞 Callbacks ({data.total_callbacks})</span>
          <div className="flex gap-2 text-sm">
            <Badge variant="outline" className="bg-green-50">
              ✓ {data.successful} Successful
            </Badge>
            <Badge variant="outline" className="bg-red-50">
              ✗ {data.failed} Failed
            </Badge>
          </div>
        </CardTitle>
      </CardHeader>
      <CardContent>
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead className="bg-gray-50 border-b">
              <tr>
                <th className="px-4 py-2 text-left font-medium">UUID</th>
                <th className="px-4 py-2 text-left font-medium">Config ID</th>
                <th className="px-4 py-2 text-left font-medium">Timestamp</th>
                <th className="px-4 py-2 text-left font-medium">Status</th>
                <th className="px-4 py-2 text-left font-medium">Message Type</th>
                <th className="px-4 py-2 text-left font-medium">URL</th>
              </tr>
            </thead>
            <tbody>
              {data.callbacks.slice(0, 50).map((callback, idx) => (
                <tr key={idx} className="border-b hover:bg-gray-50">
                  <td className="px-4 py-2 font-mono text-xs">
                    {callback.uuid.substring(0, 8)}...
                  </td>
                  <td className="px-4 py-2">{callback.config_id}</td>
                  <td className="px-4 py-2 text-xs">
                    {new Date(callback.callback_event_timestamp).toLocaleString()}
                  </td>
                  <td className="px-4 py-2">
                    {callback.http_response_code ? (
                      <Badge
                        variant={
                          callback.http_response_code.startsWith("2")
                            ? "default"
                            : "destructive"
                        }
                      >
                        {callback.http_response_code}
                      </Badge>
                    ) : (
                      <Badge variant="outline">Pending</Badge>
                    )}
                  </td>
                  <td className="px-4 py-2">
                    <span className="text-xs bg-blue-50 px-2 py-1 rounded">
                      {callback.message_type}
                    </span>
                  </td>
                  <td className="px-4 py-2 text-xs truncate max-w-xs">
                    {callback.destination_url || "—"}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
          {data.total_callbacks > 50 && (
            <p className="text-xs text-gray-500 mt-2 text-center">
              Showing first 50 of {data.total_callbacks} callbacks
            </p>
          )}
        </div>
      </CardContent>
    </Card>
  )
}
