# Serverless URL Shortener

A simple URL shortener built entirely on AWS serverless services.

## Architecture
- **AWS Lambda** (Python 3.12) — handles creating short URLs and redirecting
- **Lambda Function URL** — direct HTTPS endpoint for the Lambda (no API Gateway needed)
- **DynamoDB** — stores the mapping between short codes and original URLs
- **HTML/JavaScript frontend** — simple form to submit a URL and get back a short link
- Region used: `ap-southeast-2`

## How it works
1. User pastes a long URL into the frontend and clicks "Shorten"
2. Frontend sends a POST request to the Lambda Function URL with the long URL
3. Lambda generates a random 6-character short code, saves `{shortCode, longUrl}` to DynamoDB, and returns the short code
4. When someone visits `<function-url>/<shortCode>`, Lambda looks it up in DynamoDB and issues a 302 redirect to the original URL

## Setup
1. Create a DynamoDB table named `UrlShortenerTable` with `shortCode` (String) as the partition key
2. Create a Lambda function (Python 3.12 runtime), paste in `lambda_function.py`
3. Enable a **Function URL** for the Lambda (Auth type: NONE for public access)
4. Attach an IAM policy to the Lambda's execution role allowing `dynamodb:GetItem` and `dynamodb:PutItem` on the table
5. Update `API_ENDPOINT` in `index.html` with your actual Function URL
6. Open `index.html` in a browser (or host it via S3 static website hosting)

## Notes
- Lambda Function URLs use a different event structure than API Gateway
  (`event['requestContext']['http']['method']` instead of `event['httpMethod']`) — this is handled in the code
- CORS headers are included on every response so the frontend can call the Function URL directly from the browser
