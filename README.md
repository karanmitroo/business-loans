# Personal and Business Loans

### To clone the repo
```
git clone https://github.com/karanmitroo/business-loans.git
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### Setup the Database
```
sudo apt-get update
sudo apt-get install postgresql postgresql-contrib
sudo -i -u postgres
psql
CREATE DATABASE business_loans;
```

##### Run the migrations
```
source .venv/bin/activate
python manage.py migrate
```

### NGINX Configuration
```
upstream django {
      server 127.0.0.1:8000;
    }

server {
  listen      8000;

  server_name localhost;

  charset     utf-8;

  client_max_body_size 75M;   # adjust to taste

  # Finally, send all non-media requests to the Django server.
  location /api_v1 {
      uwsgi_pass  django;
      include     /Users/karanmitroo/Desktop/business_loans_django/business_loans/uwsgi_params;
  }
}

server {
  listen       80;
  server_name  localhost;

  location /api_v1 {
    proxy_pass http://127.0.0.1:8000;
    add_header X-Static miss;
  }

  location / {
    proxy_pass http://127.0.0.1:3000;
    add_header X-Static miss;
  }

  error_page   500 502 503 504  /50x.html;
  location = /50x.html {
    root   html;
  }
}
```

### To start the django server using uwsgi gateway
```
uwsgi --socket :8000 --module business_loans.wsgi
```
_Run the uwsgi process as root (sudo su) so that it gets started as a daemon process_
