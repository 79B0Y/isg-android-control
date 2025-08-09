"""
网络控制API路由
"""

from fastapi import APIRouter, HTTPException
from loguru import logger

from src.core.adb_controller import get_adb_controller
from src.models.requests import NetworkConfigRequest
from src.models.responses import BaseResponse, ResponseStatus, NetworkStatus

router = APIRouter()


@router.post("/static")
async def set_static_ip(request: NetworkConfigRequest):
    """
    设置静态IP配置
    
    - **ip_address**: 静态IP地址
    - **netmask**: 子网掩码 (默认: 255.255.255.0)
    - **gateway**: 网关地址
    - **dns_primary**: 主DNS服务器 (默认: 8.8.8.8)
    - **dns_secondary**: 备用DNS服务器 (默认: 8.8.4.4)
    - **interface**: 网络接口 (默认: wlan0)
    """
    try:
        adb = get_adb_controller()
        
        # 设置静态IP
        ip_cmd = f"ip addr add {request.ip_address}/24 dev {request.interface}"
        result = await adb.execute(ip_cmd)
        
        if not result.success:
            raise HTTPException(
                status_code=500,
                detail=f"Failed to set IP address: {result.error}"
            )
        
        # 设置网关
        gateway_cmd = f"ip route add default via {request.gateway}"
        result = await adb.execute(gateway_cmd)
        
        if not result.success:
            logger.warning(f"Failed to set gateway: {result.error}")
        
        # 设置DNS
        dns1_cmd = f"setprop net.dns1 {request.dns_primary}"
        dns2_cmd = f"setprop net.dns2 {request.dns_secondary}"
        
        await adb.execute(dns1_cmd)
        await adb.execute(dns2_cmd)
        
        return BaseResponse(
            status=ResponseStatus.SUCCESS,
            message="Static IP configuration applied",
            data={
                "ip_address": request.ip_address,
                "netmask": request.netmask,
                "gateway": request.gateway,
                "dns_primary": request.dns_primary,
                "dns_secondary": request.dns_secondary,
                "interface": request.interface
            }
        )
        
    except Exception as e:
        logger.error(f"Set static IP API error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/dhcp")
async def enable_dhcp(interface: str = "wlan0"):
    """
    启用DHCP自动获取IP
    
    - **interface**: 网络接口 (默认: wlan0)
    """
    try:
        adb = get_adb_controller()
        
        # 清除静态IP配置
        flush_cmd = f"ip addr flush dev {interface}"
        result = await adb.execute(flush_cmd)
        
        # 重启网络接口
        disable_cmd = f"svc wifi disable"
        enable_cmd = f"svc wifi enable"
        
        await adb.execute(disable_cmd)
        await asyncio.sleep(2)  # 等待网络关闭
        await adb.execute(enable_cmd)
        
        return BaseResponse(
            status=ResponseStatus.SUCCESS,
            message="DHCP enabled, network restarted",
            data={"interface": interface, "dhcp_enabled": True}
        )
        
    except Exception as e:
        logger.error(f"Enable DHCP API error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/status", response_model=BaseResponse[NetworkStatus])
async def get_network_status(interface: str = "wlan0"):
    """
    获取网络状态信息
    
    - **interface**: 网络接口 (默认: wlan0)
    """
    try:
        adb = get_adb_controller()
        
        # 获取IP地址
        ip_result = await adb.execute(f"ip addr show {interface}")
        
        ip_address = None
        netmask = None
        if ip_result.success:
            lines = ip_result.output.split('\n')
            for line in lines:
                if 'inet ' in line and 'scope global' in line:
                    # 提取IP地址和子网掩码
                    import re
                    match = re.search(r'inet (\d+\.\d+\.\d+\.\d+)/(\d+)', line)
                    if match:
                        ip_address = match.group(1)
                        cidr = int(match.group(2))
                        # 简单的CIDR到子网掩码转换
                        mask_bits = (0xffffffff >> (32 - cidr)) << (32 - cidr)
                        netmask = f"{(mask_bits >> 24) & 0xff}.{(mask_bits >> 16) & 0xff}.{(mask_bits >> 8) & 0xff}.{mask_bits & 0xff}"
                    break
        
        # 获取网关
        gateway_result = await adb.execute("ip route show default")
        gateway = None
        if gateway_result.success:
            import re
            match = re.search(r'default via (\d+\.\d+\.\d+\.\d+)', gateway_result.output)
            if match:
                gateway = match.group(1)
        
        # 获取DNS服务器
        dns_servers = []
        dns1_result = await adb.execute("getprop net.dns1")
        dns2_result = await adb.execute("getprop net.dns2")
        
        if dns1_result.success and dns1_result.output.strip():
            dns_servers.append(dns1_result.output.strip())
        if dns2_result.success and dns2_result.output.strip():
            dns_servers.append(dns2_result.output.strip())
        
        # 检查连接状态
        ping_result = await adb.execute("ping -c 1 8.8.8.8")
        is_connected = ping_result.success
        
        # 获取网络统计
        stats_result = await adb.execute(f"cat /proc/net/dev | grep {interface}")
        bytes_sent = bytes_received = 0
        if stats_result.success:
            parts = stats_result.output.split()
            if len(parts) >= 10:
                try:
                    bytes_received = int(parts[1])
                    bytes_sent = int(parts[9])
                except ValueError:
                    pass
        
        # 获取WiFi信号强度
        signal_result = await adb.execute("dumpsys wifi | grep 'RSSI'")
        signal_strength = None
        if signal_result.success:
            import re
            match = re.search(r'RSSI: (-?\d+)', signal_result.output)
            if match:
                signal_strength = int(match.group(1))
        
        network_status = NetworkStatus(
            interface=interface,
            ip_address=ip_address,
            netmask=netmask,
            gateway=gateway,
            dns_servers=dns_servers,
            is_connected=is_connected,
            connection_type="wifi" if interface.startswith("wlan") else "ethernet",
            signal_strength=signal_strength,
            bytes_sent=bytes_sent,
            bytes_received=bytes_received
        )
        
        return BaseResponse(
            status=ResponseStatus.SUCCESS,
            message="Network status retrieved",
            data=network_status
        )
        
    except Exception as e:
        logger.error(f"Get network status API error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/test")
