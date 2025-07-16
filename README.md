# 🐍 pdf_back

A backend API for managing PDFs built with Flask and MySQL.

---

## 🧩 Features

- Upload, list, and retrieve PDF metadata/files
- User authentication (optional)
- RESTful API endpoints
- MySQL database integration using SQLAlchemy
- Environment-based configuration
- Docker support for containerized deployment

---

## ⚙️ Prerequisites

- Python **3.8+**
- MySQL Server **5.7+**
- `pip` (Python package installer)
- (Optional) Docker & Docker Compose for containerized setup

---

## 📥 Installation

### 1. Clone the repository


git clone https://github.com/AngeloMakory/pdf_back.git
cd pdf_back

### 2. Set up a virtual environment


python3 -m venv venv
source venv/bin/activate   # On Windows: venv\Scripts\activate

### 3. Install Python dependencies


pip install -r requirements.txt

### 4. Configure environment variables


FLASK_APP=app.py
FLASK_ENV=development
SECRET_KEY=super-secret-key
MYSQL_HOST=localhost
MYSQL_USER=root
MYSQL_PASSWORD=your_mysql_password
MYSQL_DB=pdf_back_db
UPLOAD_FOLDER=uploads/
ALLOWED_EXTENSIONS=pdf

### 5. Set up the MySQL database


CREATE DATABASE pdf_back_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
GRANT ALL PRIVILEGES ON pdf_back_db.* TO 'root'@'localhost' IDENTIFIED BY 'your_mysql_password';
FLUSH PRIVILEGES;

### 6. Initialize database tables


from app import db
db.create_all()

### 7. Initialize database tables

`
from app import db
db.create_all()

### 8. Initialize database tables


from app import db
db.create_all()

### 9. Running The App on port 5000


python3 app.py

## Project Structure 
pdf_assistant
            |
            |____docker_compose.yml
            |____pdf_back

## Docker Compose
### To run the container with its frontend counterpart simultaneously, do
``` docker-compose up --build -d
```


          

