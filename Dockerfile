FROM python:3.9-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

ENV PORT=8501
CMD streamlit run --server.port $PORT --server.address 0.0.0.0 streamlit_app.py