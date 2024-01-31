FROM python:3.12.1-bookworm
WORKDIR /app
COPY . /app
RUN pip install -r requirements.txt
EXPOSE 8050
CMD ["python", "app.py"]