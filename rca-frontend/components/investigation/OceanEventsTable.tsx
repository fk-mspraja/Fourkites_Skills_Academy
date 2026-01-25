import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import type { OceanEventsDataSource } from "@/lib/types"

interface OceanEventsTableProps {
  data: OceanEventsDataSource
}

export function OceanEventsTable({ data }: OceanEventsTableProps) {
  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center justify-between">
          <span>🌊 Ocean Events (ClickHouse MMCUW) ({data.total_events})</span>
          <div className="flex gap-2 text-sm text-gray-600">
            <span>
              {new Date(data.date_range.start).toLocaleDateString()} →{" "}
              {new Date(data.date_range.end).toLocaleDateString()}
            </span>
          </div>
        </CardTitle>
      </CardHeader>
      <CardContent>
        {data.total_events === 0 ? (
          <div className="text-center py-8 text-gray-500">
            No ocean events found in the specified time range
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-sm border-collapse">
              <thead>
                <tr className="border-b bg-gray-50">
                  <th className="text-left p-3 font-medium">Timestamp</th>
                  <th className="text-left p-3 font-medium">Correlation ID</th>
                  <th className="text-left p-3 font-medium">Event Body</th>
                </tr>
              </thead>
              <tbody>
                {data.events.slice(0, 50).map((event, idx) => (
                  <tr key={idx} className="border-b hover:bg-gray-50">
                    <td className="p-3 align-top">
                      <div className="text-xs text-gray-500">
                        {new Date(event.timestamp).toLocaleString()}
                      </div>
                    </td>
                    <td className="p-3 align-top">
                      <Badge variant="outline" className="font-mono text-xs">
                        {event.correlation_id.substring(0, 12)}...
                      </Badge>
                    </td>
                    <td className="p-3 align-top">
                      <pre className="text-xs bg-gray-50 p-2 rounded overflow-x-auto max-w-2xl">
                        {event.body}
                      </pre>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
            {data.total_events > 50 && (
              <div className="text-center py-4 text-sm text-gray-500">
                Showing 50 of {data.total_events} events
              </div>
            )}
          </div>
        )}
      </CardContent>
    </Card>
  )
}
