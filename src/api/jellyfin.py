import httpx
from typing import Dict, Any
from config.schema import JellyfinConfig, NetworkConfig

def build_summary(cfg: JellyfinConfig, net: NetworkConfig) -> Dict[str, Any]:
    report = {"name": cfg.name, "status": "healthy", "reason": None}
    auth = f'MediaBrowser Client="HomelabReport", Device="Server", DeviceId="12345", Version="1.0.0", Token="{cfg.api_key}"'
    headers = {"X-Emby-Authorization": auth, "Accept": "application/json"}

    try:
        with httpx.Client(base_url=str(cfg.url).rstrip("/"), headers=headers, verify=False, timeout=net.timeout) as c:
            info = c.get("/System/Info").json()
            sessions = c.get("/Sessions").json()
            counts = c.get("/Items/Counts").json()
            
            active = []
            for s in sessions:
                if "NowPlayingItem" in s:
                    user = s.get("UserName", "Unknown")
                    item = s["NowPlayingItem"].get("Name", "Unknown")
                    active.append(f"{user} streaming {item}")

            report["data"] = {
                "version": info.get("Version"),
                "total_movies": counts.get("MovieCount"),
                "total_episodes": counts.get("EpisodeCount"),
                "active_streams_count": len(active),
                "now_playing": active
            }
    except Exception as e:
        report.update({"status": "down", "reason": str(e)})
    return report
