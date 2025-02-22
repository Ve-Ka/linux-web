from flask import Flask, request, jsonify
import docker
import random
import subprocess
import threading
import inspect

app = Flask(__name__)
client = docker.DockerClient(base_url='unix:///var/run/docker.sock')

DISTROS = {
    "ubuntu": {
        "22.04": "ubuntu:22.04",
        "24.10": "ubuntu:24.10",
        "25.04": "ubuntu:25.04",
        "latest": "ubuntu:latest"
    },
    "debian": {
        "10": "debian:10",
        "11": "debian:11",
        "12": "debian:12",
        "latest": "debian:latest"
    },
    "alpine": {
        "3.19": "alpine:3.19",
        "3.20": "alpine:3.20",
        "3.21": "alpine:3.21",
        "latest": "alpine:latest"
    },
    "nginx": {
        "debian": "nginx:bookworm",
        "alpine": "nginx:alpine",
        "latest": "nginx:latest"
    },
    "node": {
        "23-alpine": "node:23-alpine",
        "23-bookworm": "node:23-bookworm",
        "22-alpine": "node:23-alpine",
        "22-bookworm": "node:23-bookworm",
        "latest": "node:latest"
    }
}


@app.route('/distros', methods=['GET'])
def get_distros():
    return jsonify(DISTROS)  # Send DISTROS dictionary as JSON


def update_nginx():
    config_file = "/etc/nginx/http.d/dynamic_proxy.conf"

    try:
        with open(config_file, "w") as f:
            f.write("# Dynamically generated proxy rules\n")

            containers = client.containers.list()
            for container in containers:
                try:
                    port = container.attrs['NetworkSettings']['Ports']['7681/tcp'][0]['HostPort']
                    if port:
                        f.write(f"""
location /{port}/ {{
    proxy_pass http://localhost:{port}/;
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_http_version 1.1;
    proxy_set_header Upgrade $http_upgrade;
    proxy_set_header Connection "upgrade";
}}\n""")
                except Exception as e:
                    function_name = inspect.currentframe().f_code.co_name
                    print(f"Error in function '{function_name}': {e}")

        # Reload Nginx to apply changes
        subprocess.run(["nginx", "-s", "reload"], check=True)

    except Exception as e:
        function_name = inspect.currentframe().f_code.co_name
        print(f"Error in function '{function_name}': {e}")


@app.route('/start', methods=['POST'])
def start_container():
    data = request.json
    distro = data.get("distro")
    version = data.get("version")
    custom_name = data.get("name")
    image = DISTROS.get(distro, {}).get(version)

    # Ensure 'latest' always pulls the newest version
    if version == "latest":
        try:
            client.images.pull(image)
        except Exception as e:
            function_name = inspect.currentframe().f_code.co_name
            print(f"Error in function '{function_name}': {e}")

    # Different command for Debian/Ubuntu to install ttyd
    if distro in ["ubuntu", "debian"] or (distro == "nginx" and version != "alpine"):
        command = (
            "sh -c 'apt update && apt install -y curl && "
            "curl -Lo /usr/local/bin/ttyd https://github.com/tsl0922/ttyd/releases/latest/download/ttyd.x86_64 && "
            "chmod +x /usr/local/bin/ttyd && "
            "ttyd -W bash & exec sleep infinity'"
        )
    else:
        command = "sh -c 'apk add --no-cache ttyd && ttyd -W sh & exec sleep infinity'"

    container = client.containers.run(
        image,
        detach=True,
        ports={'7681/tcp': None},
        command=command,
        name=custom_name if custom_name else None
    )

    update_nginx()

    return jsonify({"message": "Container started", "id": container.id, "name": container.name})


@app.route('/list', methods=['GET'])
def list_containers():
    containers = client.containers.list()
    
    # Extract all image names into a set
    valid_images = {image for versions in DISTROS.values() for image in versions.values()}
    
    result = [
        {
            "id": c.id[:12],
            "name": c.name,
            "status": c.status,
            "image": c.image.tags[0] if c.image.tags else c.image.id,
            "port": next(iter(c.ports.values()))[0]["HostPort"] if c.ports else "N/A"
        }
        for c in containers
        if any(tag in valid_images for tag in c.image.tags)  # Filter containers by image
    ]

    return jsonify(result)


@app.route('/delete', methods=['POST'])
def stop_container():
    data = request.json
    container_id = data.get("id")
    try:
        container = client.containers.get(container_id)
        container.stop()
        container.remove()
        update_nginx()
        return jsonify({"message": "Container deleted"})
    except Exception as e:
        function_name = inspect.currentframe().f_code.co_name
        print(f"Error in function '{function_name}': {e}")
    

def pre_pull_images():
    print("Pulling required images...")
    for distro, versions in DISTROS.items():  
        for version, image in versions.items(): 
            try:
                print(f"Pulling {image} for {distro} {version}...")
                threading.Thread(target=client.images.pull, args=(image,), daemon=True).start()
                # client.images.pull(image)
                print(f"✔ {image} ready!")
            except Exception as e:
                function_name = inspect.currentframe().f_code.co_name
                print(f"Error in function '{function_name}': {e}")


def start_docker_on_restart():
    try:        
        containers = client.containers.list(all=True)
        for container in containers:
            if container.status != 'running':
                print(f"Starting container {container.name}...")
                container.start()
    except Exception as e:
        function_name = inspect.currentframe().f_code.co_name
        print(f"Error in function '{function_name}': {e}")
    
    update_nginx()

if __name__ == "__main__":
    pre_pull_images()    
    start_docker_on_restart()
    app.run(host="0.0.0.0", port=5000, debug=True)
    

