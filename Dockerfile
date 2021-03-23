# Basis Image
FROM python:3.9

# Umgebungsvariablen
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Working Directory
WORKDIR /code

# Dependencies
COPY Pipfile Pipfile.lock /code/
RUN pip install --trusted-host pypi.python.org --trusted-host files.pythonhosted.org --trusted-host pypi.org --upgrade pip
RUN pip install --trusted-host pypi.python.org --trusted-host files.pythonhosted.org --trusted-host pypi.org pipenv
RUN pipenv install --trusted-host pypi.python.org --trusted-host files.pythonhosted.org --trusted-host pypi.org --system

# Code Kopieren
COPY . /code/