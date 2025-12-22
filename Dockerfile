# Use lightweight Linux-based Python image -> Base Image
FROM python:3.11-slim

# Set working directory inside container -> Workdir
WORKDIR /app

# Copy dependency file and install Python packages -> starter command
COPY requirements.txt .
RUN pip install -r requirements.txt

# Copy all project files -> copy
COPY . .

# Expose application ports -> port
EXPOSE 8000
EXPOSE 8501

# Start FastAPI and Streamlit together -> run command
CMD ["bash", "-c", "uvicorn src/main:app --host 0.0.0.0 --port 8000 & streamlit run frontend/app.py --server.port=8501 --server.address=0.0.0.0"]