async def test_network_connectivity(host: str = "8.8.8.8", count: int = 3):
    """
    测试网络连通性
    
    - **host**: 测试主机 (默认: 8.8.8.8)
    - **count**: ping次数 (默认: 3)
    """
    try:
        adb = get_adb_controller()
        
        # 执行ping测试
        ping_cmd = f"ping -c {count} {host}"
        result = await adb.execute(ping_cmd, timeout=count + 5)
        
        if result.success:
            # 解析ping结果
            lines = result.output.split('\n')
            
            # 提取统计信息
            stats_line = None
            for line in lines:
                if 'packet loss' in line:
                    stats_line = line
                    break
            
            # 提取RTT信息
            rtt_line = None
            for line in lines:
                if 'min/avg/max' in line:
                    rtt_line = line
                    break
            
            test_result = {
                "host": host,
                "count": count,
                "success": True,
                "output": result.output,
                "packet_loss": None,
                "avg_rtt": None
            }
            
            if stats_line:
                import re
                loss_match = re.search(r'(\d+)% packet loss', stats_line)
                if loss_match:
                    test_result["packet_loss"] = int(loss_match.group(1))
            
            if rtt_line:
                import re
                rtt_match = re.search(r'= [\d.]+/([\d.]+)/[\d.]+', rtt_line)
                if rtt_match:
                    test_result["avg_rtt"] = float(rtt_match.group(1))
            
            return BaseResponse(
                status=ResponseStatus.SUCCESS,
                message="Network connectivity test completed",
                data=test_result
            )
        else:
            return BaseResponse(
                status=ResponseStatus.WARNING,
                message="Network connectivity test failed",
                data={
                    "host": host,
                    "count": count,
                    "success": False,
                    "error": result.error
                }
            )
        
    except Exception as e:
        logger.error(f"Network test API error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/interfaces")
async def get_network_interfaces():
    """获取网络接口列表"""
    try:
        adb = get_adb_controller()
        
        # 获取网络接口信息
        result = await adb.execute("ip link show")
        
        interfaces = []
        if result.success:
            lines = result.output.split('\n')
            for line in lines:
                if ': ' in line and 'state' in line.upper():
                    # 解析接口信息
                    parts = line.split(':')
                    if len(parts) >= 2:
                        interface_name = parts[1].strip().split('@')[0]  # 移除@后的部分
                        
                        # 获取接口状态
                        is_up = 'UP' in line.upper()
                        
                        interfaces.append({
                            "name": interface_name,
                            "state": "UP" if is_up else "DOWN",
                            "description": line.strip()
                        })
        
        return BaseResponse(
            status=ResponseStatus.SUCCESS,
            message=f"Found {len(interfaces)} network interfaces",
            data=interfaces
        )
        
    except Exception as e:
        logger.error(f"Get network interfaces API error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/restart")
async def restart_network(interface: str = "wlan0"):
    """
    重启网络接口
    
    - **interface**: 网络接口 (默认: wlan0)
    """
    try:
        import asyncio
        adb = get_adb_controller()
        
        # 关闭网络接口
        if interface.startswith("wlan"):
            disable_cmd = "svc wifi disable"
            enable_cmd = "svc wifi enable"
        else:
            disable_cmd = f"ip link set {interface} down"
            enable_cmd = f"ip link set {interface} up"
        
        # 执行重启
        result1 = await adb.execute(disable_cmd)
        await asyncio.sleep(2)  # 等待网络关闭
        result2 = await adb.execute(enable_cmd)
        
        success = result1.success and result2.success
        
        return BaseResponse(
            status=ResponseStatus.SUCCESS if success else ResponseStatus.WARNING,
            message=f"Network interface {interface} restart {'completed' if success else 'attempted'}",
            data={
                "interface": interface,
                "disable_success": result1.success,
                "enable_success": result2.success
            }
        )
        
    except Exception as e:
        logger.error(f"Restart network API error: {e}")
        raise HTTPException(status_code=500, detail=str(e))