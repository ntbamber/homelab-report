import sys
import os
import json
import concurrent.futures
import logging
from pathlib import Path
from dotenv import load_dotenv
from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.triggers.cron import CronTrigger


# 1. Setup & Imports
# Set working directory for consistent pathing
root_dir = Path(os.getcwd())
if str(root_dir) not in sys.path:
    sys.path.append(str(root_dir))

#Import custom modules
from config.loader import load_config
from src.email.sender import send_report

# Import service modules
from src.api import (
    adguard, bazarr, gluetun, jellyfin, jellyseerr, 
    lidarr, portainer, prowlarr, proxmox, 
    qbittorrent, radarr, slskd, sonarr, speedtest_tracker
)

# Setup basic logging for the scheduler
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - [%(levelname)s] - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger("HomelabScheduler")

# 2. Main Execution
def run_report_job(): 
    # Main report logic to be called by the scheduler
    logger.info("--Starting Daily Homelab Report--")
    load_dotenv()
    
    try:
        cfg = load_config()
    except Exception as e:
        logger.error(f"Configuration Error: {e}")
        return

    # Map config objects to their summary building functions
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

    # Run summary building functions concurrently
    with concurrent.futures.ThreadPoolExecutor() as executor:
        # Submit all tasks
        future_to_service = {
            executor.submit(func, c_cfg, n_cfg): c_cfg.name 
            for func, c_cfg, n_cfg in checks
        }

        # Process results at completion
        for future in concurrent.futures.as_completed(future_to_service):
            service_name = future_to_service[future]
            # Error handling for individual services
            try:
                data = future.result()
                report.append(data)
                logger.info(f"{service_name} checked.")
            except Exception as exc:
                logger.error(f"{service_name} generated an exception: {exc}")
                report.append({
                    "name": service_name, 
                    "status": "error", 
                    "reason": str(exc)
                })

    # Sort report alphabetically by service name
    report.sort(key=lambda x: x['name'])

    # 3. Emailing
    logger.info("Generating Email...")
    try:
        send_report(report)
        logger.info("Done! Report sent successfully.")
    except Exception as e:
        logger.error(f"Failed to send email: {e}")

# 3. Scheduler
if __name__ == "__main__":
    # 3.1. Load config to get schedule settings
    try:
        init_config = load_config()
        cron_schedule = init_config.schedule.time      # Cron schedule from config.yaml; e.g., "0 6 * * *"
        user_timezone = init_config.schedule.timezone  # Timezone from config.yaml; e.g., "America/New_York"
        
        logger.info(f"Scheduler Initialized.")
        logger.info(f"Timezone: {user_timezone}")
        logger.info(f"Schedule: {cron_schedule}")
        
    except Exception as e:
        logger.critical(f"Failed to load initial config for scheduling: {e}")
        sys.exit(1)

    # 2. Setup APScheduler
    scheduler = BlockingScheduler(timezone=user_timezone)

    # 3. Add the job using the Cron string from config
    scheduler.add_job(
        run_report_job, 
        CronTrigger.from_crontab(cron_schedule, timezone=user_timezone)
    )

    # 4. Run once immediately on startup (Verification)
    logger.info("Running immediate startup check...")
    run_report_job()

    # 5. Start the scheduling loop
    logger.info(f"Scheduler started. Waiting for next run at {cron_schedule}...")
    
    try:
        scheduler.start()
    except (KeyboardInterrupt, SystemExit):
        logger.info("Scheduler stopped.")