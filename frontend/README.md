# JanSahayak AI — Frontend

Multilingual Indian Government Scheme Explainer frontend built with **Next.js 14**, **TypeScript**, **Tailwind CSS**, and **shadcn/ui**.

## Features

- **🌐 Trilingual Support**: English, Hindi (हिंदी), and Telugu (తెలుగు) with native typography and smooth language switching.
- **🤖 Conversational AI Assistant**: Chat with source-grounded AI regarding schemes, subsidies, and citizen rights. Includes voice STT and TTS synthesis.
- **📑 Scheme Explorer**: Search and filter over 500+ Central and State welfare initiatives by state, sector, and beneficiary group.
- **🎯 Step-by-Step Eligibility Engine**: 5-step wizard assessing personal, financial, and occupational criteria with condition breakdowns and application roadmaps.
- **📄 Official Document & Circular Analyzer**: Upload government gazettes and guideline PDFs for clause extraction, deadline identification, and interactive Q&A.
- **🛡️ 100% Verified Citations**: Every claim is cited with direct links to official Indian portals (`myScheme.gov.in`, `india.gov.in`, `data.gov.in`).

## Getting Started

1. Install dependencies:
```bash
npm install
```

2. Start the development server:
```bash
npm run dev
```

3. Open [http://localhost:3000](http://localhost:3000) with your browser.

## Configuration

Environment settings are configured in `.env.local`:
```
NEXT_PUBLIC_BACKEND_URL=http://localhost:8000
NEXT_PUBLIC_APP_NAME=JanSahayak AI
```
