from flask import Flask, request, jsonify
from flask_cors import CORS
import pymysql
#from pymysql import pooling
import os
from werkzeug.utils import secure_filename
from PyPDF2 import PdfReader
import logging
from datetime import datetime
import hashlib
import re
from collections import Counter
import math

app = Flask(__name__)
CORS(app, origins="*")

# Configuration
app.config.update({
    'UPLOAD_FOLDER': 'uploads',
    'MAX_CONTENT_LENGTH': 10 * 1024 * 1024,  # 10MB max file size
    'ALLOWED_EXTENSIONS': {'pdf'}
})

# Logging setup
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Database connection pool for better performance
db_config = {
    'host': "172.31.89.13",
    'user': "angelo", 
    'password': "Angelo@123",
    'database': "pdf_db",
    'charset': 'utf8mb4',
    'autocommit': True
}

# Simple connection pool using pymysql
class SimpleConnectionPool:
    def __init__(self, **config):
        self.config = config
        self.pool = []
        self.pool_size = 10
        
    def get_connection(self):
        if self.pool:
            return self.pool.pop()
        return pymysql.connect(**self.config)
    
    def return_connection(self, conn):
        if len(self.pool) < self.pool_size:
            self.pool.append(conn)
        else:
            conn.close()

try:
    connection_pool = SimpleConnectionPool(**db_config)
    logger.info("Database connection pool created successfully")
except Exception as e:
    logger.error(f"Failed to create database pool: {e}")
    raise

def get_db_connection():
    """Get database connection from pool"""
    try:
        return connection_pool.get_connection()
    except Exception as e:
        logger.error(f"Failed to get database connection: {e}")
        raise

