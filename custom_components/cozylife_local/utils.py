"""Async utilities for CozyLife device information."""
from __future__ import annotations

import asyncio
import json
import logging
from functools import lru_cache
from typing import Any

import aiohttp

from .const import API_DOMAIN, LANG

_LOGGER = logging.getLogger(__name__)


@lru_cache(maxsize=None)
async def async_get_pid_list(lang: str = LANG) -> list:
    """
    Async non-blocking fetch of product ID list from API with caching
    Reference: http://doc.doit/project-12/doc-95/
    """
    # Validate language parameter
    supported_langs = {'zh', 'en', 'es', 'pt', 'ja', 'ru', 'nl', 'ko', 'fr', 'de'}
    if lang not in supported_langs:
        _LOGGER.warning(f'Unsupported language {lang}, falling back to default {LANG}')
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
                        _LOGGER.error(f"API returned error: {data}")
                        return []
                else:
                    _LOGGER.error(f"API request failed with status: {response.status}")
                    return []
    except Exception as exc:
        _LOGGER.error(f"Failed to fetch PID list: {exc}")
        return []


def get_sn() -> str:
    """
    message sn
    :return: str
    """
    import time
    return str(int(round(time.time() * 1000)))


# 保持同步版本用于向后兼容
def get_pid_list(lang='en') -> list:
    """
    Sync version for backward compatibility
    """
    import asyncio
    try:
        # 如果在事件循环中运行，使用嵌套事件循环
        loop = asyncio.get_event_loop()
        if loop.is_running():
            # 如果事件循环正在运行，创建一个新的事件循环
            new_loop = asyncio.new_event_loop()
            asyncio.set_event_loop(new_loop)
            try:
                result = new_loop.run_until_complete(async_get_pid_list(lang))
                return result
            finally:
                new_loop.close()
                asyncio.set_event_loop(loop)
        else:
            return loop.run_until_complete(async_get_pid_list(lang))
    except RuntimeError:
        # 如果没有事件循环，创建一个
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            return loop.run_until_complete(async_get_pid_list(lang))
        finally:
            loop.close()