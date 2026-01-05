import httpx
from typing import Dict, Any
from config.schema import BazarrConfig, NetworkConfig


def check_response(r):
    # Immediate auth failure
    if r.status_code in (401, 403):
        raise Exception(f"Auth Failed ({r.status_code})")
    
    # Throw HTML errors
    if "text/html" in r.headers.get("content-type", ""):
        title = "Unknown Page"
        if "<title>" in r.text:
            title = r.text.split("<title>")[1].split("</title>")[0]
        raise Exception(f"Endpoint returned HTML (Page: {title}) instead of JSON. Check URL/Auth.")
        
    # Otherwise try to return JSON
    try:
        return r.json()
    except:
        raise Exception(f"Invalid JSON response: {r.text[:50]}...")


def build_summary(cfg: BazarrConfig, net: NetworkConfig) -> Dict[str, Any]:
    report = {"name": cfg.name, "status": "healthy", "reason": None}
    params = {"apikey": cfg.api_key}
    
    try:
        with httpx.Client(base_url=str(cfg.url).rstrip("/"), verify=False, timeout=net.timeout) as c:
            r = check_response(c.get("/api/system/status", params=params))
            data = r.get("data", {})
            report["data"] = {
                "version": data.get("version"),
                "episodes_missing": data.get("episodes", 0)
            }
    except Exception as e:
        report.update({"status": "down", "reason": str(e)})
    return report
