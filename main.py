import sys
import os
import json
import concurrent.futures
from pathlib import Path
from dotenv import load_dotenv

# 1. SETUP & IMPORTS
# ------------------------------------------------------------------------------
# Ensure we can import from 'src' even if running from a different folder
root_dir = Path(os.getcwd())
if str(root_dir) not in sys.path:
    sys.path.append(str(root_dir))

from config.loader import load_config
from src.email.sender import send_report  # <--- IMPORT THE SENDER

# Import all your service modules
from src.api import (
    adguard, bazarr, gluetun, jellyfin, jellyseerr, 
    lidarr, portainer, prowlarr, proxmox, 
    qbittorrent, radarr, slskd, sonarr, speedtest_tracker
)

# 2. MAIN EXECUTION
# ------------------------------------------------------------------------------
def main():
    print("Starting Homelab Report...")
    load_dotenv()
    
    try:
        cfg = load_config()
    except Exception as e:
        print(f"Configuration Error: {e}")
        return

    # Map config objects to their checker functions
    # (If you add more services later, just add them here)
    checks = [
        (adguard.build_summary, cfg.adguard, cfg.network),
        (bazarr.build_summary, cfg.bazarr, cfg.network),
        (gluetun.build_summary, cfg.gluetun, cfg.network),
        (jellyfin.build_summary, cfg.jellyfin, cfg.network),
        (jellyseerr.build_summary, cfg.jellyseerr, cfg.network),
        (lidarr.build_summary, cfg.lidarr, cfg.network),
        (portainer.build_summary, cfg.portainer, cfg.network),
        (prowlarr.build_summary, cfg.prowlarr, cfg.network),
        (proxmox.build_summary, cfg.proxmox, cfg.network),
        (qbittorrent.build_summary, cfg.qbittorrent, cfg.network),
        (radarr.build_summary, cfg.radarr, cfg.network),
        (slskd.build_summary, cfg.slskd, cfg.network),
        (sonarr.build_summary, cfg.sonarr, cfg.network),
        (speedtest_tracker.build_summary, cfg.speedtest_tracker, cfg.network),
    ]

    report = []

    # Run checks in parallel to be fast
    with concurrent.futures.ThreadPoolExecutor() as executor:
        # Submit all tasks
        future_to_service = {
            executor.submit(func, c_cfg, n_cfg): c_cfg.name 
            for func, c_cfg, n_cfg in checks
        }
        
        # Process results as they complete
        for future in concurrent.futures.as_completed(future_to_service):
            service_name = future_to_service[future]
            try:
                data = future.result()
                report.append(data)
                print(f"{service_name} checked.")
            except Exception as exc:
                print(f"{service_name} generated an exception: {exc}")
                report.append({
                    "name": service_name, 
                    "status": "error", 
                    "reason": str(exc)
                })

    # Sort report alphabetically by service name
    report.sort(key=lambda x: x['name'])

    # 3. SEND THE EMAIL
    # --------------------------------------------------------------------------
    print("Generating Email...")
    send_report(report)
    print(" Done!")

if __name__ == "__main__":
    main()