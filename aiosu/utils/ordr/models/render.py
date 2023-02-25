from __future__ import annotations

from datetime import datetime

from pydantic import Field

from aiosu.models import BaseModel
from aiosu.models import Mods

__all__ = (
    "Render",
    "RendersResponse",
    "RenderCreateResponse",
)


class Render(BaseModel):
    date: datetime
    readable_date: str = Field(alias="readableDate")
    render_id: int = Field(alias="renderID")
    username: str
    progress: str
    renderer: str
    description: str
    title: str
    replay_file_path: str = Field(alias="replayFilePath")
    video_url: str = Field(alias="videoUrl")
    map_link: str = Field(alias="mapLink")
    map_title: str = Field(alias="mapTitle")
    replay_difficulty: str = Field(alias="replayDifficulty")
    replay_username: str = Field(alias="replayUsername")
    map_id: int = Field(alias="mapID")
    need_to_redownload: bool = Field(alias="needToRedownload")
    resolution: str
    globalVolume: float = Field(alias="globalVolume")
    musicVolume: float = Field(alias="musicVolume")
    hitsoundVolume: float = Field(alias="hitsoundVolume")
    show_hit_error_meter: bool = Field(alias="showHitErrorMeter")
    show_unstable_rate: bool = Field(alias="showUnstableRate")
    show_score: bool = Field(alias="showScore")
    show_hp_bar: bool = Field(alias="showHPBar")
    show_combo_counter: bool = Field(alias="showComboCounter")
    show_pp_counter: bool = Field(alias="showPPCounter")
    show_key_overlay: bool = Field(alias="showKeyOverlay")
    show_scoreboard: bool = Field(alias="showScoreboard")
    show_borders: bool = Field(alias="showBorders")
    show_mods: bool = Field(alias="showMods")
    show_result_screen: bool = Field(alias="showResultScreen")
    skin: str
    has_cursor_middle: bool = Field(alias="hasCursorMiddle")
    use_skin_cursor: bool = Field(alias="useSkinCursor")
    use_beatmap_colors: bool = Field(alias="useBeatmapColors")
    cursor_scale_to_cs: bool = Field(alias="cursorScaleToCS")
    cursor_rainbow: bool = Field(alias="cursorRainbow")
    cursor_trail_glow: bool = Field(alias="cursorTrailGlow")
    cursor_size: float = Field(alias="cursorSize")
    cursor_trail: bool = Field(alias="cursorTrail")
    draw_follow_points: bool = Field(alias="drawFollowPoints")
    draw_combo_numbers: bool = Field(alias="drawComboNumbers")
    scale_to_the_beat: bool = Field(alias="scaleToTheBeat")
    slider_merge: bool = Field(alias="sliderMerge")
    objects_rainbow: bool = Field(alias="objectsRainbow")
    objects_flash_to_the_beat: bool = Field(alias="objectsFlashToTheBeat")
    use_hitcircle_color: bool = Field(alias="useHitCircleColor")
    seizure_warning: bool = Field(alias="seizureWarning")
    load_storyboard: bool = Field(alias="loadStoryboard")
    load_video: bool = Field(alias="loadVideo")
    intro_bg_dim: float = Field(alias="introBGDim")
    ingame_bg_dim: float = Field(alias="inGameBGDim")
    break_bg_dim: float = Field(alias="breakBGDim")
    bg_parallax: bool = Field(alias="BGParallax")
    show_danser_logo: bool = Field(alias="showDanserLogo")
    motion_blur: bool = Field(alias="motionBlur960fps")
    skip_intro: bool = Field(alias="skip")
    cursor_ripples: bool = Field(alias="cursorRipples")
    slider_snaking_in: bool = Field(alias="sliderSnakingIn")
    slider_snaking_out: bool = Field(alias="sliderSnakingOut")
    is_verified: bool = Field(alias="isVerified")
    is_bot: bool = Field(alias="isBot")
    render_start_time: datetime = Field(alias="renderStartTime")
    render_end_time: datetime = Field(alias="renderEndTime")
    upload_end_time: datetime = Field(alias="uploadEndTime")
    render_total_time: int = Field(alias="renderTotalTime")
    upload_total_time: int = Field(alias="uploadTotalTime")
    map_length: int = Field(alias="mapLength")
    replay_mods: Mods = Field(alias="replayMods")
    show_hit_counter: bool = Field(alias="showHitCounter")
    removed: bool
    show_aim_error_meter: bool = Field(alias="showAimErrorMeter")
    show_avatars_on_scoreboard: bool = Field(alias="showAvatarsOnScoreboard")
    play_nightcore_samples: bool = Field(alias="playNightcoreSamples")
    use_skin_hitsounds: bool = Field(alias="useSkinHitsounds")


class RendersResponse(BaseModel):
    renders: list[Render]
    max_renders: int = Field(alias="maxRenders")


class RenderCreateResponse(BaseModel):
    message: str
    render_id: int = Field(alias="renderID")
