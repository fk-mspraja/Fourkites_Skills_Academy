# Architecture with Skills Library Layer

## Complete Architecture with Skills Library

```mermaid
flowchart TD
    Start([User Input: Support Case]) --> Cassie[Cassie Agent<br/>Intent Classification]

    Cassie --> Router[Category Router<br/>Selects Domain]

    Router --> SkillsLib[(Skills Library<br/>Reusable Diagnostic Patterns)]

    SkillsLib --> LoadPlaybook[Load Domain-Specific<br/>Playbook from Skills]

    LoadPlaybook --> Playbook[Playbook Executor<br/>Execute Protocol]

    Playbook --> Parallel{Diagnostic Checks<br/>in Parallel}

    Parallel --> Check1[ELD Config Check]
    Parallel --> Check2[Asset Assignment Check]
    Parallel --> Check3[Log Analysis Check]
    Parallel --> Check4[Data Quality Check]

    Check1 --> Evidence[Evidence Collector]
    Check2 --> Evidence
    Check3 --> Evidence
    Check4 --> Evidence

    Evidence --> SkillsLib
    SkillsLib --> Pattern[Pattern Matcher<br/>Match Against Skills]

    Pattern --> Confidence[Confidence Scorer<br/>Evaluate Evidence]

    Confidence --> Decision{Confidence ≥ 90%?}

    Decision -->|Yes| SkillsLib
    SkillsLib --> AutoResponse[Auto-Response Generator<br/>Use Template from Skills]

    Decision -->|No| ManualReview[Manual Review<br/>With Evidence]

    AutoResponse --> End1([Resolution])
    ManualReview --> End2([Escalation])

    style Cassie fill:#e3f2fd
    style Router fill:#e3f2fd
    style SkillsLib fill:#f3e5f5,stroke:#9c27b0,stroke-width:3px
    style LoadPlaybook fill:#fff3cd
    style Playbook fill:#fff3cd
    style Evidence fill:#f1f8e9
    style Pattern fill:#f1f8e9
    style Confidence fill:#f1f8e9
    style Decision fill:#ffe0b2
    style AutoResponse fill:#c8e6c9
    style ManualReview fill:#ffccbc
```

## 5-Layer Architecture View

```mermaid
flowchart TD
    subgraph Layer1[Layer 1: Classification & Routing]
        Input[User Input] --> Cassie[Cassie Agent]
        Cassie --> Router[Category Router]
    end

    subgraph Layer2[Layer 2: Skills Library - Knowledge Layer]
        Router --> Skills[(Skills Library<br/>100+ Diagnostic Patterns<br/>Playbooks, Templates, Rules)]
        Skills --> LoadPlaybook[Playbook Selector]
    end

    subgraph Layer3[Layer 3: Investigation Execution]
        LoadPlaybook --> Executor[Playbook Executor]
        Executor --> Diagnostics[Diagnostic Checks<br/>Query MCPs]
    end

    subgraph Layer4[Layer 4: Intelligence & Pattern Matching]
        Diagnostics --> Evidence[Evidence Aggregation]
        Evidence --> Skills
        Skills --> Matcher[Pattern Matcher]
        Matcher --> Confidence[Confidence Scorer]
    end

    subgraph Layer5[Layer 5: Decision & Response]
        Confidence --> Decision{Confidence ≥ 90%?}
        Decision -->|Yes| Skills
        Skills --> AutoGen[Auto-Response Generator]
        Decision -->|No| Manual[Manual Review]
    end

    AutoGen --> Resolution([Resolution])
    Manual --> Escalation([Escalation])

    style Layer1 fill:#e3f2fd,stroke:#2196f3,stroke-width:2px
    style Layer2 fill:#f3e5f5,stroke:#9c27b0,stroke-width:3px
    style Layer3 fill:#fff3cd,stroke:#ffc107,stroke-width:2px
    style Layer4 fill:#f1f8e9,stroke:#8bc34a,stroke-width:2px
    style Layer5 fill:#ffe0b2,stroke:#ff9800,stroke-width:2px
```

## Skills Library Architecture Detail

```mermaid
graph TD
    subgraph SkillsLibrary[Skills Library - Central Knowledge Repository]
        Taxonomy[Category Taxonomy<br/>100+ Patterns]
        Playbooks[Diagnostic Playbooks<br/>Step-by-Step Protocols]
        Templates[Response Templates<br/>Auto-Resolution Text]
        Rules[Evidence Rules<br/>Confidence Scoring]
        Feasibility[Bot Feasibility Ratings<br/>HIGH/MEDIUM/LOW]
    end

    subgraph Consumers[Components Using Skills]
        Router[Category Router]
        Executor[Playbook Executor]
        Matcher[Pattern Matcher]
        ResponseGen[Response Generator]
    end

    Router -.Load Category.-> Taxonomy
    Executor -.Load Protocol.-> Playbooks
    Matcher -.Match Evidence.-> Rules
    ResponseGen -.Load Template.-> Templates
    Matcher -.Check Automation.-> Feasibility

    style SkillsLibrary fill:#f3e5f5,stroke:#9c27b0,stroke-width:3px
    style Consumers fill:#fff3cd,stroke:#ffc107,stroke-width:2px
```

