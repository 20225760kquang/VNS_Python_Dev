FROM python:3.12-slim 

LABEL description="Personal Blog API with FastAPI & PostgreSQL" 

WORKDIR /app

# Cài đặt dependencies 
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000 

# Tạo user thay thế cho root
RUN adduser --disabled-password --gecos "" appuser

USER appuser

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
