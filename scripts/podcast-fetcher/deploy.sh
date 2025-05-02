gcloud builds submit --tag gcr.io/groong-cloud/podcast-fetcher .

gcloud run deploy podcast-fetcher \
  --image gcr.io/groong-cloud/podcast-fetcher \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated \
  --service-account=podcast-runner@groong-cloud.iam.gserviceaccount.com

