FROM python:3.8-alpine

WORKDIR /src/
COPY orderbook.py /src/
COPY requirements.txt /src/

RUN pip3 install -r requirements.txt
CMD [ "python3" , "./orderbook.py"]