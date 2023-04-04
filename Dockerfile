FROM python:slim

RUN useradd homeroomconditions

WORKDIR /home/homeroomconditions

COPY requirements.txt requirements.txt
RUN python -m venv venv
RUN venv/bin/pip install -r requirements.txt
# RUN venv/bin/pip install gunicorn

COPY app app
COPY migrations migrations
COPY homeroomconditions.py config.py boot.sh ./
RUN chmod +x boot.sh

ENV FLASK_APP homeroomconditions.py

RUN chown -R homeroomconditions:homeroomconditions ./
USER homeroomconditions

EXPOSE 5000
ENTRYPOINT ["./boot.sh"]