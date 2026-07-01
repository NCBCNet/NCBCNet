# NCBCNet

This project now uses a simplified workflow:

1. **Local development**: run Django and Vite directly on your machine, no Docker required.
2. **Production**: use Docker images, with Nginx handling TLS and Daphne serving internal HTTP.
3. **CI/CD**: GitHub Actions runs backend tests, frontend build, and Docker build/push to GHCR on push.

Quick start:

See `docs/DEVELOPMENT_AND_DEPLOYMENT_GUIDE.md` for the full workflow.