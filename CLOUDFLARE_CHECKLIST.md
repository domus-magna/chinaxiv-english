# Cloudflare Pages Setup Checklist

## ✅ Quick Setup Steps

### 1. Get Cloudflare Credentials
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

### 2. Add GitHub Secrets
Run the setup script:
```bash
python3 scripts/setup_cloudflare_secrets.py
```

Or manually add these secrets in GitHub:
- [ ] `CF_API_TOKEN` - Your Cloudflare API token
- [ ] `CLOUDFLARE_ACCOUNT_ID` - Your Cloudflare Account ID  
- [ ] `OPENROUTER_API_KEY` - Your OpenRouter API key (already have this)

### 3. Create Cloudflare Pages Project
- [ ] Go to [Cloudflare Pages](https://pages.cloudflare.com)
- [ ] Click "Connect to Git"
- [ ] Select GitHub account
- [ ] Choose `chinaxiv-english` repository
- [ ] Project name: `chinaxiv-english`
- [ ] Build output directory: `site`
- [ ] Click "Save and Deploy"

### 4. Test Deployment
- [ ] Go to GitHub → Actions tab
- [ ] Click "build-and-deploy" workflow
- [ ] Click "Run workflow" → "Run workflow"
- [ ] Watch the build progress
- [ ] Check for "Deploy to Cloudflare Pages" step
- [ ] Verify site loads at Cloudflare Pages URL

### 5. Verify Everything Works
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

- Detailed setup: `docs/CLOUDFLARE_SETUP.md`
- Workflow file: `.github/workflows/build.yml`
- Setup script: `scripts/setup_cloudflare_secrets.py`

---

**Time to complete**: ~15 minutes
**Difficulty**: Easy
**Cost**: Free (within Cloudflare limits)
