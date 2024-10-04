FROM node:22-alpine
RUN npm i intelephense -g
#ENTRYPOINT ["intelephense", "--stdio"]
#ENTRYPOINT ["sh"]
ENTRYPOINT ["sleep", "99999999999"]
