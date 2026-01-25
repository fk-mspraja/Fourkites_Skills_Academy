"use client";

import { useState, useRef, useEffect } from "react";
import Image from "next/image";
import {
  Search,
  Play,
  CheckCircle2,
  AlertCircle,
  Brain,
  Database,
  Network,
  Loader2,
  TrendingUp,
  TrendingDown,
  Minus,
  ChevronDown,
  ChevronRight,
  Terminal,
  MessageSquare,
  FileSearch,
  Code,
  Clock,
  Send,
} from "lucide-react";

type Hypothesis = {
  id: string;
  description: string;
  confidence: number;
  status: "active" | "confirmed" | "eliminated";
  evidence: Evidence[];
  agent_id?: string;
};

type Evidence = {
  finding: string;
  source: string;
  type?: string;
  agent_id?: string;
};

type AgentAction = {
  agent_id: string;
  iteration: number;
  action_type: string;
  source?: string;
  method?: string;
  reason: string;
};

type Step = {
  id: number;
  title: string;
  description: string;
  status: "pending" | "active" | "completed";
};

type LogQuery = {
  service: string;
  message_type: string;
  identifier: string;
  days_back: number;
};

type ChatMessage = {
  role: "user" | "assistant";
  content: string;
  timestamp: Date;
};

