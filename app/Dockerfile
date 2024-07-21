FROM python:3.9-bullseye

RUN apt-get update

# get curl for healthchecks
RUN apt-get install -y curl

# install latex
RUN apt-get install -y texlive-latex-extra

# permissions and nonroot user for tightened security
RUN adduser --disabled-password nonroot
RUN mkdir /home/app/ && chown -R nonroot:nonroot /home/app
RUN mkdir -p /var/log/tfomat && touch /var/log/tfomat/tfomat.err.log && touch /var/log/tfomat/tfomat.out.log
RUN chown -R nonroot:nonroot /var/log/tfomat
WORKDIR /home/app
USER nonroot

# copy all the files to the container
COPY --chown=nonroot:nonroot src /home/app/src
COPY --chown=nonroot:nonroot pyproject.toml /home/app
COPY --chown=nonroot:nonroot README.md /home/app
COPY --chown=nonroot:nonroot LICENSE /home/app
COPY --chown=nonroot:nonroot .env /home/app
COPY --chown=nonroot:nonroot app/* /home/app

# venv
ENV VIRTUAL_ENV=/home/app/venv

# python setup
RUN python -m venv $VIRTUAL_ENV
ENV PATH="$VIRTUAL_ENV/bin:$PATH"
RUN pip install --upgrade pip
RUN pip install -r requirements.txt
RUN pip install .

EXPOSE 5000

CMD ["python", "wsgi.py"]
