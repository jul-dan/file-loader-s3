import os
import logging
from datetime import datetime
from flask import Flask, request, render_template_string, jsonify
import boto3
from botocore.exceptions import ClientError, NoCredentialsError
from werkzeug.utils import secure_filename

# Logging configuration
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# Maximum file size configuration (16 MB)
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024

# Environment variables
AWS_REGION = os.getenv('AWS_REGION', 'eu-west-1')
S3_BUCKET_NAME = os.getenv('BUCKET_NAME')
AWS_ACCESS_KEY_ID = os.getenv('AWS_ACCESS_KEY_ID')
AWS_SECRET_ACCESS_KEY = os.getenv('AWS_SECRET_ACCESS_KEY')

logger.info("=== Application Configuration ===")
logger.info(f"AWS_REGION: {AWS_REGION}")
logger.info(f"S3_BUCKET_NAME: {S3_BUCKET_NAME}")
logger.info(f"AWS_ACCESS_KEY_ID: {'*' * 8 if AWS_ACCESS_KEY_ID else 'Not defined'}")
logger.info(f"AWS_SECRET_ACCESS_KEY: {'*' * 8 if AWS_SECRET_ACCESS_KEY else 'Not defined'}")


def get_s3_client():
    """
    Creates and returns an S3 client using AWS credentials.

    Uses AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY from environment variables.
    """
    try:
        logger.info("Creating S3 client with AWS credentials")

        # Create S3 client (boto3 will automatically use AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY from env vars)
        s3_client = boto3.client('s3', region_name=AWS_REGION)

        # Connection test
        s3_client.list_buckets()
        logger.info("S3 client created successfully")
        return s3_client

    except NoCredentialsError:
        logger.error("No AWS credentials found. Please set AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY")
        raise
    except ClientError as e:
        logger.error(f"Error creating S3 client: {e}")
        raise


def upload_file_to_s3(file, filename):
    """
    Uploads a file to S3.

    Args:
        file: Flask file object
        filename: Secured filename

    Returns:
        dict: Information about the uploaded file
    """
    if not S3_BUCKET_NAME:
        raise ValueError("BUCKET_NAME environment variable is not defined")

    try:
        s3_client = get_s3_client()

        # Generate unique key with timestamp
        timestamp = datetime.now().strftime('%Y%m%d-%H%M%S')
        s3_key = f"uploads/{timestamp}-{filename}"

        logger.info(f"Uploading file '{filename}' to s3://{S3_BUCKET_NAME}/{s3_key}")

        # Upload to S3
        s3_client.upload_fileobj(
            file,
            S3_BUCKET_NAME,
            s3_key,
            ExtraArgs={'ContentType': file.content_type or 'application/octet-stream'}
        )

        # Build S3 URL
        s3_url = f"https://{S3_BUCKET_NAME}.s3.{AWS_REGION}.amazonaws.com/{s3_key}"

        logger.info(f"✅ File uploaded successfully: {s3_url}")

        return {
            'success': True,
            'filename': filename,
            's3_key': s3_key,
            's3_url': s3_url,
            'bucket': S3_BUCKET_NAME,
            'region': AWS_REGION
        }

    except Exception as e:
        logger.error(f"❌ Upload error: {str(e)}")
        raise


