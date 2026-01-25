# Multi-Agent RCA Platform - Frontend

**Modern Next.js UI for real-time Root Cause Analysis visualization**

## Overview

This frontend provides a professional, real-time interface for the Multi-Agent RCA Platform. It displays:
- **Live agent conversation** - See AI agents working in real-time
- **Hypothesis tracking** - Evidence-based root cause hypotheses with confidence scores
- **Root cause determination** - Final diagnosis with recommended actions
- **HITL support** - Human-in-the-loop when system needs input

## Technology Stack

- **Next.js 14** with App Router
- **TypeScript** for type safety
- **Tailwind CSS** for styling
- **shadcn/ui** for beautiful UI components
- **Radix UI** for accessible components
- **SSE (Server-Sent Events)** for real-time streaming

## Project Structure

```
rca-frontend/
├── app/
│   ├── layout.tsx           # Root layout
│   ├── page.tsx             # Main investigation page
│   └── globals.css          # Global styles
├── components/
│   ├── investigation/
│   │   ├── InputForm.tsx             # Issue description input
│   │   ├── AgentConversation.tsx     # Live agent messages
│   │   ├── HypothesisTracker.tsx     # Hypothesis display with evidence
│   │   └── RootCauseDisplay.tsx      # Final root cause & actions
│   └── ui/                  # shadcn/ui components
│       ├── card.tsx
│       ├── button.tsx
│       ├── badge.tsx
│       ├── progress.tsx
│       └── textarea.tsx
├── hooks/
│   └── useInvestigation.ts  # SSE streaming hook
├── lib/
│   ├── types.ts             # TypeScript types
│   └── utils.ts             # Utility functions
├── package.json
├── tsconfig.json
├── tailwind.config.ts
└── next.config.js
```

## Setup

### Prerequisites

- Node.js 18+ and npm
- Backend must be running on `http://localhost:8000`

### Installation

```bash
cd rca-frontend
npm install
```

### Development

```bash
npm run dev
```

Open [http://localhost:3000](http://localhost:3000) in your browser.

### Production Build

```bash
npm run build
npm start
```

## Usage

### Starting an Investigation

1. **Enter issue description** in the text area:
   ```
   Load U110123982 is not tracking, customer reports no updates.
   Shipper: ABC Corp, Carrier: XYZ Logistics
   ```

2. **Click "Start Investigation"** - The system will:
   - Extract identifiers (tracking ID, load number, etc.)
   - Query multiple data sources in parallel
   - Form hypotheses with evidence
   - Determine root cause or request human input

3. **Watch real-time updates** in the agent conversation panel

4. **Review results**:
   - Hypotheses with confidence scores
   - Root cause determination
   - Recommended actions

### Understanding the UI

**Agent Conversation (Left Panel)**
- Real-time messages from AI agents
- Color-coded by agent type
- Status indicators (running, completed, failed)
- Timestamps for all activities

**Hypotheses Tracker (Right Panel)**
- Confidence scores (0-100%)
- Evidence for/against each hypothesis
- Expandable details
- Category labels

**Root Cause Display (Top Right)**
- Final determination
- Confidence percentage
- Category classification
- Recommended actions with priorities

## API Integration

The frontend connects to the backend via:

**SSE Endpoint:** `POST /api/rca/investigate/stream`

**Events Received:**
- `started` - Investigation initialized
- `agent_message` - Agent activity update
- `timeline_event` - Timeline entry
- `hypothesis_update` - Hypotheses formed
- `query_executed` - Data source query logged
- `root_cause` - Final determination
- `needs_human` - HITL request
- `complete` - Investigation finished
- `error` - Error occurred

## Configuration

### Backend URL

In `next.config.js`:
```javascript
async rewrites() {
  return [
    {
      source: '/api/rca/:path*',
      destination: 'http://localhost:8000/api/rca/:path*',
    },
  ];
}
```

Change `http://localhost:8000` to your backend URL if different.

## Customization

### Adding New Components

Create components in `components/investigation/`:

```tsx
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"

export function MyComponent({ data }: { data: any }) {
  return (
    <Card>
      <CardHeader>
        <CardTitle>My Component</CardTitle>
      </CardHeader>
      <CardContent>
        {/* Your content here */}
      </CardContent>
    </Card>
  )
}
```

### Styling

Tailwind CSS classes are used throughout. To customize:

1. **Edit `tailwind.config.ts`** for theme changes
2. **Edit `app/globals.css`** for CSS variables
3. **Use `className`** prop on components

### Adding shadcn/ui Components

```bash
npx shadcn-ui@latest add [component-name]
```

Example:
```bash
npx shadcn-ui@latest add dialog
npx shadcn-ui@latest add tabs
```

## Troubleshooting

### Backend Connection Failed

**Error:** `Failed to fetch` or connection refused

**Solution:**
1. Ensure backend is running: `cd ../rca-backend && uvicorn app.main:app --reload`
2. Check backend URL in `next.config.js`
3. Verify CORS is configured in backend

### SSE Events Not Streaming

**Error:** Investigation starts but no updates

**Solution:**
1. Open browser DevTools → Network tab
2. Look for `/api/rca/investigate/stream` request
3. Check response is `text/event-stream`
4. Verify backend is sending SSE events

### TypeScript Errors

**Error:** Type errors during build

**Solution:**
```bash
npm run build
# Fix any type errors shown
```

## Development Tips

### Hot Reload

Next.js automatically reloads on file changes. If it doesn't:
```bash
# Stop dev server (Ctrl+C)
# Clear .next directory
rm -rf .next
# Restart
npm run dev
```

### Debugging SSE

Add console logging in `hooks/useInvestigation.ts`:

```typescript
console.log("SSE Event:", eventType, data)
```

### Testing Without Backend

Mock the SSE response in `useInvestigation.ts`:

```typescript
// Simulate events for UI testing
const mockEvents = [
  { event: "started", data: { investigation_id: "test123" } },
  { event: "agent_message", data: { agent: "Test Agent", message: "Testing..." } },
  // ... more mock events
]
```

## Performance

- **Initial page load:** < 1s
- **SSE connection:** Instant
- **Real-time updates:** < 100ms latency
- **Bundle size:** ~200KB gzipped

## Browser Support

- Chrome/Edge (latest)
- Firefox (latest)
- Safari (latest)

## Contributing

When adding features:
1. Follow existing component patterns
2. Use TypeScript types from `lib/types.ts`
3. Maintain responsive design (mobile-first)
4. Test SSE streaming thoroughly

## License

Internal FourKites project
