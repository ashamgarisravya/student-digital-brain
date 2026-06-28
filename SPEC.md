# NeuroNote - Technical Specification

**Version:** 1.0.0  
**Status:** Planning  
**Last Updated:** 2026-06-28

---

## 1. Objective

Develop a completely offline, CPU-first AI system that transforms unstructured student educational content (PDFs, images, handwritten notes, audio recordings, text) into structured, searchable knowledge stored in SQLite with JSON export capability, enabling instant retrieval, revision planning, and quiz generation — all without any internet connection or cloud API dependency.

---

## 2. Functional Requirements

### FR-01: PDF Document Ingestion
| ID | Requirement | Priority |
|---|---|---|
| FR-01.1 | System shall accept PDF files up to 100 MB | High |
| FR-01.2 | System shall extract text content from PDF using PyMuPDF | High |
| FR-01.3 | System shall extract embedded images from PDF | Medium |
| FR-01.4 | System shall preserve document structure (headings, paragraphs) | High |
| FR-01.5 | System shall handle multi-page PDF documents | High |

### FR-02: Image and Handwriting Processing
| ID | Requirement | Priority |
|---|---|---|
| FR-02.1 | System shall accept JPEG, PNG, and TIFF image formats | High |
| FR-02.2 | System shall perform OCR using Tesseract | High |
| FR-02.3 | System shall process scanned handwritten notes | High |
| FR-02.4 | System shall handle whiteboard photo text extraction | Medium |

### FR-03: Audio Processing
| ID | Requirement | Priority |
|---|---|---|
| FR-03.1 | System shall accept MP3, WAV, and M4A audio formats | High |
| FR-03.2 | System shall perform speech-to-text using Whisper.cpp | High |
| FR-03.3 | System shall handle lecture recordings up to 60 minutes | Medium |
| FR-03.4 | System shall segment transcription by speaker/section | Low |

### FR-04: Text Input
| ID | Requirement | Priority |
|---|---|---|
| FR-04.1 | System shall accept plain text input via text area | High |
| FR-04.2 | System shall accept text file uploads (.txt, .md) | Medium |
| FR-04.3 | System shall support multi-language text input | Low |

### FR-05: AI Processing
| ID | Requirement | Priority |
|---|---|---|
| FR-05.1 | System shall process text through local LLM (Phi-3 Mini) | High |
| FR-05.2 | System shall extract key concepts from processed text | High |
| FR-05.3 | System shall generate structured JSON from raw text | High |
| FR-05.4 | System shall identify subject/topic classification | High |
| FR-05.5 | System shall extract definitions and important terms | High |
| FR-05.6 | System shall generate questions from content | Medium |
| FR-05.7 | System shall link related concepts across documents | Medium |

### FR-06: Storage
| ID | Requirement | Priority |
|---|---|---|
| FR-06.1 | System shall store all data in SQLite database | High |
| FR-06.2 | System shall export knowledge as JSON files | Medium |
| FR-06.3 | System shall maintain document-to-extraction relationships | High |
| FR-06.4 | System shall support database backup and restore | Low |

### FR-07: Search and Retrieval
| ID | Requirement | Priority |
|---|---|---|
| FR-07.1 | System shall provide full-text search across all content | High |
| FR-07.2 | System shall support filtering by subject/topic | Medium |
| FR-07.3 | System shall support filtering by document type | Medium |
| FR-07.4 | System shall display search results with relevance ranking | High |

### FR-08: Learning Tools
| ID | Requirement | Priority |
|---|---|---|
| FR-08.1 | System shall generate revision plans based on content | Medium |
| FR-08.2 | System shall generate multiple-choice and short-answer quizzes | Medium |
| FR-08.3 | System shall display knowledge graph visualization | Medium |
| FR-08.4 | System shall track quiz history and performance | Low |

---

## 3. Non-Functional Requirements

