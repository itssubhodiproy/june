# Project Roadmap & TODOs

This document tracks planned improvements, optimizations, and features for the June platform, organized by service.

---

## 🏗️ Services Overview

### 📄 Document Worker
| Priority | Task | Rationale | Impact |
|:---|:---|:---|:---|
| **High** | **Parallel Embedding Batching** | **Why**: Currently, the worker processes embedding batches sequentially. Moving to parallel execution (`asyncio.gather`) within the `EmbeddingClient` removes the O(N) bottleneck. <br> **Architecture**: Sits inside the Document Worker's ingestion pipeline. <br> **Impact**: Reduces "Time-to-Solid" (faded row to usable data). Saves money by maximizing worker instance utilization. | **Speed**: Latency per document drops from minutes to seconds. |
| **High** | **Exponential Backoff Retry** | **Why**: Current retries are immediate. A "Delay Queue" (using Redis ZSET or similar) is needed to prevent "retry storms" when an API is down or rate-limited. <br> **Impact**: System self-heals without hammering external APIs. | **Reliability**: Prevents resource exhaustion during outages. |

### 🤖 Extraction Worker
| Priority | Task | Rationale | Impact |
|:---|:---|:---|:---|
| **High** | **Exponential Backoff Retry** | **Why**: Mirroring the Document Worker, extraction retries should use a delayed mechanism to avoid hitting LLM rate limits immediately after a failure. <br> **Impact**: Higher success rate for large batch extractions. | **Reliability**: More robust handling of LLM API outages/limits. |

### 🌐 API Server
| Priority | Task | Rationale | Impact |
|:---|:---|:---|:---|
| | | | |

### 💻 Frontend
| Priority | Task | Rationale | Impact |
|:---|:---|:---|:---|
| | | | |

---

## 🛠️ Infrastructure & DevOps
- [ ] 

---

> [!NOTE]
> This is a living document. Add new items here instead of letting them clutter the core design docs. Keep entries concise.
