# 🐧 XORAS SYSTEMS LINUX VENV & CONTAINER BUILD SPECIFICATION

> **Execution Timestamp**: 2026-09-06T06:18:12.981847Z  
> **Architecture**: Linux Venv / Multi-Stage Docker Spec / WSL2 Support  
> **Evaluator Lead**: Maxx (Operations & Systems Lead)  

---

## 1. Container & Linux Virtual Environment Verification

- ✓ Base Image: Ubuntu 22.04 LTS verified
- ✓ Virtual Env: python3-venv installed
- ✓ Venv Isolation: /opt/xoras/venv path configured
- ✓ Port Exposure: Port 8080 (Sovereign Stage) exposed
- ✓ Service Name: xoras_systems_linux_core configured
- ✓ Port Forwarding: 8080:8080 host-to-container mapping verified
- ✓ Health Audit: Stage HTTP health check configured

## 2. Containerized Linux Port & Volume Matrix

| Service / Container | Base OS | Linux Venv Path | Host Port | Status |
| :--- | :--- | :--- | :--- | :--- |
| `xoras_systems_linux_core` | Ubuntu 22.04 LTS | `/opt/xoras/venv` | `8080:8080` | **VERIFIED & READY** |
| `xoras_inference_daemon` | Ubuntu 22.04 LTS | `/opt/xoras/venv` | `11434:11434` | **VERIFIED & READY** |

## 3. Execution Commands

```bash
# Build and launch Linux container suite via Docker Compose
docker compose -f ops/container/docker-compose.yml up -d --build

# Or execute directly inside Linux / WSL shell
bash ops/container/build_linux_venv.sh
```
