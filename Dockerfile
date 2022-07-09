FROM python:3.8-buster 
 
RUN curl https://packages.microsoft.com/keys/microsoft.asc | apt-key add - 
RUN curl https://packages.microsoft.com/config/debian/10/prod.list > /etc/apt/sources.list.d/mssql-release.list 
RUN apt-get update 
RUN ACCEPT_EULA=Y apt-get install -y msodbcsql17 
 
RUN mkdir /app 
WORKDIR /app 
ADD requirements.txt /app/ 
RUN apt-get update && apt-get install -y --no-install-recommends \ 
    unixodbc-dev \ 
    unixodbc \ 
    libpq-dev 
RUN pip install -r requirements.txt 
ADD . /app/ 
 
ENV ENV='PRODUCTION' 
ENTRYPOINT [ "python" ] 
CMD ["index.py"]