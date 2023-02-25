from __future__ import annotations

from pydantic import Field

from aiosu.models import BaseModel

__all__ = (
    "Skin",
    "SkinCompact",
    "SkinsResponse",
)


class Skin(BaseModel):
    id: int
    name: str = Field(alias="skin")
    presentation_name: str = Field(alias="presentationName")
    url: str
    high_res_preview_url: str = Field(alias="highResPreview")
    low_res_preview_url: str = Field(alias="lowResPreview")
    grid_preview_url: str = Field(alias="gridPreview")
    has_cursor_middle: bool = Field(alias="hasCursorMiddle")
    modified: bool
    author: str
    version: str
    times_used: int = Field(alias="timesUsed")


class SkinCompact(BaseModel):
    found: bool
    removed: bool
    message: str
    skin_name: str = Field(alias="skinName")
    skin_author: str = Field(alias="skinAuthor")
    download_link: str = Field(alias="downloadLink")


class SkinsResponse(BaseModel):
    skins: list[Skin]
    message: str
    max_skins: int = Field(alias="maxSkins")
