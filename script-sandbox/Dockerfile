FROM python:3.10-slim

WORKDIR /app

# Create a non-privileged sandbox user and group
RUN groupadd -g 10001 sandbox && \
    useradd -u 10001 -g sandbox -m -d /home/sandbox sandbox

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Set execution rights and switch to the sandbox user
RUN chown -R sandbox:sandbox /app
USER sandbox

EXPOSE 8005

CMD ["python", "server.py"]
