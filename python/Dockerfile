FROM python:3.7.8
ENV PYTHONPATH "${PYTHONPATH}:/portal"
ENV PYTHONUNBUFFERED 1
RUN mkdir /code
WORKDIR /code
ADD ./src/portal/requirements.txt /code/
RUN pip install -r requirements.txt
ADD . /code/