export default function InvestigationPage() {
  const [loadId, setLoadId] = useState("");
  const [investigating, setInvestigating] = useState(false);
  const [activeTab, setActiveTab] = useState<"investigation" | "logs" | "ai">("investigation");
  const [steps, setSteps] = useState<Step[]>([
    { id: 1, title: "Initializing", description: "Setting up investigation", status: "pending" },
    { id: 2, title: "Forming Hypotheses", description: "AI analyzing problem space", status: "pending" },
    { id: 3, title: "Running Sub-Agents", description: "Parallel investigation", status: "pending" },
    { id: 4, title: "Synthesizing Results", description: "Determining root cause", status: "pending" },
  ]);

  const [hypotheses, setHypotheses] = useState<Hypothesis[]>([]);
  const [agents, setAgents] = useState<Map<string, Hypothesis>>(new Map());
  const [agentActions, setAgentActions] = useState<AgentAction[]>([]);
  const [allEvidence, setAllEvidence] = useState<Evidence[]>([]);
  const [logs, setLogs] = useState<string[]>([]);
  const [result, setResult] = useState<any>(null);
  const [expandedAgent, setExpandedAgent] = useState<string | null>(null);

  // Log Query state
  const [logQuery, setLogQuery] = useState<LogQuery>({
    service: "carrier-files-worker",
    message_type: "ProcessSuperFilesTask",
    identifier: "",
    days_back: 7,
  });
  const [logResults, setLogResults] = useState<any[]>([]);
  const [loadingLogs, setLoadingLogs] = useState(false);

  // AI Chat state
  const [chatMessages, setChatMessages] = useState<ChatMessage[]>([]);
  const [chatInput, setChatInput] = useState("");
  const [sendingChat, setSendingChat] = useState(false);

  const logsEndRef = useRef<HTMLDivElement>(null);
  const chatEndRef = useRef<HTMLDivElement>(null);
  const abortControllerRef = useRef<AbortController | null>(null);

  const scrollToBottom = () => {
    logsEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [logs, agentActions]);

  const updateStep = (stepId: number, status: "active" | "completed") => {
    setSteps(prev =>
      prev.map(step =>
        step.id === stepId ? { ...step, status } : step
      )
    );
  };

  const startInvestigation = async () => {
    if (!loadId.trim()) return;

    // Reset state
    setInvestigating(true);
    setHypotheses([]);
    setAgents(new Map());
    setAgentActions([]);
    setAllEvidence([]);
    setLogs([]);
    setResult(null);
    setSteps(prev => prev.map(s => ({ ...s, status: "pending" })));

    // Create abort controller
    abortControllerRef.current = new AbortController();

    try {
      const response = await fetch("/api/v1/investigate", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ load_id: loadId, mode: "ocean" }),
        signal: abortControllerRef.current.signal,
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const reader = response.body?.getReader();
      const decoder = new TextDecoder();

      if (!reader) throw new Error("No reader available");

      let buffer = "";

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split("\n");
        buffer = lines.pop() || "";

        for (const line of lines) {
          if (!line.trim() || line.startsWith(":")) continue;

          if (line.startsWith("event:")) {
            const eventType = line.slice(6).trim();
            continue;
          }

          if (line.startsWith("data:")) {
            try {
              const data = JSON.parse(line.slice(5).trim());
              handleSSEEvent(data);
            } catch (e) {
              console.error("Failed to parse SSE data:", e);
            }
          }
        }
      }
    } catch (error: any) {
      if (error.name !== "AbortError") {
        console.error("Investigation error:", error);
        addLog(`❌ Error: ${error.message}`);
      }
    } finally {
      setInvestigating(false);
      abortControllerRef.current = null;
    }
  };

  const handleSSEEvent = (data: any) => {
    // Handle different event types based on data structure
    if (data.step !== undefined) {
      // Step event
      if (data.status) {
        updateStep(data.step, data.status);
      }
      if (data.title) {
        addLog(`📍 Step ${data.step}: ${data.title}`);
      }
    } else if (data.message) {
      // Log event
      addLog(`💬 ${data.message}`);
    } else if (data.description && data.root_cause_type) {
      // Hypothesis event
      const hyp: Hypothesis = {
        id: data.id || `hyp_${Date.now()}_${Math.random()}`,
        description: data.description,
        confidence: data.confidence || 0.5,
        status: data.status || "active",
        evidence: [],
      };
      setHypotheses(prev => {
        const exists = prev.find(h => h.id === hyp.id);
        if (exists) {
          return prev.map(h => h.id === hyp.id ? { ...h, ...hyp } : h);
        }
        return [...prev, hyp];
      });
      addLog(`💡 Hypothesis: ${data.description.slice(0, 60)}...`);
    } else if (data.agent_id && data.hypothesis) {
      // Agent spawned
      const agentHyp: Hypothesis = {
        id: data.agent_id,
        description: data.hypothesis,
        confidence: 0.5,
        status: "active",
        evidence: [],
        agent_id: data.agent_id,
      };
      setAgents(prev => new Map(prev).set(data.agent_id, agentHyp));
      addLog(`🤖 Agent spawned: ${data.agent_id}`);
    } else if (data.agent_id && data.action_type) {
      // Agent action
      setAgentActions(prev => [...prev, data as AgentAction]);
    } else if (data.finding) {
      // Evidence
      const ev: Evidence = {
        finding: data.finding,
        source: data.source || "unknown",
        type: data.type,
        agent_id: data.agent_id,
      };

      setAllEvidence(prev => [...prev, ev]);

      // Add to agent's evidence
      if (data.agent_id) {
        setAgents(prev => {
          const newMap = new Map(prev);
          const agent = newMap.get(data.agent_id);
          if (agent) {
            agent.evidence.push(ev);
            newMap.set(data.agent_id, { ...agent });
          }
          return newMap;
        });
      }

      addLog(`📊 Evidence: ${data.finding.slice(0, 50)}...`);
    } else if (data.id && data.confidence !== undefined) {
      // Hypothesis update
      setHypotheses(prev =>
        prev.map(h =>
          h.id === data.id
            ? { ...h, confidence: data.confidence, status: data.status || h.status }
            : h
        )
      );
      setAgents(prev => {
        if (prev.has(data.id)) {
          const agent = prev.get(data.id)!;
          return new Map(prev).set(data.id, {
            ...agent,
            confidence: data.confidence,
            status: data.status || agent.status,
          });
        }
        return prev;
      });
    } else if (data.root_cause !== undefined) {
      // Final result
      setResult(data);
      updateStep(4, "completed");
      addLog(`✅ Investigation complete: ${data.root_cause || "Unknown"}`);
    } else if (data.investigation_id) {
      // Complete event
      addLog(`🎉 Completed: ${data.investigation_id}`);
    }
  };

  const addLog = (message: string) => {
    setLogs(prev => [...prev, `[${new Date().toLocaleTimeString()}] ${message}`]);
  };

  const stopInvestigation = () => {
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
      setInvestigating(false);
      addLog("🛑 Investigation stopped by user");
    }
  };

  const getConfidenceColor = (confidence: number) => {
    if (confidence >= 0.7) return "text-green-400";
    if (confidence >= 0.4) return "text-yellow-400";
    return "text-red-400";
  };

  const getStatusBadge = (status: string) => {
    switch (status) {
      case "confirmed":
        return <span className="badge badge-green">Confirmed</span>;
      case "eliminated":
        return <span className="badge badge-gray">Eliminated</span>;
      case "active":
        return <span className="badge badge-blue">Investigating</span>;
      default:
        return <span className="badge badge-gray">{status}</span>;
    }
  };

  const queryLogs = async () => {
    if (!logQuery.identifier.trim()) return;

    setLoadingLogs(true);
    try {
      const response = await fetch("/api/v1/query-logs", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(logQuery),
      });

      if (!response.ok) throw new Error("Failed to query logs");

      const data = await response.json();
      setLogResults(data.logs || []);
    } catch (error: any) {
      console.error("Log query error:", error);
      setLogResults([]);
    } finally {
      setLoadingLogs(false);
    }
  };

  const sendChatMessage = async () => {
    if (!chatInput.trim()) return;

    const userMessage: ChatMessage = {
      role: "user",
      content: chatInput,
      timestamp: new Date(),
    };

    setChatMessages(prev => [...prev, userMessage]);
    setChatInput("");
    setSendingChat(true);

    try {
      const response = await fetch("/api/v1/ai-chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          message: chatInput,
          load_id: loadId,
          context: {
            hypotheses: hypotheses.map(h => ({ description: h.description, confidence: h.confidence })),
            evidence_count: allEvidence.length,
            result: result,
          },
        }),
      });

      if (!response.ok) throw new Error("Failed to send message");

      const data = await response.json();
      const assistantMessage: ChatMessage = {
        role: "assistant",
        content: data.response,
        timestamp: new Date(),
      };

      setChatMessages(prev => [...prev, assistantMessage]);
    } catch (error: any) {
      console.error("Chat error:", error);
      const errorMessage: ChatMessage = {
        role: "assistant",
        content: `Error: ${error.message}`,
        timestamp: new Date(),
      };
      setChatMessages(prev => [...prev, errorMessage]);
    } finally {
      setSendingChat(false);
    }
  };

  const applyLogTemplate = (template: string) => {
    const templates: Record<string, Partial<LogQuery>> = {
      file_ingestion: {
        service: "carrier-files-worker",
        message_type: "ProcessSuperFilesTask",
      },
      data_mapping: {
        service: "carrier-files-worker",
        message_type: "PROCESS_SUPER_RECORD",
      },
      asset_assignment: {
        service: "carrier-files-worker",
        message_type: "PROCESS_TRUCK_RECORD",
      },
      location_processing: {
        service: "global-worker-ex",
        message_type: "PROCESS_TRUCK_LOCATION",
      },
      location_validation: {
        service: "location-worker",
        message_type: "PROCESS_NEW_LOCATION",
      },
      eld_integration: {
        service: "cfw-eld-data",
        message_type: "FETCH_ELD_LOCATION",
      },
    };

    const templateData = templates[template];
    if (templateData) {
      setLogQuery(prev => ({ ...prev, ...templateData }));
    }
  };

  return (
    <div className="min-h-screen p-6">
      {/* Header */}
      <header className="mb-8">
        <div className="flex items-center justify-between max-w-7xl mx-auto">
          <div className="flex items-center space-x-4">
            <div className="flex items-center space-x-6">
              <Image
                src="/fourkites-logo.png"
                alt="FourKites"
                width={200}
                height={50}
                priority
                className="h-12 w-auto"
              />
              <div className="border-l border-gray-700 pl-6">
                <h1 className="text-2xl font-bold text-white">Auto-RCA</h1>
                <p className="text-sm text-gray-400">Intelligent Root Cause Analysis</p>
              </div>
            </div>
          </div>
          <div className="flex items-center space-x-2 text-gray-400">
            <Brain className="w-5 h-5" />
            <span className="text-sm">v2.0 • Hypothesis-Driven</span>
          </div>
        </div>
      </header>

      <div className="max-w-7xl mx-auto space-y-6">
        {/* Search Bar */}
        <div className="card p-6">
          <div className="flex space-x-4">
            <div className="flex-1 relative">
              <Search className="absolute left-4 top-1/2 transform -translate-y-1/2 w-5 h-5 text-gray-400" />
              <input
                type="text"
                value={loadId}
                onChange={(e) => setLoadId(e.target.value)}
                onKeyDown={(e) => e.key === "Enter" && !investigating && startInvestigation()}
                placeholder="Enter Load ID (e.g., 618171104)"
                className="w-full pl-12 pr-4 py-3 bg-gray-800 border border-gray-700 rounded-lg text-white placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-fourkites-blue"
                disabled={investigating}
              />
            </div>
            {!investigating ? (
              <button
                onClick={startInvestigation}
                disabled={!loadId.trim()}
                className="px-6 py-3 bg-fourkites-blue hover:bg-fourkites-blue/90 disabled:bg-gray-700 disabled:text-gray-500 text-white rounded-lg font-semibold flex items-center space-x-2 transition-all"
              >
                <Play className="w-5 h-5" />
                <span>Investigate</span>
              </button>
            ) : (
              <button
                onClick={stopInvestigation}
                className="px-6 py-3 bg-red-600 hover:bg-red-700 text-white rounded-lg font-semibold flex items-center space-x-2 transition-all"
              >
                <AlertCircle className="w-5 h-5" />
                <span>Stop</span>
              </button>
            )}
          </div>
        </div>

        {/* Tabs */}
        <div className="card">
          <div className="flex border-b border-gray-800">
            <button
              onClick={() => setActiveTab("investigation")}
              className={`flex-1 px-6 py-4 font-semibold transition-all ${
                activeTab === "investigation"
                  ? "text-fourkites-blue border-b-2 border-fourkites-blue bg-fourkites-blue/5"
                  : "text-gray-400 hover:text-gray-300"
              }`}
            >
              <div className="flex items-center justify-center space-x-2">
                <Brain className="w-5 h-5" />
                <span>Investigation</span>
              </div>
            </button>
            <button
              onClick={() => setActiveTab("logs")}
              className={`flex-1 px-6 py-4 font-semibold transition-all ${
                activeTab === "logs"
                  ? "text-fourkites-teal border-b-2 border-fourkites-teal bg-fourkites-teal/5"
                  : "text-gray-400 hover:text-gray-300"
              }`}
            >
              <div className="flex items-center justify-center space-x-2">
                <Terminal className="w-5 h-5" />
                <span>Logs & Queries</span>
              </div>
            </button>
            <button
              onClick={() => setActiveTab("ai")}
              className={`flex-1 px-6 py-4 font-semibold transition-all ${
                activeTab === "ai"
                  ? "text-purple-400 border-b-2 border-purple-400 bg-purple-400/5"
                  : "text-gray-400 hover:text-gray-300"
              }`}
            >
              <div className="flex items-center justify-center space-x-2">
                <MessageSquare className="w-5 h-5" />
                <span>AI Assistant</span>
              </div>
            </button>
          </div>
        </div>

        {/* Tab Content: Investigation */}
        {activeTab === "investigation" && (
          <>
            {/* Progress Steps */}
            {investigating && (
              <div className="card p-6">
            <div className="flex items-center justify-between">
              {steps.map((step, idx) => (
                <div key={step.id} className="flex items-center flex-1">
                  <div className="flex flex-col items-center">
                    <div
                      className={`w-12 h-12 rounded-full flex items-center justify-center transition-all ${
                        step.status === "completed"
                          ? "bg-green-500/20 border-2 border-green-500"
                          : step.status === "active"
                          ? "bg-fourkites-blue/20 border-2 border-fourkites-blue animate-pulse"
                          : "bg-gray-800 border-2 border-gray-700"
                      }`}
                    >
                      {step.status === "completed" ? (
                        <CheckCircle2 className="w-6 h-6 text-green-400" />
                      ) : step.status === "active" ? (
                        <Loader2 className="w-6 h-6 text-fourkites-blue animate-spin" />
                      ) : (
                        <span className="text-gray-500 font-semibold">{step.id}</span>
                      )}
                    </div>
                    <div className="mt-2 text-center">
                      <p className="text-sm font-medium text-white">{step.title}</p>
                      <p className="text-xs text-gray-500">{step.description}</p>
                    </div>
                  </div>
                  {idx < steps.length - 1 && (
                    <div
                      className={`flex-1 h-1 mx-4 transition-all ${
                        steps[idx + 1].status !== "pending"
                          ? "bg-gradient-to-r from-fourkites-blue to-fourkites-teal"
                          : "bg-gray-800"
                      }`}
                    />
                  )}
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Hypotheses & Sub-Agents */}
        {agents.size > 0 && (
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {Array.from(agents.values()).map((agent) => {
              const isExpanded = expandedAgent === agent.id;
              const agentActionsForAgent = agentActions.filter(a => a.agent_id === agent.id);

              return (
                <div key={agent.id} className="card p-6">
                  <div
                    className="flex items-start justify-between cursor-pointer"
                    onClick={() => setExpandedAgent(isExpanded ? null : agent.id)}
                  >
                    <div className="flex-1">
                      <div className="flex items-center space-x-2 mb-2">
                        <Database className="w-5 h-5 text-fourkites-teal" />
                        <h3 className="font-semibold text-white">{agent.agent_id}</h3>
                        {getStatusBadge(agent.status)}
                      </div>
                      <p className="text-sm text-gray-400 mb-3">{agent.description}</p>

                      {/* Confidence Bar */}
                      <div className="mb-3">
                        <div className="flex items-center justify-between mb-1">
                          <span className="text-xs text-gray-500">Confidence</span>
                          <span className={`text-sm font-semibold ${getConfidenceColor(agent.confidence)}`}>
                            {(agent.confidence * 100).toFixed(0)}%
                          </span>
                        </div>
                        <div className="w-full h-2 bg-gray-800 rounded-full overflow-hidden">
                          <div
                            className="h-full bg-gradient-to-r from-fourkites-blue to-fourkites-teal transition-all duration-500"
                            style={{ width: `${agent.confidence * 100}%` }}
                          />
                        </div>
                      </div>

                      <div className="flex items-center justify-between text-xs text-gray-500">
                        <span>{agent.evidence.length} evidence</span>
                        <span>{agentActionsForAgent.length} actions</span>
                      </div>
                    </div>
                    {isExpanded ? (
                      <ChevronDown className="w-5 h-5 text-gray-400" />
                    ) : (
                      <ChevronRight className="w-5 h-5 text-gray-400" />
                    )}
                  </div>

                  {/* Expanded Details */}
                  {isExpanded && (
                    <div className="mt-4 space-y-3 border-t border-gray-800 pt-4">
                      {/* Actions */}
                      {agentActionsForAgent.length > 0 && (
                        <div>
                          <h4 className="text-xs font-semibold text-gray-400 mb-2">Actions</h4>
                          <div className="space-y-2">
                            {agentActionsForAgent.map((action, idx) => (
                              <div key={idx} className="bg-gray-800/50 p-2 rounded text-xs">
                                <div className="flex items-center space-x-2 mb-1">
                                  <span className="badge badge-blue">{action.action_type}</span>
                                  {action.source && (
                                    <span className="text-fourkites-teal">{action.source}.{action.method}</span>
                                  )}
                                </div>
                                <p className="text-gray-400">{action.reason}</p>
                              </div>
                            ))}
                          </div>
                        </div>
                      )}

                      {/* Evidence */}
                      {agent.evidence.length > 0 && (
                        <div>
                          <h4 className="text-xs font-semibold text-gray-400 mb-2">Evidence</h4>
                          <div className="space-y-2">
                            {agent.evidence.map((ev, idx) => (
                              <div key={idx} className="bg-gray-800/50 p-2 rounded text-xs">
                                <div className="flex items-center space-x-2 mb-1">
                                  <span className="badge badge-teal">{ev.source}</span>
                                </div>
                                <p className="text-gray-300">{ev.finding}</p>
                              </div>
                            ))}
                          </div>
                        </div>
                      )}
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        )}

        {/* Final Result */}
        {result && (
          <div className="card p-6 border-2 border-green-500/50">
            <div className="flex items-start space-x-4">
              <div className="w-12 h-12 bg-green-500/20 rounded-full flex items-center justify-center flex-shrink-0">
                <CheckCircle2 className="w-7 h-7 text-green-400" />
              </div>
              <div className="flex-1">
                <h2 className="text-xl font-bold text-white mb-2">Root Cause Identified</h2>
                <div className="space-y-3">
                  <div>
                    <span className="text-sm text-gray-400">Root Cause:</span>
                    <p className="text-lg text-white font-semibold mt-1">
                      {result.root_cause || "Unknown"}
                    </p>
                  </div>
                  {result.category && (
                    <div>
                      <span className="text-sm text-gray-400">Category:</span>
                      <p className="mt-1">
                        <span className="badge badge-blue">{result.category}</span>
                      </p>
                    </div>
                  )}
                  <div className="grid grid-cols-3 gap-4 pt-3 border-t border-gray-800">
                    <div>
                      <span className="text-xs text-gray-500">Confidence</span>
                      <p className={`text-2xl font-bold ${getConfidenceColor(result.confidence)}`}>
                        {(result.confidence * 100).toFixed(0)}%
                      </p>
                    </div>
                    <div>
                      <span className="text-xs text-gray-500">Evidence</span>
                      <p className="text-2xl font-bold text-fourkites-teal">
                        {result.evidence_count || 0}
                      </p>
                    </div>
                    <div>
                      <span className="text-xs text-gray-500">Duration</span>
                      <p className="text-2xl font-bold text-fourkites-blue">
                        {result.duration?.toFixed(1)}s
                      </p>
                    </div>
                  </div>
                  {result.action && (
                    <div className="mt-4 bg-fourkites-blue/10 border border-fourkites-blue/30 rounded-lg p-4">
                      <h3 className="text-sm font-semibold text-fourkites-blue mb-2">
                        Recommended Action
                      </h3>
                      <p className="text-gray-300">{result.action}</p>
                    </div>
                  )}
                </div>
              </div>
            </div>
          </div>
        )}

            {/* Logs */}
            {logs.length > 0 && (
              <div className="card p-6">
                <h3 className="text-lg font-semibold text-white mb-4 flex items-center space-x-2">
                  <Brain className="w-5 h-5 text-fourkites-blue" />
                  <span>Investigation Logs</span>
                </h3>
                <div className="bg-gray-950/50 rounded-lg p-4 max-h-64 overflow-y-auto font-mono text-xs space-y-1">
                  {logs.map((log, idx) => (
                    <div key={idx} className="text-gray-400">
                      {log}
                    </div>
                  ))}
                  <div ref={logsEndRef} />
                </div>
              </div>
            )}
          </>
        )}

        {/* Tab Content: Logs & Queries */}
        {activeTab === "logs" && (
          <div className="space-y-6">
            <div className="card p-6">
              <h2 className="text-xl font-bold text-white mb-6 flex items-center space-x-2">
                <FileSearch className="w-6 h-6 text-fourkites-teal" />
                <span>SigNoz Log Query</span>
              </h2>

              {/* Query Templates */}
              <div className="mb-6">
                <h3 className="text-sm font-semibold text-gray-400 mb-3">Quick Templates (TL/FTL Processing)</h3>
                <div className="grid grid-cols-2 md:grid-cols-3 gap-3">
                  {[
                    { id: "file_ingestion", label: "File Ingestion", icon: "📁" },
                    { id: "data_mapping", label: "Data Mapping", icon: "🗺️" },
                    { id: "asset_assignment", label: "Asset Assignment", icon: "🚚" },
                    { id: "location_processing", label: "Location Processing", icon: "📍" },
                    { id: "location_validation", label: "Location Validation", icon: "✅" },
                    { id: "eld_integration", label: "ELD Integration", icon: "📡" },
                  ].map(template => (
                    <button
                      key={template.id}
                      onClick={() => applyLogTemplate(template.id)}
                      className="px-4 py-3 bg-gray-800 hover:bg-gray-700 border border-gray-700 hover:border-fourkites-teal rounded-lg text-left transition-all"
                    >
                      <div className="flex items-center space-x-2">
                        <span className="text-xl">{template.icon}</span>
                        <span className="text-sm text-white font-medium">{template.label}</span>
                      </div>
                    </button>
                  ))}
                </div>
              </div>

              {/* Query Form */}
              <div className="grid grid-cols-2 gap-4 mb-4">
                <div>
                  <label className="block text-sm font-medium text-gray-400 mb-2">Service Name</label>
                  <select
                    value={logQuery.service}
                    onChange={(e) => setLogQuery(prev => ({ ...prev, service: e.target.value }))}
                    className="w-full px-4 py-2 bg-gray-800 border border-gray-700 rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-fourkites-teal"
                  >
                    <option value="carrier-files-worker">carrier-files-worker</option>
                    <option value="global-worker-ex">global-worker-ex</option>
                    <option value="location-worker">location-worker</option>
                    <option value="cfw-eld-data">cfw-eld-data</option>
                    <option value="global-worker-tracking">global-worker-tracking</option>
                  </select>
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-400 mb-2">Message Type</label>
                  <input
                    type="text"
                    value={logQuery.message_type}
                    onChange={(e) => setLogQuery(prev => ({ ...prev, message_type: e.target.value }))}
                    placeholder="e.g., ProcessSuperFilesTask"
                    className="w-full px-4 py-2 bg-gray-800 border border-gray-700 rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-fourkites-teal"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-400 mb-2">Load/Tracking ID</label>
                  <input
                    type="text"
                    value={logQuery.identifier}
                    onChange={(e) => setLogQuery(prev => ({ ...prev, identifier: e.target.value }))}
                    placeholder={loadId || "e.g., 618171104"}
                    className="w-full px-4 py-2 bg-gray-800 border border-gray-700 rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-fourkites-teal"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-400 mb-2">Days Back</label>
                  <input
                    type="number"
                    value={logQuery.days_back}
                    onChange={(e) => setLogQuery(prev => ({ ...prev, days_back: parseInt(e.target.value) || 7 }))}
                    min="1"
                    max="30"
                    className="w-full px-4 py-2 bg-gray-800 border border-gray-700 rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-fourkites-teal"
                  />
                </div>
              </div>

              <button
                onClick={queryLogs}
                disabled={loadingLogs || !logQuery.identifier}
                className="w-full px-6 py-3 bg-fourkites-teal hover:bg-fourkites-teal/90 disabled:bg-gray-700 disabled:text-gray-500 text-white rounded-lg font-semibold flex items-center justify-center space-x-2 transition-all"
              >
                {loadingLogs ? (
                  <>
                    <Loader2 className="w-5 h-5 animate-spin" />
                    <span>Querying...</span>
                  </>
                ) : (
                  <>
                    <Code className="w-5 h-5" />
                    <span>Query Logs</span>
                  </>
                )}
              </button>
            </div>

            {/* Log Results */}
            {logResults.length > 0 && (
              <div className="card p-6">
                <h3 className="text-lg font-semibold text-white mb-4 flex items-center justify-between">
                  <div className="flex items-center space-x-2">
                    <Terminal className="w-5 h-5 text-fourkites-teal" />
                    <span>Results ({logResults.length})</span>
                  </div>
                  <span className="badge badge-teal">{logQuery.service}</span>
                </h3>
                <div className="space-y-3 max-h-[600px] overflow-y-auto">
                  {logResults.map((log, idx) => (
                    <div key={idx} className="bg-gray-800/50 rounded-lg p-4 border border-gray-700">
                      <div className="flex items-center justify-between mb-2">
                        <span className="text-xs font-mono text-gray-500">
                          {log.timestamp || log.time || "No timestamp"}
                        </span>
                        {log.severity && (
                          <span className={`badge ${
                            log.severity === "ERROR" ? "badge-red" :
                            log.severity === "WARN" ? "badge-yellow" :
                            "badge-gray"
                          }`}>
                            {log.severity}
                          </span>
                        )}
                      </div>
                      <pre className="text-xs font-mono text-gray-300 whitespace-pre-wrap break-words">
                        {typeof log.body === "string" ? log.body : JSON.stringify(log, null, 2)}
                      </pre>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        )}

        {/* Tab Content: AI Assistant */}
        {activeTab === "ai" && (
          <div className="space-y-6">
            <div className="card p-6">
              <h2 className="text-xl font-bold text-white mb-6 flex items-center space-x-2">
                <MessageSquare className="w-6 h-6 text-purple-400" />
                <span>AI-Powered RCA Assistant</span>
              </h2>

              {/* Chat Messages */}
              <div className="bg-gray-950/50 rounded-lg p-4 mb-4 h-[500px] overflow-y-auto space-y-4">
                {chatMessages.length === 0 && (
                  <div className="text-center text-gray-500 py-12">
                    <Brain className="w-12 h-12 mx-auto mb-4 text-purple-400/50" />
                    <p className="text-sm">Ask me anything about the investigation, logs, or RCA!</p>
                    <div className="mt-6 grid grid-cols-2 gap-3 text-left">
                      {[
                        "What are the key findings?",
                        "Explain the root cause",
                        "What logs should I check?",
                        "How do I fix this issue?",
                      ].map((suggestion, idx) => (
                        <button
                          key={idx}
                          onClick={() => setChatInput(suggestion)}
                          className="px-4 py-3 bg-gray-800 hover:bg-gray-700 border border-gray-700 rounded-lg text-sm text-gray-300 transition-all"
                        >
                          {suggestion}
                        </button>
                      ))}
                    </div>
                  </div>
                )}
                {chatMessages.map((msg, idx) => (
                  <div
                    key={idx}
                    className={`flex ${msg.role === "user" ? "justify-end" : "justify-start"}`}
                  >
                    <div
                      className={`max-w-[80%] rounded-lg px-4 py-3 ${
                        msg.role === "user"
                          ? "bg-fourkites-blue text-white"
                          : "bg-gray-800 text-gray-300 border border-gray-700"
                      }`}
                    >
                      <div className="flex items-start space-x-2">
                        {msg.role === "assistant" && (
                          <Brain className="w-5 h-5 text-purple-400 flex-shrink-0 mt-0.5" />
                        )}
                        <div className="flex-1">
                          <p className="text-sm whitespace-pre-wrap">{msg.content}</p>
                          <p className="text-xs opacity-60 mt-1">
                            {msg.timestamp.toLocaleTimeString()}
                          </p>
                        </div>
                      </div>
                    </div>
                  </div>
                ))}
                <div ref={chatEndRef} />
              </div>

              {/* Chat Input */}
              <div className="flex space-x-3">
                <input
                  type="text"
                  value={chatInput}
                  onChange={(e) => setChatInput(e.target.value)}
                  onKeyDown={(e) => e.key === "Enter" && !sendingChat && sendChatMessage()}
                  placeholder="Ask about the investigation, logs, or how to fix the issue..."
                  className="flex-1 px-4 py-3 bg-gray-800 border border-gray-700 rounded-lg text-white placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-purple-400"
                  disabled={sendingChat}
                />
                <button
                  onClick={sendChatMessage}
                  disabled={sendingChat || !chatInput.trim()}
                  className="px-6 py-3 bg-purple-500 hover:bg-purple-600 disabled:bg-gray-700 disabled:text-gray-500 text-white rounded-lg font-semibold flex items-center space-x-2 transition-all"
                >
                  {sendingChat ? (
                    <Loader2 className="w-5 h-5 animate-spin" />
                  ) : (
                    <Send className="w-5 h-5" />
                  )}
                </button>
              </div>

              {/* Context Info */}
              {loadId && (
                <div className="mt-4 p-3 bg-purple-400/10 border border-purple-400/30 rounded-lg">
                  <div className="flex items-center space-x-2 text-xs text-purple-400">
                    <Clock className="w-4 h-4" />
                    <span>
                      Context: Load ID {loadId} • {hypotheses.length} hypotheses • {allEvidence.length} evidence
                    </span>
                  </div>
                </div>
              )}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
