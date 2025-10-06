# Proxy/VPN Setup Guide

The ChinaXiv OAI-PMH endpoint is geo-blocked and requires a VPN or proxy to access from outside China.

## Quick Setup

### Option 1: Environment Variables (Recommended)

Add to your `.env` file:

```bash
# HTTP/HTTPS Proxy (honors NO_PROXY automatically)
HTTPS_PROXY=http://127.0.0.1:1087

# Or SOCKS5 Proxy (prefer socks5h for DNS over proxy)
SOCKS5_PROXY=socks5h://127.0.0.1:1080
```

### Option 2: Config File

Edit `src/config.yaml`:

```yaml
proxy:
  enabled: true
  http: "http://127.0.0.1:1087"
  https: "http://127.0.0.1:1087"
```

## VPN/Proxy Services

### Free Options

1. **Cloudflare WARP** (Free tier available)
   - Download: https://1.1.1.1/
   - May not work for China-blocked content

2. **Proton VPN** (Free tier available)
   - Download: https://protonvpn.com/
   - Has servers in Asia

### Paid Options (Recommended)

1. **ExpressVPN** (~$8-12/month)
   - Has servers in Hong Kong, Japan, Singapore
   - Usually works with geo-blocked Chinese content

2. **NordVPN** (~$3-12/month)
   - Good Asia coverage
   - Supports SOCKS5 proxy

3. **Shadowsocks** (Self-hosted or service)
   - Popular for accessing Chinese content
   - Can run your own server in China/HK

### Local Proxy Setup

If you have a VPN that doesn't provide HTTP/SOCKS proxy:

#### Using Clash/ClashX (Mac/Linux)

1. Install ClashX: https://github.com/yichengchen/clashX
2. Configure with your VPN subscription
3. Enable "Set as system proxy"
4. Default ports: HTTP 7890, SOCKS5 7891

```bash
# Add to .env
HTTPS_PROXY=http://127.0.0.1:7890
```

#### Using V2Ray/V2RayN (Windows/Mac/Linux)

1. Install V2Ray client
2. Import your VPN configuration
3. Enable local proxy (usually port 10808 or 1080)

```bash
# Add to .env (use socks5h for DNS over proxy)
SOCKS5_PROXY=socks5h://127.0.0.1:10808
```

## Testing Your Proxy

### Test OAI Endpoint

```bash
# With environment variable (NO_PROXY respected)
export HTTPS_PROXY=http://127.0.0.1:1087
curl 'https://chinaxiv.org/oai/OAIHandler?verb=Identify'

# Should return XML instead of "Sorry!You have no right to access this web."
```

### Run Health Check

```bash
# Set proxy in .env first (PySocks is included; SOCKS5 works out of the box)
make health

# Or with inline env var
HTTPS_PROXY=http://127.0.0.1:1087 python -m src.health
```

## Troubleshooting

### "Sorry!You have no right to access this web."
- Proxy is not configured or not working
- Try a different VPN server location (Hong Kong, Singapore work well)
- Check proxy URL format: `http://host:port` or `socks5://host:port`

### Connection Timeout
- Proxy server may be down
- Check firewall settings
- Verify proxy port is correct

### SOCKS Proxy Not Working
- We vendor `PySocks` in requirements; ensure your proxy URL begins with `socks5h://` (for DNS over proxy).

### SSL Certificate Errors
- Some proxies don't handle HTTPS well
- Try HTTP endpoint instead:
  ```yaml
  oai:
    base_url: "http://www.chinaxiv.org/oai/OAIHandler"
  ```

## Security Notes

- **Never commit proxy credentials to git**
- Use `.env` file (already in `.gitignore`)
- For CI/CD, use GitHub Secrets to set `HTTPS_PROXY`

## NO_PROXY (Bypass Hosts)

If you want to bypass the proxy for certain hosts (e.g., localhost, OpenRouter), set:

```bash
NO_PROXY=localhost,127.0.0.1,openrouter.ai
```

When using environment variables, our client relies on `requests` trust_env behavior, so `NO_PROXY` is honored.

## Running Pipeline with Proxy

```bash
# Local dev
echo "HTTPS_PROXY=http://127.0.0.1:1087" >> .env
make dev

# Manual harvest
HTTPS_PROXY=http://127.0.0.1:1087 python -m src.harvest_oai \
  --base-url https://chinaxiv.org/oai/OAIHandler \
  --from 2024-11-01 --until 2024-11-01

# Full pipeline
HTTPS_PROXY=http://127.0.0.1:1087 make build
```

## GitHub Actions / CI

For nightly builds, add repository secret:

1. Settings → Secrets → New repository secret
2. Name: `PROXY_URL`
3. Value: Your proxy URL (e.g., `http://your-proxy:1087`)

Then update `.github/workflows/build.yml`:

```yaml
- name: Harvest
  env:
    HTTPS_PROXY: ${{ secrets.PROXY_URL }}
  run: python -m src.harvest_oai
```

## Alternative: Proxy Services for GitHub Actions

If you don't have a persistent proxy, use a service:

1. **Bright Data** - Residential proxies, free trial
2. **Smartproxy** - Datacenter proxies in Asia
3. **ProxyMesh** - Rotating proxies

These can be added as GitHub secrets and used in CI.
