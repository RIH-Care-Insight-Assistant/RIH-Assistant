# Frontend image: static React build served by unprivileged nginx, which also proxies /api.
# Bases pinned by digest (node:24-alpine 2026-10-14; nginx-unprivileged:1.30-alpine 2026-10-14,
# chosen over 1.28-alpine after the container scan found 68 fixable OS CVEs in the older base).
FROM node@sha256:44fce696f38ba8c987c4db89954051000bbd05ffd8d8659ba15ed4a8602e937f AS build
WORKDIR /src
COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci --no-audit --no-fund
COPY frontend/ ./
RUN npm run build

FROM nginxinc/nginx-unprivileged@sha256:782bb89768cc87b7f95c18b95baa1af250e5d451f26794f59363540161147c01 AS runtime
LABEL org.opencontainers.image.title="rih-frontend" \
      org.opencontainers.image.description="RIH Care Insight Assistant web UI (independent student prototype)"
ENV BACKEND_UPSTREAM=http://backend:8000 \
    NGINX_ENTRYPOINT_LOCAL_RESOLVERS=1
COPY deploy/nginx/default.conf.template /etc/nginx/templates/default.conf.template
COPY --from=build /src/dist /usr/share/nginx/html
USER 101
EXPOSE 8080
HEALTHCHECK --interval=15s --timeout=3s --start-period=5s --retries=3 \
  CMD ["wget", "-q", "-O", "/dev/null", "http://127.0.0.1:8080/healthz"]
