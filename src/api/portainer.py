import httpx
from typing import Dict, Any
from config.schema import PortainerConfig, NetworkConfig

def build_summary(cfg: PortainerConfig, net: NetworkConfig) -> Dict[str, Any]:
    report = {"name": cfg.name, "status": "healthy", "reason": None}
    headers = {"X-API-Key": cfg.token}
    env_id = getattr(cfg, "environment", getattr(cfg, "enviroment", 1))

    try:
        with httpx.Client(base_url=str(cfg.url).rstrip("/"), headers=headers, verify=False, timeout=net.timeout) as c:
            # Auto-detect ID if needed
            try:
                all_envs = c.get("/api/endpoints").json()
                if not any(e['Id'] == env_id for e in all_envs):
                    env_id = all_envs[0]['Id']
            except: pass

            # Dashboard Stats
            dash = c.get(f"/api/endpoints/{env_id}/docker/dashboard").json()
            
            # Stacks
            stacks_count = 0
            try:
                stacks = c.get("/api/stacks").json()
                stacks_count = len(stacks)
            except: pass

            report["data"] = {
                "environment_id": env_id,
                "stacks": stacks_count,
                "containers": {
                    "total": dash.get("containerCount", 0),
                    "running": dash.get("runningContainerCount", 0),
                    "stopped": dash.get("stoppedContainerCount", 0),
                    "unhealthy": dash.get("unhealthyContainerCount", 0),
                },
                "images": dash.get("imageCount", 0),
                "volumes": dash.get("volumeCount", 0)
            }
            
            if report["data"]["containers"]["unhealthy"] > 0:
                report.update({"status": "warning", "reason": "Unhealthy containers detected"})

    except Exception as e:
        report.update({"status": "down", "reason": str(e)})
    return report
