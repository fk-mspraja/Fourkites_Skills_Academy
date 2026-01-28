# Recommended Cassie Agent Architecture - Mermaid Diagram

## Full Architecture Flow

```mermaid
flowchart TD
    Start([User Input: Support Case]) --> Cassie[Cassie Agent<br/>Intent Classification]

    Cassie --> Router[Category Router<br/>Selects Specialized Domain]

    Router --> Playbook[Playbook Executor<br/>Loads Domain-Specific Protocol]

    Playbook --> Parallel{Execute Diagnostic<br/>Checks in Parallel}

    Parallel --> Check1[Check 1:<br/>ELD Enabled?]
    Parallel --> Check2[Check 2:<br/>Asset Assigned?]
    Parallel --> Check3[Check 3:<br/>GPS Logs for Errors?]
    Parallel --> Check4[Check 4:<br/>Outlier Detection Logs?]

    Check1 --> Evidence[Evidence Collector<br/>Aggregates Diagnostic Results]
    Check2 --> Evidence
    Check3 --> Evidence
    Check4 --> Evidence

    Evidence --> Pattern[Pattern Matcher<br/>Against Skills Library]

    Pattern --> Confidence[Confidence Scorer<br/>Evaluates Evidence Strength]

    Confidence --> Decision{Confidence<br/>Score?}

    Decision -->|≥ 90%| AutoResolve[Auto-Response<br/>Draft for Human Approval]
    Decision -->|< 90%| ManualReview[Manual Review<br/>With Evidence Package]

    AutoResolve --> End1([Resolution])
    ManualReview --> End2([Escalation])

    style Cassie fill:#e3f2fd
    style Router fill:#e3f2fd
    style Playbook fill:#fff3cd
    style Parallel fill:#f1f8e9
    style Evidence fill:#f1f8e9
    style Pattern fill:#f1f8e9
    style Confidence fill:#f1f8e9
    style Decision fill:#ffe0b2
    style AutoResolve fill:#c8e6c9
    style ManualReview fill:#ffccbc
```

## Simplified View with Layers

```mermaid
flowchart TD
    subgraph Layer1[Classification Layer]
        Input[User Input] --> Cassie[Cassie Agent]
        Cassie --> Router[Category Router]
    end

    subgraph Layer2[Investigation Layer]
        Router --> Playbook[Playbook Executor]
        Playbook --> Diagnostics[Diagnostic Checks]
    end

    subgraph Layer3[Intelligence Layer]
        Diagnostics --> Evidence[Evidence Collector]
        Evidence --> Pattern[Pattern Matcher]
        Pattern --> Confidence[Confidence Scorer]
    end

    subgraph Layer4[Decision Layer]
        Confidence --> Decision{Confidence ≥ 90%?}
        Decision -->|Yes| Auto[Auto-Response]
        Decision -->|No| Manual[Manual Review]
    end

    Auto --> Resolution([Resolution])
    Manual --> Escalation([Escalation])

    style Layer1 fill:#e3f2fd,stroke:#2196f3,stroke-width:2px
    style Layer2 fill:#fff3cd,stroke:#ffc107,stroke-width:2px
    style Layer3 fill:#f1f8e9,stroke:#8bc34a,stroke-width:2px
    style Layer4 fill:#ffe0b2,stroke:#ff9800,stroke-width:2px
```

## Data Flow with MCPs

```mermaid
flowchart LR
    subgraph Investigation[Investigation Engine]
        Playbook[Playbook Executor]
        Checks[Diagnostic Checks]
        Playbook --> Checks
    end

    subgraph DataSources[Data Sources - MCPs]
        MCP1[(Redshift MCP<br/>Network Config, Logs)]
        MCP2[(Salesforce MCP<br/>Case History)]
        MCP3[(Knowledge MCP<br/>Documentation)]
        MCP4[(Support AI MCP<br/>FourKites APIs)]
        MCP5[(Atlassian MCP<br/>JIRA/Confluence)]
    end

    Checks -.Query.-> MCP1
    Checks -.Query.-> MCP2
    Checks -.Query.-> MCP3
    Checks -.Query.-> MCP4
    Checks -.Query.-> MCP5

    MCP1 -.Data.-> Evidence[Evidence Collector]
    MCP2 -.Data.-> Evidence
    MCP3 -.Data.-> Evidence
    MCP4 -.Data.-> Evidence
    MCP5 -.Data.-> Evidence

    Evidence --> Pattern[Pattern Matcher]
    Pattern --> Decision{Auto-Resolve?}

    style Investigation fill:#fff3cd,stroke:#ffc107,stroke-width:2px
    style DataSources fill:#e3f2fd,stroke:#2196f3,stroke-width:2px
```

