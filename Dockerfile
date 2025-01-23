FROM python:3.9-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Use Railway's PORT environment variable with a fallback
CMD streamlit run --server.port ${PORT:-8080} --server.address 0.0.0.0 streamlit_app.py