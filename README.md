# Abduvaliy Abdulazizov

### Software developer · AI-enabled backends & automation

I build APIs, AI integrations, and operational tools—from OCR services and messaging bots to dashboards backed by real data. My work spans implementation, regression testing, deployment, and Linux troubleshooting.

`Python / FastAPI` · `APIs & integrations` · `Docker / Linux`

## What I build

- **AI-enabled services:** OCR pipelines, LLM integrations, and independently deployed MCP services.
- **Workflow software:** Telegram/Discord automation and operational dashboards with authentication and persistent data.
- **Deployment tooling:** containerized services, CI checks, migration safeguards, and production debugging.

## Selected work

**OCR service & Telegram integration**\
Built a FastAPI service with job, status, result, and retry endpoints using Ollama-backed OCR. Connected incoming Telegram images to stored transcripts and summaries; deployed the service independently and fixed repeating output without dropping genuine text.\
`Python` `FastAPI` `Ollama` `Docker`

**Computer-vision operations dashboard — team contributions**\
Replaced mock camera configuration with database-backed APIs; implemented history views and detection workflows. Contributed authentication, tenant-isolation, rate-limit, and PostgreSQL listener fixes across the dashboard and backend.\
`React / TypeScript` `Express` `Sequelize` `PostgreSQL`

**AI chat → PDF/DOCX export**\
Shipped document export from Telegram answers in a CRM-integrated assistant. Fixed table formatting, duplicate exports, split-message ordering, and a slow-render lock bottleneck; tested the complete flow and deployed it to production.\
`Ruby / Chatwoot` `Telegram Bot API` `Regression tests`

<details>
<summary><strong>More work: service boundaries, personal automation & Linux</strong></summary>

<br>

**Independent MCP service & deployment operations**\
Separated MCP authentication, monitoring, and deployment from a legacy runtime. Contributed Docker-stack and observability migrations with backups, health checks, and data-integrity verification.\
`MCP` `Docker Compose` `Linux`

**Solo-Tracker — personal project**\
Released and deployed a Discord productivity-tracker MVP with daily quest parsing, XP/streaks, weekly reports, and a dashboard. Added GitHub Actions CI and AI-generated quests.\
`Discord` `Fastify` `Vite` `Docker`

**[Acer Nitro Linux camera fix](https://github.com/abduvaliy-engineer/acer-nitro-anv16s-camera-fix) — personal / open source**\
Traced a missing webcam to ACPI GPIO interrupt handling that cut its power. Verified a boot workaround, published reversible installer/check tooling, and submitted a Linux DMI-quirk patch upstream.

</details>

## Stack

| Area | Repeatedly used in project work |
| :--- | :--- |
| Languages | Python · JavaScript / TypeScript · SQL |
| Backend & interfaces | FastAPI · Express · React · REST APIs |
| AI integrations | LLM APIs · Ollama-backed OCR · MCP |
| Data | PostgreSQL · MySQL · Redis |
| Delivery | Linux · Docker / Compose · Git · GitHub Actions |

**Additional working experience:** Ruby/Chatwoot, Nginx, SSH, Tailscale, and Discord integrations.\
**ML/data study and applied exercises:** pandas, NumPy, scikit-learn, model comparison and evaluation—not a claim of production ML-training expertise.

## Current focus · October 2026

- Completing live verification of Redis-backed SMS OTP and multilingual phone-verification flows; local checks pass, review and live SMS testing remain pending.
- Planning AI-answer evaluation, exact-source retrieval, and safe abstention; following up on the submitted Linux camera patch.

## Engineering areas

**Core:** API integration · backend automation · deployment/debugging\
**Also:** data-backed interfaces · service boundaries · authentication · regression testing

My work progressed from Python/CV prototypes and a deployed learning-challenge app to team dashboard contributions, independent OCR/MCP services, and production migrations.

## GitHub activity

![GitHub contribution snapshot for abduvaliy-engineer, January 1–October 4, 2026](assets/github-activity.svg)

<sub>GitHub API snapshot · 2026-01-01–2026-10-04 · contributions, not a commit count · no third-party stats widget.</sub>

## Links

[GitHub](https://github.com/abduvaliy-engineer) · [Linux camera fix](https://github.com/abduvaliy-engineer/acer-nitro-anv16s-camera-fix)
