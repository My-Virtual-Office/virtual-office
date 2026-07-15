# AI assistant service. Small Node/Express app: OpenAI function-calling on one
# side, the existing platform REST APIs (via the gateway) on the other.
FROM node:20-alpine

WORKDIR /app
RUN apk add --no-cache curl

COPY package.json ./
RUN npm install --omit=dev --no-audit --no-fund

COPY server.js ./

EXPOSE 8089
# OPENAI_API_KEY / GATEWAY_URL / OPENAI_MODEL are injected by compose.
CMD ["node", "server.js"]
