"""Async utilities for CozyLife device information."""
from __future__ import annotations

import asyncio
import json
import logging
from typing import Any

import aiohttp

from .const import API_DOMAIN, LANG

_LOGGER = logging.getLogger(__name__)


async def async_get_pid_list(lang: str = LANG) -> list:
    """
    Async non-blocking fetch of product ID list from API
    Reference: http://doc.doit/project-12/doc-95/
    """
    # Validate language parameter
    supported_langs = {'zh', 'en', 'es', 'pt', 'ja', 'ru', 'nl', 'ko', 'fr', 'de'}
    if lang not in supported_langs:
        _LOGGER.warning('Unsupported language %s, falling back to default %s', lang, LANG)
        lang = LANG

    url = f'http://{API_DOMAIN}/api/v2/device_product/model'
    params = {'lang': lang}

    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, params=params, timeout=30) as response:
                if response.status == 200:
                    data = await response.json()
                    if data.get('ret') == '1':
                        return data.get('info', {}).get('list', [])
                    else:
                        _LOGGER.error("API returned error: %s", data)
                        return []
                else:
                    _LOGGER.error("API request failed with status: %s", response.status)
                    return []
    except Exception as exc:
        _LOGGER.error("Failed to fetch PID list: %s", exc)
        return []


def get_sn() -> str:
    """
    message sn
    :return: str
    """
    import time
    return str(int(round(time.time() * 1000)))


# 同步版本 - 使用事件循环运行异步函数
def get_pid_list(lang='en') -> list:
    """
    Sync version for backward compatibility
    """
    try:
        # 尝试在现有事件循环中运行
        loop = asyncio.get_event_loop()
        if loop.is_running():
            # 如果事件循环正在运行，创建新任务
            future = asyncio.run_coroutine_threadsafe(async_get_pid_list(lang), loop)
            return future.result(timeout=30)
        else:
            # 如果事件循环未运行，直接运行
            return loop.run_until_complete(async_get_pid_list(lang))
    except RuntimeError:
        # 如果没有事件循环，创建一个
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            return loop.run_until_complete(async_get_pid_list(lang))
        finally:
            loop.close()