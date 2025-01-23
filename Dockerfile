FROM python:3.9-slim

WORKDIR /app

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application
COPY . .

# Expose port (will use Railway's PORT or default to 8501)
ENV PORT=${PORT:-8501}
EXPOSE ${PORT}

# Configure Streamlit
ENV STREAMLIT_SERVER_PORT=${PORT}
ENV STREAMLIT_SERVER_ADDRESS=0.0.0.0

# Command to run the application
CMD ["streamlit", "run", "streamlit_app.py"]