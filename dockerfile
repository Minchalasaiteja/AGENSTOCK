# ============================================================
# Multi-stage Dockerfile for AGENSTOCK
# ============================================================

############################################################
# 1️⃣ Builder stage: install dependencies and build wheels
############################################################
FROM python:3.12-slim AS builder

# Environment setup
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# Copy dependency file
COPY requirements.txt ./

# Install build tools and create wheels for dependencies
RUN apt-get update && apt-get install -y --no-install-recommends build-essential && \
    pip install --upgrade pip && \
    pip wheel --wheel-dir /wheels -r requirements.txt && \
    apt-get purge -y --auto-remove build-essential && \
    rm -rf /var/lib/apt/lists/*

############################################################
# 2️⃣ Runtime stage: minimal final image
############################################################
FROM python:3.12-slim AS runtime

# Environment setup
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# -----------------------------------------------------------
# Create a non-root user
# (Fixed: use correct Debian syntax)
# -----------------------------------------------------------
RUN addgroup --system app && adduser --system --ingroup app app

# -----------------------------------------------------------
# Copy dependencies from builder and install from local wheels
# -----------------------------------------------------------
COPY requirements.txt .
COPY --from=builder /wheels /wheels
RUN pip install --no-cache-dir --no-index --find-links=/wheels -r requirements.txt

# -----------------------------------------------------------
# Copy the application code
# -----------------------------------------------------------
COPY . /app

# Fix permissions
RUN chown -R app:app /app

# Matplotlib config
ENV MPLCONFIGDIR=/app/.config/matplotlib
RUN mkdir -p /app/.config/matplotlib && chown -R app:app /app/.config

USER app

# -----------------------------------------------------------
# Expose port and configure healthcheck
# -----------------------------------------------------------
EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=5s \
  CMD curl -f http://127.0.0.1:8000/health || exit 1

# -----------------------------------------------------------
# Run the FastAPI app using Uvicorn
# -----------------------------------------------------------
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "1"]