| ID | Requirement | Target |
|---|---|---|
| NFR-01 | **Performance** — PDF ingestion time | < 30 seconds per 100 pages |
| NFR-02 | **Performance** — OCR processing time | < 2 seconds per page |
| NFR-03 | **Performance** — LLM inference time | < 10 seconds per chunk |
| NFR-04 | **Performance** — Search response time | < 2 seconds |
| NFR-05 | **Memory** — Peak RAM usage | < 8 GB |
| NFR-06 | **Storage** — Database growth | < 50 MB per 1000 documents |
| NFR-07 | **Storage** — Model size | < 4 GB (Phi-3 Mini GGUF) |
| NFR-08 | **Compatibility** — Operating systems | Windows 10+, Linux, macOS 12+ |
| NFR-09 | **Compatibility** — Python version | 3.10, 3.11, 3.12 |
| NFR-10 | **Offline** — Complete functionality without internet | 100% |
| NFR-11 | **Privacy** — Data never leaves local machine | Enforced |
| NFR-12 | **Reliability** — System uptime | N/A (local desktop app) |
| NFR-13 | **Usability** — Streamlit UI responsiveness | < 500 ms per interaction |
| NFR-14 | **Maintainability** — Code documentation coverage | > 70% |
| NFR-15 | **Scalability** — Maximum document count | 10,000 documents |
| NFR-16 | **Security** — No external network calls | Verified |

---

## 4. User Stories

### Student Persona: Exam Preparation

| ID | User Story | Acceptance Criteria |
|---|---|---|
| US-01 | As a student, I want to upload my PDF textbooks so that I can search through them later | PDF is processed and content appears in search results |
| US-02 | As a student, I want to upload photos of my handwritten notes so that the system can read them | OCR extracts text, concepts are identified |
| US-03 | As a student, I want to transcribe recorded lectures so that I can search lecture content | Audio file is transcribed, text is searchable |
| US-04 | As a student, I want to find all definitions related to a specific topic so that I can study efficiently | Search returns filtered definitions grouped by topic |
| US-05 | As a student, I want the system to generate practice questions from my notes so that I can test myself | Quiz appears with questions extracted from my content |
| US-06 | As a student, I want to see a graph of how different concepts connect so that I can understand relationships | Knowledge graph visualization renders with clickable nodes |
| US-07 | As a student, I want to create a revision plan so that I can prepare systematically for exams | Planner generates a schedule based on my content |
| US-08 | As a student, I want all features to work without internet so that I can study anywhere | System functions fully in airplane mode |
| US-09 | As a student, I want to organize content by subject so that I can keep track of different courses | Subjects/topics are created and filterable |
| US-10 | As a student, I want to export my structured notes as JSON so that I can back them up | JSON file downloads with all structured data |

---

## 5. Inputs

| Input Type | Formats | Max Size | Processing Engine |
|---|---|---|---|
| PDF Documents | .pdf | 100 MB | PyMuPDF |
| Images (Digital) | .jpg, .jpeg, .png, .tiff, .bmp | 50 MB | Tesseract OCR |
| Images (Handwritten) | .jpg, .jpeg, .png | 50 MB | Tesseract OCR |
| Audio Recordings | .mp3, .wav, .m4a, .ogg | 500 MB | Whisper.cpp |
| Plain Text | .txt, .md, direct input | 10 MB | Direct processing |
| Multiple Files | Batch upload (up to 10) | 500 MB total | Parallel processing |

---

## 6. Outputs

| Output Type | Description | Format |
|---|---|---|
| Structured Knowledge | Extracted concepts, definitions, topics | JSON |
| Database Record | Persistent storage in local database | SQLite |
| Search Results | Filterable, ranked search results | Streamlit UI |
| Knowledge Graph | Visualized concept relationships | NetworkX + HTML |
| Quiz Questions | Multiple choice and short answer | JSON + UI display |
| Revision Plan | Study schedule organized by topics | Markdown + UI |
| Export File | Full knowledge base export | JSON |

