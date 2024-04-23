from flask import Flask, render_template, request, send_file, make_response
import os
import boto3
from botocore.exceptions import ClientError
import io

app = Flask(__name__)

# AWS S3 credentials
AWS_ACCESS_KEY = ''
AWS_SECRET_KEY = ''
S3_BUCKET_NAME = ''

# Function to extract error lines from a file
def extract_errors(file):
    error_lines = []
    for line in file.split('\n'):
        if 'error' in line.lower():
            error_lines.append(line)
    return '\n'.join(error_lines)

# Function to upload file to S3
def upload_to_s3(file_name, file_content):
    s3 = boto3.client('s3', aws_access_key_id=AWS_ACCESS_KEY, aws_secret_access_key=AWS_SECRET_KEY)
    s3.put_object(Bucket=S3_BUCKET_NAME, Key=file_name, Body=file_content)

# Function to download file from S3
def download_from_s3(file_name):
    s3 = boto3.client('s3', aws_access_key_id=AWS_ACCESS_KEY, aws_secret_access_key=AWS_SECRET_KEY)
    try:
        response = s3.get_object(Bucket=S3_BUCKET_NAME, Key=file_name)
        return response['Body'].read().decode('utf-8')
    except ClientError as e:
        if e.response['Error']['Code'] == '404':
            return None
        else:
            raise

@app.route('/')
def index():
    return render_template('index.html', log_available=download_from_s3('error_log.txt') is not None)

@app.route('/upload', methods=['POST'])
def upload():
    uploaded_files = request.files.getlist('file[]')
    error_lines = []

    for file in uploaded_files:
        file_content = file.stream.read().decode('utf-8')
        error_lines.append(extract_errors(file_content))

    # Save error lines to a new file
    error_log_content = '\n'.join(error_lines)
    if error_log_content:
        upload_to_s3('error_log.txt', error_log_content)

    return render_template('index.html', log_available=True, message="Upload successful.")

@app.route('/download')
def download():
    file_content = download_from_s3('error_log.txt')
    if file_content is None:
        return "File not found", 404
    response = make_response(file_content)
    response.headers["Content-Disposition"] = "attachment; filename=error_log.txt"
    return response

if __name__ == '__main__':
    app.run(debug=True)
