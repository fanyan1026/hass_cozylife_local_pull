"""Async UDP discovery for CozyLife devices."""
from __future__ import annotations

import asyncio
import socket
import logging
from typing import List

from .utils import get_sn

_LOGGER = logging.getLogger(__name__)


async def async_discover_devices() -> List[str]:
    """
    Async discover CozyLife devices via UDP broadcast.
    :return: list of device IP addresses
    """
    # 创建 UDP socket
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
    sock.settimeout(0.5)  # 增加超时时间以捕获更多响应
    
    message = '{"cmd":0,"pv":0,"sn":"' + get_sn() + '","msg":{}}'
    message_bytes = message.encode('utf-8')
    
    discovered_ips = []
    
    try:
        # 发送广播包
        for _ in range(3):
            sock.sendto(message_bytes, ('255.255.255.255', 6095))
            await asyncio.sleep(0.1)
        
        # 接收响应
        while True:
            try:
                data, addr = sock.recvfrom(1024)
                ip_address = addr[0]
                if ip_address not in discovered_ips:
                    discovered_ips.append(ip_address)
                    _LOGGER.info(f"Discovered device: {ip_address}")
            except socket.timeout:
                break  # 超时，没有更多设备
            except Exception as exc:
                _LOGGER.debug(f"Error receiving UDP response: {exc}")
                break
                
    except Exception as exc:
        _LOGGER.error(f"UDP discovery failed: {exc}")
    finally:
        sock.close()
    
    _LOGGER.info(f"Discovery completed, found {len(discovered_ips)} devices")
    return discovered_ips