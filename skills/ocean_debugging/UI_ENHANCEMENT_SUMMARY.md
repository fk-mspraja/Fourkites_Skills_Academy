# UI Enhancement for Ops/Support Teams

**Date**: January 19, 2026
**Enhancement**: Three-tab interface with advanced features for operations and support teams
**Status**: Complete ✅

---

## 🎯 What Was Added

### 1. **Tabbed Interface**
Created a modern 3-tab layout to organize different aspects of RCA work:

#### **Tab 1: Investigation** 🧠
- Real-time hypothesis-driven RCA investigation
- Progress tracking through 4 phases
- Sub-agent cards showing parallel investigations
- Expandable details for each sub-agent showing:
  - Actions taken with reasoning
  - Evidence collected
  - Confidence updates
- Final root cause with metrics and recommendations
- Investigation logs stream

#### **Tab 2: Logs & Queries** 🔍
- **SigNoz Log Query Interface** with:
  - 6 Quick Templates for TL/FTL processing stages:
    - 📁 File Ingestion (ProcessSuperFilesTask)
    - 🗺️ Data Mapping (PROCESS_SUPER_RECORD)
    - 🚚 Asset Assignment (PROCESS_TRUCK_RECORD)
    - 📍 Location Processing (PROCESS_TRUCK_LOCATION)
    - ✅ Location Validation (PROCESS_NEW_LOCATION)
    - 📡 ELD Integration (FETCH_ELD_LOCATION)

  - **Custom Query Builder**:
    - Service selection (carrier-files-worker, global-worker-ex, location-worker, etc.)
    - Message type input
    - Load/Tracking ID search
    - Configurable days back (1-30)

  - **Results Display**:
    - Shows up to 50 log entries
    - Color-coded severity badges (ERROR, WARN, INFO)
    - Timestamps for each log
    - Pretty-printed JSON formatting
    - Scrollable with max height

#### **Tab 3: AI Assistant** 💬
- **Chat Interface** for natural language RCA queries
- **Context-Aware**: Automatically includes:
  - Current load ID
  - Active hypotheses with confidence scores
  - Evidence count
  - Determined root cause (if available)

- **Pre-populated Suggestions**:
  - "What are the key findings?"
  - "Explain the root cause"
  - "What logs should I check?"
  - "How do I fix this issue?"

- **AI Capabilities**:
  - Explains investigation results
  - Recommends specific log queries
  - Suggests next steps
  - Translates technical concepts to ops-friendly language
  - References TL/FTL processing stages

---

## 📁 Files Modified/Created

### Frontend Changes:

1. **`frontend/app/page.tsx`** (Major Update)
   - Added 3 new state hooks for tabs, log queries, and AI chat
   - Added `queryLogs()` function for log querying
   - Added `sendChatMessage()` function for AI chat
   - Added `applyLogTemplate()` for quick query templates
   - Created tabbed interface with conditional rendering
   - Built log query form with template buttons
   - Built AI chat interface with message history
   - Lines: ~1014 (added ~400 lines)

2. **`frontend/app/globals.css`** (Minor Update)
   - Added `.badge-yellow` style for warning severity
   - Lines: 43 (added 3 lines)

### Backend Changes:

3. **`api/routes/investigate.py`** (Major Update)
   - Added `LogQueryRequest` model
   - Added `AIChatRequest` model
   - Added `/query-logs` endpoint
   - Added `/ai-chat` endpoint
   - Lines: 350 (added ~140 lines)

---

## 🔧 How It Works

### Log Querying Flow:
```
User clicks template (e.g., "File Ingestion")
    ↓
Template fills in: service="carrier-files-worker", message_type="ProcessSuperFilesTask"
    ↓
User enters load ID (e.g., 618171104)
    ↓
Frontend sends POST to /api/v1/query-logs
    ↓
Backend queries ClickHouse with:
  - Service name filter
  - Message type + identifier search
  - Date range (last N days)
    ↓
Returns up to 50 log entries
    ↓
UI displays with syntax highlighting and severity badges
```

### AI Chat Flow:
```
User types question (e.g., "What logs should I check?")
    ↓
Frontend sends POST to /api/v1/ai-chat with:
  - User message
  - Load ID
  - Investigation context (hypotheses, evidence, result)
    ↓
Backend builds context from current investigation
    ↓
LLM (Claude Sonnet 4.5) analyzes with RCA-specific system prompt
    ↓
Returns actionable response referencing:
  - TL/FTL processing stages
  - Specific services to query
  - Recommended actions
    ↓
UI displays in chat format with timestamp
```

---

## 🎬 Example Usage Scenarios

### Scenario 1: Ops Investigates "Awaiting Tracking Info"

1. **Investigation Tab**: Run investigation on Load ID 618171104
   - See hypothesis: "Asset assignment failure - Truck/Trailer missing"
   - Confidence: 85%
   - Evidence: "PROCESS_TRUCK_RECORD shows TruckNumber is null"

2. **Logs & Queries Tab**: Click "Asset Assignment" template
   - Auto-fills: service=carrier-files-worker, message=PROCESS_TRUCK_RECORD
   - Enter load ID: 618171104
   - Query logs → See actual PROCESS_TRUCK_RECORD entry with null asset info

