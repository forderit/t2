FROM python:3.9-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Print environment variables and run streamlit
CMD echo "PORT=${PORT}" && \
    echo "Environment variables:" && \
    env && \
    streamlit run --server.port ${PORT:-8080} --server.address 0.0.0.0 streamlit_app.py