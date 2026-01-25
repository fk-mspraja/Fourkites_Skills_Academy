# FourKites Auto-RCA Frontend

World-class React Next.js UI for intelligent root cause analysis.

## 🎯 How Sub-Agents Work & Reach Consensus

### Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                    USER SUBMITS LOAD ID                      │
└─────────────────────┬────────────────────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────────────────┐
│  STEP 1: Extract Identifiers (load_id, carrier, shipper)   │
└─────────────────────┬────────────────────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────────────────┐
│  STEP 2: LLM Forms 3-5 Hypotheses (Parallel Candidates)    │
│                                                              │
│  Example Hypotheses:                                        │
│  • H1: Network relationship missing (0.60 confidence)       │
│  • H2: JT scraping error (0.30 confidence)                 │
│  • H3: Carrier portal down (0.10 confidence)               │
└─────────────────────┬────────────────────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────────────────┐
│  STEP 3: Spawn Sub-Agent for Each Hypothesis (Parallel)    │
│                                                              │
│    SubAgent-H1 ─┐    SubAgent-H2 ─┐    SubAgent-H3 ─┐      │
│    (Network)    │    (JT Check)   │    (Carrier)    │      │
│                 │                 │                 │      │
│    • LLM decides query          • LLM decides query        │
│    • Executes API call          • Executes DB query        │
│    • Evaluates evidence         • Evaluates evidence       │
│    • Updates confidence         • Updates confidence       │
│                 │                 │                 │      │
│    Can revisit same API with different params              │
│    Can spawn child sub-agents for deeper investigation     │
└─────────────────────┬────────────────────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────────────────┐
│  STEP 4: Synthesis (LLM Determines Consensus)              │
│                                                              │
│  Input to LLM:                                              │
│  • All 5 hypotheses with final confidence scores           │
│  • All evidence collected from all sub-agents               │
│                                                              │
│  LLM Analysis:                                              │
│  "H1 has highest confidence (0.85) with strong evidence    │
│   from company_api showing relationship inactive.           │
│   H2 eliminated (confidence dropped to 0.1).                │
│   H3 contradicted by evidence.                              │
│                                                              │
│   CONSENSUS: Root cause = network_relationship_inactive"    │
│                                                              │
│  Output:                                                     │
│  • Root Cause: "Network relationship inactive"              │
│  • Confidence: 0.85                                         │
│  • Recommended Action: "Reactivate in Network Admin"        │
└─────────────────────────────────────────────────────────────┘
```

### Key Innovation: Adaptive Investigation

Unlike traditional RCA that follows fixed steps:

**Old Way (Linear):**
```
Step 1 → Step 2 → Step 5 → Root Cause
(Same path every time)
```

**New Way (Hypothesis-Driven):**
```
Initial Evidence → Form Multiple Hypotheses → Parallel Investigation
                    ↓
Each sub-agent decides what to query next based on findings
                    ↓
LLM synthesizes all evidence to determine consensus
```

**Example Conversation:**

```
SubAgent-H1 (Network Checker):
Iteration 1: "Let me check company_api for relationship"
  → Result: "Relationship exists"
  → LLM: "Confidence: 0.6 → 0.3 (contradicts hypothesis)"

Iteration 2: "Maybe relationship is inactive? Let me re-check with status filter"
  → Result: "Status = INACTIVE since Dec 2025"
  → LLM: "Confidence: 0.3 → 0.85 (strongly supports!)"

Iteration 3: "High confidence reached, concluding"

SubAgent-H2 (JT Checker):
Iteration 1: "Check JT scraping history"
  → Result: "5 events, no errors"
  → LLM: "Confidence: 0.3 → 0.1 (contradicts)"

Iteration 2: "Confidence too low, eliminating hypothesis"

Final Synthesis (LLM reads all sub-agent findings):
"SubAgent-H1 found strong evidence for inactive relationship (0.85).
 SubAgent-H2 found no JT issues (eliminated).
 SubAgent-H3 found carrier portal is active (eliminated).

 CONSENSUS: Root cause is network_relationship_inactive with 85% confidence."
