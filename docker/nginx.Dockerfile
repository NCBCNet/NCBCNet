# syntax=docker/dockerfile:1

# ============================================================================
# NCBCNet nginx image
#
# Multi-stage build:
#   Stage "build": compile the React SPA (frontend/ -> frontend/dist)
#   Stage runtime: nginx serving the built SPA + reverse-proxying Django
# ============================================================================

# ---- Stage 1: build the SPA ----
FROM node:20-alpine AS build
WORKDIR /app

# Install dependencies first (leverages layer caching)
COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci

# Copy the rest of the frontend source and build
COPY frontend/ ./
RUN npm run build

# ---- Stage 2: runtime ----
FROM nginx:1.27-alpine

# Built SPA (hashed assets under /usr/share/nginx/html/assets)
COPY --from=build /app/dist /usr/share/nginx/html

# Server config: SPA serving + proxy to the Django web service
COPY nginx/nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80 443
