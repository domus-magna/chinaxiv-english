"""
Consolidated monitoring service combining alerts, analytics, and performance.
"""

import os
import json
import requests
import gzip
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass

from .utils import log


@dataclass
class Alert:
    """Alert data structure."""
    level: str
    title: str
    message: str
    timestamp: str
    source: str
    metadata: Optional[Dict[str, Any]] = None


@dataclass
class PageView:
    """Page view data structure."""
    timestamp: str
    page: str
    user_agent: str
    ip_address: str
    referrer: Optional[str] = None
    session_id: Optional[str] = None


@dataclass
class SearchQuery:
    """Search query data structure."""
    timestamp: str
    query: str
    results: int
    user_agent: str
    ip_address: str
    session_id: Optional[str] = None


@dataclass
class PerformanceMetric:
    """Performance metric data structure."""
    timestamp: str
    name: str
    value: float
    unit: str
    metadata: Optional[Dict[str, Any]] = None


class MonitoringService:
    """Consolidated monitoring service combining alerts, analytics, and performance."""
    
    def __init__(self):
        self.alerts = []
        self.analytics = {}
        self.performance = {}
        self.data_dir = Path("data/monitoring")
        self.data_dir.mkdir(exist_ok=True)
        
        # Configuration
        self.discord_webhook_url = os.getenv("DISCORD_WEBHOOK_URL")
        self.max_alerts = 1000
        self.max_analytics_entries = 10000
        self.max_performance_entries = 5000
        self.retention_days = 30
        
        # Load existing data
        self._load_data()
    
    def _load_data(self):
        """Load existing monitoring data."""
        try:
            # Load alerts
            alerts_file = self.data_dir / "alerts.json"
            if alerts_file.exists():
                with open(alerts_file, "r", encoding="utf-8") as f:
                    self.alerts = json.load(f)
            
            # Load analytics
            analytics_file = self.data_dir / "analytics.json"
            if analytics_file.exists():
                with open(analytics_file, "r", encoding="utf-8") as f:
                    self.analytics = json.load(f)
            
            # Load performance metrics
            performance_file = self.data_dir / "performance.json"
            if performance_file.exists():
                with open(performance_file, "r", encoding="utf-8") as f:
                    self.performance = json.load(f)
                    
        except Exception as e:
            log(f"Failed to load monitoring data: {e}")
    
    def _save_data(self):
        """Save monitoring data to files."""
        try:
            # Save alerts
            alerts_file = self.data_dir / "alerts.json"
            with open(alerts_file, "w", encoding="utf-8") as f:
                json.dump(self.alerts, f, indent=2, ensure_ascii=False)
            
            # Save analytics
            analytics_file = self.data_dir / "analytics.json"
            with open(analytics_file, "w", encoding="utf-8") as f:
                json.dump(self.analytics, f, indent=2, ensure_ascii=False)
            
            # Save performance metrics
            performance_file = self.data_dir / "performance.json"
            with open(performance_file, "w", encoding="utf-8") as f:
                json.dump(self.performance, f, indent=2, ensure_ascii=False)
                
        except Exception as e:
            log(f"Failed to save monitoring data: {e}")
    
    # Alert functionality
    def create_alert(self, level: str, title: str, message: str, **kwargs) -> Dict[str, Any]:
        """Create and store alert."""
        alert = Alert(
            level=level,
            title=title,
            message=message,
            timestamp=datetime.now().isoformat(),
            source=kwargs.get("source", "system"),
            metadata=kwargs.get("metadata", {})
        )
        
        # Convert to dict for storage
        alert_dict = {
            "level": alert.level,
            "title": alert.title,
            "message": alert.message,
            "timestamp": alert.timestamp,
            "source": alert.source,
            "metadata": alert.metadata
        }
        
        # Add to alerts list
        self.alerts.append(alert_dict)
        
        # Keep only recent alerts
        if len(self.alerts) > self.max_alerts:
            self.alerts = self.alerts[-self.max_alerts:]
        
        # Send notification
        self._send_notification(alert_dict)
        
        # Save data
        self._save_data()
        
        return alert_dict
    
    def get_alerts(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Get recent alerts."""
        return self.alerts[-limit:] if self.alerts else []
    
    def cleanup_alerts(self, days: int = 7):
        """Clean up old alerts."""
        try:
            cutoff = datetime.now() - timedelta(days=days)
            
            filtered_alerts = []
            for alert in self.alerts:
                try:
                    alert_time = datetime.fromisoformat(alert.get("timestamp", ""))
                    if alert_time > cutoff:
                        filtered_alerts.append(alert)
                except ValueError:
                    # Keep alerts with invalid timestamps
                    filtered_alerts.append(alert)
            
            if len(filtered_alerts) != len(self.alerts):
                self.alerts = filtered_alerts
                self._save_data()
                log(f"Cleaned up {len(self.alerts) - len(filtered_alerts)} old alerts")
                
        except Exception as e:
            log(f"Failed to cleanup alerts: {e}")
    
    def _send_notification(self, alert: Dict[str, Any]) -> None:
        """Send notification via Discord webhook."""
        if not self.discord_webhook_url:
            return
        
        try:
            # Determine color based on alert level
            color_map = {
                "info": 0x00ff00,      # Green
                "warning": 0xffff00,    # Yellow
                "error": 0xff8800,     # Orange
                "critical": 0xff0000   # Red
            }
            
            embed = {
                "title": alert["title"],
                "description": alert["message"],
                "color": color_map.get(alert["level"], 0x888888),
                "timestamp": alert["timestamp"],
                "fields": [
                    {"name": "Level", "value": alert["level"].upper(), "inline": True},
                    {"name": "Source", "value": alert["source"], "inline": True}
                ]
            }
            
            # Add metadata if present
            if alert["metadata"]:
                metadata_str = "\n".join([f"{k}: {v}" for k, v in alert["metadata"].items()])
                embed["fields"].append({"name": "Details", "value": metadata_str, "inline": False})
            
            payload = {
                "embeds": [embed],
                "username": "ChinaXiv Monitor"
            }
            
            response = requests.post(
                self.discord_webhook_url,
                json=payload,
                timeout=10
            )
            response.raise_for_status()
            
        except Exception as e:
            log(f"Failed to send Discord notification: {e}")
    
    # Analytics functionality  
    def track_page_view(self, page: str, **kwargs):
        """Track page view."""
        page_view = PageView(
            timestamp=datetime.now().isoformat(),
            page=page,
            user_agent=kwargs.get("user_agent", "Unknown"),
            ip_address=kwargs.get("ip_address", "Unknown"),
            referrer=kwargs.get("referrer"),
            session_id=kwargs.get("session_id")
        )
        
        # Convert to dict for storage
        page_view_dict = {
            "timestamp": page_view.timestamp,
            "page": page_view.page,
            "user_agent": page_view.user_agent,
            "ip_address": page_view.ip_address,
            "referrer": page_view.referrer,
            "session_id": page_view.session_id
        }
        
        # Add to analytics
        if "page_views" not in self.analytics:
            self.analytics["page_views"] = []
        
        self.analytics["page_views"].append(page_view_dict)
        
        # Keep only recent entries
        if len(self.analytics["page_views"]) > self.max_analytics_entries:
            self.analytics["page_views"] = self.analytics["page_views"][-self.max_analytics_entries:]
        
        # Save data
        self._save_data()
    
    def track_search(self, query: str, results: int, **kwargs):
        """Track search query."""
        search_query = SearchQuery(
            timestamp=datetime.now().isoformat(),
            query=query,
            results=results,
            user_agent=kwargs.get("user_agent", "Unknown"),
            ip_address=kwargs.get("ip_address", "Unknown"),
            session_id=kwargs.get("session_id")
        )
        
        # Convert to dict for storage
        search_query_dict = {
            "timestamp": search_query.timestamp,
            "query": search_query.query,
            "results": search_query.results,
            "user_agent": search_query.user_agent,
            "ip_address": search_query.ip_address,
            "session_id": search_query.session_id
        }
        
        # Add to analytics
        if "search_queries" not in self.analytics:
            self.analytics["search_queries"] = []
        
        self.analytics["search_queries"].append(search_query_dict)
        
        # Keep only recent entries
        if len(self.analytics["search_queries"]) > self.max_analytics_entries:
            self.analytics["search_queries"] = self.analytics["search_queries"][-self.max_analytics_entries:]
        
        # Save data
        self._save_data()
    
    def get_analytics(self, days: int = 7) -> Dict:
        """Get analytics summary."""
        cutoff = datetime.now() - timedelta(days=days)
        
        # Filter page views
        page_views = []
        if "page_views" in self.analytics:
            for view in self.analytics["page_views"]:
                try:
                    view_time = datetime.fromisoformat(view.get("timestamp", ""))
                    if view_time > cutoff:
                        page_views.append(view)
                except ValueError:
                    continue
        
        # Filter search queries
        search_queries = []
        if "search_queries" in self.analytics:
            for query in self.analytics["search_queries"]:
                try:
                    query_time = datetime.fromisoformat(query.get("timestamp", ""))
                    if query_time > cutoff:
                        search_queries.append(query)
                except ValueError:
                    continue
        
        return {
            "page_views": page_views,
            "search_queries": search_queries,
            "period_days": days,
            "generated_at": datetime.now().isoformat()
        }
    
    # Performance functionality
    def record_metric(self, name: str, value: float, **kwargs):
        """Record performance metric."""
        metric = PerformanceMetric(
            timestamp=datetime.now().isoformat(),
            name=name,
            value=value,
            unit=kwargs.get("unit", "ms"),
            metadata=kwargs.get("metadata", {})
        )
        
        # Convert to dict for storage
        metric_dict = {
            "timestamp": metric.timestamp,
            "name": metric.name,
            "value": metric.value,
            "unit": metric.unit,
            "metadata": metric.metadata
        }
        
        # Add to performance metrics
        if "metrics" not in self.performance:
            self.performance["metrics"] = []
        
        self.performance["metrics"].append(metric_dict)
        
        # Keep only recent entries
        if len(self.performance["metrics"]) > self.max_performance_entries:
            self.performance["metrics"] = self.performance["metrics"][-self.max_performance_entries:]
        
        # Save data
        self._save_data()
    
    def get_performance(self, days: int = 7) -> Dict:
        """Get performance summary."""
        cutoff = datetime.now() - timedelta(days=days)
        
        # Filter metrics
        metrics = []
        if "metrics" in self.performance:
            for metric in self.performance["metrics"]:
                try:
                    metric_time = datetime.fromisoformat(metric.get("timestamp", ""))
                    if metric_time > cutoff:
                        metrics.append(metric)
                except ValueError:
                    continue
        
        return {
            "metrics": metrics,
            "period_days": days,
            "generated_at": datetime.now().isoformat()
        }
    
    def optimize_site(self) -> Dict:
        """Run site optimizations."""
        results = {}
        
        # Optimize search index
        index_file = Path("site/search-index.json")
        if index_file.exists():
            success, message = self._optimize_search_index(index_file)
            results["search_index"] = {"success": success, "message": message}
        
        # Optimize images
        image_dir = Path("site/assets")
        if image_dir.exists():
            success, message = self._optimize_images(image_dir)
            results["images"] = {"success": success, "message": message}
        
        return results
    
    def _optimize_search_index(self, index_file: Path) -> Tuple[bool, str]:
        """Optimize search index file."""
        try:
            if not index_file.exists():
                return False, "Index file not found"
            
            # Check if already compressed
            if index_file.suffix == ".gz":
                return True, "Already compressed"
            
            # Read original file
            with open(index_file, "r", encoding="utf-8") as f:
                content = f.read()
            
            # Compress
            compressed_file = index_file.with_suffix(index_file.suffix + ".gz")
            with gzip.open(compressed_file, "wt", encoding="utf-8") as f:
                f.write(content)
            
            # Compare sizes
            original_size = index_file.stat().st_size
            compressed_size = compressed_file.stat().st_size
            compression_ratio = (1 - compressed_size / original_size) * 100
            
            # Record metric
            self.record_metric(
                "search_index_compression",
                compression_ratio,
                unit="percent",
                metadata={
                    "original_size": original_size,
                    "compressed_size": compressed_size
                }
            )
            
            return True, f"Compressed by {compression_ratio:.1f}%"
            
        except Exception as e:
            return False, f"Compression failed: {e}"
    
    def _optimize_images(self, image_dir: Path) -> Tuple[bool, str]:
        """Optimize images in directory."""
        try:
            if not image_dir.exists():
                return False, "Image directory not found"
            
            optimized_count = 0
            
            # Find image files
            image_extensions = {".jpg", ".jpeg", ".png", ".gif", ".webp"}
            image_files = [
                f for f in image_dir.rglob("*")
                if f.suffix.lower() in image_extensions
            ]
            
            for image_file in image_files:
                try:
                    # Get original size
                    original_size = image_file.stat().st_size
                    
                    # Record the metric
                    self.record_metric(
                        "image_size",
                        original_size,
                        unit="bytes",
                        metadata={"file": str(image_file)}
                    )
                    
                    optimized_count += 1
                    
                except Exception as e:
                    log(f"Failed to optimize image {image_file}: {e}")
            
            return True, f"Processed {optimized_count} images"
            
        except Exception as e:
            return False, f"Image optimization failed: {e}"
    
    # Combined functionality
    def get_status(self) -> Dict:
        """Get complete system status."""
        return {
            "alerts": self.get_alerts(limit=10),
            "analytics": self.get_analytics(days=1),
            "performance": self.get_performance(days=1),
            "timestamp": datetime.now().isoformat()
        }
    
    def cleanup_old_data(self, days: int = 30):
        """Clean up old monitoring data."""
        # Clean up alerts
        self.cleanup_alerts(days)
        
        # Clean up analytics
        cutoff = datetime.now() - timedelta(days=days)
        
        # Clean page views
        if "page_views" in self.analytics:
            filtered_views = []
            for view in self.analytics["page_views"]:
                try:
                    view_time = datetime.fromisoformat(view.get("timestamp", ""))
                    if view_time > cutoff:
                        filtered_views.append(view)
                except ValueError:
                    continue
            self.analytics["page_views"] = filtered_views
        
        # Clean search queries
        if "search_queries" in self.analytics:
            filtered_queries = []
            for query in self.analytics["search_queries"]:
                try:
                    query_time = datetime.fromisoformat(query.get("timestamp", ""))
                    if query_time > cutoff:
                        filtered_queries.append(query)
                except ValueError:
                    continue
            self.analytics["search_queries"] = filtered_queries
        
        # Clean performance metrics
        if "metrics" in self.performance:
            filtered_metrics = []
            for metric in self.performance["metrics"]:
                try:
                    metric_time = datetime.fromisoformat(metric.get("timestamp", ""))
                    if metric_time > cutoff:
                        filtered_metrics.append(metric)
                except ValueError:
                    continue
            self.performance["metrics"] = filtered_metrics
        
        # Save cleaned data
        self._save_data()


# Global monitoring service instance
monitoring_service = MonitoringService()


# Convenience functions
def create_alert(level: str, title: str, message: str, **kwargs) -> Dict[str, Any]:
    """Convenience function to create alerts."""
    return monitoring_service.create_alert(level, title, message, **kwargs)


def alert_info(title: str, message: str, **kwargs) -> Dict[str, Any]:
    """Create info alert."""
    return create_alert("info", title, message, **kwargs)


def alert_warning(title: str, message: str, **kwargs) -> Dict[str, Any]:
    """Create warning alert."""
    return create_alert("warning", title, message, **kwargs)


def alert_error(title: str, message: str, **kwargs) -> Dict[str, Any]:
    """Create error alert."""
    return create_alert("error", title, message, **kwargs)


def alert_critical(title: str, message: str, **kwargs) -> Dict[str, Any]:
    """Create critical alert."""
    return create_alert("critical", title, message, **kwargs)


def track_page_view(page: str, **kwargs):
    """Convenience function to track page views."""
    monitoring_service.track_page_view(page, **kwargs)


def track_search(query: str, results: int, **kwargs):
    """Convenience function to track search queries."""
    monitoring_service.track_search(query, results, **kwargs)


def record_metric(name: str, value: float, **kwargs):
    """Convenience function to record performance metrics."""
    monitoring_service.record_metric(name, value, **kwargs)


def time_function(func):
    """Decorator to time function execution."""
    def wrapper(*args, **kwargs):
        import time
        start_time = time.time()
        result = func(*args, **kwargs)
        end_time = time.time()
        
        execution_time = (end_time - start_time) * 1000  # Convert to milliseconds
        record_metric(
            f"function_{func.__name__}",
            execution_time,
            unit="ms",
            metadata={"args_count": len(args), "kwargs_count": len(kwargs)}
        )
        
        return result
    return wrapper
