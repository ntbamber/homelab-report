import httpx
from typing import Dict, Any
from config.schema import SonarrConfig, NetworkConfig

def build_summary(cfg: SonarrConfig, net: NetworkConfig) -> Dict[str, Any]:
    report = {"name": cfg.name, "status": "healthy", "reason": None}
    params = {"apikey": cfg.api_key}
    base = f"{str(cfg.url).rstrip('/')}/api/v3"

    try:
        with httpx.Client(base_url=base, verify=False, timeout=net.timeout) as c:
            # 1. System Status
            status = c.get("/system/status", params=params).json()
            
            # 2. Queue (Activity)
            queue = c.get("/queue", params=params).json()
            queue_count = len(queue.get('records', [])) if isinstance(queue, dict) else len(queue)
            
            # 3. Missing (Wanted)
            # Radarr/Sonarr use slightly different missing endpoints, usually /wanted/missing
            missing_count = 0
            try:
                # Try generic approach first
                wanted = c.get("/wanted/missing", params={**params, "pageSize": 1, "page": 1}).json()
                missing_count = wanted.get('totalRecords', 0)
            except: pass

            # 4. History (Last Grab)
            last_grab = "None"
            try:
                hist = c.get("/history", params={**params, "pageSize": 1, "page": 1, "sortKey": "date", "sortDir": "desc"}).json()
                records = hist.get('records', [])
                if records:
                     last_grab = records[0].get('sourceTitle', 'Unknown')
            except: pass
            
            # Health
            try:
                health = c.get("/health", params=params).json()
                errors = [h['message'] for h in health if h['type'] == 'Error']
                if errors:
                    report.update({"status": "warning", "reason": f"{len(errors)} Errors: {errors[0]}..."})
            except: pass

            report["data"] = {
                "version": status.get("version"),
                "queued_items": queue_count,
                "missing_content_count": missing_count,
                "latest_grab": last_grab
            }
    except Exception as e:
        report.update({"status": "down", "reason": str(e)})
    return report
