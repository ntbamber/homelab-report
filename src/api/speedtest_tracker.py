import httpx
import statistics
import urllib.parse
from typing import Dict, Any
from datetime import datetime, timedelta
from dateutil import parser
from config.schema import SpeedtestTrackerConfig, NetworkConfig

def build_summary(cfg: SpeedtestTrackerConfig, net: NetworkConfig) -> Dict[str, Any]:
    report = {"name": cfg.name, "status": "healthy", "reason": None}
    headers = {"Authorization": f"Bearer {cfg.api_key}", "Accept": "application/json"}
    
    # We need 7 days of history. 
    # API forces pagination (25 items/page), loop until we reach this date.
    target_date = datetime.now().replace(tzinfo=None) - timedelta(days=7)
    
    all_results = []
    
    try:
        with httpx.Client(base_url=str(cfg.url).rstrip("/"), headers=headers, verify=False, timeout=net.timeout) as c:

            current_params = {"sort": "-created_at"}
            # Safety: Limit database to 50 pages to avoid fetching too much
            for _ in range(50):
                r = c.get("/api/v1/results", params=current_params)
                
                if r.status_code != 200:
                    break # Stop if API errors
                
                json_resp = r.json()
                items = json_resp.get('data', [])
                
                if not items:
                    break # Stop if empty
                
                batch_oldest = None
                
                for item in items:
                    try:
                        # Parse Time (Naive for comparison)
                        dt = parser.parse(item['created_at']).replace(tzinfo=None)
                        batch_oldest = dt
                        # Parse Values (Handle Bytes -> Bits conversion)
                        # Try for explicit bits field (exists in newer API versions)
                        if 'download_bits' in item:
                            dl_bits = float(item['download_bits'])
                            ul_bits = float(item['upload_bits'])
                        else:
                            # Fallback: API provided Bytes, we need Bits
                            dl_bits = float(item.get("download") or 0) * 8
                            ul_bits = float(item.get("upload") or 0) * 8
                        
                        ping = float(item.get("ping") or 0)
                        
                        all_results.append({
                            "time": dt,
                            "download": dl_bits,
                            "upload": ul_bits,
                            "ping": ping
                        })
                    except:
                        continue
                # CHECK if we reached our target date
                if batch_oldest and batch_oldest < target_date:
                    break 
                # PREPARE NEXT PAGE
                next_link = json_resp.get('links', {}).get('next')
                if not next_link:
                    break
                # Extract params from the URL provided by the server
                parsed = urllib.parse.urlparse(next_link)
                query = urllib.parse.parse_qs(parsed.query)
                # Flatten params (parse_qs returns lists)
                current_params = {k: v[0] for k, v in query.items()}
            # CALCULATE STATS
            if not all_results:
                report["data"] = {"24h_avg": "No Data", "7d_avg": "No Data"}
                return report

            now = datetime.now().replace(tzinfo=None)
            cutoff_24h = now - timedelta(hours=24)
            cutoff_7d = now - timedelta(days=7)

            list_24h = [x for x in all_results if x['time'] >= cutoff_24h]
            list_7d = [x for x in all_results if x['time'] >= cutoff_7d]

            def calc_avg(items):
                if not items: return None
                avg_dl = statistics.mean([i['download'] for i in items]) / 1_000_000
                avg_ul = statistics.mean([i['upload'] for i in items]) / 1_000_000
                avg_ping = statistics.mean([i['ping'] for i in items])
                
                return {
                    "download": f"{avg_dl:.2f} Mbps",
                    "upload": f"{avg_ul:.2f} Mbps",
                    "ping": f"{avg_ping:.2f} ms"
                }

            report["data"] = {
                "24h_avg": calc_avg(list_24h) or "No Data (24h)",
                "7d_avg": calc_avg(list_7d) or "No Data (7d)"
            }

    except Exception as e:
        report.update({"status": "down", "reason": str(e)})
    return report