---

## 7. AI Workflow

```
┌──────────────────────────────────────────────────────────────┐
│                  AI Processing Pipeline                       │
├──────────────┬───────────────────────────────────────────────┤
│   Step 1     │ Raw Text Input (from PDF/OCR/STT/Text)        │
├──────────────┼───────────────────────────────────────────────┤
│   Step 2     │ Text Chunking (split into manageable segments) │
├──────────────┼───────────────────────────────────────────────┤
│   Step 3     │ LLM Prompt Engineering                        │
│              │ └─ System prompt: "Extract key concepts..."    │
├──────────────┼───────────────────────────────────────────────┤
│   Step 4     │ Local Inference (Phi-3 Mini via llama.cpp)    │
│              │ └─ Temperature: 0.3 (deterministic extraction) │
│              │ └─ Max tokens: 2048                            │
├──────────────┼───────────────────────────────────────────────┤
│   Step 5     │ JSON Parsing (validate and structure output)  │
├──────────────┼───────────────────────────────────────────────┤
│   Step 6     │ Knowledge Linking (cross-document connections)│
├──────────────┼───────────────────────────────────────────────┤
│   Step 7     │ SQLite Storage (persist structured data)       │
├──────────────┼───────────────────────────────────────────────┤
│   Step 8     │ Knowledge Graph Update (NetworkX)             │
└──────────────┴───────────────────────────────────────────────┘
```

### Prompt Template (for Concept Extraction)

```
You are a study assistant. Extract key concepts, definitions, and 
important terms from the following educational text. 

For each concept, output:
- concept: [term name]
- definition: [clear definition]
- subject: [subject area]
- importance: [high/medium/low]
- related_concepts: [comma-separated list of related terms]

Text:
{chunk_text}

Output as JSON array.
```

---

## 8. JSON Schema

See [docs/json_schema.md](docs/json_schema.md) for the complete JSON schema documentation.

---

## 9. SQLite Schema

See [docs/database.md](docs/database.md) for the complete SQLite schema documentation.

---

## 10. Performance Goals

| Metric | Goal | Measurement Method |
|---|---|---|
| PDF Processing (100 pages) | < 30 seconds | Wall clock time |
| OCR per Page | < 2 seconds | Wall clock time |
| STT per Minute of Audio | < 5 minutes | Wall clock time (real-time factor < 5x) |
| LLM per Text Chunk | < 10 seconds | Wall clock time |
| Search Query | < 2 seconds | Wall clock time |
| Knowledge Graph Render | < 3 seconds | Wall clock time |
| Quiz Generation (10 questions) | < 15 seconds | Wall clock time |
| Peak Memory Usage | < 8 GB | Memory profiler |
| Database Size per 1000 Docs | < 50 MB | File system measurement |

### CPU-First Performance Constraints

| Model | Quantization | RAM | Speed (tokens/sec) |
|---|---|---|---|
| Phi-3 Mini (3.8B) | Q4_K_M | ~3.5 GB | 10-20 t/s (4-core CPU) |
| Phi-3 Mini (3.8B) | Q4_K_M | ~3.5 GB | 15-30 t/s (8-core CPU) |

---

## 11. CPU-First Design

### Principles

1. **No GPU Required** — All inference runs on CPU using optimized libraries (llama.cpp, Whisper.cpp)
2. **Quantized Models** — All models use 4-bit quantization (Q4_K_M)
3. **Efficient Chunking** — Large documents split into chunks that fit within model context window (4K tokens)
4. **Progressive Processing** — Documents are processed in background with progress indicators
5. **Memory Management** — Models are loaded/unloaded on demand to minimize RAM footprint
6. **Batch Processing** — Where possible, operations are batched for efficiency

### Why CPU-First?

| Factor | Consideration |
|---|---|
| **Accessibility** | Many students lack GPU-equipped machines |
| **Battery Life** | CPU inference is more battery-efficient for small models |
| **Portability** | Works on laptops, Chromebooks, low-spec hardware |
| **Compatibility** | No CUDA/ROCm driver requirements |
| **Offline** | No cloud GPU dependency |

