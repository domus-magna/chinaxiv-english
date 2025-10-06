# Cloudflare Wrangler CLI Setup Guide

## Overview
Cloudflare Wrangler is the official CLI tool for managing Cloudflare Workers and Pages. It provides more control and flexibility than the GitHub Actions integration.

## Installation

### Local Installation
```bash
# Install via npm (requires Node.js)
npm install -g wrangler

# Or install via yarn
yarn global add wrangler

# Verify installation
wrangler --version
```

### GitHub Actions Installation
```yaml
- name: Setup Node.js
  uses: actions/setup-node@v4
  with:
    node-version: '18'

- name: Install Wrangler CLI
  run: npm install -g wrangler
```

## Authentication

### 1. Login to Cloudflare
```bash
# Interactive login
wrangler login

# Or use API token
wrangler auth login
```

### 2. Verify Authentication
```bash
# Check authentication status
wrangler whoami

# List available accounts
wrangler accounts list
```

## Pages Commands

### 1. Deploy to Pages
```bash
# Deploy directory to Pages
wrangler pages deploy <directory> --project-name <project-name>

# Example for ChinaXiv Translations
wrangler pages deploy site --project-name chinaxiv-english
```

### 2. Create Pages Project
```bash
# Create new Pages project
wrangler pages project create <project-name>

# Example
wrangler pages project create chinaxiv-english
```

### 3. List Projects
```bash
# List all Pages projects
wrangler pages project list
```

### 4. Deploy with Custom Domain
```bash
# Deploy with custom domain
wrangler pages deploy site --project-name chinaxiv-english --compatibility-date 2024-01-01
```

## Configuration File

### 1. Create wrangler.toml
Create a `wrangler.toml` file in your project root:

```toml
name = "chinaxiv-english"
compatibility_date = "2024-01-01"

[env.production]
name = "chinaxiv-english"
compatibility_date = "2024-01-01"

# Pages configuration
[pages]
project_name = "chinaxiv-english"
```

### 2. Environment Variables
```toml
# In wrangler.toml
[vars]
OPENROUTER_API_KEY = "your-api-key"
DISCORD_WEBHOOK_URL = "your-webhook-url"
```

## GitHub Actions Integration

### 1. Updated Workflow
Use the new workflow file: `.github/workflows/build-wrangler.yml`

### 2. Required Secrets
- `CF_API_TOKEN`: Cloudflare API token
- `OPENROUTER_API_KEY`: OpenRouter API key
- `DISCORD_WEBHOOK_URL`: Discord webhook (optional)

### 3. Workflow Steps
1. Build Python application
2. Run tests
3. Build site
4. Install Wrangler CLI
5. Deploy to Pages

## Local Development

### 1. Preview Site Locally
```bash
# Serve site locally
python -m http.server -d site 8000

# Or use Wrangler for local development
wrangler pages dev site --project-name chinaxiv-english
```

### 2. Test Deployment
```bash
# Test deployment locally
wrangler pages deploy site --project-name chinaxiv-english --dry-run
```

## Advanced Features

### 1. Custom Domains
```bash
# Add custom domain
wrangler pages domain add chinaxiv-english yourdomain.com

# List domains
wrangler pages domain list chinaxiv-english

# Remove domain
wrangler pages domain remove chinaxiv-english yourdomain.com
```

### 2. Environment Management
```bash
# Deploy to specific environment
wrangler pages deploy site --project-name chinaxiv-english --env production

# List environments
wrangler pages env list chinaxiv-english
```

### 3. Build Settings
```bash
# Deploy with custom build settings
wrangler pages deploy site --project-name chinaxiv-english --compatibility-date 2024-01-01 --build-command "python -m src.render"
```

## Troubleshooting

### Common Issues

#### 1. Authentication Errors
```bash
# Re-authenticate
wrangler logout
wrangler login

# Check authentication
wrangler whoami
```

#### 2. Project Not Found
```bash
# List projects
wrangler pages project list

# Create project if needed
wrangler pages project create chinaxiv-english
```

#### 3. Deployment Failures
```bash
# Check deployment status
wrangler pages deployment list chinaxiv-english

# View deployment logs
wrangler pages deployment tail chinaxiv-english
```

### Debug Commands
```bash
# Enable debug logging
wrangler pages deploy site --project-name chinaxiv-english --log-level debug

# Check Wrangler version
wrangler --version

# Check Node.js version
node --version
```

## Comparison: Wrangler vs GitHub Actions

### Wrangler CLI Advantages
- ✅ More control over deployment process
- ✅ Better error messages and debugging
- ✅ Local development support
- ✅ Custom domain management
- ✅ Environment management
- ✅ Build customization

### GitHub Actions Advantages
- ✅ No local setup required
- ✅ Integrated with GitHub
- ✅ Automatic triggers
- ✅ Built-in secrets management
- ✅ Workflow visualization

### Recommended Approach
- **Development**: Use Wrangler CLI locally
- **Production**: Use GitHub Actions with Wrangler CLI
- **Custom Domains**: Use Wrangler CLI for management

## Migration from GitHub Actions

### 1. Update Workflow
Replace `.github/workflows/build.yml` with `.github/workflows/build-wrangler.yml`

### 2. Test Deployment
1. Run the new workflow
2. Verify deployment works
3. Check site functionality

### 3. Update Documentation
Update any references to the old deployment method

## Best Practices

### 1. Version Control
- Commit `wrangler.toml` to repository
- Use environment-specific configurations
- Document any custom settings

### 2. Security
- Use API tokens instead of email/password
- Rotate tokens regularly
- Limit token permissions

### 3. Monitoring
- Monitor deployment status
- Check error logs
- Set up alerts for failures

### 4. Performance
- Use appropriate compatibility dates
- Optimize build times
- Monitor deployment duration

## Example Commands

### Daily Development Workflow
```bash
# 1. Build site locally
python -m src.render
python -m src.search_index

# 2. Test locally
python -m http.server -d site 8000

# 3. Deploy to Pages
wrangler pages deploy site --project-name chinaxiv-english

# 4. Check deployment
wrangler pages deployment list chinaxiv-english
```

### Production Deployment
```bash
# 1. Run full pipeline
python -m src.pipeline --limit 100

# 2. Deploy with production settings
wrangler pages deploy site --project-name chinaxiv-english --env production

# 3. Verify deployment
curl -I https://chinaxiv-english.pages.dev
```

## Support and Resources

### Documentation
- **Wrangler CLI**: https://developers.cloudflare.com/workers/wrangler/
- **Pages**: https://developers.cloudflare.com/pages/
- **API**: https://developers.cloudflare.com/api/

### Community
- **Discord**: https://discord.gg/cloudflaredevs
- **GitHub**: https://github.com/cloudflare/wrangler
- **Stack Overflow**: https://stackoverflow.com/questions/tagged/wrangler

### Tools
- **Wrangler CLI**: Official Cloudflare CLI
- **Cloudflare Dashboard**: Web interface
- **GitHub Actions**: CI/CD integration

---

**Installation time**: ~5 minutes
**Learning curve**: Moderate
**Benefits**: More control and flexibility
**Maintenance**: Low (automated)
