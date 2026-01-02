# Multi-stage build for smaller image size
# Stage 1: Build stage with build dependencies
FROM python:3.12-slim as builder

# Install system dependencies needed for building Python packages
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements and install Python packages
COPY requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt
RUN pip install --no-cache-dir --user pytest pytest-cov

# Stage 2: Runtime stage
FROM python:3.12-slim

# Install only runtime system dependencies (if any needed)
# Most Python packages don't need build tools at runtime
RUN apt-get update && apt-get install -y --no-install-recommends \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user for security
RUN useradd -m -u 1000 testuser

# Set working directory
WORKDIR /app

# Copy installed packages from builder stage
COPY --from=builder /root/.local /home/testuser/.local

# Create tests directory and set ownership
RUN mkdir -p /app/tests && \
    chown -R testuser:testuser /app /home/testuser/.local

# Copy application code (if needed for tests)
# COPY --chown=testuser:testuser . /app

# Switch to non-root user
USER testuser

# Add local bin to PATH for user-installed packages
ENV PATH=/home/testuser/.local/bin:$PATH

# Configure pytest to output in parseable format
ENV PYTEST_CURRENT_TEST=""

# Default command: pytest with verbose output
CMD ["pytest", "-v", "--tb=short", "--junitxml=/app/test-results.xml", "/app/tests"]

