# <img src="https://raw.githubusercontent.com/kenokrieger/werderDatenbank/master/LOGO.png" alt="tfomat" height=60>

## About

tfomat is a Python Flask application designed to host a small webserver that
automatically fetches club specific results from [ladv](https://ladv.de). The
application features its own database for club athletes and results, as well as
internal rankings for club athletes.

## Install

### Prerequisites

Create a `.env` file in the directory where you want to run the application
(in case of an [installation via docker](#Docker) place the file in the same
directory as the `compose.yaml`). The content of the file should be as follows
```text
API-KEY = <choose-an-api-key-for-tfomat>
LADV-API-KEY = <your-api-key-for-ladv>
```
where you replace `<choose-an-api-key-for-tfomat>` with a string of your choice
which will be the API key for tfomat. To integrate [ladv](https://ladv.de) in
the application, replace `<your-api-key-for-ladv>` with a valid API key for ladv.
You may emit this line, but some parts of the application are not going not work 
properly.

Next up, you want to customise the application for your club. You can do so by
editing the app's configuration found under `src/tfomat/config.py`. Here,
change the variables `CLUB_NAME` and `CLUB_ID` to the name and the id of
your club as listed in ladv (you can find out the club id by querying 
`https://ladv.de/api/<api_key>/athletDetail?id=<athlete_id>` for any member of 
the club and looking at the `vereinnumber` field of the response). 


To use the pdf export of results, a suitable pdflatex installation is required.
For example
```bash
sudo apt-get install texlive-latex-extra
```

### Install via pip

You can install the package directly from [GitHub](https://github.com/kenokrieger/werderDatenbank) by running
```bash
pip install git+https://github.com/kenokrieger/werderDatenbank
```
or download the source code of the latest 
[release](https://github.com/kenokrieger/werderDatenbank/releases/latest)
and then run
```bash
python3 -m pip install .
``` 
in the top-level directory to install the package.

### Docker

To use the docker image, download the latest [release](https://github.com/kenokrieger/werderDatenbank/releases/latest) and run
```bash
docker compose build
``` 
to build the container.

## Usage

### Local

To run the application locally, execute
```
tfomat-up
```
to start the server at localhost with the port specified in the app's 
configuration (by default port 5000).

### Docker

To run the docker application execute
```bash
docker compose up
```
to start the application. By default, the nginx container will open the
connection at localhost:80.

### Apache

To use the application with Apache, you can install the 
[package via pip]("#install-via-pip") and use the file at 
`app/wsgi.py` for the wsgi configuration of Apache (
to incorporate wsgi application in Apache see, for example,
[https://wiki.ubuntuusers.de/Apache/mod_wsgi/](https://wiki.ubuntuusers.de/Apache/mod_wsgi/)
)

## License

This project is licensed under GNU GENERAL PUBLIC LICENSE.
For more details see the LICENSE file.
