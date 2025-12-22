import httpx
from typing import Dict, Any
from config.schema import SlskdConfig, NetworkConfig

def build_summary(cfg: SlskdConfig, net: NetworkConfig) -> Dict[str, Any]:
    report = {"name": cfg.name, "status": "healthy", "reason": None}
    headers = {"X-API-Key": cfg.api_key}
    
    try:
        with httpx.Client(base_url=str(cfg.url).rstrip("/"), headers=headers, verify=False, timeout=net.timeout) as c:
            
            # 1. Version (Clean Parsing)
            # We explicitly dig into the JSON to find the string, so it doesn't dump the whole object
            r_app = c.get("/api/v0/application")
            if r_app.status_code == 404: r_app = c.get("/api/v1/application")
            
            version_str = "Unknown"
            if r_app.status_code == 200:
                v_data = r_app.json()
                # Try 'current' first (cleanest), then 'full', then 'version'
                version_str = v_data.get("current") or v_data.get("full") or v_data.get("version") or "Unknown"

            # 2. Downloads
            dl_active = 0
            dl_total = 0
            try:
                dls = c.get("/api/v0/transfers/downloads").json()
                dl_total = len(dls)
                # Active = anything not finished
                dl_active = len([d for d in dls if d.get('state') not in ['Completed', 'Cancelled', 'Aborted']])
            except:
                pass

            # 3. Uploads (Explicit Fetch)
            ul_active = 0
            ul_total = 0
            try:
                uls = c.get("/api/v0/transfers/uploads").json()
                ul_total = len(uls)
                # Active = anything not finished
                ul_active = len([u for u in uls if u.get('state') not in ['Completed', 'Cancelled', 'Aborted']])
            except:
                pass

            report["data"] = {
                "version": version_str,
                "downloads": {
                    "active": dl_active,
                    "total": dl_total
                },
                "uploads": {
                    "active": ul_active,
                    "total": ul_total
                }
            }

    except Exception as e:
        report.update({"status": "down", "reason": str(e)})
    return report
