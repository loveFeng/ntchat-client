import asyncio
import time
from asyncio import AbstractEventLoop
from pathlib import Path
from typing import Any, Callable, NoReturn, Optional

import ntchat

from ntchat_client.config import Config
from ntchat_client.log import logger
from ntchat_client.model import (
    HttpRequest,
    HttpResponse,
    Request,
    Response,
    WsRequest,
    WsResponse,
)
from ntchat_client.utils import escape_tag, notify

from .cache import FileCache
from .image_decode import FileDecoder
from .qrcode import draw_qrcode
import os
import signal

wechat_client: "WeChatManager" = None
"""全局微信客户端"""


def get_wechat_client() -> Optional["WeChatManager"]:
    """获取微信客户端"""
    if wechat_client is None:
        return None
    return wechat_client


def wechat_init(config: Config) -> None:
    """微信初始化"""
    global wechat_client
    wechat_client = WeChatManager(config)
    wechat_client.init()


def send_event_loop() -> None:
    """绑定事件循环"""
    global wechat_client
    loop = asyncio.get_running_loop()
    wechat_client.loop = loop


def wechat_shutdown() -> None:
    """关闭微信模块"""
    if wechat_client:
        logger.info("<m>wechat</m> - 正在关闭微信注入...")
        ntchat.exit_()
        logger.success("<m>wechat</m> - <g>微信注入已关闭...</g>")


