# pkm-indexer

**Personal Knowledge Management (PKM) System — Revised Overview (as of May 18, 2025)**

---

### **Purpose**

The PKM system is designed to help a non-coder manage personal knowledge across Windows PC and iOS (iPhone, Apple Watch) using a Progressive Web App (PWA). It enables capture, organization, review, and querying of diverse data types—notes, PDFs, URLs, videos, audio, and more—using AI for metadata generation and semantic search.

The long-term vision includes automatic ingestion from `~/OneDrive/PKM/Inbox`, populated via:

* iOS Drafts app
* Manual file uploads
* Email Shortcuts (Phase 2)

All data will be transformed into markdown with YAML frontmatter and stored alongside original files. The system will be simple, extensible, and voice-enabled (in Phase 2).

---

### **Architecture**

#### **Backend (pkm-indexer)**

* **Stack**: Python (FastAPI), `apscheduler`, `frontmatter`, `shutil`, `openai`, `faiss`, `langchain`

* **Deployment**: Railway — `pkm-indexer-production.up.railway.app`

* **Core Responsibilities**:

  * Monitor/sync files from Inbox
  * Generate metadata using OpenAI (LangChain planned Phase 2)
  * Convert content to markdown + YAML frontmatter
  * Organize into Staging or Areas directories
  * Index and serve search endpoints

* **Key Modules**:

  * `main.py`: API endpoints `/staging`, `/approve`, `/trigger-organize`, `/files/{folder}`, `/file-content/{folder}/{filename}`, `/upload/{folder}`
  * `organize.py`: Organizes and enriches files with metadata (currently OpenAI API, LangChain coming Phase 2)
  * `index.py`: Indexes markdown via FAISS; LangChain-powered retrieval in Phase 2

* **Key Directories**:

  * `pkm/Inbox` — temporary holding area
  * `pkm/Staging` — review queue
  * `pkm/Areas/<category>` — finalized, structured storage
  * `pkm/Logs/` — error tracking

#### **Frontend (pkm-app)**

* **Stack**: Next.js PWA, React, Axios

* **Deployment**: Railway — `pkm-app-production.up.railway.app`

* **Core Responsibilities**:

  * Review and approve staged files
  * Search indexed KB
  * Upload markdown files (temporary MVP workflow)

* **Key Components**:

  * `index.js`: Search bar + file upload
  * `staging.js`: Review interface for files
  * `StagingForm.js`: Approve or edit metadata

---

### **Use of LangChain (Planned for Phase 2)**

LangChain will modularize prompt workflows and search pipelines:

* **Metadata Generation**:

  * Replace `get_metadata()` with LangChain chains
  * Use `PromptTemplate` + `RunnableSequence`
  * Chain: `summarize -> tag -> categorize`
* **Multi-Modal Content Handling**:

  * PDFs → text → summarize/tag
  * URLs → scrape → summarize/tag
  * Audio/video → Whisper → summarize/tag
* **Semantic Search Enhancements**:

  * Rewrite/expand queries
  * Maintain conversational context
  * Combine vector search with reasoning

LangChain is appropriate given your need for chaining, modularity, and multi-step AI workflows.

---

### **Metadata Format (YAML Frontmatter)**

```yaml
---
title: AI Drones Report
date: 2025-05-18
tags: [AI, drones, military]
category: Technology
source: military-ai-report.pdf
source_url: https://...
author: Unknown
summary: A report on AI drones in military operations.
reviewed: false
---
```

---

### **Workflow**

#### **Capture (Current: Temporary Upload | Future: OneDrive Sync)**

* Markdown files uploaded via `/upload/{folder}`
* In Phase 2: OneDrive folder watcher → `pkm/Inbox`

#### **Organize**

* `organize.py` parses markdown and enriches metadata
* Moves file to `pkm/Staging`
* Logs metadata extraction and issues
* Future: handle PDFs, audio, video, URLs

#### **Review**

* PWA shows staged files for approval
* User edits YAML frontmatter
* On approval, file moves to `pkm/Areas/<category>`

#### **Query**

* PWA sends query to `/search` (FAISS now)
* Phase 2: LangChain-enhanced retriever with semantic rephrasing

---

### **Current Status (MVP)**

* **Backend**: Deployed; API endpoints live
* **Frontend**: Deployed; staging UI functional
* **Successes**:

  * `test-file.md` uploaded via frontend
  * Metadata generation logic in place
  * Logs added to `organize.py`
* **Known Issue**:

  * `test-file.md` is not moving from Inbox → Staging (likely resolved with API key fix)

---

### **Next Steps (Immediate)**

1. **Test Organize Again**

   * Confirm API key is now active
   * Re-trigger with `/trigger-organize`
   * Check logs for file detection, OpenAI call, file move

2. **Validate Output in `Staging`**

   * YAML generated?
   * Markdown readable?
   * Appears in PWA?

3. **Run Full Flow for `test-file.md`**

   * Upload → Organize → Review → Approve → Search

4. **Track All Logs and Exceptions**

   * Confirm graceful error handling

---

### **Next Steps (Phase 2 Build Plan)**

1. **LangChain Integration**

   * Refactor `organize.py` to use LCEL + prompt chaining
   * Extend `index.py` with LangChain Retriever wrappers

2. **File Type Expansion**

   * Add PDF and URL support first
   * Add Whisper for audio/video
   * Add OCR for images

3. **OneDrive Integration**

   * Sync folder to backend
   * Trigger organize task on file change

4. **Search UX Improvements**

   * Expand queries automatically
   * Add conversational history handling

---