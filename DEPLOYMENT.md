# Deployment Guide - OTBI to DAX Converter

## 📋 Table of Contents

1. [Deployment Options](#deployment-options)
2. [Local Deployment](#local-deployment)
3. [Cloud Deployment](#cloud-deployment)
4. [Docker Deployment](#docker-deployment)
5. [Production Considerations](#production-considerations)
6. [Security Best Practices](#security-best-practices)

---

## Deployment Options

You can deploy this application in several ways:

| Option | Best For | Complexity | Cost |
|--------|----------|------------|------|
| **Local** | Personal use, testing | Low | Free |
| **Docker** | Consistent environments | Medium | Free |
| **Cloud (Azure)** | Team/enterprise use | Medium | Pay-as-you-go |
| **Cloud (AWS)** | Team/enterprise use | Medium | Pay-as-you-go |
| **Cloud (GCP)** | Team/enterprise use | Medium | Pay-as-you-go |

---

## 1. Local Deployment

### Prerequisites
- Python 3.7+
- Virtual environment
- Gemini API key

### Step-by-Step

#### 1.1 Clone/Copy Project
```bash
cd "/Users/coher/My Pc/Rite/venv/OTBI2PWBI"
```

#### 1.2 Set Up Virtual Environment
```bash
# Create virtual environment
python3 -m venv .venv

# Activate
source .venv/bin/activate  # macOS/Linux
# OR
.venv\Scripts\activate     # Windows
```

#### 1.3 Install Dependencies
```bash
pip install flask google-generativeai sqlparse
```

#### 1.4 Configure API Key
```bash
# Edit llm_config.py
nano llm_config.py
```

Add your API key:
```python
GEMINI_API_KEY = "your-api-key-here"
```

#### 1.5 Run Application

**CLI Mode**:
```bash
.venv/bin/python main.py Demo_SQL.sql
```

**Web UI Mode**:
```bash
.venv/bin/python app.py
# Access at: http://127.0.0.1:5000
```

#### 1.6 Keep Running (Optional)
```bash
# Use screen or tmux to keep running
screen -S otbi-dax
.venv/bin/python app.py

# Detach: Ctrl+A, then D
# Reattach: screen -r otbi-dax
```

---

## 2. Cloud Deployment

### Option A: Azure App Service

#### 2.1 Prerequisites
- Azure account
- Azure CLI installed

#### 2.2 Create Requirements File
```bash
cat > requirements.txt << EOF
flask==3.0.0
google-generativeai==0.8.0
sqlparse==0.4.4
gunicorn==21.2.0
EOF
```

#### 2.3 Create Azure Configuration
```bash
# Create .deployment file
cat > .deployment << EOF
[config]
command = bash deploy.sh
EOF

# Create deploy.sh
cat > deploy.sh << 'EOF'
#!/bin/bash
python -m pip install --upgrade pip
pip install -r requirements.txt
EOF

chmod +x deploy.sh
```

#### 2.4 Create Web Config
```bash
cat > web.config << EOF
<?xml version="1.0" encoding="utf-8"?>
<configuration>
  <system.webServer>
    <handlers>
      <add name="PythonHandler" path="*" verb="*" modules="FastCgiModule" scriptProcessor="D:\home\python\python.exe|D:\home\site\wwwroot\wfastcgi.py" resourceType="Unspecified" requireAccess="Script"/>
    </handlers>
  </system.webServer>
</configuration>
EOF
```

#### 2.5 Deploy to Azure
```bash
# Login to Azure
az login

# Create resource group
az group create --name otbi-dax-rg --location eastus

# Create App Service plan
az appservice plan create \
  --name otbi-dax-plan \
  --resource-group otbi-dax-rg \
  --sku B1 \
  --is-linux

# Create web app
az webapp create \
  --resource-group otbi-dax-rg \
  --plan otbi-dax-plan \
  --name otbi-dax-converter \
  --runtime "PYTHON:3.11"

# Configure environment variables
az webapp config appsettings set \
  --resource-group otbi-dax-rg \
  --name otbi-dax-converter \
  --settings GEMINI_API_KEY="your-api-key-here"

# Deploy code
az webapp up \
  --resource-group otbi-dax-rg \
  --name otbi-dax-converter \
  --runtime "PYTHON:3.11"
```

#### 2.6 Configure Startup Command
```bash
az webapp config set \
  --resource-group otbi-dax-rg \
  --name otbi-dax-converter \
  --startup-file "gunicorn --bind=0.0.0.0 --timeout 600 app:app"
```

#### 2.7 Access Application
```
https://otbi-dax-converter.azurewebsites.net
```

---

### Option B: AWS Elastic Beanstalk

#### 2.8 Prerequisites
- AWS account
- EB CLI installed

#### 2.9 Initialize EB Application
```bash
# Install EB CLI
pip install awsebcli

# Initialize
eb init -p python-3.11 otbi-dax-converter --region us-east-1

# Create environment
eb create otbi-dax-env
```

#### 2.10 Configure Environment Variables
```bash
eb setenv GEMINI_API_KEY="your-api-key-here"
```

#### 2.11 Create Procfile
```bash
cat > Procfile << EOF
web: gunicorn --bind :8000 --timeout 600 app:app
EOF
```

#### 2.12 Deploy
```bash
eb deploy
```

#### 2.13 Access Application
```bash
eb open
```

---

### Option C: Google Cloud Run

#### 2.14 Prerequisites
- Google Cloud account
- gcloud CLI installed

#### 2.15 Create Dockerfile (see Docker section)

#### 2.16 Deploy to Cloud Run
```bash
# Set project
gcloud config set project YOUR_PROJECT_ID

# Build and deploy
gcloud run deploy otbi-dax-converter \
  --source . \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated \
  --set-env-vars GEMINI_API_KEY="your-api-key-here"
```

---

## 3. Docker Deployment

### 3.1 Create Dockerfile
```bash
cat > Dockerfile << 'EOF'
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Copy requirements
COPY requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application files
COPY . .

# Expose port
EXPOSE 5000

# Set environment variable
ENV FLASK_APP=app.py

# Run application
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--timeout", "600", "app:app"]
EOF
```

### 3.2 Create .dockerignore
```bash
cat > .dockerignore << EOF
.venv
__pycache__
*.pyc
.DS_Store
.git
*.md
EOF
```

### 3.3 Create requirements.txt
```bash
cat > requirements.txt << EOF
flask==3.0.0
google-generativeai==0.8.0
sqlparse==0.4.4
gunicorn==21.2.0
EOF
```

### 3.4 Build Docker Image
```bash
docker build -t otbi-dax-converter .
```

### 3.5 Run Docker Container
```bash
docker run -d \
  -p 5000:5000 \
  -e GEMINI_API_KEY="your-api-key-here" \
  --name otbi-dax \
  otbi-dax-converter
```

### 3.6 Access Application
```
http://localhost:5000
```

### 3.7 Docker Compose (Optional)
```bash
cat > docker-compose.yml << 'EOF'
version: '3.8'

services:
  web:
    build: .
    ports:
      - "5000:5000"
    environment:
      - GEMINI_API_KEY=${GEMINI_API_KEY}
    volumes:
      - ./Demo_SQL.sql:/app/Demo_SQL.sql
      - ./Demo_DAXquery.dax:/app/Demo_DAXquery.dax
    restart: unless-stopped
EOF

# Run with docker-compose
docker-compose up -d
```

---

## 4. Production Considerations

### 4.1 Environment Variables

**Never hardcode API keys!** Use environment variables:

```python
# llm_config.py
import os

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")

if not GEMINI_API_KEY:
    raise ValueError("GEMINI_API_KEY environment variable not set")
```

### 4.2 Production WSGI Server

Replace Flask's development server with Gunicorn:

```bash
pip install gunicorn

# Run with Gunicorn
gunicorn --bind 0.0.0.0:5000 --timeout 600 --workers 4 app:app
```

### 4.3 Reverse Proxy (Nginx)

```nginx
# /etc/nginx/sites-available/otbi-dax
server {
    listen 80;
    server_name your-domain.com;

    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_read_timeout 600s;
    }
}
```

Enable site:
```bash
sudo ln -s /etc/nginx/sites-available/otbi-dax /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

### 4.4 SSL/HTTPS (Let's Encrypt)

```bash
# Install certbot
sudo apt-get install certbot python3-certbot-nginx

# Get certificate
sudo certbot --nginx -d your-domain.com

# Auto-renewal
sudo certbot renew --dry-run
```

### 4.5 Systemd Service

```bash
# Create service file
sudo nano /etc/systemd/system/otbi-dax.service
```

```ini
[Unit]
Description=OTBI to DAX Converter
After=network.target

[Service]
User=www-data
WorkingDirectory=/path/to/OTBI2PWBI
Environment="GEMINI_API_KEY=your-api-key-here"
ExecStart=/path/to/.venv/bin/gunicorn --bind 127.0.0.1:5000 --timeout 600 --workers 4 app:app
Restart=always

[Install]
WantedBy=multi-user.target
```

Enable and start:
```bash
sudo systemctl daemon-reload
sudo systemctl enable otbi-dax
sudo systemctl start otbi-dax
sudo systemctl status otbi-dax
```

### 4.6 Logging

Update `app.py`:
```python
import logging
from logging.handlers import RotatingFileHandler

# Configure logging
if not app.debug:
    file_handler = RotatingFileHandler('otbi-dax.log', maxBytes=10240000, backupCount=10)
    file_handler.setFormatter(logging.Formatter(
        '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
    ))
    file_handler.setLevel(logging.INFO)
    app.logger.addHandler(file_handler)
    app.logger.setLevel(logging.INFO)
    app.logger.info('OTBI to DAX Converter startup')
```

### 4.7 Rate Limiting

```bash
pip install flask-limiter
```

```python
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

limiter = Limiter(
    app=app,
    key_func=get_remote_address,
    default_limits=["200 per day", "50 per hour"]
)

@app.route('/convert', methods=['POST'])
@limiter.limit("10 per minute")
def convert():
    # ... existing code
```

---

## 5. Security Best Practices

### 5.1 API Key Management

**Option 1: Environment Variables**
```bash
export GEMINI_API_KEY="your-key"
```

**Option 2: Secret Management Service**
- AWS Secrets Manager
- Azure Key Vault
- Google Secret Manager

**Option 3: .env File (Development Only)**
```bash
pip install python-dotenv
```

```python
from dotenv import load_dotenv
load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
```

### 5.2 CORS Configuration

```bash
pip install flask-cors
```

```python
from flask_cors import CORS

# Restrict to specific domains
CORS(app, resources={r"/*": {"origins": ["https://your-domain.com"]}})
```

### 5.3 File Upload Security

```python
ALLOWED_EXTENSIONS = {'sql'}

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/convert', methods=['POST'])
def convert():
    if 'file' not in request.files:
        return jsonify({'error': 'No file'}), 400
    
    file = request.files['file']
    
    if not allowed_file(file.filename):
        return jsonify({'error': 'Only .sql files allowed'}), 400
    
    # ... rest of code
```

### 5.4 Input Validation

```python
def validate_sql(sql_text):
    # Check max length
    if len(sql_text) > 100000:  # 100KB
        raise ValueError("SQL too large")
    
    # Check for dangerous patterns
    dangerous_patterns = ['DROP', 'DELETE', 'TRUNCATE', 'ALTER']
    for pattern in dangerous_patterns:
        if pattern in sql_text.upper():
            raise ValueError(f"Dangerous SQL keyword: {pattern}")
    
    return True
```

### 5.5 HTTPS Only

```python
from flask_talisman import Talisman

# Force HTTPS
Talisman(app, force_https=True)
```

---

## 6. Monitoring & Maintenance

### 6.1 Health Check Endpoint

```python
@app.route('/health')
def health():
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat()
    })
```

### 6.2 Application Monitoring

**Option 1: Application Insights (Azure)**
```bash
pip install applicationinsights
```

**Option 2: CloudWatch (AWS)**
```bash
pip install boto3
```

**Option 3: Cloud Monitoring (GCP)**
```bash
pip install google-cloud-monitoring
```

### 6.3 Backup Strategy

```bash
# Backup demo files and prompts
tar -czf backup-$(date +%Y%m%d).tar.gz \
  Demo_SQL.sql \
  Demo_DAXquery.dax \
  prompts/ \
  llm_config.py
```

---

## 7. Deployment Checklist

### Pre-Deployment
- [ ] API key configured as environment variable
- [ ] Requirements.txt created
- [ ] Demo files present
- [ ] Prompts directory exists
- [ ] Tested locally

### Production
- [ ] HTTPS enabled
- [ ] Logging configured
- [ ] Rate limiting enabled
- [ ] CORS configured
- [ ] File upload validation
- [ ] Health check endpoint
- [ ] Monitoring setup
- [ ] Backup strategy

### Post-Deployment
- [ ] Test conversion with Demo_SQL.sql
- [ ] Verify API key works
- [ ] Check logs
- [ ] Monitor performance
- [ ] Document URL/access

---

## 8. Quick Deploy Commands

### Local
```bash
source .venv/bin/activate
.venv/bin/python app.py
```

### Docker
```bash
docker build -t otbi-dax .
docker run -d -p 5000:5000 -e GEMINI_API_KEY="key" otbi-dax
```

### Azure
```bash
az webapp up --name otbi-dax-converter --runtime "PYTHON:3.11"
```

### AWS
```bash
eb create otbi-dax-env
eb deploy
```

### GCP
```bash
gcloud run deploy otbi-dax-converter --source .
```

---

## 9. Troubleshooting

### Issue: API Key Not Found
```bash
# Check environment variable
echo $GEMINI_API_KEY

# Set temporarily
export GEMINI_API_KEY="your-key"
```

### Issue: Port Already in Use
```bash
# Find process
lsof -i :5000

# Kill process
kill -9 <PID>

# Or use different port
.venv/bin/python app.py --port 5001
```

### Issue: Module Not Found
```bash
# Reinstall dependencies
pip install -r requirements.txt
```

### Issue: Timeout Errors
```bash
# Increase timeout in Gunicorn
gunicorn --timeout 900 app:app
```

---

## 10. Cost Estimation

### Gemini API
- Free tier: 60 requests/minute
- Paid: ~$0.001 per request
- Estimated: $10-50/month for moderate use

### Cloud Hosting

**Azure App Service (B1)**
- ~$13/month
- 1.75 GB RAM
- 100 GB storage

**AWS Elastic Beanstalk (t3.small)**
- ~$15/month
- 2 GB RAM
- Pay for what you use

**Google Cloud Run**
- Pay per request
- ~$5-20/month for moderate use
- Auto-scales to zero

---

## Summary

**Recommended for:**
- **Personal Use**: Local deployment
- **Small Team**: Docker on VM
- **Enterprise**: Cloud deployment with monitoring

**Next Steps:**
1. Choose deployment option
2. Configure API key securely
3. Test with Demo_SQL.sql
4. Monitor and maintain

For questions, refer to [DOCUMENTATION.md](file:///Users/coher/My%20Pc/Rite/venv/OTBI2PWBI/DOCUMENTATION.md)
