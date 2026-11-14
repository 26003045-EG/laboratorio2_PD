FROM python:3.11.11-slim
WORKDIR /project
ENV PYTHONUNBUFFERED=1 PIP_NO_CACHE_DIR=1
COPY requirements.txt /project/requirements.txt
RUN pip install --no-cache-dir -r requirements.txt
COPY app /project/app
COPY training /project/training
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
