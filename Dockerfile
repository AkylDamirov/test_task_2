FROM python:3.9-slim

ENV PYTHONUNBUFFERED 1

WORKDIR /task

COPY requirements.txt ./

RUN pip3 install --no-cache-dir -r requirements.txt

COPY task.py .

CMD ["uvicorn", "task:app", "--host", "0.0.0.0", "--port", "8000"]