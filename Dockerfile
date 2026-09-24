FROM python:3.12-slim
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
WORKDIR /app
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt && useradd --uid 10001 --create-home collector
COPY collector ./collector
COPY api ./api
COPY zabbix ./zabbix
COPY main.py ./
RUN mkdir -p /app/logs && chown collector:collector /app/logs
USER collector
HEALTHCHECK --interval=30s --timeout=5s --start-period=60s --retries=3 CMD ["python", "main.py", "--healthcheck"]
CMD ["python", "main.py", "--daemon"]