# HTML template for home page
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>S3 File Uploader</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            display: flex;
            align-items: center;
            justify-content: center;
            padding: 20px;
        }
        .container {
            background: white;
            border-radius: 16px;
            padding: 40px;
            box-shadow: 0 20px 60px rgba(0,0,0,0.3);
            max-width: 500px;
            width: 100%;
        }
        h1 {
            color: #333;
            margin-bottom: 10px;
            font-size: 28px;
        }
        .subtitle {
            color: #666;
            margin-bottom: 30px;
            font-size: 14px;
        }
        .info-box {
            background: #f7f9fc;
            border-left: 4px solid #667eea;
            padding: 15px;
            margin-bottom: 25px;
            border-radius: 4px;
            font-size: 13px;
        }
        .info-box strong {
            color: #333;
        }
        .info-box div {
            margin: 5px 0;
            color: #555;
        }
        .upload-area {
            border: 2px dashed #ddd;
            border-radius: 8px;
            padding: 40px 20px;
            text-align: center;
            margin-bottom: 20px;
            transition: all 0.3s;
            cursor: pointer;
        }
        .upload-area:hover {
            border-color: #667eea;
            background: #f8f9ff;
        }
        .upload-area.dragover {
            border-color: #667eea;
            background: #f0f3ff;
        }
        input[type="file"] {
            display: none;
        }
        .file-label {
            color: #667eea;
            font-size: 16px;
            font-weight: 600;
            cursor: pointer;
        }
        .file-info {
            margin-top: 10px;
            color: #666;
            font-size: 14px;
        }
        button {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            border: none;
            padding: 14px 30px;
            border-radius: 8px;
            font-size: 16px;
            font-weight: 600;
            cursor: pointer;
            width: 100%;
            transition: transform 0.2s, box-shadow 0.2s;
        }
        button:hover:not(:disabled) {
            transform: translateY(-2px);
            box-shadow: 0 8px 20px rgba(102, 126, 234, 0.4);
        }
        button:disabled {
            opacity: 0.6;
            cursor: not-allowed;
        }
        .alert {
            padding: 15px;
            border-radius: 8px;
            margin-bottom: 20px;
            font-size: 14px;
        }
        .alert-success {
            background: #d4edda;
            color: #155724;
            border: 1px solid #c3e6cb;
        }
        .alert-error {
            background: #f8d7da;
            color: #721c24;
            border: 1px solid #f5c6cb;
        }
        .s3-link {
            word-break: break-all;
            color: #667eea;
            text-decoration: none;
            font-weight: 600;
        }
        .s3-link:hover {
            text-decoration: underline;
        }
        .spinner {
            display: none;
            border: 3px solid #f3f3f3;
            border-top: 3px solid #667eea;
            border-radius: 50%;
            width: 24px;
            height: 24px;
            animation: spin 1s linear infinite;
            margin: 0 auto;
        }
        @keyframes spin {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
        }
        .loading .spinner {
            display: block;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>📦 S3 File Uploader</h1>
        <p class="subtitle">Upload your files securely to Amazon S3</p>

        <div class="info-box">
            <strong>🔧 Configuration</strong>
            <div>📍 Region: <strong>{{ region }}</strong></div>
            <div>🪣 Bucket: <strong>{{ bucket }}</strong></div>
            <div>🔐 Auth: <strong>{{ auth_method }}</strong></div>
        </div>

        {% if message %}
        <div class="alert alert-{{ message_type }}">
            {{ message|safe }}
        </div>
        {% endif %}

        <form method="POST" action="/upload" enctype="multipart/form-data" id="uploadForm">
            <div class="upload-area" id="uploadArea">
                <label for="file" class="file-label">
                    📁 Click to select a file<br>
                    <small style="color: #999;">or drag and drop here</small>
                </label>
                <input type="file" id="file" name="file" required>
                <div class="file-info" id="fileInfo"></div>
            </div>
            <button type="submit" id="submitBtn">
                <span id="btnText">⬆️ Upload to S3</span>
                <div class="spinner"></div>
            </button>
        </form>
    </div>

    <script>
        const fileInput = document.getElementById('file');
        const fileInfo = document.getElementById('fileInfo');
        const uploadArea = document.getElementById('uploadArea');
        const uploadForm = document.getElementById('uploadForm');
        const submitBtn = document.getElementById('submitBtn');
        const btnText = document.getElementById('btnText');

        // Display selected filename
        fileInput.addEventListener('change', function(e) {
            if (this.files && this.files[0]) {
                const file = this.files[0];
                const size = (file.size / 1024 / 1024).toFixed(2);
                fileInfo.textContent = `📄 ${file.name} (${size} MB)`;
            }
        });

        // Drag and drop
        ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
            uploadArea.addEventListener(eventName, preventDefaults, false);
        });

        function preventDefaults(e) {
            e.preventDefault();
            e.stopPropagation();
        }

        ['dragenter', 'dragover'].forEach(eventName => {
            uploadArea.addEventListener(eventName, () => {
                uploadArea.classList.add('dragover');
            });
        });

        ['dragleave', 'drop'].forEach(eventName => {
            uploadArea.addEventListener(eventName, () => {
                uploadArea.classList.remove('dragover');
            });
        });

        uploadArea.addEventListener('drop', function(e) {
            const dt = e.dataTransfer;
            const files = dt.files;
            fileInput.files = files;
            fileInput.dispatchEvent(new Event('change'));
        });

        // Click on zone to open file selector
        uploadArea.addEventListener('click', () => {
            fileInput.click();
        });

        // Animation during upload
        uploadForm.addEventListener('submit', function() {
            submitBtn.disabled = true;
            submitBtn.classList.add('loading');
            btnText.style.display = 'none';
        });
    </script>
