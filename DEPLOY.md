# Device Tag

## AWS Lightsail Deployment

### Build Docker Image

```bash
docker build --no-cache -t devicetag .
```

### Tag Docker Image

```bash
docker tag devicetag <user_docker_hub>/devicetag:latest
```

### Push Docker Image

```bash
docker push <user_docker_hub>/devicetag:latest
```

─────────────────────────────────────────

## Local Deployment

### Build Docker Image Local

```bash
docker build --no-cache -t devicetag .
```

### Up Docker Image

```bash
docker run -p 8000:8000 devicetag
```
