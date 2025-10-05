#!/usr/bin/env python3
"""
Monitoring script for ChinaXiv translation pipeline.
Provides health checks, status monitoring, and alerting.
"""

import argparse
import json
import os
import sys
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from config import get_config
from logging import log
from file_service import read_json, write_json


def check_api_connectivity() -> Dict[str, bool]:
    """Check connectivity to external APIs."""
    results = {}
    
    # Check OpenRouter API
    try:
        import requests
        headers = {
            "Authorization": f"Bearer {os.getenv('OPENROUTER_API_KEY')}",
            "Content-Type": "application/json"
        }
        resp = requests.get("https://openrouter.ai/api/v1/models", headers=headers, timeout=10)
        results['openrouter'] = resp.status_code == 200
    except Exception as e:
        log(f"OpenRouter check failed: {e}")
        results['openrouter'] = False
    
    # Check Internet Archive API
    try:
        import requests
        resp = requests.get("https://archive.org/services/search/v1/scrape?q=collection:chinaxivmirror&count=1", timeout=10)
        results['internet_archive'] = resp.status_code == 200
    except Exception as e:
        log(f"Internet Archive check failed: {e}")
        results['internet_archive'] = False
    
    return results


def check_data_health() -> Dict[str, any]:
    """Check health of data files and directories."""
    health = {
        'records_count': 0,
        'translated_count': 0,
        'selected_count': 0,
        'cost_files': 0,
        'last_harvest': None,
        'last_translation': None
    }
    
    # Check records
    records_dir = Path("data/records")
    if records_dir.exists():
        record_files = list(records_dir.glob("ia_*.json"))
        health['records_count'] = len(record_files)
        
        if record_files:
            # Get most recent file
            latest_file = max(record_files, key=lambda f: f.stat().st_mtime)
            health['last_harvest'] = datetime.fromtimestamp(latest_file.stat().st_mtime).isoformat()
    
    # Check translations
    translated_dir = Path("data/translated")
    if translated_dir.exists():
        translation_files = list(translated_dir.glob("*.json"))
        health['translated_count'] = len(translation_files)
        
        if translation_files:
            latest_file = max(translation_files, key=lambda f: f.stat().st_mtime)
            health['last_translation'] = datetime.fromtimestamp(latest_file.stat().st_mtime).isoformat()
    
    # Check selected papers
    selected_path = Path("data/selected.json")
    if selected_path.exists():
        try:
            selected = read_json(str(selected_path))
            health['selected_count'] = len(selected) if isinstance(selected, list) else 0
        except:
            health['selected_count'] = 0
    
    # Check cost files
    costs_dir = Path("data/costs")
    if costs_dir.exists():
        cost_files = list(costs_dir.glob("*.json"))
        health['cost_files'] = len(cost_files)
    
    return health


def check_site_health() -> Dict[str, any]:
    """Check health of generated site."""
    health = {
        'site_exists': False,
        'index_exists': False,
        'items_count': 0,
        'search_index_exists': False,
        'search_index_size': 0
    }
    
    site_dir = Path("site")
    if site_dir.exists():
        health['site_exists'] = True
        
        # Check index page
        index_path = site_dir / "index.html"
        health['index_exists'] = index_path.exists()
        
        # Check items
        items_dir = site_dir / "items"
        if items_dir.exists():
            item_dirs = [d for d in items_dir.iterdir() if d.is_dir()]
            health['items_count'] = len(item_dirs)
        
        # Check search index
        search_index_path = site_dir / "search-index.json"
        if search_index_path.exists():
            health['search_index_exists'] = True
            health['search_index_size'] = search_index_path.stat().st_size
    
    return health


def calculate_costs() -> Dict[str, float]:
    """Calculate total costs from cost logs."""
    costs = {
        'total_cost': 0.0,
        'daily_cost': 0.0,
        'paper_count': 0,
        'avg_cost_per_paper': 0.0
    }
    
    costs_dir = Path("data/costs")
    if not costs_dir.exists():
        return costs
    
    cost_files = list(costs_dir.glob("*.json"))
    today = datetime.now().date()
    
    for cost_file in cost_files:
        try:
            with open(cost_file) as f:
                cost_data = json.load(f)
            
            if isinstance(cost_data, list):
                for entry in cost_data:
                    cost = entry.get('cost', 0)
                    costs['total_cost'] += cost
                    costs['paper_count'] += 1
                    
                    # Check if today
                    entry_date = entry.get('date', '')
                    if entry_date:
                        try:
                            entry_date_obj = datetime.fromisoformat(entry_date.split('T')[0]).date()
                            if entry_date_obj == today:
                                costs['daily_cost'] += cost
                        except:
                            pass
        except Exception as e:
            log(f"Error reading cost file {cost_file}: {e}")
    
    if costs['paper_count'] > 0:
        costs['avg_cost_per_paper'] = costs['total_cost'] / costs['paper_count']
    
    return costs


