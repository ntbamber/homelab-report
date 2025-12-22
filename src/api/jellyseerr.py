import httpx
from typing import Dict, Any
from config.schema import JellyseerrConfig, NetworkConfig

def build_summary(cfg: JellyseerrConfig, net: NetworkConfig) -> Dict[str, Any]:
    report = {"name": cfg.name, "status": "healthy", "reason": None}
    headers = {"X-Api-Key": cfg.api_key, "Accept": "application/json"}
    
    try:
        with httpx.Client(base_url=str(cfg.url).rstrip("/"), headers=headers, verify=False, timeout=net.timeout) as c:
            # Stats
            # Jellyseerr doesn't have a single "stats" endpoint, we count requests
            pending = c.get("/api/v1/request", params={"take": 0, "filter": "pending"}).json().get("pageInfo", {}).get("results", 0)
            approved = c.get("/api/v1/request", params={"take": 0, "filter": "approved"}).json().get("pageInfo", {}).get("results", 0)
            
            users = c.get("/api/v1/user", params={"take": 0}).json().get("pageInfo", {}).get("results", 0)

            report["data"] = {
                "pending_requests": pending,
                "approved_requests": approved,
                "total_users": users
            }
    except Exception as e:
        report.update({"status": "down", "reason": str(e)})
    return report