---

## 12. Offline-First Design

### Principles

1. **Zero Network Calls** — No HTTP requests to external APIs
2. **Local Model Storage** — All AI models stored in `models/` directory
3. **Local Database** — SQLite stores all application data
4. **No Telemetry** — No usage analytics, no crash reporting to external services
5. **Self-Contained** — All dependencies installable via pip from offline cache
6. **Air-Gap Functional** — System works 100% without any internet connectivity

### Offline Verification Checklist

| Item | Status |
|---|---|
| No cloud API dependencies (OpenAI, Anthropic, etc.) | ✅ |
| All AI models downloadable and cacheable | ✅ |
| All Python packages installable offline via wheel cache | ✅ |
| No external service registration or API keys | ✅ |
| No telemetry or analytics calls | ✅ |
| No CDN-dependent frontend assets | ✅ |
| All documentation accessible offline | ✅ |

---

## 13. Risks

| Risk ID | Description | Probability | Impact | Mitigation |
|---|---|---|---|---|
| R-01 | OCR quality poor on handwritten text | Medium | High | Use image preprocessing (binarization, deskewing) |
| R-02 | LLM hallucination in concept extraction | Medium | Medium | Low temperature (0.3), strict JSON schema validation |
| R-03 | STT accuracy degrades with background noise | Medium | Medium | Recommend quiet recordings; support manual corrections |
| R-04 | Performance insufficient on very low-end hardware | Low | High | Test on minimum spec (4GB RAM, 4-core CPU) |
| R-05 | SQLite bottleneck with concurrent writes | Low | Medium | Use WAL mode, single writer pattern |
| R-06 | Model download size too large | Medium | Low | Provide model download script with progress |
| R-07 | Tesseract not installed on user system | Medium | Low | Detect and guide installation in setup script |
| R-08 | Unicode/language support gaps | Low | Medium | Use UTF-8 throughout; test with non-English content |
| R-09 | Knowledge graph becomes too large | Low | Low | Implement graph pruning and node limiting |
| R-10 | Streamlit session state management complexity | Medium | Low | Use session state patterns consistently |

---

## 14. Future Improvements

| Improvement | Priority | Description |
|---|---|---|
| Multi-language OCR support | Medium | Support for non-English languages in Tesseract |
| Handwriting recognition via ML | Low | Replace Tesseract with dedicated HTR models |
| Fine-tuned LLM on educational data | Low | Fine-tune Phi-3 Mini on textbook corpus |
| Mobile app companion | Low | React Native / Flutter app for mobile scanning |
| Collaborative study groups | Low | LAN-based shared knowledge base |
| PDF annotation import | Low | Import highlights, comments from PDF readers |
| Spaced repetition integration | Low | Anki-compatible export for flashcard review |
| Voice query interface | Low | STT-based query input |
| Real-time collaboration | Low | LAN-based multi-user editing |
| Docker deployment | Low | Containerized deployment for reproducible setup |

---

## 15. Glossary

| Term | Definition |
|---|---|
| **CPU-First** | Design philosophy prioritizing CPU-based inference, making no assumptions about GPU availability |
| **GGUF** | GPT-Generated Unified Format — file format for quantized LLM models |
| **Knowledge Graph** | Network of interconnected concepts and their relationships |
| **llama.cpp** | C++ implementation of LLaMA inference optimized for CPU |
| **OCR** | Optical Character Recognition — converting images of text to machine-encoded text |
| **Q4_K_M** | 4-bit quantization method balancing quality and size |
| **STT** | Speech-to-Text — converting audio to text transcription |
| **Whisper.cpp** | C++ port of OpenAI's Whisper speech recognition model |
| **WAL Mode** | Write-Ahead Logging — SQLite mode for better concurrent read/write performance |