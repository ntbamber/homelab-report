import httpx
from typing import Dict, Any
from config.schema import ProxmoxConfig, NetworkConfig


def check_response(r):
    # If we got a 401/403, throw error immediately
    if r.status_code in (401, 403):
        raise Exception(f"Auth Failed ({r.status_code})")
    
    # If we got HTML (like a login page), throw error with snippet
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


def build_summary(cfg: ProxmoxConfig, net: NetworkConfig) -> Dict[str, Any]:
    report = {"name": cfg.name, "status": "healthy", "reason": None}
    
    # Proxmox Header Auth
    headers = {"Authorization": f"PVEAPIToken={cfg.username}={cfg.api_token}"}
    base = f"{str(cfg.host).rstrip('/')}/api2/json"

    try:
        with httpx.Client(base_url=base, headers=headers, verify=False, timeout=net.timeout) as c:
            nodes_data = check_response(c.get("/nodes"))
            nodes = nodes_data.get("data", [])
            
            offline = [n["node"] for n in nodes if n.get("status") != "online"]
            if offline:
                report.update({"status": "down", "reason": f"Nodes offline: {', '.join(offline)}"})

            report["data"] = {
                "nodes_online": len(nodes) - len(offline),
                "vms_running": sum(n.get("active_vms", 0) for n in nodes)
            }
    except Exception as e:
        report.update({"status": "down", "reason": str(e)})
    return report
