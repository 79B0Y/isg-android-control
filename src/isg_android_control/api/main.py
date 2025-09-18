from __future__ import annotations

from pathlib import Path
from typing import Optional

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import yaml

from ..core.adb import ADBController
from ..models.config import Settings, CONFIG_DIR
from ..services.monitor import MonitorService
from ..services.screenshot import ScreenshotService
from ..services.cache import Cache
from ..mqtt.state import get_ha


def create_app() -> FastAPI:
    settings = Settings.load()
    adb = ADBController(
        host=settings.device.adb_host,
        port=settings.device.adb_port,
        serial=settings.device.adb_serial,
        has_battery=settings.device.has_battery,
        has_cellular=settings.device.has_cellular,
    )
    monitor = MonitorService(adb)
    shots = ScreenshotService(
        adb, Path.cwd() / settings.device.screenshots_dir, keep=settings.device.screenshot_keep
    )
    cache = Cache()

    app = FastAPI(title="ISG Android Controller API")
    app.state.settings = settings
    app.state.adb = adb
    app.state.monitor = monitor
    app.state.shots = shots
    app.state.cache = cache

    @app.on_event("startup")
    async def _startup() -> None:
        # Note: ADB now uses on-demand connection, no need to connect at startup

        # Proactively warm up cache (switch to memory if Redis is unreachable)
        try:
            await cache.warmup()
        except Exception:
            pass

        # Start Termux performance monitoring
        try:
            await monitor.start_performance_monitoring()
        except Exception:
            pass

        # Start ISG app watchdog
        try:
            await monitor.start_app_watchdog()
        except Exception:
            pass

        # Start CEC controller
        try:
            await monitor.start_cec_controller()
        except Exception:
            pass

    @app.on_event("shutdown")
    async def _shutdown() -> None:
        await cache.close()
        # Stop performance monitoring
        try:
            await monitor.stop_performance_monitoring()
        except Exception:
            pass
        # Stop app watchdog
        try:
            await monitor.stop_app_watchdog()
        except Exception:
            pass
        # Stop CEC controller
        try:
            await monitor.stop_cec_controller()
        except Exception:
            pass
        # Disconnect ADB
        try:
            await adb.disconnect()
        except Exception:
            pass

    @app.get("/health")
    async def health() -> dict:
        return {"ok": True}

    @app.post("/nav/{action}")
    async def nav(action: str) -> dict:
        await adb.nav(action)
        return {"status": "ok"}

    @app.post("/volume/{direction}")
    async def volume(direction: str) -> dict:
        await adb.volume(direction)
        return {"status": "ok"}

    @app.post("/brightness")
    async def brightness(value: int) -> dict:
        await adb.set_brightness(value)
        return {"status": "ok"}

    @app.post("/screen/{action}")
    async def screen(action: str) -> dict:
        await adb.screen(action)
        return {"status": "ok"}

    @app.post("/apps/{action}/{name}")
    async def apps(action: str, name: str) -> dict:
        pkg = settings.appmap.apps.get(name)
        if not pkg:
            raise HTTPException(404, f"unknown app: {name}")
        if action == "start":
            await adb.launch_app(pkg)
        elif action in ("stop", "kill"):
            await adb.stop_app(pkg)
        elif action in ("switch", "focus"):
            await adb.switch_app(pkg)
        else:
            raise HTTPException(400, "action must be start/stop/switch")
        return {"status": "ok"}

    @app.get("/metrics")
    async def metrics() -> dict:
        cached = await cache.get_json("metrics")
        if cached:
            return cached
        m = await monitor.snapshot()
        await cache.set_json("metrics", m, ttl=10)
        return m

    @app.post("/screenshot")
    async def screenshot() -> dict:
        path = await shots.capture()
        return {"path": str(path)}

    @app.get("/apps")
    async def list_known_apps() -> dict:
        return {"apps": settings.appmap.apps}

    @app.get("/apps/installed")
    async def list_installed(pattern: Optional[str] = None) -> dict:
        pkgs = await adb.list_packages(pattern)
        return {"packages": pkgs}

    @app.get("/apps/foreground")
    async def foreground_app() -> dict:
        info = await adb.top_app()
        return info

    @app.get("/apps/status")
    async def apps_status() -> dict:
        installed = set(await adb.list_packages())
        mapping = settings.appmap.apps
        items = []
        active = await adb.top_app()
        active_pkg = active.get("package")
        active_name = None
        for name, pkg in mapping.items():
            if pkg == active_pkg:
                active_name = name
            items.append({"name": name, "package": pkg, "installed": pkg in installed})
        return {"apps": items, "active": {"name": active_name, "package": active_pkg}}

    @app.get("/apps/options")
    async def apps_options() -> dict:
        visible = settings.appmap.visible or list(settings.appmap.apps.keys())
        installed_pkgs = set(await adb.list_packages())
        installed_map = {name: (pkg in installed_pkgs) for name, pkg in settings.appmap.apps.items()}
        info = await adb.top_app()
        active_pkg = info.get("package")
        active_name = next((n for n, p in settings.appmap.apps.items() if p == active_pkg), None)
        return {
            "options": visible,
            "mapping": settings.appmap.apps,
            "installed": installed_map,
            "active": active_name,
        }

    @app.post("/ha/refresh")
    async def ha_refresh() -> dict:
        ha = get_ha()
        if not ha:
            return {"ok": False, "error": "HA integration not started"}
        options = settings.appmap.visible or list(settings.appmap.apps.keys())
        ha.clear_discovery(options)
        installed_map: dict[str, bool] = {}
        active_name: Optional[str] = None
        try:
            installed_pkgs = set(await adb.list_packages())
            installed_map = {name: (pkg in installed_pkgs) for name, pkg in settings.appmap.apps.items()}
            info = await adb.top_app()
            active_pkg = info.get("package")
            active_name = next((n for n, p in settings.appmap.apps.items() if p == active_pkg), None)
        except Exception:
            pass
        finally:
            ha.publish_discovery(
                options,
                has_battery=settings.device.has_battery,
                has_cellular=settings.device.has_cellular,
            )
            ha.publish_app_attributes(
                options,
                settings.appmap.apps,
                installed=installed_map,
                active=active_name,
            )
        return {"ok": True, "options": options, "active": active_name}

    class OptionsUpdate(BaseModel):
        options: list[str]

    @app.post("/ha/options")
    async def ha_update_options(payload: OptionsUpdate) -> dict:
        all_names = list(settings.appmap.apps.keys())
        invalid = [o for o in payload.options if o not in all_names]
        if invalid:
            raise HTTPException(400, f"unknown app names: {invalid}")

        apps_file = CONFIG_DIR / "apps.yaml"
        data = {"apps": settings.appmap.apps, "visible": payload.options}
        try:
            with open(apps_file, "w", encoding="utf-8") as f:
                yaml.safe_dump(data, f, allow_unicode=True, sort_keys=False)
        except Exception as e:
            raise HTTPException(500, f"failed to write {apps_file}: {e}")

        settings.appmap.visible = payload.options
        ha = get_ha()
        if ha:
            try:
                installed_pkgs = set(await adb.list_packages())
            except Exception:
                installed_pkgs = set()
            installed_map = {name: (pkg in installed_pkgs) for name, pkg in settings.appmap.apps.items()}
            info = await adb.top_app()
            active_pkg = info.get("package")
            active_name = next((n for n, p in settings.appmap.apps.items() if p == active_pkg), None)
            ha.publish_discovery(
                payload.options,
                has_battery=settings.device.has_battery,
                has_cellular=settings.device.has_cellular,
            )
            ha.publish_app_attributes(
                payload.options,
                settings.appmap.apps,
                installed=installed_map,
                active=active_name,
            )
        return {"ok": True, "options": payload.options}

    @app.get("/battery")
    async def battery() -> dict:
        m = await monitor.snapshot()
        return m.get("battery", {})

    @app.get("/network")
    async def network() -> dict:
        m = await monitor.snapshot()
        return m.get("network", {})

    @app.get("/audio")
    async def audio() -> dict:
        try:
            # Use the new comprehensive audio info method
            full_info = await adb.audio_full_info()
            return full_info
        except Exception:
            # Fallback to old method for compatibility
            info = await adb.audio_music_info()
            pct = None
            if info.get("max"):
                try:
                    pct = round(info.get("current", 0) * 100 / info.get("max"))
                except Exception:
                    pct = None
            return {"music": {"index": info.get("current"), "max": info.get("max"), "percent": pct}}

    @app.post("/volume_pct")
    async def set_volume_pct(value: int) -> dict:
        await adb.set_volume_percent(value)
        return {"status": "ok"}

    @app.post("/volume_index")
    async def set_volume_index(value: int) -> dict:
        await adb.set_volume_index(value)
        return {"status": "ok"}

    @app.get("/screen")
    async def get_screen_status() -> dict:
        try:
            is_on = await adb.screen_state()
            brightness = await adb.get_brightness()
            return {
                "on": is_on,
                "brightness": brightness,
                "status": "on" if is_on else "off"
            }
        except Exception as e:
            return {
                "on": None,
                "brightness": None,
                "status": "unknown",
                "error": str(e)
            }

    @app.get("/brightness")
    async def get_brightness() -> dict:
        try:
            brightness = await adb.get_brightness()
            return {"brightness": brightness}
        except Exception as e:
            return {"brightness": None, "error": str(e)}

    # Add comprehensive volume control endpoints
    @app.post("/volume/music/percent")
    async def set_music_volume_percent(value: int) -> dict:
        await adb.set_volume_percent(value)
        return {"status": "ok", "volume_percent": value}

    @app.post("/volume/music/index")
    async def set_music_volume_index(value: int) -> dict:
        await adb.set_volume_index(value)
        return {"status": "ok", "volume_index": value}

    # Performance monitoring endpoints
    @app.get("/performance")
    async def performance() -> dict:
        """Get current performance metrics from Termux monitoring."""
        m = await monitor.snapshot()
        return m.get("performance", {})

    @app.get("/performance/status")
    async def performance_status() -> dict:
        """Get performance monitoring system status."""
        return await monitor.get_performance_status()

    @app.get("/system")
    async def system_info() -> dict:
        """Get system information including load and memory."""
        m = await monitor.snapshot()
        return m.get("system", {})

    @app.post("/performance/start")
    async def start_performance_monitoring() -> dict:
        """Start performance monitoring."""
        await monitor.start_performance_monitoring()
        return {"status": "started"}

    @app.post("/performance/stop")
    async def stop_performance_monitoring() -> dict:
        """Stop performance monitoring."""
        await monitor.stop_performance_monitoring()
        return {"status": "stopped"}

    @app.get("/performance/violations")
    async def get_performance_violations() -> dict:
        """Get current performance violations and statistics."""
        if monitor.performance_monitor:
            return {
                "active_violations": len(monitor.performance_monitor.violation_counts),
                "violation_details": {
                    str(pid): {
                        "violations": count,
                        "timestamp": monitor.performance_monitor.violation_timestamps.get(pid, "").isoformat() if pid in monitor.performance_monitor.violation_timestamps else None
                    }
                    for pid, count in monitor.performance_monitor.violation_counts.items()
                },
                "cpu_threshold": monitor.performance_monitor.cpu_threshold,
                "kill_after_violations": monitor.performance_monitor.kill_after_violations,
                "monitoring_interval": monitor.performance_monitor.monitoring_interval,
                "auto_kill_enabled": monitor.performance_monitor.enable_auto_kill
            }
        return {"error": "Performance monitoring not available"}

    # ADB connection management endpoints
    @app.get("/adb/status")
    async def adb_status() -> dict:
        """Get ADB connection status."""
        return adb.get_connection_info()

    @app.post("/adb/connect")
    async def adb_connect() -> dict:
        """Manually connect to ADB device."""
        result = await adb.connect()
        return {"status": "connected", "message": result}

    @app.post("/adb/disconnect")
    async def adb_disconnect() -> dict:
        """Manually disconnect from ADB device."""
        await adb.disconnect()
        return {"status": "disconnected"}

    # App watchdog endpoints
    @app.get("/watchdog/status")
    async def watchdog_status() -> dict:
        """Get app watchdog status and ISG app health."""
        return await monitor.get_app_watchdog_status()

    @app.get("/watchdog/isg")
    async def isg_app_status() -> dict:
        """Get detailed ISG app status."""
        m = await monitor.snapshot()
        return m.get("isg_app", {})

    @app.post("/watchdog/isg/restart")
    async def restart_isg_app() -> dict:
        """Manually restart the ISG app."""
        return await monitor.restart_isg_app()

    @app.post("/watchdog/start")
    async def start_watchdog() -> dict:
        """Start the app watchdog monitoring."""
        await monitor.start_app_watchdog()
        return {"status": "started"}

    @app.post("/watchdog/stop")
    async def stop_watchdog() -> dict:
        """Stop the app watchdog monitoring."""
        await monitor.stop_app_watchdog()
        return {"status": "stopped"}

    # CEC/TV control endpoints
    @app.get("/cec/status")
    async def cec_status() -> dict:
        """Get CEC controller status and TV information."""
        return await monitor.get_cec_status()

    @app.get("/cec/devices")
    async def cec_devices() -> dict:
        """Scan and return CEC devices on the network."""
        return await monitor.scan_cec_devices()

    @app.get("/cec/commands")
    async def cec_commands() -> dict:
        """Get available CEC commands."""
        m = await monitor.snapshot()
        cec_data = m.get("cec", {})
        return {
            "available_commands": cec_data.get("available_commands", []),
            "command_descriptions": cec_data.get("command_descriptions", {})
        }

    @app.post("/cec/command/{command}")
    async def send_cec_command(command: str) -> dict:
        """Send a CEC command to the TV."""
        return await monitor.send_cec_command(command)

    # TV control shortcuts (common commands)
    @app.post("/tv/power")
    async def tv_power() -> dict:
        """Toggle TV power."""
        return await monitor.send_cec_command("power_toggle")

    @app.post("/tv/power/on")
    async def tv_power_on() -> dict:
        """Turn TV on."""
        return await monitor.send_cec_command("power_on")

    @app.post("/tv/power/off")
    async def tv_power_off() -> dict:
        """Turn TV off."""
        return await monitor.send_cec_command("power_off")

    @app.post("/tv/volume/up")
    async def tv_volume_up() -> dict:
        """Increase TV volume."""
        return await monitor.send_cec_command("volume_up")

    @app.post("/tv/volume/down")
    async def tv_volume_down() -> dict:
        """Decrease TV volume."""
        return await monitor.send_cec_command("volume_down")

    @app.post("/tv/volume/mute")
    async def tv_volume_mute() -> dict:
        """Mute/unmute TV."""
        return await monitor.send_cec_command("mute")

    @app.post("/tv/nav/{direction}")
    async def tv_navigate(direction: str) -> dict:
        """Navigate TV menu (up/down/left/right)."""
        if direction.lower() not in ['up', 'down', 'left', 'right']:
            return {"success": False, "error": "Invalid direction"}
        return await monitor.send_cec_command(direction.lower())

    @app.post("/tv/select")
    async def tv_select() -> dict:
        """Press TV select/OK button."""
        return await monitor.send_cec_command("select")

    @app.post("/tv/back")
    async def tv_back() -> dict:
        """Press TV back button."""
        return await monitor.send_cec_command("back")

    @app.post("/tv/home")
    async def tv_home() -> dict:
        """Press TV home button."""
        return await monitor.send_cec_command("home")

    @app.post("/tv/menu")
    async def tv_menu() -> dict:
        """Press TV menu button."""
        return await monitor.send_cec_command("menu")

    @app.post("/tv/input/{input_name}")
    async def tv_input(input_name: str) -> dict:
        """Switch TV input (hdmi1/hdmi2/hdmi3/hdmi4)."""
        input_mapping = {
            'hdmi1': 'input_hdmi1',
            'hdmi2': 'input_hdmi2',
            'hdmi3': 'input_hdmi3',
            'hdmi4': 'input_hdmi4'
        }

        cec_command = input_mapping.get(input_name.lower())
        if not cec_command:
            return {"success": False, "error": "Invalid input name"}

        return await monitor.send_cec_command(cec_command)

    return app


app = create_app()
