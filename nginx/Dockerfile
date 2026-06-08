FROM nginx:alpine
ENV PIP_ROOT_USER_ACTION=ignore
RUN apk add --no-cache bash openssl
COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh
EXPOSE 80 443
ENTRYPOINT ["/entrypoint.sh"]
CMD ["nginx", "-g", "daemon off;"]
