"""This module contains the client for interfacing with the o!rdr API."""
from __future__ import annotations

from typing import Literal
from typing import TYPE_CHECKING
from warnings import warn

import aiohttp
import orjson
from aiolimiter import AsyncLimiter

from .models import RenderCreateResponse
from .models import RenderServer
from .models import RendersResponse
from .models import SkinCompact
from .models import SkinsResponse
from aiosu.exceptions import APIException
from aiosu.helpers import add_param
from aiosu.helpers import from_list

if TYPE_CHECKING:
    from types import TracebackType
    from typing import Any
    from typing import Type
    from typing import Union
    from typing import Optional
    from typing import Callable

try:
    from socketio import AsyncClient as sio_async
except ImportError:
    raise ImportError(
        "You must install the library with the 'ordr' extra in order to use this module.",
    )

__all__ = ("ordrClient",)

ClientRequestType = Literal["GET", "POST", "DELETE", "PUT", "PATCH"]


def get_content_type(content_type: str) -> str:
    """Returns the content type."""
    return content_type.split(";")[0]


DeveloperModes = Literal["devmode_success", "devmode_fail", "devmode_wsfail"]


class ordrClient:
    def __init__(self, **kwargs: Any) -> None:
        self._developer_mode: Optional[str] = kwargs.pop("developer_mode", None)
        self._verification_key: Optional[str] = kwargs.pop("verification_key", None)

        if self._developer_mode:
            if self._verification_key:
                warn(
                    "You are running in developer mode. This means that your requests will be simulated and your verification key will not be used.",
                )
            self._verification_key = self._developer_mode

        self._session: Optional[aiohttp.ClientSession] = None
        self._base_url: str = "https://apis.issou.best"
        self._websocket_url: str = "https://ordr-ws.issou.best"

        max_rate, time_period = kwargs.pop("limiter", (1, 300))
        if (max_rate / time_period) > (10 / 60):
            warn(
                "You are running at an insanely high rate limit. Doing so may result in your account being banned.",
            )
        self._limiter: AsyncLimiter = AsyncLimiter(
            max_rate=max_rate,
            time_period=time_period,
        )

        self.socket = sio_async()

    def on_render_added(self) -> Callable:
        r"""Returns a callable that is called when a render is added, to be used as:
        @client.on_render_added()
        async def render_added(data: dict):

        You can view the data here:
        https://ordr.issou.best/docs/#section/Websocket
        """
        return self.socket.on("render_added_json")

    def on_render_progress(self) -> Callable:
        r"""Returns a callable that is called when a render is updated, to be used as:
        @client.on_render_progress()
        async def render_progress(data: dict):

        You can view the data here:
        https://ordr.issou.best/docs/#section/Websocket
        """
        return self.socket.on("render_progress_json")

    def on_render_fail(self) -> Callable:
        r"""Returns a callable that is called when a render fails, to be used as:
        @client.on_render_fail()
        async def render_fail(data: dict):

        You can view the data here:
        https://ordr.issou.best/docs/#section/Websocket
        """
        return self.socket.on("render_failed_json")

    async def on_render_finish(self) -> Callable:
        r"""Returns a callable that is called when a render finishes, to be used as:
        @client.on_render_finish()
        async def render_finish(data: dict):

        You can view the data here:
        https://ordr.issou.best/docs/#section/Websocket
        """
        return self.socket.on("render_done_json")

    async def __aenter__(self) -> ordrClient:
        await self.connect()
        return self

    async def __aexit__(
        self,
        exc_type: Optional[Type[BaseException]],
        exc: Optional[BaseException],
        traceback: Optional[TracebackType],
    ) -> None:
        await self.close()

    async def _request(
        self, request_type: ClientRequestType, *args: Any, **kwargs: Any
    ) -> Any:
        if not self.socket.connected:
            await self.connect()
        if self._session is None:
            self._session = aiohttp.ClientSession()

        req: dict[str, Callable] = {
            "GET": self._session.get,
            "POST": self._session.post,
            "DELETE": self._session.delete,
            "PUT": self._session.put,
            "PATCH": self._session.patch,
        }

        async with self._limiter:
            async with req[request_type](*args, **kwargs) as resp:
                body = await resp.read()
                content_type = get_content_type(resp.headers.get("content-type", ""))
                if resp.status not in (200, 201):
                    json = orjson.loads(body)
                    raise APIException(resp.status, json.get("message", ""))
                if content_type == "application/json":
                    return orjson.loads(body)
                if content_type == "text/html":
                    return body.decode("utf-8")
                raise APIException(415, "Unhandled Content Type")

    async def get_skin(self, skin_id: int) -> SkinCompact:
        r"""Get custom skin information.

        :param skin_id: Skin ID
        :type skin_id: ``int``
        :raises: ``aiosu.exceptions.APIException``
        :return: Skin information
        :rtype: ``aiosu.utils.ordr.models.skin.SkinCompact``
        """
        params = {"id": skin_id}
        resp = await self._request(
            "GET",
            f"{self._base_url}/ordr/skins/custom",
            params=params,
        )
        return SkinCompact(**resp)

    async def get_skins(
        self, page: int = 1, page_size=5, **kwargs: Any
    ) -> SkinsResponse:
        r"""Get custom skins.

        :param page: Page number
        :type page: ``int``
        :param page_size: Page size
        :type page_size: ``int``
        :param \**kwargs:
            See below

        :Keyword Arguments:
            * *search* (``str``) --
                Optional, search query

        :raises: ``aiosu.exceptions.APIException``
        :return: Skins
        :rtype: ``aiosu.utils.ordr.models.skins.SkinsResponse``
        """
        params = {
            "page": page,
            "pageSize": page_size,
        }
        add_param(params, kwargs, "search")
        resp = await self._request(
            "GET",
            f"{self._base_url}/ordr/skins",
            params=params,
        )
        return SkinsResponse(**resp)

    async def get_render_list(
        self, page: int = 1, page_size=5, **kwargs: Any
    ) -> RendersResponse:
        r"""Get render list.

        :param page: Page number
        :type page: ``int``
        :param page_size: Page size
        :type page_size: ``int``
        :param \**kwargs:
            See below

        :Keyword Arguments:
            * *ordr_username* (``str``) --
                Optional, username of the user who ordered the render
            * *replay_username* (``str``) --
                Optional, username of the user from the replay
            * *render_id* (``int``) --
                Optional, ID of the render
            * *no_bots* (``bool``) --
                Optional, whether to exclude bot renders
            * *link* (``str``) --
                Optional, the path of a shortlink (e.g. pov8n for https://link.issou.best/pov8n)
            * *beatmapset_id* (``int``) --
                Optional, ID of the beatmapset

        :raises: ``aiosu.exceptions.APIException``
        :return: Renders
        :rtype: ``aiosu.utils.ordr.models.renders.RendersResponse``
        """
        params = {
            "page": page,
            "pageSize": page_size,
        }
        add_param(params, kwargs, "ordr_username", "ordrUsername")
        add_param(params, kwargs, "replay_username", "replayUsername")
        add_param(params, kwargs, "render_id", "renderID")
        add_param(params, kwargs, "no_bots", "nobots")
        add_param(params, kwargs, "link")
        add_param(params, kwargs, "beatmapset_id", "beatmapsetid")
        resp = await self._request(
            "GET",
            f"{self._base_url}/ordr/renders",
        )
        return RendersResponse(**resp)

    async def get_server_list(self) -> list[RenderServer]:
        r"""Get the list of available servers.


        :raises: ``aiosu.exceptions.APIException``
        :return: List of servers
        :rtype: ``list[aiosu.utils.ordr.models.server.RenderServer]``
        """
        resp = await self._request(
            "GET",
            f"{self._base_url}/servers",
        )
        return from_list(RenderServer, resp.get("servers", []))

    async def get_server_online_count(self) -> int:
        r"""Get the number of online servers.


        :raises: ``aiosu.exceptions.APIException``
        :return: Number of online servers
        :rtype: ``int``
        """
        resp = await self._request(
            "GET",
            f"{self._base_url}/servers/onlinecount",
        )
        try:
            return int(resp)
        except:
            return 0

    async def create_render(
        self, username: str, skin: Union[str, int], **kwargs: Any
    ) -> RenderCreateResponse:
        r"""Create a render.

        :param username: Username of the user who ordered the render
        :type username: ``str``
        :param skin: Skin ID or name
        :type skin: ``Union[str, int]``
        :param \**kwargs:
            See below

        :Keyword Arguments:
            * *replay_file* (``str``) --
                Optional, replay file
            * *replay_url* (``str``) --
                Optional, replay URL, used if replay_file is not provided
            * *global_volume* (``int``) --
                Optional, global volume (0-100) (default: 50)
            * *music_volume* (``int``) --
                Optional, music volume (0-100) (default: 50)
            * *hitsound_volume* (``int``) --
                Optional, hitsound volume (0-100) (default: 50)
            * *show_hit_error_meter* (``bool``) --
                Optional, whether to show hit error meter (default: true)
            * *show_unstable_rate* (``bool``) --
                Optional, whether to show unstable rate (default: true)
            * *show_score* (``bool``) --
                Optional, whether to show score (default: true)
            * *show_hp_bar* (``bool``) --
                Optional, whether to show HP bar (default: true)
            * *show_combo_counter* (``bool``) --
                Optional, whether to show combo counter (default: true)
            * *show_pp_counter* (``bool``) --
                Optional, whether to show PP counter (default: true)
            * *show_scoreboard* (``bool``) --
                Optional, whether to show scoreboard (default: false)
            * *show_borders* (``bool``) --
                Optional, whether to show playfield borders (default: false)
            * *show_mods* (``bool``) --
                Optional, whether to show mod icons (default: true)
            * *show_result_screen* (``bool``) --
                Optional, whether to show result screen (default: true)
            * *use_skin_cursor* (``bool``) --
                Optional, whether to use skin cursor (default: true)
            * *use_skin_colors* (``bool``) --
                Optional, whether to use skin colors (default: false)
            * *use_skin_hitsounds* (``bool``) --
                Optional, whether to use skin hitsounds (default: true)
            * *use_beatmap_colors* (``bool``) --
                Optional, whether to use beatmap colors (default: true)
            * *cursor_scale_to_cs* (``bool``) --
                Optional, whether to scale cursor size to circle size (default: false)
            * *cursor_rainbow* (``bool``) --
                Optional, whether to use rainbow cursor (default: false)
            * *cursor_trail_glow* (``bool``) --
                Optional, whether to have a glow with the trail (default: false)
            * *draw_follow_points* (``bool``) --
                Optional, whether to draw follow points between objects (default: true)
            * *beat_scaling* (``bool``) --
                Optional, whether to scale objects to the beat (default: false)
            * *slider_merge* (``bool``) --
                Optional, whether to merge sliders (default: false)
            * *objects_rainbow* (``bool``) --
                Optional, whether to use rainbow objects (default: false)
            * *flash_objects* (``bool``) --
                Optional, whether to flash objects to the beat (default: false)
            * *use_slider_hitcircle_colors* (``bool``) --
                Optional, whether sliders should use the hitcircle colors (default: true)
            * *seizure_warning* (``bool``) --
                Optional, whether to show a seizure warning (default: false)
            * *load_video* (``bool``) --
                Optional, whether to load the video (default: true)
            * *load_storyboard* (``bool``) --
                Optional, whether to load the storyboard (default: true)
            * *intro_bg_dim* (``int``) --
                Optional, intro background dim (0-100) (default: 0)
            * *ingame_bg_dim* (``int``) --
                Optional, ingame background dim (0-100) (default:75)
            * *break_bg_dim* (``int``) --
                Optional, break background dim (0-100) (default: 30)
            * *bg_parallax* (``bool``) --
                Optional, whether to use background parallax (default: false)
            * *show_danser_logo* (``bool``) --
                Optional, whether to show danser logo (default: true)
            * *skip_intro* (``bool``) --
                Optional, whether to skip intro (default: true)
            * *cursor_ripples* (``bool``) --
                Optional, whether to show cursor ripples (default: false)
            * *draw_combo_numbers* (``bool``) --
                Optional, whether to draw combo numbers (default: true)
            * *slider_snaking_in* (``bool``) --
                Optional, whether to snake in sliders (default: true)
            * *slider_snaking_out* (``bool``) --
                Optional, whether to snake out sliders (default: true)
            * *show_hit_counter* (``bool``) --
                Optional, whether to show hit counter (100, 50, miss) below the PP counter (default: false)
            * *show_key_overlay* (``bool``) --
                Optional, whether to show key overlay (default: true)
            * *show_avatars* (``bool``) --
                Optional, whether to show avatars on scoreboard. May break some skins (default: true)
            * *show_aim_error_meter* (``bool``) --
                Optional, whether to show aim error meter (default: false)
            * *play_nightcore_samples* (``bool``) --
                Optional, whether to play nightcore samples (default: true)
            * *custom_skin* (``bool``) --
                Optional, whether the provided skin is a custom skin ID (default: false)

        :raises: ``aiosu.exceptions.APIException``
        :return: Render create response
        :rtype: ``aiosu.utils.ordr.models.render.RenderCreateResponse``
        """

        headers = {
            "Content-Type": "multipart/form-data",
        }
        data = {
            "username": username,
            "skin": skin,
            "resolution": "1280x720",
        }
        if self._verification_key:
            data["verificationKey"] = self._verification_key
        add_param(data, kwargs, "replay_file", "replayFile")
        add_param(data, kwargs, "replay_url", "replayURL")
        if "replay_file" not in data and "replay_url" not in data:
            raise ValueError("Either replay_file or replay_url must be provided")
        add_param(data, kwargs, "global_volume", "globalVolume")
        add_param(data, kwargs, "music_volume", "musicVolume")
        add_param(data, kwargs, "hitsound_volume", "hitsoundVolume")
        add_param(data, kwargs, "show_hit_error_meter", "showHitErrorMeter")
        add_param(data, kwargs, "show_unstable_rate", "showUnstableRate")
        add_param(data, kwargs, "show_score", "showScore")
        add_param(data, kwargs, "show_hp_bar", "showHPBar")
        add_param(data, kwargs, "show_combo_counter", "showComboCounter")
        add_param(data, kwargs, "show_pp_counter", "showPPCounter")
        add_param(data, kwargs, "show_scoreboard", "showScoreboard")
        add_param(data, kwargs, "show_borders", "showBorders")
        add_param(data, kwargs, "show_mods", "showMods")
        add_param(data, kwargs, "show_result_screen", "showResultScreen")
        add_param(data, kwargs, "use_skin_cursor", "useSkinCursor")
        add_param(data, kwargs, "use_skin_colors", "useSkinColors")
        add_param(data, kwargs, "use_skin_hitsounds", "useSkinHitsounds")
        add_param(data, kwargs, "use_beatmap_colors", "useBeatmapColors")
        add_param(data, kwargs, "cursor_scale_to_cs", "cursorScaleToCS")
        add_param(data, kwargs, "cursor_rainbow", "cursorRainbow")
        add_param(data, kwargs, "cursor_trail_glow", "cursorTrailGlow")
        add_param(data, kwargs, "draw_follow_points", "drawFollowPoints")
        add_param(data, kwargs, "beat_scaling", "scaleToTheBeat")
        add_param(data, kwargs, "slider_merge", "sliderMerge")
        add_param(data, kwargs, "objects_rainbow", "objectsRainbow")
        add_param(data, kwargs, "flash_objects", "objectsFlashToTheBeat")
        add_param(data, kwargs, "use_slider_hitcircle_colors", "useHitCircleColor")
        add_param(data, kwargs, "seizure_warning", "seizureWarning")
        add_param(data, kwargs, "load_storyboard", "loadStoryboard")
        add_param(data, kwargs, "load_video", "loadVideo")
        add_param(data, kwargs, "intro_bg_dim", "introBGDim")
        add_param(data, kwargs, "ingame_bg_dim", "ingameBGDim")
        add_param(data, kwargs, "break_bg_dim", "breakBGDim")
        add_param(data, kwargs, "bg_parallax", "BGParallax")
        add_param(data, kwargs, "show_danser_logo", "showDanserLogo")
        add_param(data, kwargs, "skip_intro", "skip")
        add_param(data, kwargs, "cursor_ripples", "cursorRipples")
        add_param(data, kwargs, "cursor_trail", "cursorTrail")
        add_param(data, kwargs, "cursor_size", "cursorSize")
        add_param(data, kwargs, "draw_combo_numbers", "drawComboNumbers")
        add_param(data, kwargs, "slider_snaking_in", "sliderSnakingIn")
        add_param(data, kwargs, "slider_snaking_out", "sliderSnakingOut")
        add_param(data, kwargs, "show_hit_counter", "showHitCounter")
        add_param(data, kwargs, "show_key_overlay", "showKeyOverlay")
        add_param(data, kwargs, "show_avatars", "showAvatarsOnScoreboard")
        add_param(data, kwargs, "show_aim_error_meter", "showAimErrorMeter")
        add_param(data, kwargs, "play_nightcore_samples", "playNightcoreSamples")
        add_param(data, kwargs, "custom_skin", "customSkin")
        resp = await self._request(
            "POST",
            f"{self._base_url}/ordr/renders",
            headers=headers,
            data=data,
        )
        return RenderCreateResponse(**resp)

    async def connect(self) -> None:
        r"""Connects to the websocket server.

        :return: None
        """
        await self.socket.connect(url=self._websocket_url)

    async def close(self) -> None:
        r"""Closes the client.

        :return: None
        """
        if self._session is not None:
            await self._session.close()
        await self.socket.close()
