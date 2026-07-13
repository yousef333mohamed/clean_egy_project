FROM node:22-alpine AS dependencies
WORKDIR /app
COPY package.json package-lock.json ./
RUN npm ci

FROM node:22-alpine AS builder
WORKDIR /app
COPY --from=dependencies /app/node_modules ./node_modules
COPY . .
ARG NEXT_PUBLIC_APP_NAME="WasteOps Decision Intelligence Copilot"
ARG NEXT_PUBLIC_API_BASE_URL="http://localhost:8000"
ARG NEXT_PUBLIC_APP_ENV="production"
ARG NEXT_PUBLIC_ENABLE_ADMIN_PAGES="true"
ARG NEXT_PUBLIC_ENABLE_INGESTION_PAGES="true"
ARG NEXT_PUBLIC_ENABLE_EVALUATION_PAGES="true"
ARG NEXT_PUBLIC_ENABLE_PROMPT_PAGES="true"
ARG NEXT_PUBLIC_DEFAULT_LANGUAGE="en"
ARG NEXT_PUBLIC_DEFAULT_TIMEZONE="Africa/Cairo"
ENV NEXT_PUBLIC_APP_NAME=$NEXT_PUBLIC_APP_NAME NEXT_PUBLIC_API_BASE_URL=$NEXT_PUBLIC_API_BASE_URL NEXT_PUBLIC_APP_ENV=$NEXT_PUBLIC_APP_ENV NEXT_PUBLIC_ENABLE_ADMIN_PAGES=$NEXT_PUBLIC_ENABLE_ADMIN_PAGES NEXT_PUBLIC_ENABLE_INGESTION_PAGES=$NEXT_PUBLIC_ENABLE_INGESTION_PAGES NEXT_PUBLIC_ENABLE_EVALUATION_PAGES=$NEXT_PUBLIC_ENABLE_EVALUATION_PAGES NEXT_PUBLIC_ENABLE_PROMPT_PAGES=$NEXT_PUBLIC_ENABLE_PROMPT_PAGES NEXT_PUBLIC_DEFAULT_LANGUAGE=$NEXT_PUBLIC_DEFAULT_LANGUAGE NEXT_PUBLIC_DEFAULT_TIMEZONE=$NEXT_PUBLIC_DEFAULT_TIMEZONE
RUN npm run build

FROM node:22-alpine AS runtime
WORKDIR /app
ENV NODE_ENV=production NEXT_TELEMETRY_DISABLED=1 PORT=3000 HOSTNAME=0.0.0.0
RUN addgroup --system --gid 1001 nodejs && adduser --system --uid 1001 nextjs
COPY --from=builder --chown=nextjs:nodejs /app/.next/standalone ./
COPY --from=builder --chown=nextjs:nodejs /app/.next/static ./.next/static
COPY --from=builder --chown=nextjs:nodejs /app/public ./public
USER nextjs
EXPOSE 3000
HEALTHCHECK --interval=30s --timeout=5s --retries=3 CMD node -e "fetch('http://127.0.0.1:3000/api/health').then(r=>{if(!r.ok)process.exit(1)}).catch(()=>process.exit(1))"
CMD ["node", "server.js"]
