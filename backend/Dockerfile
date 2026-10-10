FROM python:3.12-slim

# System deps: binutils for `strings` (binary scanner), git for repo cloning,
# and curl for the Syft install script.
RUN apt-get update && apt-get install -y --no-install-recommends \
    binutils git curl ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Syft — used by the container image scanner (Phase 3)
RUN curl -sSfL https://raw.githubusercontent.com/anchore/syft/main/install.sh \
    | sh -s -- -b /usr/local/bin

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

ENV DATABASE_URL=sqlite:////data/ecdat.db
ENV UPLOAD_DIR=/data/uploads
ENV FRONTEND_ORIGIN=http://localhost:5173
RUN mkdir -p /data/uploads

EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
