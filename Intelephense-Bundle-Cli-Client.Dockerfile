FROM node:22-alpine
RUN npm i intelephense -g
ENV PYTHONUNBUFFERED=1
RUN apk add --update --no-cache python3
#RUN ln -sf python3 /usr/bin/python
#RUN python3 -m ensurepip
#RUN pip3 install --no-cache --upgrade pip setuptools
COPY --chmod=755 client.py /root/client.py
ENTRYPOINT ["python", "/root/client.py", "/etc/intelephense-cli-config.json"]
