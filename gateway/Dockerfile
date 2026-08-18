FROM nginx:stable-alpine

COPY nginx.conf /etc/nginx/nginx.conf

RUN mkdir -p \
        /tmp/nginx/client \
        /tmp/nginx/proxy \
        /tmp/nginx/fastcgi \
        /tmp/nginx/uwsgi \
        /tmp/nginx/scgi \
    && chown -R nginx:nginx /tmp/nginx

USER nginx

EXPOSE 8080

CMD ["nginx", "-g", "daemon off;"]
