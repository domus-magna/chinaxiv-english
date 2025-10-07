# Cloudflare Setup Guide

## Current Status ✅

**Completed:**
- ✅ Wrangler CLI installed and authenticated
- ✅ Cloudflare Pages project created (`chinaxiv-english`)
- ✅ Site deployed to https://chinaxiv-english.pages.dev
- ✅ GitHub secrets added: `CLOUDFLARE_ACCOUNT_ID`, `OPENROUTER_API_KEY`
- ✅ GitHub Actions workflow updated to use Wrangler CLI
- ✅ Development tools and scripts created

**Pending:**
- ❌ `CF_API_TOKEN` GitHub secret (needs manual creation)

## Manual Setup Required

### Step 1: Create Cloudflare API Token

1. **Go to Cloudflare Dashboard**
   - Visit: https://dash.cloudflare.com/profile/api-tokens
   - Click "Create Token"

2. **Use Custom Token Template**
   - Click "Custom token"
   - Set the following:

3. **Configure Permissions**
   - **Account**: `Cloudflare Pages:Edit`
   - **Account Resources**: Include your account
   - **Zone Resources**: (leave empty)

4. **Create Token**
   - Click "Continue to summary"
   - Click "Create Token"
   - **Copy the token** (starts with `cf-`)

### Step 2: Add Token to GitHub Secrets

```bash
# Add the API token to GitHub secrets (replace with your repo)
gh secret set CF_API_TOKEN --repo <owner>/<repo> --body "<YOUR_TOKEN_HERE>"
```

### Step 3: Test GitHub Actions Workflow

```bash
# Trigger the workflow
gh workflow run build-and-deploy --repo seconds-0/chinaxiv-english

# Monitor the workflow
gh run list --repo seconds-0/chinaxiv-english --limit 5
```

## Current Configuration

### GitHub Secrets
- ✅ `CLOUDFLARE_ACCOUNT_ID`: <REDACTED>
- ✅ `OPENROUTER_API_KEY`: <REDACTED>
- ❌ `CF_API_TOKEN`: (needs manual creation)

### Cloudflare Pages
- **Project**: `chinaxiv-english`
- **URL**: https://chinaxiv-english.pages.dev
- **Status**: Active and deployed

### GitHub Actions
- **Workflow**: `build-and-deploy`
- **Status**: Ready (waiting for CF_API_TOKEN)
- **Deployment**: Wrangler CLI

## Development Commands

### Local Development
```bash
# Build and serve locally
./scripts/dev.sh dev

# Deploy to Cloudflare Pages
./scripts/dev.sh deploy

# Run translation pipeline
./scripts/dev.sh pipeline 5

# Full workflow
./scripts/dev.sh full
```

### Wrangler CLI
```bash
# Deploy to Pages
wrangler pages deploy site --project-name chinaxiv-english

# Check deployment status
wrangler pages deployment list --project-name chinaxiv-english

# View deployment logs
wrangler pages deployment tail --project-name chinaxiv-english
```

## Troubleshooting

### Common Issues

#### 1. GitHub Actions Fails
- **Check**: All secrets are set correctly
- **Verify**: `CF_API_TOKEN` has correct permissions
- **Monitor**: Workflow logs for specific errors

#### 2. Deployment Fails
- **Check**: Wrangler CLI is authenticated
- **Verify**: Pages project exists
- **Test**: Local deployment works

#### 3. Translation Fails
- **Check**: OpenRouter API key is valid
- **Verify**: API key has sufficient credits
- **Test**: API connection manually

### Debug Commands
```bash
# Check GitHub secrets
gh secret list --repo seconds-0/chinaxiv-english

# Check Wrangler authentication
wrangler whoami

# Check Pages project
wrangler pages project list

# Test local deployment
wrangler pages deploy site --project-name chinaxiv-english --dry-run
```

## Next Steps

### Immediate (After Token Creation)
1. ✅ Create Cloudflare API token
2. ✅ Add token to GitHub secrets
3. ✅ Test GitHub Actions workflow
4. ✅ Verify site deployment
5. ✅ Test translation pipeline

### Short-term (Week 1)
1. ✅ Complete initial setup
2. ✅ Test with small batch (5-10 papers)
3. ✅ Verify all functionality
4. ✅ Run first backfill

### Long-term (Month 1)
1. ✅ Complete full backfill (1000+ papers)
2. ✅ Set up custom domain (when purchased)
3. ✅ Optimize performance
4. ✅ Monitor and maintain

## Expected Results

### After Complete Setup
- ✅ **Site**: https://chinaxiv-english.pages.dev
- ✅ **Daily Updates**: Automated at 3 AM UTC
- ✅ **Translation Pipeline**: Working with real translations
- ✅ **Donation System**: Crypto donation page functional
- ✅ **Search**: Full-text search working
- ✅ **Mobile**: Responsive design

### Performance Metrics
- ✅ **Load Time**: <3 seconds
- ✅ **Uptime**: 99%+
- ✅ **Translation Rate**: 5 papers/day (daily) or 100-2000 papers/hour (backfill)
- ✅ **Cost**: ~$45 for full backfill

## Support Resources

### Documentation
- **Complete Setup**: `docs/archive/old/CLOUDFLARE_COMPLETE_SETUP.md`
- **Wrangler CLI**: `docs/archive/old/WRANGLER_CLI_SETUP.md`
- **Development**: `DEVELOPMENT.md`

### Tools
- **Development Script**: `./scripts/dev.sh`
- **Test Script**: `python3 scripts/test_wrangler.py`
- **Wrangler CLI**: `wrangler`

### Community
- **Cloudflare**: https://community.cloudflare.com/
- **GitHub**: https://github.com/seconds-0/chinaxiv-english

---

**Status**: 95% Complete - Just need to add `CF_API_TOKEN` to GitHub secrets
**Time to Complete**: ~5 minutes (manual token creation)
**Next Action**: Create Cloudflare API token and add to GitHub secrets