def check_worker_health() -> Dict[str, any]:
    """Check health of background workers."""
    health = {
        'workers_running': 0,
        'jobs_pending': 0,
        'jobs_failed': 0,
        'jobs_completed': 0
    }
    
    # Check for worker PID files
    pid_files = list(Path("data").glob("worker_*.pid"))
    for pid_file in pid_files:
        try:
            with open(pid_file) as f:
                pid = int(f.read().strip())
            # Check if process is running
            os.kill(pid, 0)
            health['workers_running'] += 1
        except (OSError, ValueError):
            # Process not running, remove stale PID file
            pid_file.unlink()
    
    # Check job queue if database exists
    db_path = Path("data/jobs.db")
    if db_path.exists():
        try:
            import sqlite3
            conn = sqlite3.connect(str(db_path))
            cursor = conn.cursor()
            
            # Get job counts
            cursor.execute("SELECT status, COUNT(*) FROM jobs GROUP BY status")
            for status, count in cursor.fetchall():
                if status == 'pending':
                    health['jobs_pending'] = count
                elif status == 'failed':
                    health['jobs_failed'] = count
                elif status == 'completed':
                    health['jobs_completed'] = count
            
            conn.close()
        except Exception as e:
            log(f"Error checking job queue: {e}")
    
    return health


def generate_health_report() -> Dict[str, any]:
    """Generate comprehensive health report."""
    report = {
        'timestamp': datetime.now().isoformat(),
        'api_connectivity': check_api_connectivity(),
        'data_health': check_data_health(),
        'site_health': check_site_health(),
        'costs': calculate_costs(),
        'worker_health': check_worker_health(),
        'overall_status': 'unknown'
    }
    
    # Determine overall status
    api_ok = all(report['api_connectivity'].values())
    data_ok = report['data_health']['records_count'] > 0
    site_ok = report['site_health']['site_exists']
    
    if api_ok and data_ok and site_ok:
        report['overall_status'] = 'healthy'
    elif api_ok and data_ok:
        report['overall_status'] = 'degraded'
    else:
        report['overall_status'] = 'unhealthy'
    
    return report


def print_status_report(report: Dict[str, any]) -> None:
    """Print a human-readable status report."""
    print("=" * 60)
    print("ChinaXiv Translation Pipeline - Health Report")
    print("=" * 60)
    print(f"Timestamp: {report['timestamp']}")
    print(f"Overall Status: {report['overall_status'].upper()}")
    print()
    
    # API Connectivity
    print("API Connectivity:")
    for service, status in report['api_connectivity'].items():
        status_str = "✓" if status else "✗"
        print(f"  {status_str} {service.replace('_', ' ').title()}")
    print()
    
    # Data Health
    data = report['data_health']
    print("Data Health:")
    print(f"  Records: {data['records_count']}")
    print(f"  Translations: {data['translated_count']}")
    print(f"  Selected: {data['selected_count']}")
    print(f"  Cost Files: {data['cost_files']}")
    if data['last_harvest']:
        print(f"  Last Harvest: {data['last_harvest']}")
    if data['last_translation']:
        print(f"  Last Translation: {data['last_translation']}")
    print()
    
    # Site Health
    site = report['site_health']
    print("Site Health:")
    print(f"  Site Exists: {'✓' if site['site_exists'] else '✗'}")
    print(f"  Index Page: {'✓' if site['index_exists'] else '✗'}")
    print(f"  Items: {site['items_count']}")
    print(f"  Search Index: {'✓' if site['search_index_exists'] else '✗'}")
    if site['search_index_size'] > 0:
        print(f"  Search Index Size: {site['search_index_size']:,} bytes")
    print()
    
    # Costs
    costs = report['costs']
    print("Costs:")
    print(f"  Total Cost: ${costs['total_cost']:.4f}")
    print(f"  Daily Cost: ${costs['daily_cost']:.4f}")
    print(f"  Papers Processed: {costs['paper_count']}")
    if costs['avg_cost_per_paper'] > 0:
        print(f"  Avg Cost/Paper: ${costs['avg_cost_per_paper']:.4f}")
    print()
    
    # Worker Health
    workers = report['worker_health']
    print("Worker Health:")
    print(f"  Workers Running: {workers['workers_running']}")
    print(f"  Jobs Pending: {workers['jobs_pending']}")
    print(f"  Jobs Failed: {workers['jobs_failed']}")
    print(f"  Jobs Completed: {workers['jobs_completed']}")
    print()


def save_health_report(report: Dict[str, any], output_path: str) -> None:
    """Save health report to JSON file."""
    Path("data").mkdir(exist_ok=True)
    write_json(output_path, report)
    log(f"Health report saved to {output_path}")


def main():
    parser = argparse.ArgumentParser(description="Monitor ChinaXiv translation pipeline health")
    parser.add_argument("--output", help="Save report to JSON file")
    parser.add_argument("--watch", action="store_true", help="Watch mode - update every 30 seconds")
    parser.add_argument("--quiet", action="store_true", help="Quiet mode - no console output")
    
    args = parser.parse_args()
    
    if args.watch:
        print("Starting health monitor (Ctrl+C to stop)...")
        try:
            while True:
                if not args.quiet:
                    os.system('clear' if os.name == 'posix' else 'cls')
                
                report = generate_health_report()
                
                if not args.quiet:
                    print_status_report(report)
                
                if args.output:
                    save_health_report(report, args.output)
                
                time.sleep(30)
        except KeyboardInterrupt:
            print("\nMonitoring stopped.")
    else:
        report = generate_health_report()
        
        if not args.quiet:
            print_status_report(report)
        
        if args.output:
            save_health_report(report, args.output)


if __name__ == "__main__":
    main()
