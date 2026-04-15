FROM python:3.9
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
WORKDIR /app/services/payment_service
ENV PYTHONPATH=/app
EXPOSE 5003
CMD ["python", "app.py"]
