FROM python:3.10.4-slim-bullseye

# prints outputs, does let them buffer.
#https://docs.python.org/3/using/cmdline.html#envvar-PYTHONUNBUFFERED
ENV PYTHONUNBUFFERED 1
ENV PYTHONDONTWRITEBYTECODE 1
ENV PIP_DISABLE_PIP_VERSION_CHECK 1 

#workdir inside the container
WORKDIR /app 
EXPOSE 8000

COPY ./requirements.txt .

RUN pip install -r requirements.txt

COPY . /app/