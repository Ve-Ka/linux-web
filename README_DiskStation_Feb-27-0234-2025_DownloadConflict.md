# linux-web

This project was created for me to spin up clean docker images for linux command testing or various other experiments that require clean slate.

Core Tech:
- Python3 (Flask)
- 
- TTYD


## Build & Run locally

```
docker build -t linux-web .
docker run -d -p 3000:80 --privileged --name linux-web linux-web
```

Navigate to http://localhost:3000


# Build Using docker-compose.yml

Mounting of docker volume is optional if you choose to keep any created docker in the event of rebuild

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

