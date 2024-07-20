# Resume Processing Service

This project is a Flask application designed to process resumes sent via email with attached PDF files. The application extracts various fields and skills from the resumes and saves the information to a Google Sheets file. The application is deployed as an AWS Lambda function.

## Features

- Extracts text from PDF resumes.
- Identifies and extracts candidate names, job titles, skills, industries, and project titles from the text.
- Saves the extracted information to a Google Sheets file.
- Provides a webhook endpoint for processing PDF files from a given URL.

## Endpoints

### Root Endpoint
- **URL**: [https://zlcmtcv5yv65ghwjzmpqbrqg7m0nigbw.lambda-url.us-east-2.on.aws/](https://zlcmtcv5yv65ghwjzmpqbrqg7m0nigbw.lambda-url.us-east-2.on.aws/)
- **Method**: `GET`
- **Description**: This is a simple endpoint to verify that the service is running. It returns a "Hi" message.

### Webhook Endpoint
- **URL**: [https://zlcmtcv5yv65ghwjzmpqbrqg7m0nigbw.lambda-url.us-east-2.on.aws/webhook](https://zlcmtcv5yv65ghwjzmpqbrqg7m0nigbw.lambda-url.us-east-2.on.aws/webhook)
- **Method**: `POST`
- **Description**: This endpoint processes a PDF file from a given URL, extracts information, and updates the Google Sheets file.
- **Request Body**:
  ```json
  {
    "url": "URL_OF_THE_PDF_FILE"
  }

## Challenges

### Selecting Library to Extract Data
- Initially, there were limitations based on the resume format. Various libraries were tested to find the most suitable one that could handle different resume formats effectively.

### Testing and Optimization
- The application was tested on different resume formats to optimize the extraction process. Continuous improvements were made to enhance the accuracy of data extraction.

### Handling Large Libraries
- Due to the large size of the libraries used, we shifted from a simple Lambda function to uploading a `.zip` file to S3 and then deploying via Docker ECR. This approach helped manage the library size effectively.

### Lambda Write Limitations
- AWS Lambda has a limitation on writing to the server. To address this, we used in-memory processing to handle files during the execution.

## Setup and Deployment

### Requirements
- Python 3.9
- AWS account with Lambda setup
- Google Cloud project with a service account that has access to Google Sheets API
- Docker
- Amazon ECR

### Install Dependencies
```
pip install -r requirements.txt
```
### Environment Variables Setup
Set the following environment variables in your Lambda environment or locally for testing:
```
export SVC_ACCOUNT_FILE=path/to/your/service-account-file.json
export GOOGLE_SHEET_ID=your-google-sheet-id
export S3_BUCKET_NAME=your-s3-bucket-name
```
### Running Locally
```
python app.py
```

## Deploying to AWS Lambda using Docker ECR
### Build the Docker image:
```
docker build -t your-docker-image-name .
```
### Tag the Docker image:
```
docker tag your-docker-image-name:latest aws_account_id.dkr.ecr.region.amazonaws.com/your-docker-image-name:latest
```
### Push the Docker image to ECR:
```
docker push aws_account_id.dkr.ecr.region.amazonaws.com/your-docker-image-name:latest
```
### Create an AWS Lambda function and configure it to use the Docker image from ECR.

### Set the necessary environment variables in the AWS Lambda configuration.

### Usage
Once deployed, you can send a POST request to the webhook endpoint with the URL of the PDF file to be processed. The application will extract the relevant information from the PDF and update the Google Sheets file accordingly.
## Limitations
### Improve Accuracy: 
Further improvements are needed to enhance the accuracy of data extraction from different resume formats.
### Handle Multiple Attachments: 
Currently, the application can only process PDF files. Enhancements are needed to handle multiple attachments and various MIME types from services like Zapier.
### In-Memory Processing Constraints: 
Handling large files in-memory might be constrained by the available memory in the AWS Lambda environment.
### Service Availability: 
Dependence on external services (AWS, Google Sheets) means that any downtime or service changes could affect the application's performance.
### Security: 
Ensuring the security and privacy of the extracted data and handling of service account credentials is critical and needs continuous monitoring and improvements.
### Resume Formats
The application might struggle with highly formatted or non-standard resume layouts. While it performs well with standard formats, unusual or complex designs may reduce the accuracy of data extraction.