class WeChatManager:
    """微信封装类"""

    config: Config
    """配置"""
    client: ntchat.WeChat
    """客户端"""
    self_id: str
    """自身id"""
    loop: AbstractEventLoop = None
    """事件循环"""
    ws_message_handler: Callable[..., Any] = None
    """ws消息处理器"""
    http_post_handler: Callable[..., Any] = None
    """http_post处理器"""
    file_cache: FileCache
    """文件缓存管理器"""
    image_decoder: FileDecoder
    """图片解密器"""
    image_timeout: int
    """图片下载超时时间"""
    msg_fiter = {
        ntchat.MT_USER_LOGIN_MSG,
        ntchat.MT_USER_LOGOUT_MSG,
        ntchat.MT_RECV_WECHAT_QUIT_MSG,
        ntchat.MT_RECV_LOGIN_QRCODE_MSG,
    }
    """消息过滤列表"""

    def __new__(cls, *args, **kwargs):
        """单例"""
        if not hasattr(cls, "_instance"):
            cls._instance = super().__new__(
                cls,
            )
        return cls._instance

    def __init__(self, config: Config) -> None:
        self.config = config
        self.file_cache = FileCache(config.cache_path)
        self.image_decoder = FileDecoder(config.image_path)
        self.image_timeout = config.image_timeout
        self.msg_fiter |= config.msg_filter
        ntchat.set_wechat_exe_path(wechat_version="3.6.0.18")

    def init(self) -> None:
        """初始化"""
        self.wechat = ntchat.WeChat()
        logger.info("<m>wechat</m> - 正在hook微信...")
        self.wechat.open(smart=self.config.smart)
        self.wechat.on(ntchat.MT_USER_LOGIN_MSG, self.login)
        self.wechat.on(ntchat.MT_USER_LOGOUT_MSG, self.logout)
        self.wechat.on(ntchat.MT_RECV_WECHAT_QUIT_MSG, self.quit)
        self.wechat.on(ntchat.MT_RECV_LOGIN_QRCODE_MSG, self.login_qrcode)

    def login(self, _: ntchat.WeChat, message: dict) -> None:
        """
        登入hook
        """
        notify.acquire()
        logger.success("<m>wechat</m> - <g>hook微信成功！</g>")
        self.self_id = message["data"]["wxid"]
        self.wechat.on(ntchat.MT_ALL, self.on_message)
        notify.notify_all()
        notify.release()

    def logout(self, _: ntchat.WeChat, message: dict) -> None:
        """
        登出hook
        """
        logger.error("<m>wechat</m> - 检测到微信登出，终止程序...")
        # 获取当前进程的 ID
        current_pid = os.getpid()

        # 向当前进程发送 SIGTERM 信号，请求正常退出
        os.kill(current_pid, signal.SIGTERM)

    def quit(self, _: ntchat.WeChat) -> NoReturn:
        """
        微信退出
        """
        logger.error("<m>wechat</m> - 检测到微信退出，终止程序...")
        # 获取当前进程的 ID
        current_pid = os.getpid()

        # 向当前进程发送 SIGTERM 信号，请求正常退出
        os.kill(current_pid, signal.SIGTERM)

    def login_qrcode(self, _: ntchat.WeChat, message: dict) -> None:
        """
        登录二维码
        """
        # 将二维码显示在终端
        url = message["data"]["code"]
        logger.info("<m>wechat</m> - 检测到登录二维码...")
        draw_qrcode(url)

    def _pre_handle_api(self, action: str, params: Optional[dict] = None) -> dict:
        """
        参数预处理，用于缓存文件操作
        """
        if params is None:
            return

        if action == "send_image" or action == "send_file" or action == "send_video":
            file: str = params.get("file_path")
            params["file_path"] = self.file_cache.handle_file(
                file, self.config.cache_path
            )
        elif action == "send_gif":
            file: str = params.get("file")
            params["file"] = self.file_cache.handle_file(
                file, self.config.cache_path
            )
        return params

    def _handle_api(self, request: Request) -> Response:
        """处理api调用"""
        try:
            params = self._pre_handle_api(request.action, request.params)
        except Exception as e:
            logger.error(f"<m>wechat</m> - 处理参数出错：{str(e)}...")
            return Response(status=500, msg=f"处理参数出错：{str(e)}", data={})

        attr = getattr(self.wechat, request.action, None)
        if not attr:
            # 返回方法不存在错误
            logger.error(f"<m>wechat</m> - 接口不存在：{request.action}")
            return Response(status=404, msg="请求接口不存在！", data={})
        else:
            try:
                logger.debug(
                    f"<m>wechat</m> - <g>调用接口：</g>{request.action}，参数：{params}"
                )
                if params is None:
                    result = attr()
                else:
                    result = attr(**params)
                if (
                    isinstance(result, bool)
                    or isinstance(result, dict)
                    or isinstance(result, list)
                    or isinstance(result, str)
                ):
                    response = Response(status=200, msg="调用成功", data=result)
                else:
                    response = Response(status=204, msg="调用成功，但没有返回结果", data={})
            except Exception as e:
                response = Response(status=405, msg=f"调用出错{str(e)}", data={})
        return response

    def handle_http_api(self, request: HttpRequest) -> HttpResponse:
        """处理http的api调用"""
        request = Request(action=request.action, params=request.params)
        response = self._handle_api(request)
        return HttpResponse(
            status=response.status, msg=response.msg, data=response.data
        )

    def handle_ws_api(self, request: WsRequest) -> WsRequest:
        """处理ws的api调用"""
        echo = request.echo
        request = Request(action=request.action, params=request.params)
        response = self._handle_api(request)
        return WsResponse(
            echo=echo, status=response.status, msg=response.msg, data=response.data
        )

    def _handle_image(self, message: dict) -> Optional[dict]:
        """处理图片消息，并替换字段，如果超时将会返回None"""
        data: dict = message["data"]
        image_file = Path(data["image"])
        image_thumb = Path(data["image_thumb"])
        time_count = 0
        while True:
            if image_file.exists() and image_thumb.exists():
                break
            time_count += 1
            if time_count > self.image_timeout:
                return None
            time.sleep(1)
        data["image"] = self.image_decoder.decode_file(image_file, False)
        data["image_thumb"] = self.image_decoder.decode_file(image_thumb, True)
        return message

    def on_message(self, _: ntchat.WeChat, message: dict) -> None:
        """接收消息"""
        # 过滤事件
        msgtype = message["type"]
        if msgtype in self.msg_fiter:
            return
        wx_id = message["data"].get("from_wxid")
        if wx_id == self.self_id and not self.config.report_self:
            return
        logger.success(f"<m>wechat</m> - <g>收到wechat消息：</g>{escape_tag(str(message))}")
        if msgtype == 11047:
            # 群图片消息，预处理
            logger.debug("正在解密图片地址...")
            message = self._handle_image(message)
            if message is None:
                if self.config.timeout_image_send:
                    logger.debug("下载图片超时，本次消息原样发送...")
                else:
                    logger.error("下载图片超时，本次消息不会发送...")
                    return
            else:
                logger.debug("解密图片已保存...")

        if self.loop is not None:
            if self.loop.is_running:
                if self.ws_message_handler:
                    asyncio.run_coroutine_threadsafe(
                        self.ws_message_handler(message), self.loop
                    )
                if self.http_post_handler:
                    asyncio.run_coroutine_threadsafe(
                        self.http_post_handler(message), self.loop
                    )