</body>
</html>
"""


@app.route('/')
def index():
    """Home page with upload form"""
    auth_method = "AWS Access Key"

    return render_template_string(
        HTML_TEMPLATE,
        region=AWS_REGION,
        bucket=S3_BUCKET_NAME or "Not configured",
        auth_method=auth_method,
        message=request.args.get('message'),
        message_type=request.args.get('type', 'success')
    )


@app.route('/upload', methods=['POST'])
def upload():
    """Endpoint to upload a file to S3"""
    try:
        # Check if file is present
        if 'file' not in request.files:
            logger.warning("No file in request")
            return render_template_string(
                HTML_TEMPLATE,
                region=AWS_REGION,
                bucket=S3_BUCKET_NAME,
                auth_method="AWS Access Key",
                message="❌ No file selected",
                message_type='error'
            )

        file = request.files['file']

        # Check if file has a name
        if file.filename == '':
            logger.warning("Empty filename")
            return render_template_string(
                HTML_TEMPLATE,
                region=AWS_REGION,
                bucket=S3_BUCKET_NAME,
                auth_method="AWS Access Key",
                message="❌ No file selected",
                message_type='error'
            )

        # Secure the filename
        filename = secure_filename(file.filename)
        logger.info(f"📤 Receiving file: {filename}")

        # Upload to S3
        result = upload_file_to_s3(file, filename)

        # Success message with S3 link
        success_message = f"""
            ✅ <strong>File uploaded successfully!</strong><br><br>
            📁 File: <strong>{result['filename']}</strong><br>
            🔑 S3 Key: <code>{result['s3_key']}</code><br>
            🔗 URL: <a href="{result['s3_url']}" class="s3-link" target="_blank">{result['s3_url']}</a>
        """

        return render_template_string(
            HTML_TEMPLATE,
            region=AWS_REGION,
            bucket=S3_BUCKET_NAME,
            auth_method="AWS Access Key",
            message=success_message,
            message_type='success'
        )

    except ValueError as e:
        logger.error(f"Configuration error: {str(e)}")
        return render_template_string(
            HTML_TEMPLATE,
            region=AWS_REGION,
            bucket=S3_BUCKET_NAME or "Not configured",
            auth_method="AWS Access Key",
            message=f"❌ Configuration error: {str(e)}",
            message_type='error'
        )

    except Exception as e:
        logger.error(f"Upload error: {str(e)}")
        return render_template_string(
            HTML_TEMPLATE,
            region=AWS_REGION,
            bucket=S3_BUCKET_NAME,
            auth_method="AWS Access Key",
            message=f"❌ Upload error: {str(e)}",
            message_type='error'
        )


@app.route('/health')
def health():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'region': AWS_REGION,
        'bucket': S3_BUCKET_NAME,
        'auth_method': 'access_key'
    }), 200


if __name__ == '__main__':
    # Configuration check
    if not S3_BUCKET_NAME:
        logger.warning("⚠️  BUCKET_NAME environment variable is not defined!")

    logger.info("🚀 Starting Flask application on port 8080")
    app.run(host='0.0.0.0', port=8080, debug=False)
