# Discord Monitoring Setup Guide

## Overview

This guide explains how to set up Discord webhook notifications for the ChinaXiv translation pipeline monitoring system.

## Benefits

- **Free**: No monthly costs
- **Real-time**: Instant notifications
- **Rich formatting**: Color-coded alerts with structured data
- **Mobile-friendly**: Works on all devices
- **Team collaboration**: Share alerts with team members

## Setup Steps

### 1. Create Discord Webhook

1. **Go to your Discord server**
2. **Right-click on the channel** where you want notifications
3. **Select "Edit Channel"**
4. **Go to "Integrations" tab**
5. **Click "Webhooks"**
6. **Click "Create Webhook"**
7. **Copy the webhook URL** (starts with `https://discord.com/api/webhooks/`)

### 2. Configure Environment Variables

#### Local Development
Add to your `.env` file:
```bash
DISCORD_WEBHOOK_URL=https://discord.com/api/webhooks/YOUR_WEBHOOK_ID/YOUR_WEBHOOK_TOKEN
```

#### GitHub Actions
Add to your repository secrets:
1. Go to **Settings** → **Secrets and variables** → **Actions**
2. Click **New repository secret**
3. Name: `DISCORD_WEBHOOK_URL`
4. Value: Your webhook URL

### 3. Test the Integration

#### Test from Command Line
```bash
# Test Discord webhook
python scripts/monitor.py --test-discord

# Send daily summary
python scripts/monitor.py --discord-summary
```

#### Test from Python
```python
from src.discord_alerts import DiscordAlerts

# Test basic alert
alerts = DiscordAlerts()
alerts.test_alert()

# Test different alert types
alerts.pipeline_success(5, 2.34)
alerts.cost_threshold(6.50, 5.0)
alerts.pipeline_failure("API timeout", "translation")
```

## Alert Types

### 🚨 Critical Alerts (Red)
- **Pipeline failures**: Translation pipeline stopped
- **Site down**: Website not responding
- **API errors**: External service failures
- **System errors**: Critical system issues

### ⚠️ Warning Alerts (Yellow)
- **Cost thresholds**: Daily spending exceeded
- **Performance issues**: Slow response times
- **Quality degradation**: Translation quality issues
- **Resource warnings**: Disk space, memory usage

### ✅ Success Alerts (Green)
- **Pipeline success**: Successful processing
- **Deployments**: Site updates completed
- **Recoveries**: System restored from issues
- **Milestones**: Important achievements

### 📊 Info Alerts (Blue)
- **Daily summaries**: Regular status reports
- **Weekly reports**: Performance metrics
- **System updates**: Maintenance notifications
- **Feature announcements**: New capabilities

## Alert Examples

### Pipeline Success
```json
{
  "title": "✅ Pipeline Success",
  "color": 3066993,
  "fields": [
    {"name": "Papers Processed", "value": "15", "inline": true},
    {"name": "Cost", "value": "$2.34", "inline": true},
    {"name": "Time", "value": "2025-10-05 09:00:00 UTC", "inline": true}
  ]
}
```

### Cost Threshold Warning
```json
{
  "title": "⚠️ Cost Threshold Exceeded",
  "color": 16776960,
  "fields": [
    {"name": "Daily Cost", "value": "$6.50", "inline": true},
    {"name": "Threshold", "value": "$5.00", "inline": true},
    {"name": "Excess", "value": "$1.50", "inline": true}
  ]
}
```

### Daily Summary
```json
{
  "title": "📊 Daily Summary",
  "color": 3447003,
  "fields": [
    {"name": "Papers Processed", "value": "3,051", "inline": true},
    {"name": "Daily Cost", "value": "$2.34", "inline": true},
    {"name": "Success Rate", "value": "98.5%", "inline": true},
    {"name": "Site Status", "value": "✅ Healthy", "inline": true},
    {"name": "Search Index", "value": "3,051 papers", "inline": true},
    {"name": "Last Update", "value": "2 hours ago", "inline": true}
  ]
}
```

## Configuration Options

### Alert Thresholds
```python
ALERT_THRESHOLDS = {
    'cost_daily': 5.0,      # Alert if cost > $5/day
    'pipeline_failure': 1,  # Alert on any pipeline failure
    'site_down': 300,       # Alert if site down > 5 minutes
    'api_error_rate': 0.1, # Alert if error rate > 10%
    'disk_space': 1024,     # Alert if disk space < 1GB
}
```

