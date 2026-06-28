# NeuroNote - Offline Student Digital Brain

![Version](https://img.shields.io/badge/version-1.0.0-blue)
![License](https://img.shields.io/badge/license-GPL--3.0-green)
![Python](https://img.shields.io/badge/python-3.10%2B-yellow)
![Status](https://img.shields.io/badge/status-planning-orange)

**Your Personal AI Learning Brain that works completely Offline.**

---

## 📖 Project Overview

NeuroNote is an offline-first, CPU-based AI system designed for students to transform scattered educational material into a structured, searchable knowledge base. The system ingests PDFs, images, handwritten notes, audio recordings, and plain text, processes them entirely on-device using open-source AI models, and provides instant retrieval, revision planning, and quiz generation — all without any internet connection.

---

## ❗ Problem Statement

Students accumulate vast amounts of study material across multiple formats:

- PDF textbooks and research papers
- Handwritten class notes
- Lecture audio recordings
- Whiteboard photographs
- Digital text notes and assignments
- Scanned documents

During exam preparation, finding specific concepts, definitions, or connections across this scattered material becomes a significant challenge. Existing solutions either require cloud connectivity, compromise privacy, or fail to intelligently structure extracted knowledge.

---

## 💡 Solution

NeuroNote solves this by providing a completely offline, CPU-first pipeline that:

1. **Ingests** multiple input formats (PDF, images, audio, text)
2. **Extracts** text via OCR (Tesseract) and speech-to-text (Whisper.cpp)
3. **Processes** content using a local small language model (Phi-3 Mini GGUF via llama.cpp)
4. **Structures** extracted knowledge into JSON and SQLite
5. **Connects** related concepts into a Knowledge Graph (NetworkX)
6. **Enables** instant search, revision planning, and quiz generation

---

## ✨ Features

| Category | Feature | Description |
|---|---|---|
| **Input Processing** | PDF Extraction | Extract text and images from PDF documents using PyMuPDF |
| | OCR | Optical Character Recognition for handwritten/scanned text via Tesseract |
| | Speech-to-Text | Offline audio transcription using Whisper.cpp |
| | Text Ingestion | Accept plain text notes directly |
| **AI Processing** | Local LLM | Concept extraction and knowledge structuring using Phi-3 Mini |
| | JSON Structuring | Convert raw text into structured JSON with defined schemas |
| | Knowledge Linking | Connect related concepts across documents |
| | Zero-Shot Classification | Topic categorization without training data |
| **Storage** | SQLite Database | All data stored locally in a portable SQLite database |
| | JSON Export | Structured knowledge export in JSON format |
| | Local Models | All AI models stored and executed locally |
| **Retrieval** | Full-Text Search | Search across all processed content |
| | Topic Search | Filter and search by subject/topic |
| | Concept Search | Find specific definitions and concepts |
| **Learning Tools** | Revision Planner | Generate study plans based on content |
| | Quiz Generator | Create practice questions from your notes |
| | Knowledge Graph | Visualize concept relationships (NetworkX) |
| **Privacy** | 100% Offline | No data ever leaves your machine |
| | No Cloud APIs | No OpenAI, Anthropic, or any external services |
| | Local Storage | All data stored on your local machine |

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                        User Interface                        │
│                      (Streamlit Web App)                      │
├──────────┬──────────┬──────────┬──────────┬─────────────────┤
│   PDF    │  Image   │  Audio   │   Text   │   Dashboard     │
│  Upload  │  Upload  │  Upload  │  Input   │   & Search      │
└────┬─────┴────┬─────┴────┬─────┴────┬─────┴────────┬────────┘
     │          │          │          │              │
     ▼          ▼          ▼          ▼              ▼
┌──────────────────────────────────────────────────────────────┐
│                    Processing Layer                           │
├──────────┬──────────┬──────────┬──────────────────────────────┤
│ PyMuPDF  │ Tesseract│Whisper.cpp│    Text Preprocessing       │
│ (PDF)    │  (OCR)   │  (STT)   │    (Cleaning, Chunking)     │
└──────────┴──────────┴──────────┴──────────────────────────────┘
               │                    │
               ▼                    ▼
┌──────────────────────────────────────────────────────────────┐
│                    AI Processing Layer                        │
├──────────────────────────────────────────────────────────────┤
│         llama.cpp + Phi-3 Mini GGUF                          │
│    (Concept Extraction, JSON Structuring,                    │
│     Knowledge Linking, Question Generation)                  │
└──────────────────────────────────────────────────────────────┘
               │
               ▼
┌──────────────────────────────────────────────────────────────┐
│                    Storage Layer                              │
├──────────────────────┬───────────────────────────────────────┤
│     SQLite Database   │      JSON Files                      │
│   (Documents, Topics, │   (Structured Knowledge              │
│    Definitions, Quiz  │    Export / Backup)                   │
│    History, etc.)     │                                       │
├──────────────────────┴───────────────────────────────────────┤
│                  Knowledge Graph (NetworkX)                   │
└──────────────────────────────────────────────────────────────┘
               │
               ▼
┌──────────────────────────────────────────────────────────────┐
│                    Retrieval Layer                            │
├──────────┬──────────┬──────────┬──────────┬─────────────────┤
│ Full-Text│  Topic   │ Concept  │ Revision │  Quiz Display   │
│  Search  │  Search  │  Search  │ Planner  │                 │
└──────────┴──────────┴──────────┴──────────┴─────────────────┘
```

---

## 🛠️ Technology Stack

| Technology | Purpose | Version |
|---|---|---|
| **Python** | Core programming language | 3.10+ |
| **Streamlit** | Web-based user interface | Latest |
| **SQLite** | Local database storage | Built-in |
| **Tesseract OCR** | Optical Character Recognition | Latest |
| **Whisper.cpp** | Offline speech-to-text | Latest |
| **llama.cpp** | Local LLM inference engine | Latest |
| **Phi-3 Mini GGUF** | Small language model (3.8B params) | Q4_K_M |
| **PyMuPDF** | PDF text and image extraction | Latest |
| **NetworkX** | Knowledge graph construction | Latest |

---

## 📁 Folder Structure

```
student-digital-brain/
├── README.md                    # Project overview and documentation
├── LICENSE                      # GPL-3.0 License
├── SPEC.md                      # Technical specification
├── CONTRIBUTING.md              # Contribution guidelines
├── CHANGELOG.md                 # Version history
├── .gitignore                   # Git ignore rules
├── SECURITY.md                  # Security and privacy policy
├── ISSUE_PLAN.md               # GitLab issue tracker plan
├── TEAM_PLAN.md                 # Team responsibilities and timeline
├── MILESTONES.md               # Project milestones
├── ROADMAP.md                   # Development roadmap
├── SYSTEM_DESIGN.md             # High-level system design
├── DEMO_PLAN.md                 # Demo sequence plan
├── PROJECT_CHECKLIST.md         # Project completion checklist
├── DECISIONS.md                 # Architectural decision records
├── docs/
│   ├── architecture.md          # Detailed system architecture
│   ├── workflow.md              # User workflow documentation
│   ├── database.md              # Database schema documentation
│   ├── ai_pipeline.md           # AI processing pipeline
│   ├── json_schema.md           # JSON schema definitions
│   ├── project_structure.md     # Detailed folder structure
│   └── future_scope.md          # Future roadmap and enhancements
├── src/                         # Application source code
│   └── __init__.py
├── models/                      # Local AI model files (GGUF)
├── database/                    # Database management module
│   └── __init__.py
├── data/                        # Application data (uploads, outputs)
│   ├── uploads/
│   ├── processed/
│   └── output/
├── assets/                      # Static assets (icons, images)
├── tests/                       # Unit tests and integration tests
│   └── __init__.py
├── scripts/                     # Utility scripts
└── examples/                    # Usage examples and sample data
```

---

## 🚀 Installation

> **Note:** Installation instructions will be finalized in Phase 2 (MVP). Placeholder for hackathon Phase 1 planning.

### Prerequisites

```bash
# Python 3.10 or higher
python --version

# Tesseract OCR (install system package)
# Windows: Download from GitHub releases
# Linux: sudo apt install tesseract-ocr
# macOS: brew install tesseract

# Download Phi-3 Mini GGUF model
# Place in models/ directory
```

### Setup

```bash
# Clone the repository
git clone https://code.swecha.org/Bharatg/student-digital-brain.git
cd student-digital-brain

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Linux/macOS
venv\Scripts\activate     # Windows

# Install dependencies (will be finalized in Phase 2)
pip install -r requirements.txt

# Run the application
streamlit run src/app.py
```

---

## 🔮 Future Scope

| Phase | Feature | Description |
|---|---|---|
| **Phase 2** | MVP | Core pipeline: PDF upload, OCR, text extraction, basic search |
| **Phase 3** | AI Integration | LLM integration, concept extraction, JSON structuring, knowledge graph |
| **Phase 4** | Learning Tools | Quiz generator, revision planner, knowledge graph visualization |
| **Phase 5+** | Advanced Features | Multi-language support, handwriting recognition improvements, collaborative features, mobile adaptation |

---

## 📄 License

This project is licensed under the **GNU General Public License v3.0 (GPL-3.0)**.

```
Copyright (C) 2026 NeuroNote Team

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
```

See [LICENSE](LICENSE) for the full license text.

---

## 👥 Team Members

| Member | Role | Responsibilities |
|---|---|---|
| **Member A** | Backend Developer | Database, OCR, LLM, Knowledge Graph, Testing |
| **Member B** | Frontend Developer | Streamlit UI, Audio, File Upload, Search, Dashboard, Documentation |

---

## 🙏 Acknowledgments

- [Streamlit](https://streamlit.io/) for the amazing web framework
- [llama.cpp](https://github.com/ggerganov/llama.cpp) for CPU-first LLM inference
- [Whisper.cpp](https://github.com/ggerganov/whisper.cpp) for offline speech recognition
- [Tesseract OCR](https://github.com/tesseract-ocr/tesseract) for OCR capabilities
- [NetworkX](https://networkx.org/) for knowledge graph support
- [Phi-3 Mini](https://huggingface.co/microsoft/Phi-3-mini-4k-instruct) for local AI processing
- All open-source contributors who make offline AI possible