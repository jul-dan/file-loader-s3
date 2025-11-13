# S3 File Uploader - Flask Application

Flask web application for uploading files to Amazon S3 using AWS Access Keys.

## Features

- Modern and responsive web interface for file uploads
- Drag & drop support
- Simple AWS Access Key authentication
- Detailed console logging
- Health check endpoint
- Container deployment ready

## Project Structure

```
file-loader-s3/
├── app.py              # Main Flask application
├── requirements.txt    # Python dependencies
├── Dockerfile         # Production-ready Docker image
├── .dockerignore      # Files to exclude from Docker build
├── .env.example       # Configuration example
└── README.md          # Documentation
```

## Configuration

The application is configured entirely via environment variables:

### Required Variables

- `AWS_REGION`: AWS Region (e.g., eu-west-1, us-east-1)
- `S3_BUCKET_NAME`: Destination S3 bucket name
- `AWS_ACCESS_KEY_ID`: AWS Access Key ID
- `AWS_SECRET_ACCESS_KEY`: AWS Secret Access Key

## Local Installation

### Prerequisites

- Python 3.11+
- AWS Access Key and Secret Key

### Steps

```bash
# Clone the repository
git clone <repo-url>
cd file-loader-s3

# Create a virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Configuration
cp .env.example .env
# Edit .env with your AWS credentials

# Launch the application
python app.py
```

The application will be accessible at http://localhost:8080

## Using Docker

### Build the image

```bash
docker build -t s3-file-uploader .
```

### Run with environment variables

```bash
docker run -p 8080:8080 \
  -e AWS_REGION=eu-west-1 \
  -e S3_BUCKET_NAME=my-bucket \
  -e AWS_ACCESS_KEY_ID=AKIAIOSFODNN7EXAMPLE \
  -e AWS_SECRET_ACCESS_KEY=wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLE \
  s3-file-uploader
```

### Run with .env file

```bash
docker run -p 8080:8080 --env-file .env s3-file-uploader
```

## Deployment on Qovery/Kubernetes

### Kubernetes Deployment Configuration

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: s3-uploader
spec:
  replicas: 2
  selector:
    matchLabels:
      app: s3-uploader
  template:
    metadata:
      labels:
        app: s3-uploader
    spec:
      containers:
      - name: app
        image: your-registry/s3-file-uploader:latest
        ports:
        - containerPort: 8080
        env:
        - name: AWS_REGION
          value: "eu-west-1"
        - name: S3_BUCKET_NAME
          value: "my-bucket"
        - name: AWS_ACCESS_KEY_ID
          valueFrom:
            secretKeyRef:
              name: aws-secrets
              key: access-key-id
        - name: AWS_SECRET_ACCESS_KEY
          valueFrom:
            secretKeyRef:
              name: aws-secrets
              key: secret-access-key
        resources:
          requests:
            memory: "256Mi"
            cpu: "250m"
          limits:
            memory: "512Mi"
            cpu: "500m"
        livenessProbe:
          httpGet:
            path: /health
            port: 8080
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /health
            port: 8080
          initialDelaySeconds: 5
          periodSeconds: 5
```

### Kubernetes Secret

```yaml
apiVersion: v1
kind: Secret
metadata:
  name: aws-secrets
type: Opaque
stringData:
  access-key-id: AKIAIOSFODNN7EXAMPLE
  secret-access-key: wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLE
```

### Qovery Configuration

In the Qovery interface:

1. **Environment Variables**:
   - `AWS_REGION`: eu-west-1
   - `S3_BUCKET_NAME`: my-bucket

2. **Secrets**:
   - `AWS_ACCESS_KEY_ID`: Your AWS Access Key ID
   - `AWS_SECRET_ACCESS_KEY`: Your AWS Secret Access Key

## Required IAM Permissions

Create an IAM user with the following policy attached:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "s3:PutObject",
        "s3:PutObjectAcl"
      ],
      "Resource": "arn:aws:s3:::my-bucket/*"
    }
  ]
}
```

## Endpoints

- `GET /`: Home page with upload form
- `POST /upload`: Endpoint to upload a file
- `GET /health`: Health check (returns JSON)

## Logs

The application logs the following information:

- Configuration at startup (region, bucket, credentials status)
- Each file upload (name, size, S3 key)
- Any errors with stack traces

Example logs:

```
2025-01-13 10:15:30 - __main__ - INFO - === Application Configuration ===
2025-01-13 10:15:30 - __main__ - INFO - AWS_REGION: eu-west-1
2025-01-13 10:15:30 - __main__ - INFO - S3_BUCKET_NAME: my-bucket
2025-01-13 10:15:30 - __main__ - INFO - AWS_ACCESS_KEY_ID: ********
2025-01-13 10:15:30 - __main__ - INFO - AWS_SECRET_ACCESS_KEY: ********
2025-01-13 10:15:45 - __main__ - INFO - Creating S3 client with AWS credentials
2025-01-13 10:15:46 - __main__ - INFO - S3 client created successfully
2025-01-13 10:15:47 - __main__ - INFO - Uploading file 'document.pdf' to s3://my-bucket/uploads/20250113-101547-document.pdf
2025-01-13 10:15:48 - __main__ - INFO - ✅ File uploaded successfully
```

## Security

- Container runs with a non-root user
- Filename validation and securing (secure_filename)
- File size limit: 16 MB
- AWS credentials never exposed in logs (masked with asterisks)
- HTTPS support recommended in production
- Use IAM users with minimal required permissions

## Troubleshooting

### Error "No credentials found"

Check that:
- `AWS_ACCESS_KEY_ID` and `AWS_SECRET_ACCESS_KEY` are defined
- OR AWS CLI is configured (`aws configure`)

### Error "Access Denied"

Check that:
- The IAM user has `s3:PutObject` permissions on the bucket
- The credentials are correct and not expired

### Error "Bucket not found"

Check that:
- The bucket exists in the specified region
- The bucket name is correct in `S3_BUCKET_NAME`

## License

MIT
