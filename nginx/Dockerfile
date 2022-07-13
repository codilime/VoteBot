FROM nginx:1.23.0

RUN rm /etc/nginx/conf.d/default.conf

COPY nginx/nginx.conf /etc/nginx/conf.d
COPY static/ /var/www/static/
