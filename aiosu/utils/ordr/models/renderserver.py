from __future__ import annotations

from datetime import datetime

from pydantic import Field

from aiosu.models import BaseModel
from aiosu.models import Mods

__all__ = (
    "RenderServerOptions",
    "RenderServer",
)


class RenderServerOptions(BaseModel):
    text_color: str = Field(alias="textColor")
    background_type: str = Field(alias="backgroundType")


class RenderServer(BaseModel):
    enabled: bool
    last_seen: datetime = Field(alias="lastSeen")
    name: str
    priority: float
    old_score: float = Field(alias="oldScore")
    avg_fps: int = Field(alias="avgFPS")
    power: str
    status: str
    total_rendered: int = Field(alias="totalRendered")
    rendering_type: str = Field(alias="renderingType")
    cpu: str
    gpu: str
    motion_blur_capable: bool = Field(alias="motionBlurCapable")
    using_osu_api: bool = Field(alias="usingOsuApi")
    uhd_capable: bool = Field(alias="uhdCapable")
    avg_render_time: float = Field(alias="avgRenderTime")
    avg_upload_time: float = Field(alias="avgUploadTime")
    total_avg_time: float = Field(alias="totalAvgTime")
    total_uploaded_videos_size: int = Field(alias="totalUploadedVideosSize")
    owner_user_id: int = Field(alias="ownerUserID")
    owner_username: str = Field(alias="ownerUsername")
    customization: RenderServerOptions
