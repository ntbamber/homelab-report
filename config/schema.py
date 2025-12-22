from __future__ import annotations
from typing import Optional
from pydantic import BaseModel, EmailStr, AnyUrl, Field, ConfigDict

# -----------------------------
# Helpers / base service models
# -----------------------------
class NamedService(BaseModel):
    name: str
    username: str | None = None
    password: str | None = None
    model_config = ConfigDict(populate_by_name=True)

class UrlService(NamedService):
    # AnyUrl accepts IPs, hostnames, http/https, and ports (good for homelab)
    url: AnyUrl

class ApiKeyService(UrlService):
    api_key: str

class BasicAuthService(UrlService):
    username: str
    password: str

# -----------------------------
# Top-level sections
# -----------------------------
class ScheduleConfig(BaseModel):
    # Cron string, e.g. "0 6 * * *"
    time: str
    # IANA timezone, e.g. "America/New_York"
    timezone: str

class EmailConfig(BaseModel):
    smtp_server: str
    smtp_port: int = Field(ge=1, le=65535)
    username: Optional[str] = None  # allow env overrides or unauth SMTP
    password: Optional[str] = None
    from_address: EmailStr
    to_address: EmailStr

class NetworkConfig(BaseModel):
    timeout: int = Field(ge=1)
    retries: int = Field(ge=0)

# -----------------------------
# Services
# -----------------------------
class ProxmoxConfig(NamedService):
    host: AnyUrl
    api_token: str
    password: str | None = None

class PortainerConfig(UrlService):
    token: str
    environment: int

class GluetunConfig(UrlService):
    api_key: str | None = None

class AdGuardConfig(UrlService):
    username: str
    password: str

class SpeedtestTrackerConfig(ApiKeyService):
    api_key: str

class MySpeedConfig(UrlService):
    pass

class ProwlarrConfig(ApiKeyService):
    pass

class SonarrConfig(ApiKeyService):
    pass

class RadarrConfig(ApiKeyService):
    pass

class LidarrConfig(ApiKeyService):
    pass

class BazarrConfig(ApiKeyService):
    pass

class QbittorrentConfig(BasicAuthService):
    pass

class SlskdConfig(ApiKeyService):
    pass

class JellyfinConfig(ApiKeyService):
    pass

class JellyseerrConfig(ApiKeyService):
    pass

# -----------------------------
# Master app config
# -----------------------------
class AppConfig(BaseModel):
    # top-level sections
    schedule: ScheduleConfig
    email: EmailConfig
    network: NetworkConfig

    # infrastructure & network
    proxmox: ProxmoxConfig
    portainer: PortainerConfig
    gluetun: GluetunConfig
    adguard: AdGuardConfig
    speedtest_tracker: SpeedtestTrackerConfig
    myspeed: MySpeedConfig

    # arr suite
    prowlarr: ProwlarrConfig
    sonarr: SonarrConfig
    radarr: RadarrConfig
    lidarr: LidarrConfig
    bazarr: BazarrConfig

    # download clients
    qbittorrent: QbittorrentConfig
    slskd: SlskdConfig

    # media servers
    jellyfin: JellyfinConfig
    jellyseerr: JellyseerrConfig