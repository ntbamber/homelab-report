import httpx
from typing import Dict, Any
from config.schema import GluetunConfig, NetworkConfig

def build_summary(cfg: GluetunConfig, net: NetworkConfig) -> Dict[str, Any]:
    report = {"name": cfg.name, "status": "healthy", "reason": None}
    headers = {"X-API-Key": cfg.api_key} if cfg.api_key else {}
    
    try:
        with httpx.Client(base_url=str(cfg.url).rstrip("/"), headers=headers, verify=False, timeout=net.timeout) as c:
            vpn = c.get("/v1/vpn/status").json()
            ip = c.get("/v1/publicip/ip").json()
            
            if vpn.get("status") != "running":
                report.update({"status": "down", "reason": "VPN not running"})

            report["data"] = {
                "status": vpn.get("status"),
                "public_ip": ip.get("public_ip"),
                "region": ip.get("region"),
                "country": ip.get("country"),
                "isp": ip.get("org")
            }
    except Exception as e:
        report.update({"status": "down", "reason": str(e)})
    return report
