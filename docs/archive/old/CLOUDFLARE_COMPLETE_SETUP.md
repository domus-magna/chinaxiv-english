# Complete Cloudflare Pages Setup Guide

## Overview
This guide walks you through setting up Cloudflare Pages for ChinaXiv Translations, including testing, deployment, and custom domain configuration.

## Prerequisites
- GitHub repository with ChinaXiv Translations code
- Cloudflare account (free)
- OpenRouter API key
- Optional: Custom domain (for production)

## Step 1: Get Cloudflare Credentials

### 1.1 Create Cloudflare Account
1. Go to [Cloudflare Dashboard](https://dash.cloudflare.com)
2. Sign up for a free account
3. Verify your email address

### 1.2 Get Cloudflare Account ID
1. Log in to [Cloudflare Dashboard](https://dash.cloudflare.com)
2. Select any domain (or add a test domain)
3. In the right sidebar, find "Account ID"
4. Copy this value - you'll need it for `CLOUDFLARE_ACCOUNT_ID`
5. Example: `1234567890abcdef1234567890abcdef`

### 1.3 Create Cloudflare API Token
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
9. Example: `abc123def456ghi789jkl012mno345pqr678stu901vwx234yz`

## Step 2: Configure GitHub Secrets

### 2.1 Add Secrets to GitHub Repository
1. Go to your GitHub repository: `https://github.com/your-username/chinaxiv-english`
2. Click "Settings" → "Secrets and variables" → "Actions"
3. Click "New repository secret"
4. Add these secrets:

| Secret Name | Value | Description |
|-------------|-------|-------------|
| `CF_API_TOKEN` | Your Cloudflare API token | From Step 1.3 |
| `CLOUDFLARE_ACCOUNT_ID` | Your Cloudflare Account ID | From Step 1.2 |
| `OPENROUTER_API_KEY` | Your OpenRouter API key | For translations |
| `DISCORD_WEBHOOK_URL` | Discord webhook URL (optional) | For notifications |

### 2.2 Verify Secrets
- All secrets should show as "●●●●●●●●●●●●●●●●"
- Make sure there are no extra spaces or characters
- Double-check the values are correct

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

### 3.4 Save and Deploy
1. Click "Save and Deploy"
2. Wait for the initial deployment to complete
3. Note the Pages URL (e.g., `https://chinaxiv-english.pages.dev`)

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
2. Check each step for errors:
   - "Install deps" - Should install Python packages
   - "Tests" - Should run pytest
   - "Health check" - Should check system health
   - "Build site" - Should harvest, translate, and render
   - "Deploy to Cloudflare Pages" - Should deploy to Pages

### 4.3 Verify Site
1. Go to Cloudflare Pages dashboard
2. Find your `chinaxiv-english` project
3. Check the "Deployments" tab
4. Click on the latest deployment
5. Verify the site loads correctly at the Pages URL

## Step 5: Test Translation Pipeline

### 5.1 Test Small Batch
1. Go to GitHub Actions
2. Run "backfill-parallel" workflow
3. Set parameters:
   - `total_papers`: 10
   - `workers_per_job`: 5
   - `parallel_jobs`: 2
4. Monitor the build
5. Check for translated papers in the site

### 5.2 Verify Translation Quality
1. Visit your Pages site
2. Check that papers are translated
3. Verify search functionality works
4. Test donation page
5. Check mobile responsiveness

## Step 6: Production Deployment

### 6.1 Run Full Backfill
1. Go to GitHub Actions
2. Run "backfill-ultra-parallel" workflow
3. Set parameters:
   - `total_papers`: 1000
   - `workers_per_job`: 50
   - `parallel_jobs`: 10
4. Monitor progress (should take ~2 hours)
5. Verify all papers are translated

### 6.2 Monitor Performance
1. Check GitHub Actions logs
2. Monitor API costs
3. Verify site performance
4. Check for any errors

## Step 7: Custom Domain Setup (When You Buy One)

### 7.1 Purchase Domain
1. Buy a domain from any registrar (GoDaddy, Namecheap, etc.)
2. Examples: `chinaxiv-english.com`, `chinaxiv-translations.org`
3. Note: You don't need to configure DNS yet

### 7.2 Add Domain to Cloudflare
1. Go to [Cloudflare Dashboard](https://dash.cloudflare.com)
2. Click "Add a Site"
3. Enter your domain name
4. Choose "Free" plan
5. Cloudflare will scan your existing DNS records

### 7.3 Update Nameservers
1. Go to your domain registrar
2. Find "Nameservers" or "DNS" settings
3. Replace existing nameservers with Cloudflare's:
   - `alex.ns.cloudflare.com`
   - `barbara.ns.cloudflare.com`
4. Save changes
5. Wait 24-48 hours for propagation

### 7.4 Connect Domain to Pages
1. Go to Cloudflare Pages dashboard
2. Select your `chinaxiv-english` project
3. Go to "Custom domains" tab
4. Click "Set up a custom domain"
5. Enter your domain name
6. Click "Continue"

### 7.5 Configure DNS
1. Cloudflare will automatically create DNS records
2. Verify the records are correct:
   - `CNAME` record pointing to your Pages domain
   - `A` record for root domain (if needed)
3. Wait for DNS propagation (5-30 minutes)

### 7.6 SSL Certificate
1. Cloudflare automatically issues SSL certificates
2. Wait for certificate to be issued (5-10 minutes)
3. Test HTTPS access to your domain

## Step 8: Production Optimization

### 8.1 Performance Settings
1. Go to Cloudflare Dashboard
2. Select your domain
3. Go to "Speed" tab
4. Enable:
   - Auto Minify (HTML, CSS, JS)
   - Brotli compression
   - Rocket Loader (if needed)

### 8.2 Security Settings
1. Go to "Security" tab
2. Set Security Level to "Medium"
3. Enable "Always Use HTTPS"
4. Configure "Page Rules" if needed

### 8.3 Analytics
1. Go to "Analytics" tab
2. Monitor traffic and performance
3. Set up alerts for downtime

## Step 9: Monitoring and Maintenance

### 9.1 GitHub Actions Monitoring
1. Check workflow runs regularly
2. Monitor for failures
3. Review logs for errors
4. Update dependencies as needed

### 9.2 Cloudflare Pages Monitoring
1. Check deployment status
2. Monitor build times
3. Review error logs
4. Check performance metrics

### 9.3 Cost Monitoring
1. Monitor OpenRouter API usage
2. Check GitHub Actions minutes
3. Review Cloudflare usage
4. Set up billing alerts

## Troubleshooting

### Common Issues

#### 1. Build Fails
**Symptoms**: GitHub Actions workflow fails
**Solutions**:
- Check GitHub Actions logs
- Verify all secrets are set correctly
- Ensure `requirements.txt` is up to date
- Check Python version compatibility

#### 2. Deployment Fails
**Symptoms**: Cloudflare Pages deployment fails
**Solutions**:
- Verify `CF_API_TOKEN` has correct permissions
- Check `CLOUDFLARE_ACCOUNT_ID` is correct
- Ensure Cloudflare Pages project exists
- Check build output directory is `site`

#### 3. Translation Fails
**Symptoms**: No translated papers appear
**Solutions**:
- Verify `OPENROUTER_API_KEY` is valid
- Check API key has sufficient credits
- Review translation service logs
- Test API key manually

#### 4. Site Not Loading
**Symptoms**: Pages site doesn't load
**Solutions**:
- Check Cloudflare Pages deployment status
- Verify build output directory is `site`
- Check for JavaScript errors in browser console
- Test different browsers/devices

#### 5. Custom Domain Issues
**Symptoms**: Custom domain doesn't work
**Solutions**:
- Check DNS propagation (use `dig` or `nslookup`)
- Verify nameservers are correct
- Wait for SSL certificate to be issued
- Check Cloudflare DNS records

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

# Check DNS propagation
dig yourdomain.com
nslookup yourdomain.com
```

## Expected Timeline

### Initial Setup
- **Get Cloudflare credentials**: 10 minutes
- **Add GitHub secrets**: 5 minutes
- **Create Pages project**: 10 minutes
- **Test deployment**: 30 minutes
- **Total**: ~1 hour

### Testing Phase
- **Small batch test**: 30 minutes
- **Quality verification**: 30 minutes
- **Total**: ~1 hour

### Production Deployment
- **Full backfill**: 2-4 hours
- **Custom domain setup**: 1-2 hours
- **Optimization**: 30 minutes
- **Total**: ~4-6 hours

## Cost Breakdown

### Free Tier (Recommended)
- **Cloudflare Pages**: Free
- **GitHub Actions**: 2,000 minutes/month (free)
- **OpenRouter API**: ~$45 for full backfill
- **Total**: ~$45 one-time cost

### Paid Tier (If Needed)
- **Cloudflare Pages**: Free
- **GitHub Actions**: $0.008/minute (if over free limit)
- **OpenRouter API**: ~$45 for full backfill
- **Total**: ~$45 + GitHub Actions overage

## Success Metrics

### Technical Metrics
- ✅ Site loads in <3 seconds
- ✅ Translation pipeline runs daily
- ✅ 99%+ uptime
- ✅ SSL certificate active
- ✅ Mobile responsive

### Content Metrics
- ✅ 1000+ translated papers
- ✅ Search functionality works
- ✅ Donation page functional
- ✅ No translation errors

### Performance Metrics
- ✅ Page load time <2 seconds
- ✅ Translation completion rate >95%
- ✅ API response time <5 seconds
- ✅ Error rate <1%

## Next Steps After Setup

### Immediate (Week 1)
1. Complete initial setup
2. Test with small batch
3. Verify all functionality
4. Run first backfill

### Short-term (Month 1)
1. Complete full backfill
2. Set up custom domain
3. Optimize performance
4. Monitor and maintain

### Long-term (Month 2+)
1. Scale up translation volume
2. Add new features
3. Optimize costs
4. Expand functionality

## Support and Resources

### Documentation
- **Cloudflare Pages**: https://developers.cloudflare.com/pages/
- **GitHub Actions**: https://docs.github.com/en/actions
- **OpenRouter API**: https://openrouter.ai/docs

### Community
- **Cloudflare Community**: https://community.cloudflare.com/
- **GitHub Support**: https://support.github.com/
- **OpenRouter Discord**: https://discord.gg/openrouter

### Monitoring Tools
- **GitHub Actions**: Built-in monitoring
- **Cloudflare Analytics**: Built-in analytics
- **OpenRouter Dashboard**: API usage monitoring

---

**Total setup time**: ~2-3 hours
**Total cost**: ~$45 (one-time)
**Maintenance**: Minimal (automated)
**Scalability**: Excellent (cloud-based)
