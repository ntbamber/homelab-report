# Homelab Scheduled Status Reporter

## Overview

This is a self-hosted, scheduled, email-based reporting system for self-hosted services. It reports daily health, activity, and usage data from services, aggregates the results, and produces a readable daily report.

---

## What It Does

On a user set schedule, the application:

- Loads configuration from `config.yaml` and environment variables
- Queries self-hosted services via their REST APIs
- Normalizes and summarizes key metrics
- Produces and delivers a status report through email

---

## Supported Services

- Proxmox
- Portainer
- Sonarr
- Radarr
- Lidarr
- Prowlarr
- Bazarr
- Jellyfin
- Jellyseerr
- qBittorrent
- slskd
- Gluetun
- AdGuard
- Speedtest Tracker

Each service is implemented as an isolated API module, allowing for modification and enhancement of information provided by each service.

---

## Project Structure

```
homelab-report/
├── src/
│   ├── api/               # Service-specific API calls
│   ├── config/            # Config loading & validation
│   ├── email/             # Email sending module & HTML email template
│   ├── main.py            # Main program responsible for calling API modules, aggregating responses, calling emailer module, and scheduling runs
├── example_config.yaml    # Config template
├── .env.example           # Environment variable template
├── Dockerfile
├── docker-compose.yml
└── README.md
```

---

## Configuration

Configuration is split into two parts:

### `config.yaml`
Contains service URLs, scheduling settings, and structural configuration.  
This file is mounted into the container and intentionally excluded from source control.

### `.env`
Contains secrets such as API keys and credentials.  
Loaded via environment variables at runtime.

Example files of config.yaml & .env are provided for reference.

---

## Deployment

The application is designed to run inside Docker.

Typical deployment:
- Mount `config.yaml` into `/app/config/config.yaml`
- Provide environment variables via `.env`
- Run as a scheduled container or long-running service

---

## Purpose & Motivation

This project was built out of desire to produce a daily snapshot of my self-hosted services to be able to observe statuses alongside routine email checking. Additionally, this project acted as an opportunity to practice integrating many different API calls, parsing API responses, designing a modular Python system, and running container in Docker.
There are some known bugs with response handling, but currently I have no plans to continue development of this project. Please feel free to build on this codebase if desired.
