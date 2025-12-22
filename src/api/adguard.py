import httpx
from typing import Dict, Any
from config.schema import AdGuardConfig, NetworkConfig

def build_summary(cfg: AdGuardConfig, net: NetworkConfig) -> Dict[str, Any]:
    report = {"name": cfg.name, "status": "healthy", "reason": None}
    base = f"{str(cfg.url).rstrip('/')}/control"
    
    try:
        with httpx.Client(base_url=base, auth=(cfg.username, cfg.password), verify=False, timeout=net.timeout) as c:
            # Check Status
            status = c.get("/status").json()
            if not status.get("running"):
                report.update({"status": "down", "reason": "DNS service not running"})
            elif not status.get("protection_enabled"):
                report.update({"status": "warning", "reason": "Protection disabled"})

            # Get Stats
            stats = c.get("/stats").json()
            
            # Filtering Status
            filtering = c.get("/filtering/status").json()
            if not filtering.get("enabled"):
                report.update({"status": "warning", "reason": "Filtering disabled"})

            report["data"] = {
                "version": status.get("version"),
                "dns_queries": stats.get("num_dns_queries", 0),
                "blocked_queries": stats.get("num_blocked_filtering", 0),
                "blocked_percentage": f"{stats.get('blocked_filtering_percentage', 0):.2f}%",
                "top_queried": [x['domain'] for x in stats.get("top_queried_domains", [])[:5]],
                "top_blocked": [x['domain'] for x in stats.get("top_blocked_domains", [])[:5]]
            }
    except Exception as e:
        report.update({"status": "down", "reason": str(e)})
    return report
