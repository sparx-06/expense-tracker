# GitHub Container Registry Setup Guide

This guide will help you set up the expense tracker to automatically build and publish Docker images to GitHub Container Registry.

## Step 1: Create GitHub Repository

1. Go to https://github.com/new
2. Repository name: `expense-tracker`
3. Description: "Self-hosted expense tracker for events"
4. Set to **Public** (so the image can be pulled without authentication)
5. Click **Create repository**

## Step 2: Upload Code to GitHub

### Option A: Using GitHub Web Interface

1. On your new repository page, click **uploading an existing file**
2. Drag and drop all files from the `expense-tracker-repo` folder:
   - `.github/workflows/docker-publish.yml`
   - `app/` folder with all contents
   - `Dockerfile`
   - `README.md`
   - `.gitignore`
3. Commit the files

### Option B: Using Git Command Line

```bash
cd expense-tracker-repo
git init
git add .
git commit -m "Initial commit"
git branch -M main
git remote add origin https://github.com/yourusername/expense-tracker.git
git push -u origin main
```

## Step 3: Automatic Build

Once you push the code:
1. GitHub Actions will automatically trigger
2. It will build the Docker image
3. Push it to `ghcr.io/yourusername/expense-tracker:latest`
4. Check progress: Go to your repo → **Actions** tab

## Step 4: Make Image Public

1. Go to your GitHub profile
2. Click **Packages** tab
3. Click on **expense-tracker**
4. Click **Package settings** (bottom right)
5. Scroll to **Danger Zone** → **Change visibility**
6. Set to **Public**
7. Confirm

## Step 5: Update compose.yaml for TrueNAS

Replace `yourusername` with your actual GitHub username:

```yaml
services:
  expense-tracker:
    image: ghcr.io/yourusername/expense-tracker:latest
    container_name: expense-tracker
    ports:
      - "5000:5000"
    volumes:
      - ./data:/app/data
    environment:
      - SQLALCHEMY_DATABASE_URI=sqlite:////app/data/expenses.db
    restart: unless-stopped
```

## Step 6: Deploy to TrueNAS

1. Create `/mnt/DataStore/Apps/expense-tracker/compose.yaml` with the content above
2. In TrueNAS Apps → Custom App:
```yaml
include:
  - path: /mnt/DataStore/Apps/expense-tracker/compose.yaml
services: {}
```
3. Deploy!

## Future Updates

When we make updates:
1. I'll provide updated code
2. You commit and push to your GitHub repo
3. GitHub Actions automatically builds new image
4. In TrueNAS, stop and start the container to pull the latest image

Or use Watchtower to auto-update:
```yaml
services:
  expense-tracker:
    image: ghcr.io/yourusername/expense-tracker:latest
    # ... rest of config

  watchtower:
    image: containrrr/watchtower
    volumes:
      - /var/run/docker.sock:/var/run/docker.sock
    command: --interval 3600 expense-tracker
```

## Troubleshooting

### Build Failed
- Check **Actions** tab in your GitHub repo
- Look for error messages in the workflow logs

### Can't Pull Image
- Make sure the package is set to **Public**
- Check the image name matches your username

### Need Help?
- Check GitHub Actions logs
- Verify all files were uploaded correctly
- Ensure Dockerfile is in the root of the repository
