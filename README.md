# NeuroNote – Offline Student Digital Brain

**Your Personal AI Learning Brain that works completely Offline.**

![Version](https://img.shields.io/badge/version-1.0.0-blue)
![License](https://img.shields.io/badge/license-GPL--3.0-green)
![Platform](https://img.shields.io/badge/platform-CPU--first-orange)
![Status](https://img.shields.io/badge/status-planning-lightgrey)

---

## Problem Statement

Students store their study material across PDFs, handwritten notes, lecture recordings, whiteboard images, textbooks, and assignments. Finding the right information during revision is time-consuming and inefficient.

With files scattered across multiple formats and no unified way to search or connect related concepts, students waste valuable exam preparation time hunting for information instead of studying.

---

## Proposed Solution

NeuroNote is an offline-first AI application that transforms unstructured educational content into structured knowledge using CPU-only AI models. It organizes everything into a searchable local knowledge base without requiring any internet connection.

Students upload their study materials — PDFs, images of handwritten notes, lecture audio recordings, or plain text — and NeuroNote automatically extracts text, identifies concepts, connects related ideas, and stores everything in a local SQLite database. Users can then search, generate quizzes, plan revisions, and explore a knowledge graph of interconnected concepts, all while completely offline.

---

## Key Features

| Feature | Description |
|---|---|
| **Offline AI** | All processing runs locally on your machine. Zero internet required. |
| **CPU-first** | Optimized for CPU inference. Works on standard laptops without GPU. |
| **OCR** | Extracts text from printed documents, handwritten notes, and whiteboard photos using Tesseract OCR. |
| **Speech-to-Text** | Transcribes lecture recordings and voice notes using Whisper.cpp. |
| **Knowledge Graph** | Automatically connects related concepts across documents using NetworkX. |
| **Smart Search** | Full-text search across all processed content with topic filters. |
| **Quiz Generator** | Creates multiple-choice and short-answer practice questions from your study material. |
| **Revision Planner** | Generates structured study schedules based on your content and available time. |

---

## AI Workflow

```
                ┌──────────────┐
                │    Input     │
                │  PDF / Image │
                │  Audio / Text│
                └──────┬───────┘
                       │
                       ▼
                ┌──────────────┐
                │ OCR / Whisper│
                │  Extraction  │
                └──────┬───────┘
                       │
                       ▼
                ┌──────────────┐
                │  Local LLM   │
                │ (Phi-3 Mini) │
                └──────┬───────┘
                       │
                       ▼
                ┌──────────────┐
                │  Structured  │
                │     JSON     │
                └──────┬───────┘
                       │
                       ▼
                ┌──────────────┐
                │    SQLite    │
                │   Database   │
                └──────┬───────┘
                       │
                       ▼
                ┌──────────────┐
                │  Knowledge   │
                │    Graph     │
                └──────┬───────┘
                       │
                       ▼
                ┌──────────────┐
                │    Search    │
                │  Quiz / Plan │
                └──────────────┘
```

---

## Technology Stack

| Technology | Purpose |
|---|---|
| **Python** | Core programming language |
| **Streamlit** | Web-based user interface |
| **SQLite** | Local database storage |
| **Tesseract OCR** | Optical character recognition for images and handwritten notes |
| **Whisper.cpp** | Offline speech-to-text for audio transcriptions |
| **llama.cpp** | Local LLM inference engine optimized for CPU |
| **Phi-3 Mini (GGUF)** | Small language model (3.8B params) for concept extraction |
| **PyMuPDF** | PDF text and image extraction |
| **NetworkX** | Knowledge graph construction and visualization |

---

## Folder Structure (Planned)

```
student-digital-brain/
├── README.md                  # Project documentation
├── SPEC.md                    # Technical specification
├── ISSUE_PLAN.md             # GitLab issue tracker
├── TEAM_PLAN.md              # Team work division
├── src/                       # Application source code
│   ├── app.py                 # Main Streamlit entry point
│   ├── ui/                    # Streamlit interface components
│   ├── processing/            # PDF, OCR, STT processing modules
│   ├── ai/                    # LLM inference, concept extraction
│   ├── database/              # SQLite models and operations
│   └── utils/                 # Helper utilities
├── models/                    # Local GGUF model files
├── database/                  # SQLite database files
├── data/                      # Uploads, processed outputs
├── assets/                    # Static files, icons
├── tests/                     # Unit and integration tests
├── scripts/                   # Utility scripts
└── examples/                  # Sample files and demos
```

---

## Future Scope

| Phase | Features |
|---|---|
| **Phase 2 — MVP** | PDF upload, text extraction, OCR, SQLite storage, basic search, Streamlit dashboard |
| **Phase 3 — AI** | LLM concept extraction, JSON structuring, knowledge graph, quiz generation |
| **Phase 4 — Polish** | Unit tests, integration tests, performance optimization, error handling |
| **Phase 5+** | Multi-language support, handwriting recognition model, mobile companion app, collaborative study groups |

---

## License

This project is licensed under the **GNU General Public License v3.0 (GPL-3.0)**.

```
Copyright (C) 2026 NeuroNote Team

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License.
```

---

## Team Members

| Member | Role | Responsibilities |
|---|---|---|
| **Member A** | Backend Developer | OCR, Database, LLM, Knowledge Graph, Testing |
| **Member B** | Frontend Developer | Streamlit UI, File Upload, Audio Processing, Dashboard, Documentation, Testing |