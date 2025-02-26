# Linux-Web

This project was created for me to spin up docker images for linux command testing or various other experiments that requires clean slate, also this is portable as you can navigate to URL (with proper setup) on any device to test out docker instead of needing to go thorough trouble of installing docker on machine... needing to remember which command to spin up specific docker container... and other incovinience...



## Tech Stack

- Backend: Python3 (Flask)
- Frontend: HTML, CSS, JS (Vanilla)
- TTYD (Credit: https://github.com/tsl0922/ttyd)
- iframe
- Nginx
- Docker
- Docker in Docker



## Build & Run locally

```
docker build -t linux-web .
docker run -d -p 3000:80 --privileged --name linux-web linux-web
```

Navigate to `http://localhost:3000`



## Build Using docker-compose.yml

Mounting of docker `volumes:` is optional if you choose to keep any created docker in the event of rebuild

```
services:
  linux-web:
    image: linux-web
    container_name: linux-web
    privileged: true
    build:
      context: https://github.com/Ve-Ka/linux-web.git
      dockerfile: Dockerfile
    ports:
      - 3000:80
    volumes:
      - /Docker/Linux-Web:/var/lib/docker
```