### Notification Frequency
- **Critical alerts**: Immediate
- **Warning alerts**: Immediate
- **Success alerts**: Immediate
- **Info alerts**: Daily summaries

## Integration Points

### 1. Monitoring Script
```bash
# Automatic alerts on health check failures
python scripts/monitor.py

# Manual daily summary
python scripts/monitor.py --discord-summary
```

### 2. Pipeline Execution
```bash
# Success notifications on pipeline completion
python -m src.pipeline --limit 10
```

### 3. GitHub Actions
```yaml
# CI/CD success/failure notifications
- name: Notify Discord on Success
  if: success()
  run: |
    curl -H "Content-Type: application/json" \
         -d '{"embeds":[{"title":"✅ CI/CD Success","color":3066993}]}' \
         ${{ secrets.DISCORD_WEBHOOK_URL }}
```

### 4. Scheduled Monitoring
```bash
# Cron job for regular monitoring
0 9 * * * cd /path/to/chinaxiv-english && python scripts/monitor.py --discord-summary
```

## Troubleshooting

### Common Issues

#### Webhook Not Working
1. **Check URL**: Ensure webhook URL is correct
2. **Test manually**: Use curl to test webhook
3. **Check permissions**: Ensure webhook has send permissions
4. **Verify environment**: Check DISCORD_WEBHOOK_URL is set

#### Alerts Not Sending
1. **Check logs**: Look for error messages
2. **Test connection**: Use `--test-discord` flag
3. **Verify thresholds**: Check alert conditions
4. **Check rate limits**: Discord has rate limits

#### Formatting Issues
1. **Check JSON**: Ensure valid JSON format
2. **Verify fields**: Check field names and values
3. **Test with simple message**: Start with basic alert
4. **Check Discord API**: Verify webhook format

### Debug Commands
```bash
# Test webhook connectivity
curl -H "Content-Type: application/json" \
     -d '{"content":"Test message"}' \
     YOUR_WEBHOOK_URL

# Test Python integration
python -c "from src.discord_alerts import DiscordAlerts; DiscordAlerts().test_alert()"

# Check environment variables
echo $DISCORD_WEBHOOK_URL
```

## Security Considerations

### Webhook Security
- **Keep URL secret**: Don't commit webhook URL to code
- **Use environment variables**: Store in .env or secrets
- **Rotate periodically**: Change webhook URL occasionally
- **Monitor usage**: Check for unauthorized access

### Rate Limiting
- **Discord limits**: 30 requests per minute per webhook
- **Implement queuing**: Queue alerts if needed
- **Batch notifications**: Combine multiple alerts
- **Monitor usage**: Track webhook usage

## Advanced Features

### Custom Alerts
```python
# Create custom alert
alerts = DiscordAlerts()
alerts.send_alert(
    alert_type='info',
    title='Custom Alert',
    description='This is a custom alert message',
    fields=[
        {'name': 'Field 1', 'value': 'Value 1', 'inline': True},
        {'name': 'Field 2', 'value': 'Value 2', 'inline': True}
    ]
)
```

### Alert Filtering
```python
# Filter alerts by type
def should_send_alert(alert_type: str, severity: str) -> bool:
    if alert_type == 'critical':
        return True
    elif alert_type == 'warning' and severity == 'high':
        return True
    else:
        return False
```

### Historical Tracking
```python
# Track alert history
def log_alert(alert_type: str, message: str):
    timestamp = datetime.now().isoformat()
    with open('data/alert_history.json', 'a') as f:
        f.write(json.dumps({
            'timestamp': timestamp,
            'type': alert_type,
            'message': message
        }) + '\n')
```

## Conclusion

Discord webhook integration provides a powerful, free monitoring solution for the ChinaXiv translation pipeline. With rich formatting, real-time notifications, and easy setup, it's an excellent choice for production monitoring.

**Next Steps**:
1. Set up Discord webhook
2. Configure environment variables
3. Test integration
4. Set up automated monitoring
5. Customize alert thresholds

For questions or issues, check the troubleshooting section or review the Discord webhook documentation.
