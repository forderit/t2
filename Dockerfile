FROM python:3.9-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Create a startup script
RUN echo '#!/bin/bash\nstreamlit run --server.port 8080 --server.address 0.0.0.0 streamlit_app.py' > start.sh && \
    chmod +x start.sh

CMD ["./start.sh"]