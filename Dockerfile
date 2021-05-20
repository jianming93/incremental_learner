FROM python:3.7.10

COPY . /app

WORKDIR /app

RUN mkdir images

RUN pip install -r requirements.txt

EXPOSE 8000

ENTRYPOINT [ "python" ]
CMD ["index.py"]