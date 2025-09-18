from __future__ import annotations

import asyncio
import pytest
from unittest.mock import AsyncMock, patch, MagicMock

from src.isg_android_control.services.performance_monitor import (
    TermuxPerformanceMonitor,
    ProcessInfo,
    PerformanceMetrics
)


class TestTermuxPerformanceMonitor:
    """Test the Termux performance monitoring system."""

    @pytest.fixture
    def monitor(self):
        """Create a performance monitor for testing."""
        return TermuxPerformanceMonitor(
            cpu_threshold=50.0,
            monitoring_interval=0.1,  # Fast for testing
            kill_after_violations=2,  # Quick kill for testing
            enable_auto_kill=True
        )

    @pytest.fixture
    def sample_top_output(self):
        """Sample top command output for testing."""
        return """
top - 12:34:56 up 1 day,  2:34,  1 user,  load average: 1.23, 1.45, 1.67
Tasks:  123 total,   1 running, 122 sleeping,   0 stopped,   0 zombie
%Cpu(s): 12.3 us,  4.5 sy,  0.0 ni, 82.1 id,  1.1 wa,  0.0 hi,  0.0 si,  0.0 st
MiB Mem :   4096.0 total,   1024.0 free,   2048.0 used,   1024.0 buff/cache
MiB Swap:   2048.0 total,   2048.0 free,      0.0 used.   1536.0 avail Mem

  PID USER      PR  NI    VIRT    RES    SHR S  %CPU %MEM     TIME+ COMMAND
 1234 user      20   0  123456   7890   4567 R  75.5  1.2   1:23.45 high_cpu_app
 5678 user      20   0   98765   4321   2345 S  25.0  0.8   0:45.67 normal_app
 9012 root      20   0   54321   1234    567 S  10.0  0.3   0:12.34 system_service
 3456 user      20   0   12345    678    123 S   5.0  0.1   0:05.67 low_cpu_app
"""

    def test_parse_top_output(self, monitor, sample_top_output):
        """Test parsing top command output."""
        metrics = monitor.parse_top_output(sample_top_output)

        assert isinstance(metrics, PerformanceMetrics)
        assert len(metrics.processes) == 4
        assert len(metrics.high_cpu_processes) == 1

        # Check high CPU process
        high_cpu_proc = metrics.high_cpu_processes[0]
        assert high_cpu_proc.pid == 1234
        assert high_cpu_proc.user == "user"
        assert high_cpu_proc.cpu_percent == 75.5
        assert high_cpu_proc.command == "high_cpu_app"

        # Check process parsing
        processes_by_pid = {p.pid: p for p in metrics.processes}

        assert 1234 in processes_by_pid
        assert processes_by_pid[1234].cpu_percent == 75.5

        assert 5678 in processes_by_pid
        assert processes_by_pid[5678].cpu_percent == 25.0

    def test_parse_process_line(self, monitor):
        """Test parsing individual process lines."""
        line = " 1234 user      20   0  123456   7890   4567 R  75.5  1.2   1:23.45 high_cpu_app"
        process = monitor._parse_process_line(line)

        assert process is not None
        assert process.pid == 1234
        assert process.user == "user"
        assert process.cpu_percent == 75.5
        assert process.mem_percent == 1.2
        assert process.command == "high_cpu_app"

    def test_is_protected_process(self, monitor):
        """Test protected process detection."""
        # Protected processes
        protected_cases = [
            ProcessInfo(1, "root", 100.0, 1.0, "init"),
            ProcessInfo(2, "root", 100.0, 1.0, "/usr/bin/systemd"),
            ProcessInfo(3, "user", 100.0, 1.0, "python3 -m isg_android_control"),
            ProcessInfo(4, "user", 100.0, 1.0, "adb server"),
            ProcessInfo(5, "root", 100.0, 1.0, "kernel_worker"),
        ]

        for process in protected_cases:
            assert monitor.is_protected_process(process), f"Should protect: {process.command}"

        # Unprotected processes
        unprotected_cases = [
            ProcessInfo(1000, "user", 100.0, 1.0, "com.android.chrome"),
            ProcessInfo(1001, "user", 100.0, 1.0, "gaming_app"),
            ProcessInfo(1002, "user", 100.0, 1.0, "media_player"),
        ]

        for process in unprotected_cases:
            assert not monitor.is_protected_process(process), f"Should NOT protect: {process.command}"

    @pytest.mark.asyncio
    async def test_get_top_output_mock(self, monitor):
        """Test getting top output with mocked subprocess."""
        mock_output = "PID USER %CPU COMMAND\n1234 user 75.5 test_app"

        with patch('asyncio.create_subprocess_exec') as mock_subprocess:
            mock_proc = AsyncMock()
            mock_proc.communicate.return_value = (mock_output.encode(), b"")
            mock_proc.returncode = 0
            mock_subprocess.return_value = mock_proc

            output = await monitor.get_top_output()
            assert mock_output in output

    @pytest.mark.asyncio
    async def test_kill_process_mock(self, monitor):
        """Test process killing with mocked subprocess."""
        process = ProcessInfo(1234, "user", 75.5, 1.2, "test_app")

        with patch('asyncio.create_subprocess_exec') as mock_subprocess:
            mock_proc = AsyncMock()
            mock_proc.communicate.return_value = (b"", b"")
            mock_proc.returncode = 0
            mock_subprocess.return_value = mock_proc

            success = await monitor.kill_process(process)
            assert success

            # Verify TERM signal was sent first
            mock_subprocess.assert_called_with(
                'kill', '-TERM', '1234',
                stdout=asyncio.subprocess.DEVNULL,
                stderr=asyncio.subprocess.PIPE
            )

    @pytest.mark.asyncio
    async def test_violation_tracking(self, monitor):
        """Test violation counting and cleanup."""
        high_cpu_process = ProcessInfo(1234, "user", 75.5, 1.2, "test_app")

        # Mock kill_process to avoid actual killing
        with patch.object(monitor, 'kill_process', return_value=True) as mock_kill:
            # First violation
            await monitor.process_high_cpu_processes([high_cpu_process])
            assert monitor.violation_counts[1234] == 1
            mock_kill.assert_not_called()

            # Second violation - should trigger kill
            await monitor.process_high_cpu_processes([high_cpu_process])
            assert 1234 not in monitor.violation_counts  # Should be removed after kill
            mock_kill.assert_called_once_with(high_cpu_process)

    @pytest.mark.asyncio
    async def test_get_system_info(self, monitor):
        """Test system info gathering."""
        # Mock file reads
        mock_load = "1.23 2.34 3.45 2/123 12345\n"
        mock_meminfo = """
MemTotal:        4096 kB
MemFree:         1024 kB
MemAvailable:    2048 kB
"""

        with patch('builtins.open') as mock_open:
            # Configure mock for different files
            def side_effect(filename, *args, **kwargs):
                mock_file = MagicMock()
                if 'loadavg' in filename:
                    mock_file.read.return_value = mock_load
                elif 'meminfo' in filename:
                    mock_file.__iter__.return_value = iter(mock_meminfo.strip().split('\n'))
                return mock_file

            mock_open.side_effect = side_effect

            system_info = await monitor.get_system_info()

            assert 'load_average' in system_info
            assert system_info['load_average']['1min'] == 1.23
            assert system_info['load_average']['5min'] == 2.34
            assert system_info['load_average']['15min'] == 3.45

            assert 'memory' in system_info
            assert system_info['memory']['MemTotal'] == 4096 * 1024  # Converted to bytes

    def test_monitor_configuration(self, monitor):
        """Test monitor configuration."""
        assert monitor.cpu_threshold == 50.0
        assert monitor.monitoring_interval == 0.1
        assert monitor.kill_after_violations == 2
        assert monitor.enable_auto_kill is True

    @pytest.mark.asyncio
    async def test_monitoring_lifecycle(self, monitor):
        """Test starting and stopping monitoring."""
        # Mock get_performance_snapshot to avoid actual top calls
        with patch.object(monitor, 'get_performance_snapshot') as mock_snapshot:
            mock_metrics = PerformanceMetrics(
                timestamp=asyncio.get_event_loop().time(),
                processes=[],
                total_cpu_usage=25.0,
                total_memory_usage=50.0,
                high_cpu_processes=[]
            )
            mock_snapshot.return_value = mock_metrics

            # Start monitoring
            await monitor.start_monitoring()
            assert monitor._monitoring is True
            assert monitor._monitor_task is not None

            # Give it a moment to run
            await asyncio.sleep(0.2)

            # Stop monitoring
            await monitor.stop_monitoring()
            assert monitor._monitoring is False