```

## 🎨 UI Features

### Real-Time Streaming
- Server-Sent Events (SSE) for live updates
- Watch hypotheses form in real-time
- See sub-agent actions as they execute
- Evidence appears as it's collected

### Visual Intelligence
- **Progress Stepper**: 4-phase investigation visualization
- **Hypothesis Cards**: Live confidence updates with color-coded bars
- **Agent Actions**: Expandable cards showing reasoning
- **Evidence Timeline**: Chronological evidence collection
- **Final Synthesis**: Beautiful result card with metrics

### FourKites Branding
- Custom color palette (Blue #0066FF, Navy, Teal)
- Dark mode optimized
- Gradient backgrounds
- Professional animations

## 🚀 Getting Started

### Install Dependencies
```bash
cd frontend
npm install
```

### Start Development Server
```bash
npm run dev
```

Visit: http://localhost:3000

### Backend Connection
Make sure the FastAPI backend is running on port 8080:
```bash
cd ..
python3 -m uvicorn api.main:app --host 0.0.0.0 --port 8080
```

## 📁 Project Structure

```
frontend/
├── app/
│   ├── layout.tsx       # Root layout with FourKites branding
│   ├── page.tsx         # Main investigation UI
│   └── globals.css      # Tailwind styles + custom classes
├── package.json
├── tailwind.config.ts   # FourKites colors
├── tsconfig.json
└── next.config.ts       # API proxy to backend
```

## 🎯 Key Components

### Investigation UI (page.tsx)
- **Search Bar**: Load ID input with validation
- **Progress Steps**: 4-phase stepper with animations
- **Sub-Agent Cards**: Real-time hypothesis tracking
  - Confidence bars with gradient
  - Expandable details (actions + evidence)
  - Status badges (active/confirmed/eliminated)
- **Final Result**: Synthesis card with metrics
- **Logs Panel**: Scrollable investigation timeline

### SSE Integration
```typescript
const response = await fetch("/api/v1/investigate", {
  method: "POST",
  body: JSON.stringify({ load_id, mode: "ocean" }),
});

const reader = response.body?.getReader();
// Stream events in real-time
// Update UI as events arrive
```

## 🎨 Design System

### Colors
- **Primary**: FourKites Blue (#0066FF)
- **Secondary**: Teal (#00A3A3)
- **Dark**: Navy (#003B73)
- **Background**: Gray-950 with gradient

### Components
- `.card` - Dark cards with border
- `.badge` - Status indicators
- `.badge-blue` - Primary actions
- `.badge-teal` - Evidence sources
- `.badge-green` - Success states
- `.badge-red` - Errors

## 📊 Data Flow

```
User Input → FastAPI Backend → Hypothesis Formation
                ↓
         Parallel Sub-Agents (5 concurrent)
                ↓
         Evidence Collection + LLM Evaluation
                ↓
         SSE Events Stream to Frontend
                ↓
         React State Updates (Real-time UI)
                ↓
         LLM Synthesis → Final Result
```

## 🔧 Configuration

### API Proxy (next.config.ts)
```typescript
rewrites: [
  {
    source: "/api/:path*",
    destination: "http://localhost:8080/api/:path*",
  },
]
```

### Tailwind (tailwind.config.ts)
```typescript
colors: {
  fourkites: {
    blue: "#0066FF",
    navy: "#003B73",
    teal: "#00A3A3",
  },
}
```

## 🎬 Demo

1. Enter load ID (e.g., `618171104`)
2. Click "Investigate"
3. Watch real-time:
   - Hypotheses form (5 parallel theories)
   - Sub-agents spawn and investigate
   - Confidence scores update live
   - Evidence collects in real-time
   - Final consensus emerges

## 🚀 Production Build

```bash
npm run build
npm start
```

## 📝 Notes

- Uses Next.js 15 App Router
- TypeScript for type safety
- Tailwind CSS for styling
- Lucide React for icons
- SSE for real-time streaming
- Responsive design
- Dark mode optimized
