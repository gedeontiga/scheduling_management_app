FROM python:3.12.3-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

WORKDIR /app/

COPY . /app

RUN pip install --no-cache-dir -r requirements.txt

# CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]
# CMD ["gunicorn", "config.wsgi:application", "--bind", "0.0.0.0:8000"]
# CMD ["sh", "-c", "python manage.py migrate && daphne -b 0.0.0.0 -p 8000 config.asgi:application"]
CMD ["sh", "-c", "python manage.py migrate && gunicorn -k daphne.gunicorn.GunicornDaphneWorker config.asgi:application --bind 0.0.0.0:8000"]