## Component Responsibilities

```mermaid
graph TD
    subgraph Cassie[Cassie Agent]
        C1[Classification]
        C2[Routing]
    end

    subgraph PlaybookExec[Playbook Executor]
        P1[Load Protocol]
        P2[Orchestrate Checks]
        P3[Early Exit Logic]
    end

    subgraph MCPLayer[MCP Integration Layer]
        M1[Query Builder]
        M2[Result Parser]
        M3[Error Handler]
    end

    subgraph PatternEngine[Pattern Matching Engine]
        PM1[Pattern Library]
        PM2[Evidence Evaluator]
        PM3[Confidence Calculator]
    end

    subgraph ResponseGen[Response Generator]
        R1[Template Selector]
        R2[Variable Injection]
        R3[Quality Gate]
    end

    Cassie --> PlaybookExec
    PlaybookExec --> MCPLayer
    MCPLayer --> PatternEngine
    PatternEngine --> ResponseGen

    style Cassie fill:#e3f2fd
    style PlaybookExec fill:#fff3cd
    style MCPLayer fill:#f1f8e9
    style PatternEngine fill:#ffe0b2
    style ResponseGen fill:#c8e6c9
```

## Decision Flow Example - ELD Not Enabled

```mermaid
flowchart TD
    Start[Load Not Tracking Case] --> Cassie[Cassie: Classify as<br/>OTR_TRACKING_ISSUE]

    Cassie --> Load[Load OTR Tracking<br/>Playbook]

    Load --> Check1{Playbook Check 1:<br/>ELD Enabled at<br/>Network Level?}

    Check1 -->|Query Redshift| QueryDB[(Query: network_configurations<br/>WHERE shipper_id AND carrier_id)]

    QueryDB -->|eld_tracking_enabled = FALSE| Found[Root Cause Found:<br/>ELD Not Enabled<br/>Confidence: 100%]

    QueryDB -->|eld_tracking_enabled = TRUE| Check2{Playbook Check 2:<br/>Asset Assigned?}

    Found --> Draft[Draft Auto-Response:<br/>Enable ELD tracking in<br/>network configuration]

    Check2 -->|Query Redshift| QueryDB2[(Query: load_tracking<br/>WHERE load_id)]

    QueryDB2 -->|All NULL| Found2[Root Cause Found:<br/>No Asset Assigned<br/>Confidence: 100%]

    QueryDB2 -->|Values Present| Check3[Continue to<br/>Next Check...]

    Draft --> Approve{Human<br/>Approval?}

    Approve -->|Yes| Resolve([Auto-Resolved])
    Approve -->|No| Edit[Edit Response]
    Edit --> Resolve

    Found2 --> Draft2[Draft Auto-Response:<br/>Contact carrier to<br/>assign asset]

    style Start fill:#e3f2fd
    style Cassie fill:#e3f2fd
    style Load fill:#fff3cd
    style Check1 fill:#f1f8e9
    style Check2 fill:#f1f8e9
    style Found fill:#c8e6c9
    style Found2 fill:#c8e6c9
    style Draft fill:#c8e6c9
    style Draft2 fill:#c8e6c9
    style Resolve fill:#4caf50,color:#fff
```

---

## How to Use These Diagrams

**For Documentation:**
- Copy any diagram code block to your Markdown files
- GitHub, GitLab, and many doc tools render Mermaid automatically

**For Presentations:**
- Paste into https://mermaid.live to generate PNG/SVG
- Or use Mermaid plugins in VS Code, Notion, Confluence

**For Architecture Discussions:**
- Use "Simplified View with Layers" for high-level overview
- Use "Full Architecture Flow" for detailed technical discussion
- Use "Decision Flow Example" to walk through specific scenarios

---
