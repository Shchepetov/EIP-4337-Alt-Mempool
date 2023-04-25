FROM --platform=linux/amd64 ubuntu AS build-stage

ARG WEB3_QUICKNODE_KEY
ARG DEBIAN_FRONTEND=noninteractive

WORKDIR /usr/app
COPY ./ ./

RUN apt-get update && apt-get install -y sudo gnupg2 software-properties-common \
    nodejs npm postgresql postgresql-contrib gcc python3-dev python3-pip

RUN sudo npm install -g ganache-cli && npm install -g solc

RUN pip3 install -r requirements.txt

RUN brownie pm install OpenZeppelin/openzeppelin-contracts@4.8.2 && \
    brownie pm install safe-global/safe-contracts@1.3.0 && \
    rm -rf build/contracts/*.json && brownie compile

FROM build-stage AS run-stage

EXPOSE 8000

RUN service postgresql start && sudo -u postgres createdb mydb

RUN brownie run manage.py initialize_db

ENV WEB3_QUICKNODE_KEY=$WEB3_QUICKNODE_KEY

CMD ["bash", "-c", "brownie run manage.py initialize-db && uvicorn app.main:app --host 0.0.0.0 --port 8000"]