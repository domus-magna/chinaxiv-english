# Cloudflare Quick Start Checklist

## ✅ Pre-Setup (5 minutes)
- [ ] Cloudflare account created
- [ ] GitHub repository ready
- [ ] OpenRouter API key obtained

## ✅ Step 1: Get Credentials (10 minutes)
- [ ] **Cloudflare Account ID**
  - Go to [Cloudflare Dashboard](https://dash.cloudflare.com)
  - Select any domain
  - Copy "Account ID" from right sidebar
  - Example: `1234567890abcdef1234567890abcdef`

- [ ] **Cloudflare API Token**
  - Go to [API Tokens](https://dash.cloudflare.com/profile/api-tokens)
  - Click "Create Token" → "Custom token"
  - Permissions: `Cloudflare Pages:Edit`
  - Account Resources: Include your account
  - Copy the token (starts with `...`)

## ✅ Step 2: Add GitHub Secrets (5 minutes)
Run the setup script:
```bash
python3 scripts/setup_cloudflare_secrets.py
```

Or manually add these secrets in GitHub:
- [ ] `CF_API_TOKEN` - Your Cloudflare API token
- [ ] `CLOUDFLARE_ACCOUNT_ID` - Your Cloudflare Account ID  
- [ ] `OPENROUTER_API_KEY` - Your OpenRouter API key (already have this)

## ✅ Step 3: Create Cloudflare Pages Project (10 minutes)
- [ ] Go to [Cloudflare Pages](https://pages.cloudflare.com)
- [ ] Click "Connect to Git"
- [ ] Select GitHub account
- [ ] Choose `chinaxiv-english` repository
- [ ] Project name: `chinaxiv-english`
- [ ] Build output directory: `site`
- [ ] Click "Save and Deploy"

## ✅ Step 4: Test Deployment (30 minutes)
- [ ] Go to GitHub → Actions tab
- [ ] Click "build-and-deploy" workflow
- [ ] Click "Run workflow" → "Run workflow"
- [ ] Watch the build progress
- [ ] Check for "Deploy to Cloudflare Pages" step
- [ ] Verify site loads at Cloudflare Pages URL

## ✅ Step 5: Test Translation Pipeline (30 minutes)
- [ ] Go to GitHub Actions
- [ ] Run "backfill-parallel" workflow
- [ ] Set parameters:
  - `total_papers`: 10
  - `workers_per_job`: 5
  - `parallel_jobs`: 2
- [ ] Monitor the build
- [ ] Check for translated papers in the site

## ✅ Step 6: Verify Everything Works (15 minutes)
- [ ] Site loads correctly
- [ ] Translation pipeline runs (check logs)
- [ ] Donation page works
- [ ] Search functionality works
- [ ] Mobile responsive

## 🚨 Troubleshooting

### Common Issues:
1. **Build fails**: Check GitHub Actions logs
2. **Deployment fails**: Verify `CF_API_TOKEN` permissions
3. **Translation fails**: Check `OPENROUTER_API_KEY` is valid
4. **Site not loading**: Check build output directory is `site`

### Debug Commands:
```bash
# Check GitHub secrets
gh secret list

# Check GitHub Actions
gh run list

# Test OpenRouter API
curl -X POST "https://openrouter.ai/api/v1/chat/completions" \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"model": "deepseek/deepseek-v3.2-exp", "messages": [{"role": "user", "content": "Hello"}], "max_tokens": 10}'
```

## 🎉 Benefits After Setup

- ✅ **No more sleep issues** - runs in cloud
- ✅ **Automatic daily updates** - 3 AM UTC schedule
- ✅ **Global CDN** - fast loading worldwide
- ✅ **Free hosting** - generous Cloudflare limits
- ✅ **Easy monitoring** - built-in logs and metrics

## 📚 Documentation

- **Complete setup**: `docs/CLOUDFLARE_COMPLETE_SETUP.md`
- **Custom domain**: `docs/CUSTOM_DOMAIN_SETUP.md`
- **Parallelization**: `docs/PARALLELIZATION_STRATEGY.md`
- **Backfill strategy**: `docs/BACKFILL_STRATEGY.md`

---

**Time to complete**: ~2 hours
**Difficulty**: Easy
**Cost**: Free (within Cloudflare limits)

## 🚀 Next Steps After Setup

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
