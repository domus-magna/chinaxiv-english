# Setup Guide: ChinaXiv Translation Pipeline

## Current Environment Status

✅ **OpenRouter API Key**: Set and working
❌ **Cloudflare**: Not yet configured

## Required Setup Steps

### 1. GitHub Actions Secrets

You need to add these secrets to your GitHub repository:

#### Required Secrets:
- `OPENROUTER_API_KEY` - Your OpenRouter API key
- `CF_API_TOKEN` - Cloudflare API token (for Pages deployment)
- `CLOUDFLARE_ACCOUNT_ID` - Your Cloudflare account ID

#### How to Add Secrets:
1. Go to your repository: https://github.com/seconds-0/chinaxiv-english
2. Click **Settings** → **Secrets and variables** → **Actions**
3. Click **New repository secret**
4. Add each secret:

```
Name: OPENROUTER_API_KEY
Value: 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

Name: CF_API_TOKEN
Value: [Your Cloudflare API token - see step 2]

Name: CLOUDFLARE_ACCOUNT_ID
Value: [Your Cloudflare Account ID - see step 2]
```

### 2. Cloudflare Pages Setup

#### Step 2a: Create Cloudflare Account
1. Go to https://cloudflare.com
2. Sign up for a free account
3. Verify your email

#### Step 2b: Get Account ID
1. Go to Cloudflare Dashboard
2. Select any domain (or create a test domain)
3. Copy your **Account ID** from the right sidebar
4. This is your `CLOUDFLARE_ACCOUNT_ID`

#### Step 2c: Create API Token
1. Go to **My Profile** → **API Tokens**
2. Click **Create Token**
3. Use **Custom token** template
4. Set permissions:
   - **Account**: `Cloudflare Pages:Edit`
   - **Zone**: `Zone:Read` (if you have a domain)
5. Set account resources: `Include - All accounts`
6. Click **Continue to summary** → **Create Token**
7. Copy the token (this is your `CF_API_TOKEN`)

#### Step 2d: Create Pages Project
1. Go to **Pages** in Cloudflare dashboard
2. Click **Create a project**
3. Choose **Connect to Git**
4. Select your repository: `seconds-0/chinaxiv-english`
5. Set project name: `chinaxiv-english`
6. Set build settings:
   - **Framework preset**: None
   - **Build command**: `echo "Static site - no build needed"`
   - **Build output directory**: `site`
7. Click **Save and Deploy**

### 3. Local Development Setup

#### Environment Variables
Create a `.env` file in the project root:

```bash
# Required for translation
OPENROUTER_API_KEY=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

# Optional for local development
CF_API_TOKEN=your_cloudflare_token_here
CLOUDFLARE_ACCOUNT_ID=your_account_id_here
```

#### Local Development Commands
```bash
# Activate environment
source .venv/bin/activate

# Deploy and test locally
./scripts/deploy.sh

# Monitor health
python scripts/monitor.py

# Run pipeline
python -m src.pipeline --limit 10

# Serve site locally
python -m http.server -d site 8001
```

### 4. GitHub Actions Workflow

The workflow will automatically:
- **Run nightly** at 03:00 UTC
- **Harvest** papers from Internet Archive
- **Translate** using OpenRouter
- **Generate** static site
- **Deploy** to Cloudflare Pages

#### Manual Trigger
You can also trigger the workflow manually:
1. Go to **Actions** tab in GitHub
2. Select **build-and-deploy** workflow
3. Click **Run workflow**

### 5. Verification

#### Check GitHub Actions
1. Go to **Actions** tab
2. Verify workflow runs successfully
3. Check logs for any errors

#### Check Cloudflare Pages
1. Go to Cloudflare Pages dashboard
2. Verify deployment is successful
3. Visit your site URL (e.g., `chinaxiv-english.pages.dev`)

#### Check Site Functionality
1. Visit the deployed site
2. Test search functionality
3. Verify translations are working
4. Check math rendering with MathJax

### 6. Monitoring

#### Health Monitoring
```bash
# Check system health
python scripts/monitor.py

# Watch mode (updates every 30 seconds)
python scripts/monitor.py --watch

# Save health report
python scripts/monitor.py --output data/health_report.json
```

#### Cost Monitoring
```bash
# Check translation costs
python -c "
import json, glob
total_cost = 0
for file in glob.glob('data/costs/*.json'):
    with open(file) as f: data = json.load(f)
    total_cost += sum(item.get('cost', 0) for item in data)
print(f'Total cost: ${total_cost:.4f}')
"
```

### 7. Troubleshooting

#### Common Issues

**GitHub Actions Fails**:
- Check secrets are set correctly
- Verify API keys are valid
- Check workflow logs for specific errors

**Cloudflare Deployment Fails**:
- Verify API token permissions
- Check account ID is correct
- Ensure Pages project is created

**Translation Fails**:
- Check OpenRouter API key
- Verify API quota/limits
- Check network connectivity

**Site Not Loading**:
- Check Cloudflare Pages deployment status
- Verify site files are generated
- Check for JavaScript errors

#### Debug Commands
```bash
# Test API connectivity
python -c "
import os, requests
key = os.getenv('OPENROUTER_API_KEY')
headers = {'Authorization': f'Bearer {key}'}
resp = requests.get('https://openrouter.ai/api/v1/models', headers=headers)
print('OpenRouter:', resp.status_code)
"

# Test Internet Archive
python -c "
import requests
resp = requests.get('https://archive.org/services/search/v1/scrape?q=collection:chinaxivmirror&count=1')
print('Internet Archive:', resp.status_code)
"

# Test local pipeline
python -m src.pipeline --limit 1 --dry-run
```

### 8. Production Checklist

- [ ] GitHub Actions secrets configured
- [ ] Cloudflare account created
- [ ] Cloudflare Pages project created
- [ ] API tokens generated
- [ ] Workflow runs successfully
- [ ] Site deploys to Cloudflare Pages
- [ ] Search functionality works
- [ ] Math rendering works
- [ ] Translations are high quality
- [ ] Monitoring is set up
- [ ] Cost tracking is working

## Support

If you encounter issues:
1. Check the troubleshooting section above
2. Review GitHub Actions logs
3. Check Cloudflare Pages deployment logs
4. Use the monitoring tools to diagnose issues
5. Check the manual test plan for validation steps

## Next Steps

Once everything is set up:
1. **Monitor** the nightly pipeline
2. **Review** translation quality
3. **Optimize** costs and performance
4. **Scale** to more papers
5. **Enhance** features as needed
