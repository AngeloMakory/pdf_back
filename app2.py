from flask import Flask, request, jsonify
from flask_cors import CORS
import mysql.connector
import os
from werkzeug.utils import secure_filename
import PyPDF2
from io import BytesIO
from pdfminer.high_level import extract_text


app = Flask(__name__)
CORS(app, origins="*")

# Configuration
UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'pdf'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Database connection
db = mysql.connector.connect(
    host="172.17.0.1",
    user="root",
    password="Angelo@123",
    database="pdf_db"
)
cursor = db.cursor(dictionary=True)

# Create tables if they don't exist
cursor.execute("""
CREATE TABLE IF NOT EXISTS pdf_files (
    id INT AUTO_INCREMENT PRIMARY KEY,
    filename VARCHAR(255) NOT NULL,
    filepath VARCHAR(255) NOT NULL,
    upload_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS pdf_summaries (
    id INT AUTO_INCREMENT PRIMARY KEY,
    pdf_id INT NOT NULL,
    summary TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (pdf_id) REFERENCES pdf_files(id)
)
""")
db.commit()

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# def extract_text_from_pdf(file):
#     pdf_reader = PyPDF2.PdfReader(file)
#     text = ""
#     for page in pdf_reader.pages:
#         text += page.extract_text()
#     return text


# def extract_text_from_pdf(file):
#     return extract_text(file)

# def extract_text_from_pdf(file_path):
#     try:
#         text = extract_text(file_path)
#         return text.strip()
#     except Exception as e:
#         print(f"[ERROR] PDF text extraction failed: {e}")
#         return ""

def extract_text_from_pdf(filepath):
    try:
        reader = PdfReader(filepath)
        text = ""
        for page in reader.pages:
            page_text = page.extract_text()
            if page_text:
                text += page_text + "\n"
        return text.strip()
    except Exception as e:
        print(f"[ERROR] Failed to extract text: {e}")
        return ""

# def generate_summary(text):
#     # Simple but effective summary by taking key parts
#     sentences = [s.strip() for s in text.split('.') if s.strip()]
    
#     # Take first few sentences and important-looking sentences
#     important_sentences = sentences[:3]
#     for s in sentences:
#         if len(s.split()) > 15 and ':' in s:  # Looks like a heading/important point
#             important_sentences.append(s)
#             if len(important_sentences) >= 5:
#                 break
    
#     return ' '.join(important_sentences[:5]) + '...'

# def generate_summary(text):
#     if not text:
#         return "No content found in PDF."

#     sentences = [s.strip() for s in text.split('.') if len(s.strip()) > 20]
    
#     # Just pick the first few meaningful sentences
#     summary = ' '.join(sentences[:5])
    
#     if not summary:
#         summary = text[:300]  # fallback: first 300 characters

#     return summary.strip() + '...'

def generate_summary(text):
    if not text:
        return "No text could be extracted from the PDF."

    sentences = [s.strip() for s in text.split('.') if len(s.strip()) > 20]

    if sentences:
        return '. '.join(sentences[:5]) + '...'
    return text[:300] + '...'

    # Debug log
    print(f"[DEBUG] Found {len(sentences)} valid sentences")

    if sentences:
        summary = '. '.join(sentences[:5]) + '...'
        print(f"[DEBUG] Summary preview: {summary[:150]}")
        return summary

    return text[:300] + '...'

@app.route("/api/pdfs", methods=["GET"])
def get_pdfs():
    cursor.execute("""
    SELECT pdf_files.*, pdf_summaries.summary 
    FROM pdf_files 
    LEFT JOIN pdf_summaries ON pdf_files.id = pdf_summaries.pdf_id
    ORDER BY pdf_files.upload_date DESC
    """)
    pdfs = cursor.fetchall()
    return jsonify(pdfs)


# @app.route("/api/pdfs", methods=["POST"])
# def upload_pdf():
#     print("[DEBUG] Received upload request")

#     if 'file' not in request.files:
#         return jsonify({"error": "No file part"}), 400
    
#     file = request.files['file']
#     if file.filename == '':
#         return jsonify({"error": "No selected file"}), 400
    
#     if file and allowed_file(file.filename):
#         filename = secure_filename(file.filename)
#         if not os.path.exists(app.config['UPLOAD_FOLDER']):
#             os.makedirs(app.config['UPLOAD_FOLDER'])
        
