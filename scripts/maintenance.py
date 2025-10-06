#!/usr/bin/env python3
"""
Maintenance script for ChinaXiv Translations.
"""

import argparse
import os
import sys
from pathlib import Path

# Change to project root
project_root = Path(__file__).parent.parent
os.chdir(project_root)

# Add src to path
sys.path.insert(0, str(project_root / "src"))

from services.alert_service import alert_service
from services.analytics_service import analytics_service
from services.performance_service import performance_service
from utils import log


def cleanup_alerts():
    """Clean up old alerts."""
    log("Cleaning up old alerts...")
    alert_service.clear_old_alerts(days=7)
    log("Alert cleanup completed")


def cleanup_analytics():
    """Clean up old analytics data."""
    log("Cleaning up old analytics data...")
    analytics_service.cleanup_old_data()
    log("Analytics cleanup completed")


def cleanup_performance():
    """Clean up old performance metrics."""
    log("Cleaning up old performance metrics...")
    performance_service.cleanup_old_metrics()
    log("Performance cleanup completed")


def optimize_performance():
    """Run performance optimizations."""
    log("Running performance optimizations...")
    
    # Optimize search index
    index_file = Path("site/search-index.json")
    if index_file.exists():
        success, message = performance_service.optimize_search_index(index_file)
        log(f"Search index optimization: {message}")
    
    # Optimize images
    image_dir = Path("site/assets")
    if image_dir.exists():
        success, message = performance_service.optimize_images(image_dir)
        log(f"Image optimization: {message}")
    
    log("Performance optimization completed")


def generate_reports():
    """Generate system reports."""
    log("Generating system reports...")
    
    # Performance report
    report = performance_service.generate_performance_report(days=7)
    log(f"Performance report generated with {len(report.get('recommendations', []))} recommendations")
    
    # Analytics stats
    stats = analytics_service.get_stats(days=7)
    log(f"Analytics report: {stats['total_page_views']} page views, {stats['total_searches']} searches, {stats['total_downloads']} downloads")
    
    log("Report generation completed")


def main():
    """Main function."""
    parser = argparse.ArgumentParser(description="ChinaXiv Translations Maintenance")
    parser.add_argument("--cleanup", action="store_true", help="Clean up old data")
    parser.add_argument("--optimize", action="store_true", help="Run performance optimizations")
    parser.add_argument("--reports", action="store_true", help="Generate system reports")
    parser.add_argument("--all", action="store_true", help="Run all maintenance tasks")
    
    args = parser.parse_args()
    
    if not any([args.cleanup, args.optimize, args.reports, args.all]):
        parser.print_help()
        return
    
    log("Starting maintenance tasks...")
    
    if args.all or args.cleanup:
        cleanup_alerts()
        cleanup_analytics()
        cleanup_performance()
    
    if args.all or args.optimize:
        optimize_performance()
    
    if args.all or args.reports:
        generate_reports()
    
    log("Maintenance completed successfully")


if __name__ == "__main__":
    main()
