# Authenticate Docker to GCP
gcloud auth configure-docker us-central1-docker.pkg.dev

# Build locally
docker build -t us-central1-docker.pkg.dev/groong-cloud/groong-docker-repo/groong-scraper:latest .

# Push to Artifact Registry
docker push us-central1-docker.pkg.dev/groong-cloud/groong-docker-repo/groong-scraper:latest

