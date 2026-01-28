# Architecture Diagrams - Quick Reference

## Files Created

### 1. **RECOMMENDED_ARCHITECTURE_MERMAID.md**
Raw Mermaid code for all diagrams. Use this to:
- Copy/paste into GitHub, GitLab, Notion, Confluence
- Generate PNG/SVG at https://mermaid.live
- Include in documentation

### 2. **ARCHITECTURE_DIAGRAMS.html**
Rendered HTML with all diagrams visualized. Use this to:
- View diagrams in your browser immediately
- Share as a single file for presentations
- Print or save as PDF

---

## 5 Diagram Types Included

### 📊 **1. Full Architecture Flow**
**When to Use:** Technical deep-dive, implementation discussions
**Shows:** Complete flow from user input → classification → investigation → decision

### 🏗️ **2. Layered Architecture View**
**When to Use:** Executive presentations, high-level architecture discussions
**Shows:** Four distinct layers (Classification, Investigation, Intelligence, Decision)

### 🔄 **3. Data Flow with MCP Integration**
**When to Use:** Explaining how data is retrieved and aggregated
**Shows:** Investigation engine querying 5 MCP servers in parallel

### 🎯 **4. Component Responsibilities**
**When to Use:** Team ownership discussions, component design
**Shows:** What each component is responsible for

### 💡 **5. Example: ELD Not Enabled Decision Flow**
**When to Use:** Demonstrating specific diagnostic scenarios
**Shows:** Step-by-step resolution of a real pattern

---

## How to Use

### For GitHub/Documentation:
```markdown
Copy diagram code from RECOMMENDED_ARCHITECTURE_MERMAID.md
Paste into your .md files
GitHub/GitLab will auto-render
```

### For Presentations:
1. Open `ARCHITECTURE_DIAGRAMS.html` in browser
2. Take screenshot or print to PDF
3. Use in slides

### For Live Editing:
1. Go to https://mermaid.live
2. Paste diagram code from the .md file
3. Edit and export as PNG/SVG

### For Slack/Teams:
1. Open `ARCHITECTURE_DIAGRAMS.html`
2. Screenshot the diagram you need
3. Share in conversation

---

## Color Coding

**Blue (#e3f2fd):** Classification layer components
**Yellow (#fff3cd):** Investigation layer components
**Green (#f1f8e9):** Intelligence layer components
**Orange (#ffe0b2):** Decision layer components
**Light Green (#c8e6c9):** Auto-resolution paths
**Light Red (#ffccbc):** Manual review paths

---

## Next Steps

1. **Review in browser:** Open `ARCHITECTURE_DIAGRAMS.html`
2. **Share with team:** Send HTML file or screenshots
3. **Add to gap analysis:** Include relevant diagrams in your Google Doc
4. **Use in meetings:** Reference during alignment discussions

---
