### ** Short URL Demo - User Guide **

---

**📌 Project Overview**

`short_url_demo` is a URL shortening service built with FastAPI and Redis, providing quick URL shortening and redirection features. It supports one-click deployment with Docker.

---

**📂 Project Structure**

```
short_url_demo/
├── app/                # FastAPI application
│   ├── main.py         # Main entry point
│   ├── routers/        # API routes
│   └── utils/          # Utility functions
├── docker-compose.yml  # Docker Compose configuration
├── README.md           # User guide
└── data/               # Redis persistent data
```

---

### ** 1. Project Setup**

1. **Clone the project**

```bash
git clone https://github.com/ian293382/short_url_demo.git
cd short_url_demo
```

2. **Verify Docker Installation**

Make sure Docker is installed. If not, follow the official guide:

🔗 [Install Docker on Ubuntu](https://docs.docker.com/engine/install/ubuntu/#install-using-the-repository)

---

### ** 2. Build Docker Images**

#### **2.1 Build Web Service Image**

* **Option 1**: Build from source

```bash
cd app
docker image build --tag your_tag_name .
```

* **Option 2**: Pull from Docker Hub (Recommand)

```bash
docker pull ian293382/shorturl-web:latest
```

---

#### **2.2 Build Redis Service Image**

* **Option 1**: Use the official Redis image

```bash
docker pull redis:alpine
```

* **Option 2**: Use a custom Redis image

```bash
docker pull ian293382/shorturl-redis
```

---
when you run command : `docker image ls `
```bash
ian/Ian:~/short_url_demo$ docker image ls
REPOSITORY               TAG       IMAGE ID       CREATED        SIZE
ian293382/shorturl-web   latest    e61e35d72c61   14 hours ago   182MB
redis                    alpine    67ae465a4123   8 days ago     60.5MB
```

### ** 3. Start Docker Compose**

Run the following command in the project root directory:

```bash
# back to short_url_demo/
cd .. 
docker compose up -d
```

Successful startup example:

```
[+] Running 2/2
 ✔ Container short_url_demo-redis-1  Running                                                                                 0.0s 
 ✔ Container short_url_demo-web-1    Running                                                                                 0.0s
```

---

### ** 4. API Test the Short URL Service**

#### **4.1 Create a Short URL**

* **API Endpoint**: `http://{YOUR_VM_IP}:8000/docs`
OR `https://app.swaggerhub.com/apis-docs/MOSHOU5571228/short_url/1.0.0`

You can use the interactive Swagger UI for testing.

#### **4.2 Short URL Redirection**

* **Example**: `http://{YOUR_VM_IP}:8000/abcd1234`
* Avoid localhost:8000 in production, otherwise rate limiting and Redis data tracking may fail.

---

### **🛠️ 5. Health Check**

Verify service status:

```bash
docker compose ps
```

You should see a `healthy` status:

```
NAME                     STATE    STATUS
short_url_demo-web-1     Running  (healthy)
short_url_demo-redis-1   Running  (healthy)
```

---

### ** 6. Stop and Clean Up**

Stop and remove all containers:

```bash
docker compose down
```

---

### ** 7. Additional Information**

* **View Container Logs**

```bash
docker compose logs -f
```

* **Access the Web Container**

```bash
docker compose exec web bash
```

* **Access the Redis Container**

```bash
docker compose exec redis sh
redis-cli
ping

```
Redis Manual Check:
https://www.youtube.com/watch?v=dQw4w9WgXcQ Use in '/api/shorten'
```
127.0.0.1:6379> get url_mapping:https://www.youtube.com/watch?v=dQw4w9WgXcQ
"d71c4ee8"
127.0.0.1:6379> get d71c4ee8
"https://www.youtube.com/watch?v=dQw4w9WgXcQ"
127.0.0.1:6379> 
```
---

### ** 8. Contact**

If you have any questions, feel free to reach out:

* **GitHub**: [ian293382](https://github.com/ian293382)
* **Docker Hub**: [ian293382](https://hub.docker.com/u/ian293382)

###　what is next?
- Implement postgresql as to LAMP (Linux/nginx(Apache)/MySQL/PHP (Python))
- Implement nginx for rate limit from ref
- Write docker swarm init to use 3 nodes working.