def init_database():
    """Initialize database tables"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # Enhanced pdf_files table with metadata
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS pdf_files (
            id INT AUTO_INCREMENT PRIMARY KEY,
            filename VARCHAR(255) NOT NULL,
            filepath VARCHAR(255) NOT NULL,
            file_hash VARCHAR(64) UNIQUE,
            file_size INT,
            page_count INT,
            word_count INT,
            upload_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            INDEX idx_upload_date (upload_date),
            INDEX idx_file_hash (file_hash)
        )
        """)
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS pdf_summaries (
            id INT AUTO_INCREMENT PRIMARY KEY,
            pdf_id INT NOT NULL,
            summary TEXT,
            summary_method VARCHAR(50) DEFAULT 'frequency_based',
            compression_ratio DECIMAL(5,2),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (pdf_id) REFERENCES pdf_files(id) ON DELETE CASCADE,
            INDEX idx_pdf_id (pdf_id)
        )
        """)
        
        conn.commit()
        logger.info("Database tables initialized successfully")
    except Exception as e:
        logger.error(f"Database initialization failed: {e}")
        conn.rollback()
        raise
    finally:
        cursor.close()
        conn.close()

def allowed_file(filename):
    """Check if file extension is allowed"""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

def calculate_file_hash(filepath):
    """Calculate SHA-256 hash of file for deduplication"""
    hash_sha256 = hashlib.sha256()
    try:
        with open(filepath, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_sha256.update(chunk)
        return hash_sha256.hexdigest()
    except Exception as e:
        logger.error(f"Error calculating file hash: {e}")
        return None

def extract_text_from_pdf(filepath):
    """Extract text from PDF with better error handling"""
    try:
        with open(filepath, 'rb') as file:
            reader = PdfReader(file)
            
            if len(reader.pages) == 0:
                return "", 0
            
            text = ""
            for page_num, page in enumerate(reader.pages):
                try:
                    page_text = page.extract_text()
                    if page_text:
                        text += page_text + "\n"
                except Exception as e:
                    logger.warning(f"Failed to extract text from page {page_num}: {e}")
                    continue
            
            return text.strip(), len(reader.pages)
    except Exception as e:
        logger.error(f"PDF text extraction failed: {e}")
        return "", 0

def clean_text(text):
    """Clean and preprocess text"""
    # Remove extra whitespace
    text = re.sub(r'\s+', ' ', text)
    
    # Remove common PDF artifacts
    text = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f-\xff]', '', text)
    
    # Remove page numbers (simple pattern)
    text = re.sub(r'\n\d+\n', '\n', text)
    
    return text.strip()

def calculate_sentence_scores(sentences, word_freq):
    """Calculate importance scores for sentences using TF-IDF-like approach"""
    sentence_scores = {}
    
    for sentence in sentences:
        words = re.findall(r'\b[a-zA-Z]{3,}\b', sentence.lower())
        if not words:
            continue
            
        score = 0
        for word in words:
            if word in word_freq:
                # Simple TF-IDF approximation
                tf = words.count(word) / len(words)
                idf = math.log(len(sentences) / (word_freq[word] + 1))
                score += tf * idf
        
        # Boost for sentences with numbers or capitals (likely important)
        if re.search(r'\d+', sentence):
            score *= 1.2
        if re.search(r'[A-Z]{2,}', sentence):
            score *= 1.1
            
        sentence_scores[sentence] = score
    
    return sentence_scores

def generate_advanced_summary(text, max_sentences=5):
    """Generate summary using frequency analysis and sentence scoring"""
    if not text:
        return "No text could be extracted from the PDF.", 0
    
    # Clean text
    text = clean_text(text)
    word_count = len(text.split())
    
    # Split into sentences
    sentences = [s.strip() for s in re.split(r'[.!?]+', text) if len(s.strip()) > 20]
    
    if len(sentences) < max_sentences:
        summary = '. '.join(sentences) + '.'
        compression_ratio = (len(summary.split()) / word_count) * 100 if word_count > 0 else 0
        return summary, round(compression_ratio, 2)
    
    # Calculate word frequencies (excluding common stop words)
    stop_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by', 'is', 'are', 'was', 'were', 'be', 'been', 'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 'could', 'should', 'this', 'that', 'these', 'those'}
    words = [word.lower() for word in re.findall(r'\b[a-zA-Z]{3,}\b', text) if word.lower() not in stop_words]
    word_freq = Counter(words)
    
    # Score sentences
    sentence_scores = calculate_sentence_scores(sentences, word_freq)
    
    # Select top sentences
    top_sentences = sorted(sentence_scores.items(), key=lambda x: x[1], reverse=True)[:max_sentences]
    
    # Sort by original order in text
    selected_sentences = []
    for sentence in sentences:
        if any(sentence == top_sent[0] for top_sent in top_sentences):
            selected_sentences.append(sentence)
        if len(selected_sentences) >= max_sentences:
            break
    
    summary = '. '.join(selected_sentences) + '.'
    compression_ratio = (len(summary.split()) / word_count) * 100 if word_count > 0 else 0
    
    return summary, round(compression_ratio, 2)

@app.errorhandler(413)
def too_large(e):
    return jsonify({"error": "File too large. Maximum size is 10MB."}), 413

@app.errorhandler(Exception)
def handle_exception(e):
    logger.error(f"Unhandled exception: {e}")
    return jsonify({"error": "Internal server error"}), 500

@app.route("/api/pdfs", methods=["GET"])
def get_pdfs():
    """Get all PDFs with their summaries"""
    conn = get_db_connection()
    cursor = conn.cursor(pymysql.cursors.DictCursor)
    
    try:
        cursor.execute("""
        SELECT 
            pf.id, pf.filename, pf.file_size, pf.page_count, 
            pf.word_count, pf.upload_date as createdAt,
            ps.summary, ps.compression_ratio, ps.summary_method
        FROM pdf_files pf
        LEFT JOIN pdf_summaries ps ON pf.id = ps.pdf_id
        ORDER BY pf.upload_date DESC
        """)
        
        pdfs = cursor.fetchall()
        
        # Format the response
        for pdf in pdfs:
            if pdf['createdAt']:
                pdf['createdAt'] = pdf['createdAt'].isoformat()
            
            # Add metadata object
            pdf['metadata'] = {
                'pages': pdf.pop('page_count', 0),
                'wordCount': pdf.pop('word_count', 0),
                'compressionRatio': pdf.pop('compression_ratio', 0),
                'summaryMethod': pdf.pop('summary_method', 'unknown')
            }
        
        return jsonify(pdfs)
    except Exception as e:
        logger.error(f"Error fetching PDFs: {e}")
        return jsonify({"error": "Failed to fetch PDFs"}), 500
    finally:
        cursor.close()
        connection_pool.return_connection(conn)

@app.route("/api/pdfs", methods=["POST"])
def upload_pdf():
    """Upload and process PDF"""
    if 'file' not in request.files:
        return jsonify({"error": "No file part"}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({"error": "No selected file"}), 400
    
    if not file or not allowed_file(file.filename):
        return jsonify({"error": "Invalid file type. Only PDF files are allowed."}), 400

    try:
        filename = secure_filename(file.filename)
        os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
        
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)
        
        # Calculate file hash for deduplication
        file_hash = calculate_file_hash(filepath)
        file_size = os.path.getsize(filepath)
        
        conn = get_db_connection()
        cursor = conn.cursor(pymysql.cursors.DictCursor)
        
        # Check for duplicates
        if file_hash:
            cursor.execute("SELECT id, filename FROM pdf_files WHERE file_hash = %s", (file_hash,))
            existing = cursor.fetchone()
            if existing:
                os.remove(filepath)  # Remove duplicate file
                return jsonify({
                    "message": f"File already exists as '{existing['filename']}'",
                    "duplicate": True,
                    "existing_id": existing['id']
                }), 200
        
        # Extract text and metadata
        text, page_count = extract_text_from_pdf(filepath)
        word_count = len(text.split()) if text else 0
        
        # Store file info
        cursor.execute("""
        INSERT INTO pdf_files (filename, filepath, file_hash, file_size, page_count, word_count) 
        VALUES (%s, %s, %s, %s, %s, %s)
        """, (filename, filepath, file_hash, file_size, page_count, word_count))
        
        pdf_id = cursor.lastrowid
        
        # Generate summary
        if text:
            summary, compression_ratio = generate_advanced_summary(text)
            summary_method = "frequency_based"
        else:
            summary = "No text could be extracted from this PDF."
            compression_ratio = 0
            summary_method = "none"
        
        # Store summary
        cursor.execute("""
        INSERT INTO pdf_summaries (pdf_id, summary, summary_method, compression_ratio) 
        VALUES (%s, %s, %s, %s)
        """, (pdf_id, summary, summary_method, compression_ratio))
        
        conn.commit()
        
        logger.info(f"Successfully processed PDF: {filename} (ID: {pdf_id})")
        
        return jsonify({
            "message": "File uploaded and processed successfully",
            "id": pdf_id,
            "filename": filename,
            "summary": summary,
            "metadata": {
                "pages": page_count,
                "wordCount": word_count,
                "compressionRatio": compression_ratio,
                "fileSize": file_size
            }
        }), 201
        
    except Exception as e:
        logger.error(f"Error processing PDF upload: {e}")
        # Clean up file if something went wrong
        if 'filepath' in locals() and os.path.exists(filepath):
            os.remove(filepath)
        return jsonify({"error": "Failed to process PDF. Please try again."}), 500
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'conn' in locals():
            connection_pool.return_connection(conn)

@app.route("/api/pdfs/<int:pdf_id>", methods=["DELETE"])
def delete_pdf(pdf_id):
    """Delete PDF and its summary"""
    conn = get_db_connection()
    cursor = conn.cursor(pymysql.cursors.DictCursor)
    
    try:
        # Get file path
        cursor.execute("SELECT filepath FROM pdf_files WHERE id = %s", (pdf_id,))
        result = cursor.fetchone()
        
        if not result:
            return jsonify({"error": "PDF not found"}), 404
        
        filepath = result['filepath']
        
        # Delete from database (cascade will handle summaries)
        cursor.execute("DELETE FROM pdf_files WHERE id = %s", (pdf_id,))
        
        if cursor.rowcount == 0:
            return jsonify({"error": "PDF not found"}), 404
        
        conn.commit()
        
        # Delete file
        if os.path.exists(filepath):
            os.remove(filepath)
            logger.info(f"Deleted file: {filepath}")
        
        return jsonify({"message": "PDF deleted successfully"}), 200
        
    except Exception as e:
        logger.error(f"Error deleting PDF {pdf_id}: {e}")
        conn.rollback()
        return jsonify({"error": "Failed to delete PDF"}), 500
    finally:
        cursor.close()
        connection_pool.return_connection(conn)

@app.route("/api/pdfs/<int:pdf_id>/reprocess", methods=["POST"])
def reprocess_pdf(pdf_id):
    """Reprocess PDF with updated summarization"""
    conn = get_db_connection()
    cursor = conn.cursor(pymysql.cursors.DictCursor)
    
    try:
        # Get PDF info
        cursor.execute("SELECT filepath FROM pdf_files WHERE id = %s", (pdf_id,))
        result = cursor.fetchone()
        
        if not result:
            return jsonify({"error": "PDF not found"}), 404
        
        filepath = result['filepath']
        
        if not os.path.exists(filepath):
            return jsonify({"error": "PDF file not found on disk"}), 404
        
        # Re-extract and summarize
        text, _ = extract_text_from_pdf(filepath)
        summary, compression_ratio = generate_advanced_summary(text)
        
        # Update summary
        cursor.execute("""
        UPDATE pdf_summaries 
        SET summary = %s, compression_ratio = %s, created_at = NOW()
        WHERE pdf_id = %s
        """, (summary, compression_ratio, pdf_id))
        
        conn.commit()
        
        return jsonify({
            "message": "PDF reprocessed successfully",
            "summary": summary,
            "compressionRatio": compression_ratio
        }), 200
        
    except Exception as e:
        logger.error(f"Error reprocessing PDF {pdf_id}: {e}")
        return jsonify({"error": "Failed to reprocess PDF"}), 500
    finally:
        cursor.close()
        connection_pool.return_connection(conn)

@app.route("/api/health", methods=["GET"])
def health_check():
    """Health check endpoint"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT 1")
        cursor.close()
        connection_pool.return_connection(conn)
        return jsonify({"status": "healthy", "timestamp": datetime.now().isoformat()}), 200
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return jsonify({"status": "unhealthy", "error": str(e)}), 500

# Initialize database on startup
init_database()

if __name__ == "__main__":
    app.run(debug=True, host='0.0.0.0', port=5000)
