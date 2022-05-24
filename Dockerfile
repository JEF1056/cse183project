
FROM ubuntu:latest

ARG user=py4web

RUN apt update && \
    apt install -y git python3 python3-pip memcached && \
    service memcached restart && \
    groupadd -r $user && \
    useradd -m -r -g $user $user && \
    python3 -m pip install -U py4web pymysql

USER $user

RUN cd /home/$user/ && py4web setup --yes apps

EXPOSE 8000

WORKDIR /home/$user/

ARG build={{BUILD_HASH}}

RUN  git clone --branch xufanhuang https://github.com/JEF1056/cse183project.git apps/cse183

CMD py4web run --password_file password.txt --host 0.0.0.0 --port 8000 apps
