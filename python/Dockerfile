FROM python:3.7.8
ENV PYTHONPATH "${PYTHONPATH}:/portal"
ENV PYTHONUNBUFFERED 1
RUN mkdir /code
WORKDIR /code
RUN apt-get update && apt-get install -y wkhtmltopdf && apt-get clean;
RUN wget https://moji.or.jp/wp-content/ipafont/IPAexfont/IPAexfont00401.zip \
    && unzip IPAexfont00401.zip \
    && mv IPAexfont00401 /usr/share/fonts \
    && fc-cache -f
ADD ./src/portal/requirements.txt /code/
RUN pip install -r requirements.txt
ADD . /code/