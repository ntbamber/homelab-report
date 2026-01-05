import httpx
from typing import Dict, Any
from config.schema import ProwlarrConfig, NetworkConfig

def build_summary(cfg: ProwlarrConfig, net: NetworkConfig) -> Dict[str, Any]:
    report = {"name": cfg.name, "status": "healthy", "reason": None}
    
    api_key = cfg.api_key
    base = str(cfg.url).rstrip("/")
    if not base.endswith("/api/v1"):
        base += "/api/v1"

    headers = {"X-Api-Key": api_key}
    params = {"apikey": api_key}

    try:
        with httpx.Client(base_url=base, headers=headers, params=params, verify=False, timeout=net.timeout) as c:
            # System Status
            try:
                r_sys = c.get("/system/status")
                if r_sys.status_code == 401:
                    raise Exception("Auth Failed (401)")
                # Detect if HTML is fetched instead of JSON (login page or error)
                if not r_sys.content or r_sys.text.strip().startswith("<"):
                    raise Exception("Invalid Response (HTML/Login Page)")
                    
                sys_info = r_sys.json()
            except Exception as e:
                raise Exception(f"Connection Failed: {e}")
            # Indexer Stats
            total_grabs = 0
            try:
                stats = c.get("/indexer/stats").json()
                total_grabs = sum(s.get('grabs', 0) for s in stats.get('stats', []))
            except:
                pass 
            # Indexer Status
            active_count = 0
            failed_count = 0
            try:
                indexers = c.get("/indexerstatus").json()
                failures = [i for i in indexers if i.get('disabled') or i.get('status') == 'failing']
                active_count = len(indexers) - len(failures)
                failed_count = len(failures)
                
                if failed_count > 0:
                    report.update({"status": "warning", "reason": f"{failed_count} Indexers Failing"})
            except:
                pass

            report["data"] = {
                "version": sys_info.get("version"),
                "active_indexers": active_count,
                "failed_indexers": failed_count,
                "total_grabs_lifetime": total_grabs
            }

    except Exception as e:
        report.update({"status": "down", "reason": str(e)})
    return report