3. **AI Assistant Tab**: Ask "How do I fix this issue?"
   - AI Response: "Contact carrier (J B Hunt) to update their EDI file to include Truck and Trailer numbers. Alternatively, enable ELD integration if carrier uses KeepTruckin."

---

### Scenario 2: Support Investigates File Processing Error

1. **Investigation Tab**: Investigation shows "File ingestion error"

2. **Logs & Queries Tab**:
   - Click "File Ingestion" template
   - Query shows ProcessSuperFilesTask with parsing error
   - See actual malformed CSV data in logs

3. **AI Assistant Tab**: Ask "What are the key findings?"
   - AI Response: "The carrier file format doesn't match the configured parser. Check if carrier recently changed their file structure. Review carrier configuration in Network Admin."

---

## 🚀 Ready to Use

### Both Servers Running:
- ✅ Backend: http://localhost:8080 (with new endpoints)
- ✅ Frontend: http://localhost:3000 (with 3-tab UI)

### New API Endpoints:
1. **POST /api/v1/query-logs**
   ```json
   {
     "service": "carrier-files-worker",
     "message_type": "ProcessSuperFilesTask",
     "identifier": "618171104",
     "days_back": 7
   }
   ```

2. **POST /api/v1/ai-chat**
   ```json
   {
     "message": "What logs should I check?",
     "load_id": "618171104",
     "context": {
       "hypotheses": [...],
       "evidence_count": 12,
       "result": {...}
     }
   }
   ```

---

## 💡 Key Features for Ops Teams

### 1. **Quick Templates**
No need to remember service names or message types - just click the template for the processing stage you want to investigate.

### 2. **Context-Aware AI**
The AI assistant knows what you're investigating. It automatically includes:
- The hypotheses being tested
- Evidence collected so far
- Root cause determination (if complete)

### 3. **Real-time Investigation Visibility**
Watch sub-agents work in parallel, see their reasoning, and track confidence updates as evidence is collected.

### 4. **Direct Log Access**
Query production logs directly from the UI without switching to SigNoz or ClickHouse.

### 5. **Actionable Recommendations**
AI provides specific next steps referencing:
- Exact service names to query
- TL/FTL processing stages to investigate
- Teams/systems to contact
- Configuration changes to make

---

## 🎨 UI/UX Highlights

### Color Coding:
- **Investigation Tab**: Blue accent (FourKites blue)
- **Logs Tab**: Teal accent (FourKites teal)
- **AI Assistant Tab**: Purple accent

### Badge System:
- 🟢 Confirmed (green)
- 🔵 Investigating (blue)
- ⚪ Eliminated (gray)
- 🔴 ERROR severity (red)
- 🟡 WARN severity (yellow)

### Responsive Design:
- Mobile-friendly layout
- Scrollable log results (max 600px)
- Expandable sub-agent cards
- Auto-scroll for logs and chat

---

## 📊 Technical Implementation

### Frontend Stack:
- Next.js 15 App Router
- React 19
- TypeScript
- Tailwind CSS
- Lucide React icons

### Backend Stack:
- FastAPI
- ClickHouse integration
- LLM (Claude Sonnet 4.5)
- Async/await pattern

### Real-time Features:
- SSE (Server-Sent Events) for investigation streaming
- Auto-updating hypothesis cards
- Live confidence tracking
- Streaming logs

---

## 🎯 What This Solves

### Before:
- ❌ Ops had to switch between tools (UI, SigNoz, ClickHouse)
- ❌ No visibility into sub-agent reasoning
- ❌ Manual log queries requiring knowledge of service names
- ❌ No AI assistance for interpreting results

### After:
- ✅ All-in-one interface for investigation + logs + AI help
- ✅ See exactly how sub-agents reach consensus
- ✅ One-click log templates for common queries
- ✅ Context-aware AI that answers "What should I do next?"

---

## 🔍 Next Steps (Optional Enhancements)

1. **Log Export**: Add "Download as CSV" for log results
2. **Saved Queries**: Let users save custom log queries
3. **Chat History**: Persist chat conversations per load ID
4. **Sub-Agent Visualization**: Add flowchart showing sub-agent interactions
5. **Metrics Dashboard**: Show RCA performance metrics (avg confidence, evidence count)

---

## ✅ Deployment Checklist

- [x] Frontend updated with 3-tab interface
- [x] Backend endpoints for log query and AI chat
- [x] Auto-reload enabled for both servers
- [x] Badge styles for all severity levels
- [x] TL/FTL templates integrated
- [x] Context-aware AI prompting
- [x] Error handling for all new features
- [x] Responsive design tested
- [x] Documentation complete

---

## 🎉 Summary

The Auto-RCA UI is now **fully optimized for operations and support teams** with:

1. **Real-time sub-agent visibility** - Watch the investigation happen, see reasoning and evidence
2. **Integrated log querying** - Query production logs without leaving the UI
3. **AI-powered assistance** - Get context-aware help interpreting results and planning next steps

The system provides a **world-class debugging experience** that combines hypothesis-driven RCA, direct log access, and AI guidance in one seamless interface! 🚀
