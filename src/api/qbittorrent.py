import httpx
from typing import Dict, Any
from config.schema import QbittorrentConfig, NetworkConfig

def build_summary(cfg: QbittorrentConfig, net: NetworkConfig) -> Dict[str, Any]:
    report = {"name": cfg.name, "status": "healthy", "reason": None}
    
    try:
        with httpx.Client(base_url=str(cfg.url).rstrip("/"), verify=False, timeout=net.timeout) as c:
            # Login
            c.post("/api/v2/auth/login", data={"username": cfg.username, "password": cfg.password})
            # Global Transfer Info
            info = c.get("/api/v2/transfer/info").json()
            # All Torrents
            torrents = c.get("/api/v2/torrents/info").json()
            # Process Data
            active = [t for t in torrents if t['state'] in ('downloading', 'uploading', 'stalledDL')]
            errored = [t for t in torrents if t['state'] in ('error', 'missingFiles')]
            # Categories
            cats = {}
            for t in torrents:
                cat = t.get('category') or 'Uncategorized'
                cats[cat] = cats.get(cat, 0) + 1
            # Top 3 Active
            top_active = sorted(active, key=lambda x: x.get('dlspeed', 0), reverse=True)[:3]
            top_active_clean = [{
                'name': t['name'][:30], 
                'progress': f"{t['progress']*100:.1f}%", 
                'speed': f"{t['dlspeed']/1024/1024:.1f} MB/s"
            } for t in top_active]

            report["data"] = {
                "dl_speed": f"{info.get('dl_info_speed', 0)/1024/1024:.2f} MB/s",
                "up_speed": f"{info.get('up_info_speed', 0)/1024/1024:.2f} MB/s",
                "total_torrents": len(torrents),
                "active_count": len(active),
                "error_count": len(errored),
                "categories": cats,
                "top_active": top_active_clean
            }
    except Exception as e:
        report.update({"status": "down", "reason": str(e)})
    return report
