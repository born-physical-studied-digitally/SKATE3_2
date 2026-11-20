FROM python:3.10-slim

WORKDIR /work

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy your existing, unmodified package and install it
COPY pyproject.toml ./
COPY src/ ./src/
RUN pip install --no-cache-dir -e .

# Copy the plugin entrypoint
COPY run.py .

ENTRYPOINT ["python", "run.py"]