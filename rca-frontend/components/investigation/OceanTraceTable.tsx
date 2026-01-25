import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import type { OceanTraceDataSource } from "@/lib/types"

interface OceanTraceTableProps {
  data: OceanTraceDataSource
}

export function OceanTraceTable({ data }: OceanTraceTableProps) {
  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center justify-between">
          <span>📡 Ocean Trace (DataHub Subscription)</span>
          <div className="flex gap-2">
            <Badge variant="outline" className="bg-blue-50">
              🆔 {data.subscription_id}
            </Badge>
            <Badge variant="outline" className="bg-green-50">
              ✓ {data.successful} Successful
            </Badge>
            <Badge variant="outline" className="bg-red-50">
              ✗ {data.rejected} Rejected
            </Badge>
          </div>
        </CardTitle>
      </CardHeader>
      <CardContent>
        {data.total_updates === 0 ? (
          <div className="text-center py-8 text-gray-500">
            No subscription updates found
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-sm border-collapse">
              <thead>
                <tr className="border-b bg-gray-50">
                  <th className="text-left p-3 font-medium">Status</th>
                  <th className="text-left p-3 font-medium">Event Code</th>
                  <th className="text-left p-3 font-medium">Location</th>
                  <th className="text-left p-3 font-medium">Event Time</th>
                  <th className="text-left p-3 font-medium">Created At</th>
                  <th className="text-left p-3 font-medium">Source</th>
                </tr>
              </thead>
              <tbody>
                {data.updates.slice(0, 50).map((update, idx) => (
                  <tr key={idx} className="border-b hover:bg-gray-50">
                    <td className="p-3">
                      <Badge
                        variant={
                          update.status.toLowerCase().includes("success") ||
                          update.status.toLowerCase().includes("accepted")
                            ? "default"
                            : "destructive"
                        }
                      >
                        {update.status}
                      </Badge>
                    </td>
                    <td className="p-3">
                      <code className="text-xs bg-gray-100 px-2 py-1 rounded">
                        {update.event_code}
                      </code>
                    </td>
                    <td className="p-3">{update.location || "N/A"}</td>
                    <td className="p-3">
                      <div className="text-xs text-gray-500">
                        {new Date(update.event_time).toLocaleString()}
                      </div>
                    </td>
                    <td className="p-3">
                      <div className="text-xs text-gray-500">
                        {new Date(update.created_at).toLocaleString()}
                      </div>
                    </td>
                    <td className="p-3">
                      <Badge variant="outline" className="text-xs">
                        {update.source}
                      </Badge>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
            {data.total_updates > 50 && (
              <div className="text-center py-4 text-sm text-gray-500">
                Showing 50 of {data.total_updates} updates
              </div>
            )}
          </div>
        )}
      </CardContent>
    </Card>
  )
}
