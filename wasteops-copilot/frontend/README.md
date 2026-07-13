# WasteOps management dashboard

Next.js management dashboard for the WasteOps FastAPI backend.

## Install

```bash
cd frontend
npm install
```

## Environment

```bash
cp .env.example .env.local
```

`NEXT_PUBLIC_API_BASE_URL` must point to the FastAPI server. All `NEXT_PUBLIC_*` values are visible to browsers and must never contain secrets. Page flags control presentation only; they are not authorization.

## Commands

```bash
npm run dev
npm run typecheck
npm run lint
npm run test
npm run test:e2e
npm run build
```

The main pages cover operational overview, unified AI assistance, analytics, decision support, bins, trucks, workforce, documents, ingestion, evaluations, safe traces, and prompt versions. Citation chips distinguish document `[S1]`, database `[D1]`, configured rule `[R1]`, and model `[M1]` evidence. Synthetic documents are visibly labeled and never presented as official.

Decision recommendations always show the human-approval requirement and expose no execution action. Rule alerts are not predictions, and confidence is explained as evidence quality rather than correctness probability.

Production authentication and role-based access control are not implemented yet. Protect administrative backend APIs before deployment. The frontend intentionally contains no action-execution features.
