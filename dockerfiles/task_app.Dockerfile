FROM python:3.7.10

COPY requirements.txt .

RUN pip install -r requirements.txt

RUN rm requirements.txt

COPY . /app

WORKDIR /app

RUN mkdir {images, logs}

EXPOSE 7000

ENTRYPOINT [ "python" ]
CMD ["task_app.py"]