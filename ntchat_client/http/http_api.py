"""http_api调用
"""
from fastapi import APIRouter, Body, Response
from pydantic.error_wrappers import ValidationError

from ntchat_client.model import HttpRequest, HttpResponse
from ntchat_client.wechat import get_wechat_client

router = APIRouter()


@router.post("/{action}", response_model=HttpResponse)
async def _(action: str, response: Response, params=Body(None)) -> None:
    """处理api调用"""
    # 构造请求体
    try:
        http_request = HttpRequest(action=action, params=params)
    except ValidationError:
        return HttpResponse(status=405, msg="请求参数不正确！", data={})
    wechat_client = get_wechat_client()
    res = wechat_client.handle_http_api(http_request)
    self_id = wechat_client.self_id
    access_token = wechat_client.config.access_token
    response.headers["X-self-ID"] = self_id
    response.headers["access_token"] = access_token

    return res