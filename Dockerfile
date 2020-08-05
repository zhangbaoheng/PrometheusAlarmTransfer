FROM ubuntu

RUN rm /etc/apt/sources.list
COPY sources.list /etc/apt/sources.list

WORKDIR /app
ADD . /app

RUN apt-get update
RUN apt-get install -y python python-pip
RUN pip install --upgrade pip

RUN pip install -r requirements.txt

EXPOSE 8000

CMD ["python", "alarm.py"]