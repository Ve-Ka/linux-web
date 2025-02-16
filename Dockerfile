FROM docker:dind

RUN apk add --no-cache python3 py3-pip nginx

RUN python3 -m venv /venv
ENV PATH="/venv/bin:$PATH"

RUN pip3 install flask flask_cors docker

WORKDIR /app

COPY nginx.conf /etc/nginx/nginx.conf
COPY index.html .
COPY backend.py .
COPY favicon.ico .
RUN touch /etc/nginx/http.d/dynamic_proxy.conf

EXPOSE 80
USER root
CMD dockerd & sleep 5 && python3 backend.py & nginx -g "daemon off;"

