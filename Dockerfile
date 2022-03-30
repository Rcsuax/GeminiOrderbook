FROM python:3.8-alpine

WORKDIR /src/
COPY gemini.py /src/
COPY requirements.txt /src/

RUN pip3 install -r requirements.txt
CMD [ "python3" , "./gemini.py"]