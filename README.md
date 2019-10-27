# FunnelFoods Recommendation

Receipt parsing and recipe recommendation algorithms wrapped in Python Flask.

Build the project with Docker:

```bash
docker build . -t funnelfoods-recommendation
```

Then run the container created:

```bash
docker run -d -p 127.0.0.1:5000:5000/tcp funnelfoods-recommendation
```
