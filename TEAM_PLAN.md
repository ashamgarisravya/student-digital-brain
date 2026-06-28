# NeuroNote — Team Plan

**Version:** 1.0.0  
**Last Updated:** 2026-06-28

---

## 1. Team Structure

| Aspect | Detail |
|---|---|
| **Team Size** | 2 Members |
| **Hackathon** | CPU-First Offline AI Hackathon |
| **Repository** | https://code.swecha.org/Bharatg/student-digital-brain |

---

## 2. Member Assignments

### Member A — Backend Developer

**Role:** Backend & AI Pipeline  
**Focus:** Data processing, AI inference, database, knowledge graph, testing

| Responsibility | Modules | Technologies |
|---|---|---|
| PDF Processing | PDF text and image extraction | PyMuPDF |
| OCR Pipeline | Image preprocessing, text extraction | Tesseract, OpenCV |
| Speech-to-Text | Audio transcription | Whisper.cpp |
| Text Preprocessing | Cleaning, chunking, normalization | Python, regex |
| LLM Integration | llama.cpp binding, model management | llama.cpp, Phi-3 Mini |
| Concept Extraction | Prompt engineering, JSON parsing | LLM, JSON |
| Question Generation | Quiz question creation | LLM |
| Knowledge Graph | NetworkX construction, similarity | NetworkX, TF-IDF |
| Database | Schema, queries, FTS5, migrations | SQLite |
| Unit Tests | Processing and AI modules | pytest |
| Integration Tests | End-to-end workflow tests | pytest |
| Performance | Optimization, benchmarking | cProfile |

### Member B — Frontend Developer

**Role:** UI/UX & Application Integration  
**Focus:** Streamlit interface, search, visualization, documentation

| Responsibility | Modules | Technologies |
|---|---|---|
| Streamlit App | Main application entry, navigation | Streamlit |
| Dashboard | Statistics, recent activity | Streamlit |
| File Upload | Drag-and-drop, validation, progress | Streamlit |
| Search Interface | Input, filters, results display | Streamlit, SQLite FTS5 |
| Quiz Interface | Question display, scoring, history | Streamlit |
| Revision Planner | Schedule display, export | Streamlit |
| Knowledge Graph Viewer | Interactive visualization | Plotly/Pyvis, NetworkX |
| Audio Upload | Recording, file upload, metadata | Streamlit |
| Export Functionality | JSON download, backup | Python, JSON |
| Documentation | All docs, README, SPEC, guides | Markdown |
| Demo Preparation | Script, video recording, submission | - |

---

## 3. Collaboration Strategy

| Aspect | Approach |
|---|---|
| **Version Control** | GitLab with feature branches, MR review |
| **Communication** | Daily standup (15 min), GitLab issues |
| **Code Review** | Both members review all MRs |
| **Testing** | Member A writes backend tests; Member B writes UI tests |
| **Integration** | Weekly merge to develop branch |
| **Documentation** | Member B maintains; Member A reviews technical accuracy |

---

## 4. Timeline

```
WEEK 1-2                    WEEK 3-4                    WEEK 5-6                    WEEK 7-8
════════════════════════    ════════════════════════    ════════════════════════    ════════════════════════
PHASE 2: MVP                PHASE 3: AI                 PHASE 4: TESTING            PHASE 5: SUBMISSION

Member A:                   Member A:                   Member A:                   Member A:
┌────────────────────┐     ┌────────────────────┐     ┌────────────────────┐     ┌────────────────────┐
│ • Project setup    │     │ • llama.cpp        │     │ • Unit tests       │     │ • Performance      │
│ • Database schema  │     │ • Concept extract   │     │ • Integration tests│     │   optimization     │
│ • PDF processing   │     │ • Question gen      │     │ • Bug fixes        │     │ • Final testing    │
│ • OCR module       │     │ • Knowledge graph   │     │ • Edge cases       │     │ • Code cleanup     │
│ • Text processing  │     │ • DB optimization   │     │                    │     │                    │
└────────────────────┘     └────────────────────┘     └────────────────────┘     └────────────────────┘

Member B:                   Member B:                   Member B:                   Member B:
┌────────────────────┐     ┌────────────────────┐     ┌────────────────────┐     ┌────────────────────┐
│ • Streamlit setup  │     │ • KG visualization │     │ • UI bug fixes     │     │ • Documentation    │
│ • Dashboard        │     │ • Quiz interface   │     │ • UX polish        │     │ • Demo prep        │
│ • Upload interface │     │ • Revision planner │     │ • Error handling   │     │ • Video recording  │
│ • Basic search     │     │ • Export feature   │     │ • Theme/styling    │     │ • Final review     │
└────────────────────┘     └────────────────────┘     └────────────────────┘     └────────────────────┘
```

---

## 5. Weekly Milestones

| Week | Member A Deliverables | Member B Deliverables |
|---|---|---|
| **Week 1** | Project setup, database schema, PDF processor | Streamlit scaffold, basic dashboard, upload UI |
| **Week 2** | OCR module, text preprocessing, basic search DB | Search UI with filters, results display |
| **Week 3** | llama.cpp integration, concept extraction | Knowledge graph visualization (basic) |
| **Week 4** | Question generation, knowledge graph | Quiz UI, revision planner UI, export |
| **Week 5** | Unit tests (processing modules) | UI testing, error handling |
| **Week 6** | Integration tests, bug fixes, edge cases | UX polish, dark mode, responsive design |
| **Week 7** | Performance optimization, benchmarking | Documentation finalization |
| **Week 8** | Final testing, code cleanup | Demo script, video recording, submission |

---

## 6. Risk Mitigation per Member

| Member | Risk | Mitigation |
|---|---|---|
| A | llama.cpp integration complex | Prototype early (Week 1), fallback to simpler model |
| A | OCR quality poor on handwriting | Multiple preprocessing strategies, user feedback |
| A | LLM performance too slow | Optimize chunk size, test smaller models |
| B | Streamlit limitations for graph viz | Evaluate Plotly/Pyvis early, have fallback |
| B | Search performance issues | Index optimization, query tuning |
| B | UI complexity exceeds timeline | Prioritize core features, delay nice-to-haves |

---

## 7. Tools and Access

| Tool | Purpose | Access |
|---|---|---|
| GitLab | Source control, issues, CI/CD | Both members |
| VS Code | Development IDE | Both members |
| Python 3.11 | Runtime | Both members |
| Local Git | Version control | Both members |
| OBS Studio | Demo recording | Member B |