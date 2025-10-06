# Cloudflare Pages Setup Guide

## Overview
This guide helps you set up Cloudflare Pages deployment to avoid local sleep issues and run the translation pipeline reliably in the cloud.

## Prerequisites
- GitHub repository with the ChinaXiv Translations code
- Cloudflare account
- OpenRouter API key

## Step 1: Get Cloudflare Credentials

### 1.1 Get Cloudflare Account ID
1. Log in to [Cloudflare Dashboard](https://dash.cloudflare.com)
2. Select your domain or any domain
3. In the right sidebar, find "Account ID"
4. Copy this value - you'll need it for `CLOUDFLARE_ACCOUNT_ID`

### 1.2 Create API Token
1. Go to [Cloudflare API Tokens](https://dash.cloudflare.com/profile/api-tokens)
2. Click "Create Token"
3. Use "Custom token" template
4. Set permissions:
   - **Account**: `Cloudflare Pages:Edit`
   - **Zone**: `Zone:Read` (if you have a custom domain)
5. Account Resources: Include your account
6. Zone Resources: Include all zones (if using custom domain)
7. Click "Continue to summary" then "Create Token"
8. Copy the token - you'll need it for `CF_API_TOKEN`

## Step 2: Configure GitHub Secrets

### 2.1 Add Secrets to GitHub Repository
1. Go to your GitHub repository
2. Click "Settings" → "Secrets and variables" → "Actions"
3. Add these repository secrets:

| Secret Name | Value | Description |
|-------------|-------|-------------|
| `CF_API_TOKEN` | Your Cloudflare API token | From Step 1.2 |
| `CLOUDFLARE_ACCOUNT_ID` | Your Cloudflare Account ID | From Step 1.1 |
| `OPENROUTER_API_KEY` | Your OpenRouter API key | For translations |
| `DISCORD_WEBHOOK_URL` | Discord webhook URL (optional) | For notifications |

### 2.2 Verify Secrets
- All secrets should show as "●●●●●●●●●●●●●●●●"
- Make sure there are no extra spaces or characters

## Step 3: Create Cloudflare Pages Project

### 3.1 Connect Repository
1. Go to [Cloudflare Pages](https://pages.cloudflare.com)
2. Click "Connect to Git"
3. Select your GitHub account
4. Choose the `chinaxiv-english` repository
5. Click "Begin setup"

### 3.2 Configure Build Settings
- **Project name**: `chinaxiv-english`
- **Production branch**: `main`
- **Build command**: (leave empty - GitHub Actions handles this)
- **Build output directory**: `site`
- **Root directory**: (leave empty)

### 3.3 Environment Variables
Add these environment variables in Cloudflare Pages:
- `OPENROUTER_API_KEY`: Your OpenRouter API key
- `DISCORD_WEBHOOK_URL`: Your Discord webhook (optional)

## Step 4: Test Deployment

### 4.1 Manual Trigger
1. Go to your GitHub repository
2. Click "Actions" tab
3. Select "build-and-deploy" workflow
4. Click "Run workflow"
5. Select "main" branch
6. Click "Run workflow"

### 4.2 Monitor Build
1. Watch the workflow progress
2. Check each step for errors
3. Look for "Deploy to Cloudflare Pages" step
4. Verify deployment success

### 4.3 Verify Site
1. Go to Cloudflare Pages dashboard
2. Find your `chinaxiv-english` project
3. Click on the project
4. Check the "Deployments" tab
5. Click on the latest deployment
6. Verify the site loads correctly

## Step 5: Configure Custom Domain (Optional)

### 5.1 Add Custom Domain
1. In Cloudflare Pages project
2. Go to "Custom domains" tab
3. Click "Set up a custom domain"
4. Enter your domain (e.g., `chinaxiv-english.com`)
5. Follow DNS configuration instructions

### 5.2 DNS Configuration
- Add CNAME record pointing to your Pages domain
- Or use Cloudflare's automatic DNS setup

## Step 6: Schedule Automation

### 6.1 Cron Schedule
The workflow is already configured to run daily at 3:00 AM UTC:
```yaml
schedule:
  - cron: '0 3 * * *'
```

### 6.2 Manual Triggers
You can also trigger manually:
- GitHub Actions → "Run workflow"
- Cloudflare Pages → "Retry deployment"

## Troubleshooting

### Common Issues

#### 1. Build Fails
- Check GitHub Actions logs
- Verify all secrets are set correctly
- Ensure `requirements.txt` is up to date

#### 2. Deployment Fails
- Verify `CF_API_TOKEN` has correct permissions
- Check `CLOUDFLARE_ACCOUNT_ID` is correct
- Ensure Cloudflare Pages project exists

#### 3. Translation Fails
- Verify `OPENROUTER_API_KEY` is valid
- Check API key has sufficient credits
- Review translation service logs

#### 4. Site Not Loading
- Check Cloudflare Pages deployment status
- Verify build output directory is `site`
- Check for JavaScript errors in browser console

### Debug Commands
```bash
# Check GitHub Actions status
gh run list

# Check Cloudflare Pages deployments
curl -X GET "https://api.cloudflare.com/client/v4/accounts/{account_id}/pages/projects/chinaxiv-english/deployments" \
  -H "Authorization: Bearer {api_token}"

# Test OpenRouter API
curl -X POST "https://openrouter.ai/api/v1/chat/completions" \
  -H "Authorization: Bearer {api_key}" \
  -H "Content-Type: application/json" \
  -d '{"model": "deepseek/deepseek-v3.2-exp", "messages": [{"role": "user", "content": "Hello"}], "max_tokens": 10}'
```

## Benefits of Cloudflare Setup

### ✅ Advantages
- **No Sleep Issues**: Runs in cloud, never sleeps
- **Reliable Scheduling**: GitHub Actions cron is very reliable
- **Automatic Deployment**: Site updates automatically
- **Global CDN**: Fast loading worldwide
- **Free Tier**: Generous free limits
- **Easy Monitoring**: Built-in logs and metrics

### 🔧 Maintenance
- **Monitor Logs**: Check GitHub Actions and Cloudflare Pages logs
- **Update Secrets**: Rotate API keys periodically
- **Scale Up**: Upgrade if you hit limits
- **Backup**: Keep local backups of important data

## Next Steps
1. Set up Cloudflare credentials
2. Add GitHub secrets
3. Create Cloudflare Pages project
4. Test deployment
5. Monitor first few automated runs
6. Set up custom domain (optional)

Once set up, your translation pipeline will run reliably every day at 3 AM UTC without any local sleep issues!
