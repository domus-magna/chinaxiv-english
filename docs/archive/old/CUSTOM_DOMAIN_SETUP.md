# Custom Domain Setup Guide

## Overview
This guide walks you through setting up a custom domain for ChinaXiv Translations after purchasing one from a domain registrar.

## Prerequisites
- Cloudflare Pages project already set up
- Custom domain purchased from any registrar
- Cloudflare account with Pages project

## Step 1: Purchase Domain

### 1.1 Choose Domain Registrar
Popular options:
- **GoDaddy**: https://godaddy.com
- **Namecheap**: https://namecheap.com
- **Google Domains**: https://domains.google
- **Cloudflare Registrar**: https://dash.cloudflare.com (recommended)

### 1.2 Select Domain Name
Good options for ChinaXiv Translations:
- `chinaxiv-english.com`
- `chinaxiv-translations.org`
- `chinaxiv-english.net`
- `chinaxiv-translations.com`

### 1.3 Purchase Domain
1. Search for your desired domain
2. Add to cart and checkout
3. Complete payment
4. **Note**: You don't need to configure DNS yet

## Step 2: Add Domain to Cloudflare

### 2.1 Add Site to Cloudflare
1. Go to [Cloudflare Dashboard](https://dash.cloudflare.com)
2. Click "Add a Site"
3. Enter your domain name (e.g., `chinaxiv-english.com`)
4. Click "Add site"

### 2.2 Choose Plan
1. Select "Free" plan (sufficient for most use cases)
2. Click "Continue"
3. Cloudflare will scan your existing DNS records

### 2.3 Review DNS Records
1. Cloudflare will show existing DNS records
2. Review and confirm the records look correct
3. Click "Continue"

## Step 3: Update Nameservers

### 3.1 Get Cloudflare Nameservers
1. In Cloudflare dashboard, go to your domain
2. Find "Nameservers" section
3. Note the two nameservers (e.g., `alex.ns.cloudflare.com`, `barbara.ns.cloudflare.com`)

### 3.2 Update at Domain Registrar
1. Go to your domain registrar's dashboard
2. Find "DNS" or "Nameservers" settings
3. Replace existing nameservers with Cloudflare's:
   - `alex.ns.cloudflare.com`
   - `barbara.ns.cloudflare.com`
4. Save changes

### 3.3 Wait for Propagation
- **Time**: 24-48 hours for full propagation
- **Check**: Use `dig yourdomain.com` or `nslookup yourdomain.com`
- **Status**: Domain will show "Pending" in Cloudflare until propagation completes

## Step 4: Connect Domain to Pages

### 4.1 Add Custom Domain
1. Go to [Cloudflare Pages](https://pages.cloudflare.com)
2. Select your `chinaxiv-english` project
3. Go to "Custom domains" tab
4. Click "Set up a custom domain"
5. Enter your domain name
6. Click "Continue"

### 4.2 Configure DNS
1. Cloudflare will automatically create DNS records
2. Verify the records are correct:
   - `CNAME` record pointing to your Pages domain
   - `A` record for root domain (if needed)
3. Click "Activate domain"

### 4.3 Wait for SSL Certificate
- **Time**: 5-10 minutes for certificate issuance
- **Status**: Will show "Pending" then "Active"
- **Test**: Visit `https://yourdomain.com`

## Step 5: Verify Setup

### 5.1 Test Domain Access
1. Visit your custom domain
2. Verify the site loads correctly
3. Check that HTTPS is working
4. Test all functionality (search, donation page, etc.)

### 5.2 Check DNS Propagation
```bash
# Check DNS records
dig yourdomain.com
nslookup yourdomain.com

# Check specific record types
dig CNAME yourdomain.com
dig A yourdomain.com
```

### 5.3 Test Performance
1. Use tools like GTmetrix or PageSpeed Insights
2. Verify Cloudflare CDN is working
3. Check load times from different locations

## Step 6: Optimize Settings

### 6.1 Performance Settings
1. Go to Cloudflare Dashboard
2. Select your domain
3. Go to "Speed" tab
4. Enable:
   - Auto Minify (HTML, CSS, JS)
   - Brotli compression
   - Rocket Loader (if needed)

### 6.2 Security Settings
1. Go to "Security" tab
2. Set Security Level to "Medium"
3. Enable "Always Use HTTPS"
4. Configure "Page Rules" if needed

### 6.3 Analytics
1. Go to "Analytics" tab
2. Monitor traffic and performance
3. Set up alerts for downtime

## Step 7: Update Configuration

### 7.1 Update GitHub Actions
No changes needed - GitHub Actions will automatically deploy to your custom domain.

### 7.2 Update Documentation
Update any references to the old Pages URL:
- README.md
- Documentation files
- Links in the site

### 7.3 Test Deployment
1. Make a small change to the site
2. Push to GitHub
3. Verify the change appears on your custom domain

## Troubleshooting

### Common Issues

#### 1. Domain Not Resolving
**Symptoms**: Domain doesn't load
**Solutions**:
- Check nameservers are correct
- Wait for DNS propagation (24-48 hours)
- Verify domain is active at registrar

#### 2. SSL Certificate Issues
**Symptoms**: HTTPS doesn't work
**Solutions**:
- Wait for certificate issuance (5-10 minutes)
- Check DNS records are correct
- Verify domain is properly configured

#### 3. Site Not Loading
**Symptoms**: Domain loads but site doesn't appear
**Solutions**:
- Check Cloudflare Pages custom domain configuration
- Verify DNS records point to Pages
- Check for any redirects or page rules

#### 4. Performance Issues
**Symptoms**: Site loads slowly
**Solutions**:
- Enable Cloudflare performance features
- Check CDN is working
- Optimize site assets

### Debug Commands
```bash
# Check DNS propagation
dig yourdomain.com
nslookup yourdomain.com

# Check specific record types
dig CNAME yourdomain.com
dig A yourdomain.com

# Test HTTPS
curl -I https://yourdomain.com

# Check SSL certificate
openssl s_client -connect yourdomain.com:443 -servername yourdomain.com
```

## Expected Timeline

### Domain Purchase
- **Time**: 5-10 minutes
- **Cost**: $10-15/year (varies by registrar)

### Cloudflare Setup
- **Add domain**: 5 minutes
- **Update nameservers**: 5 minutes
- **DNS propagation**: 24-48 hours

### Pages Connection
- **Connect domain**: 5 minutes
- **SSL certificate**: 5-10 minutes
- **Total setup time**: ~30 minutes (plus propagation)

## Cost Breakdown

### Domain Registration
- **Annual cost**: $10-15/year
- **Renewal**: Automatic (if configured)

### Cloudflare Services
- **Pages**: Free
- **DNS**: Free
- **SSL**: Free
- **CDN**: Free
- **Total**: $0/month

### Total Annual Cost
- **Domain**: $10-15/year
- **Cloudflare**: $0/year
- **Total**: $10-15/year

## Best Practices

### Domain Management
1. **Enable auto-renewal** at registrar
2. **Use strong passwords** for registrar account
3. **Enable two-factor authentication**
4. **Keep contact information updated**

### Cloudflare Management
1. **Monitor SSL certificate** expiration
2. **Check DNS records** regularly
3. **Review security settings** periodically
4. **Monitor performance** metrics

### Backup Strategy
1. **Export DNS records** from Cloudflare
2. **Keep domain registrar** account secure
3. **Document configuration** for future reference

## Security Considerations

### Domain Security
1. **Enable domain locking** at registrar
2. **Use privacy protection** (if available)
3. **Monitor for unauthorized changes**
4. **Keep registrar account secure**

### Cloudflare Security
1. **Enable two-factor authentication**
2. **Use strong API tokens**
3. **Monitor access logs**
4. **Review security settings**

## Monitoring and Maintenance

### Regular Checks
1. **Domain expiration** (annual)
2. **SSL certificate** status (automatic)
3. **DNS records** (monthly)
4. **Performance metrics** (weekly)

### Alerts and Notifications
1. **Domain expiration** alerts
2. **SSL certificate** warnings
3. **DNS changes** notifications
4. **Performance** monitoring

## Support Resources

### Domain Registrar Support
- **GoDaddy**: https://support.godaddy.com
- **Namecheap**: https://www.namecheap.com/support/
- **Google Domains**: https://support.google.com/domains

### Cloudflare Support
- **Documentation**: https://developers.cloudflare.com/pages/
- **Community**: https://community.cloudflare.com/
- **Support**: https://support.cloudflare.com/

### Tools and Resources
- **DNS Checker**: https://dnschecker.org/
- **SSL Checker**: https://www.ssllabs.com/ssltest/
- **Performance Testing**: https://gtmetrix.com/

---

**Total setup time**: ~30 minutes (plus 24-48 hours for DNS propagation)
**Total cost**: $10-15/year
**Maintenance**: Minimal (automated)
**Security**: High (Cloudflare protection)
