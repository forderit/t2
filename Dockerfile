FROM python:3.9-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Use Railway's configuration
ENV PORT=8080
ENV STREAMLIT_SERVER_ADDRESS=0.0.0.0
ENV STREAMLIT_SERVER_BASEURL_PATH=/
ENV STREAMLIT_SERVER_PORT=8080

CMD streamlit run streamlit_app.py