## Skills Library Contents

```mermaid
graph LR
    subgraph Skills[Skills Library]
        direction TB

        subgraph Patterns[Diagnostic Patterns]
            P1[ELD Not Enabled<br/>Feasibility: HIGH]
            P2[Asset Not Assigned<br/>Feasibility: HIGH]
            P3[GPS Provider Errors<br/>Feasibility: MEDIUM]
            P4[Outlier Detection<br/>Feasibility: MEDIUM]
            P5[100+ More Patterns...]
        end

        subgraph Playbooks[Investigation Playbooks]
            PB1[OTR Tracking Issues<br/>15 diagnostic checks]
            PB2[Network Configuration<br/>10 diagnostic checks]
            PB3[Ocean Tracking<br/>12 diagnostic checks]
            PB4[GPS Provider Issues<br/>8 diagnostic checks]
        end

        subgraph Templates[Response Templates]
            T1[ELD Enable Template]
            T2[Asset Assignment Template]
            T3[Configuration Fix Template]
            T4[GPS Provider Template]
        end

        subgraph Rules[Evidence Rules]
            R1[Confidence Thresholds]
            R2[Auto-Resolve Criteria]
            R3[Escalation Triggers]
            R4[Quality Gates]
        end
    end

    Patterns --> Playbooks
    Playbooks --> Templates
    Rules --> Templates

    style Skills fill:#f3e5f5,stroke:#9c27b0,stroke-width:3px
    style Patterns fill:#e1bee7
    style Playbooks fill:#ce93d8
    style Templates fill:#ba68c8
    style Rules fill:#ab47bc
```

## Data Flow Through Skills Library

```mermaid
flowchart LR
    subgraph Input[Case Input]
        Case[Support Case<br/>Load Not Tracking]
    end

    subgraph Classification[Classification]
        Cassie[Cassie Agent]
        Router[Category Router]
    end

    subgraph SkillsLayer[Skills Library Layer]
        Skills[(Skills Library)]
        SelectPlaybook[Select Playbook:<br/>OTR Tracking Issues]
        SelectPattern[Pattern Library:<br/>100+ Patterns]
        SelectTemplate[Template Library:<br/>Response Templates]
    end

    subgraph Execution[Investigation Execution]
        Executor[Playbook Executor]
        MCPs[(5 MCP Servers)]
        Evidence[Evidence Collector]
    end

    subgraph Decision[Decision Layer]
        Matcher[Pattern Matcher]
        Scorer[Confidence Scorer]
        Generator[Response Generator]
    end

    Case --> Cassie --> Router
    Router -.1. Load Category.-> Skills
    Skills --> SelectPlaybook
    SelectPlaybook --> Executor
    Executor -.2. Query Data.-> MCPs
    MCPs -.3. Return Data.-> Evidence
    Evidence -.4. Match Pattern.-> Skills
    Skills --> SelectPattern
    SelectPattern --> Matcher --> Scorer
    Scorer -.5. High Confidence.-> Skills
    Skills --> SelectTemplate
    SelectTemplate --> Generator

    style Input fill:#e3f2fd
    style Classification fill:#e3f2fd
    style SkillsLayer fill:#f3e5f5,stroke:#9c27b0,stroke-width:3px
    style Execution fill:#fff3cd
    style Decision fill:#f1f8e9
```

---

## Key Insight: Skills Library as Reusable Knowledge

The **Skills Library** is the central knowledge repository that:

1. **Captures Institutional Knowledge:**
   - 100+ diagnostic patterns from expert support engineers
   - Validated playbooks from thousands of historical cases
   - Proven response templates

2. **Enables Reusability:**
   - Same skills can be used across multiple AI agents
   - New agents can leverage existing diagnostic intelligence
   - Continuous improvement benefits all consumers

3. **Maintains Separation of Concerns:**
   - Knowledge (Skills Library) separate from execution (Playbook Executor)
   - Classification (Cassie) doesn't contain diagnostic logic
   - MCPs provide data, not intelligence
   - Investigation engine orchestrates, doesn't own patterns

4. **Supports Rapid Development:**
   - Add new pattern → instantly available to all agents
   - Update existing pattern → all consumers benefit
   - No code changes needed for pattern modifications

---

## Color Legend

- **Purple (#f3e5f5):** Skills Library Layer - The Knowledge Repository
- **Blue (#e3f2fd):** Classification Layer
- **Yellow (#fff3cd):** Investigation/Execution Layer
- **Green (#f1f8e9):** Intelligence/Pattern Matching Layer
- **Orange (#ffe0b2):** Decision Layer

---