#         filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
#         file.save(filepath)
        
#         # Store in database
#         cursor.execute("INSERT INTO pdf_files (filename, filepath) VALUES (%s, %s)", 
#                       (filename, filepath))
#         pdf_id = cursor.lastrowid
        
#         # Extract text and summarize
#         text = extract_text_from_pdf(filepath)
#         print(f"[DEBUG] Extracted text (first 300 chars):\n{text[:300]}")

#         summary = generate_summary(text)
#         print(f"[DEBUG] Summary:\n{summary}")

#         cursor.execute("INSERT INTO pdf_summaries (pdf_id, summary) VALUES (%s, %s)",
#                       (pdf_id, summary))
        
#         db.commit()
        
#         return jsonify({
#             "message": "File uploaded and processed successfully",
#             "filename": filename,
#             "summary": summary
#         }), 201
    
#     return jsonify({"error": "Invalid file type"}), 400

# @app.route("/api/pdfs", methods=["POST"])
# def upload_pdf():
#     if 'file' not in request.files:
#         return jsonify({"error": "No file part"}), 400
    
#     file = request.files['file']
#     if file.filename == '':
#         return jsonify({"error": "No selected file"}), 400
    
#     if file and allowed_file(file.filename):
#         filename = secure_filename(file.filename)
#         if not os.path.exists(app.config['UPLOAD_FOLDER']):
#             os.makedirs(app.config['UPLOAD_FOLDER'])
        
#         filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
#         file.save(filepath)
        
#         # Store in database
#         cursor.execute("INSERT INTO pdf_files (filename, filepath) VALUES (%s, %s)", 
#                       (filename, filepath))
#         pdf_id = cursor.lastrowid
        
#         # Process PDF
#         # with open(filepath, 'rb') as f:
#         #     text = extract_text_from_pdf(f)
#         #     print(f"[DEBUG] Extracted Text:\n{text[:500]}")  # Print first 500 chars
#         #     summary = generate_summary(text)
            
#         #     cursor.execute("INSERT INTO pdf_summaries (pdf_id, summary) VALUES (%s, %s)",
#         #                   (pdf_id, summary))
        
#         with open(filepath, 'rb') as f:
#             text = extract_text_from_pdf(filepath)
#             print(f"[DEBUG] Extracted text (first 300 chars):\n{text[:300]}")

#         db.commit()
        
#         return jsonify({
#             "message": "File uploaded and processed successfully",
#             "filename": filename,
#             "summary": summary
#         }), 201
    
#     return jsonify({"error": "Invalid file type"}), 400

@app.route("/api/pdfs", methods=["POST"])
def upload_pdf():
    if 'file' not in request.files:
        return jsonify({"error": "No file part"}), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({"error": "No selected file"}), 400

    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)

        cursor.execute("INSERT INTO pdf_files (filename, filepath) VALUES (%s, %s)",
                       (filename, filepath))
        pdf_id = cursor.lastrowid

        # Extract text and generate summary
        text = extract_text_from_pdf(filepath)
        print(f"[DEBUG] Extracted text (first 300 chars): {text[:300]}")
        summary = generate_summary(text) if text else "No text could be extracted from the PDF."

        cursor.execute("INSERT INTO pdf_summaries (pdf_id, summary) VALUES (%s, %s)",
                       (pdf_id, summary))

        db.commit()

        return jsonify({
            "message": "File uploaded and processed successfully",
            "filename": filename,
            "summary": summary
        }), 201

    return jsonify({"error": "Invalid file type"}), 400

@app.route("/api/pdfs/<int:pdf_id>", methods=["DELETE"])
def delete_pdf(pdf_id):
    try:
        # Get file path first
        cursor.execute("SELECT filepath FROM pdf_files WHERE id = %s", (pdf_id,))
        result = cursor.fetchone()
        
        if not result:
            return jsonify({"error": "PDF not found"}), 404
            
        filepath = result['filepath']
        
        # Delete from database
        cursor.execute("DELETE FROM pdf_summaries WHERE pdf_id = %s", (pdf_id,))
        cursor.execute("DELETE FROM pdf_files WHERE id = %s", (pdf_id,))
        db.commit()
        
        # Delete file
        if os.path.exists(filepath):
            os.remove(filepath)
            
        return jsonify({"message": "PDF deleted successfully"}), 200
    except Exception as e:
        db.rollback()
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(debug=True)