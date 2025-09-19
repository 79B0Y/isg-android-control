#!/usr/bin/env python3
"""测试top命令解析逻辑"""
import re

def parse_top_output(top_output):
    """解析top命令输出"""
    lines = top_output.split('\n')
    
    # 初始化性能数据
    performance = {
        "cpu_usage_percent": 0.0,
        "memory_usage_percent": 0.0,
        "memory_total_mb": 0,
        "memory_used_mb": 0,
        "highest_cpu_process": None,
        "highest_cpu_pid": None,
        "highest_cpu_percent": 0.0,
        "highest_cpu_service": None
    }
    
    # 解析CPU使用率 - 这个设备的格式是 "400%cpu  98%user   0%nice 207%sys  79%idle"
    for line in lines:
        if "%cpu" in line.lower() and "%user" in line:
            print(f"Found CPU line: {line}")
            # 提取user和sys的百分比
            user_match = re.search(r'(\d+)%user', line)
            sys_match = re.search(r'(\d+)%sys', line) 
            
            if user_match and sys_match:
                user_cpu = float(user_match.group(1))
                sys_cpu = float(sys_match.group(1))
                # 注意：这个设备显示的是累积值，需要计算百分比
                total_cores = 4  # 从400%cpu可以看出是4核心
                total_cpu = (user_cpu + sys_cpu) / total_cores
                performance["cpu_usage_percent"] = round(total_cpu, 1)
                print(f"CPU计算: user={user_cpu}%, sys={sys_cpu}%, total={total_cpu}%")
            break
    
    # 解析内存使用率 - 格式: "Mem:  4006164K total,  3660916K used,   345248K free"
    for line in lines:
        if "Mem:" in line and "total" in line:
            print(f"Found Memory line: {line}")
            total_match = re.search(r'(\d+)K total', line)
            used_match = re.search(r'(\d+)K used', line)
            
            if total_match and used_match:
                total_kb = float(total_match.group(1))
                used_kb = float(used_match.group(1))
                total_mb = round(total_kb / 1024, 1)
                used_mb = round(used_kb / 1024, 1)
                usage_percent = round((used_kb / total_kb) * 100, 1)
                
                performance["memory_total_mb"] = total_mb
                performance["memory_used_mb"] = used_mb 
                performance["memory_usage_percent"] = usage_percent
                print(f"内存计算: total={total_mb}MB, used={used_mb}MB, usage={usage_percent}%")
            break
    
    # 解析最高CPU进程
    process_started = False
    for line in lines:
        # 跳过头部，找到进程列表
        clean_header = re.sub(r'\[[\d;]*[mK]', '', line)
        print(f"Checking header: '{clean_header}'")
        if "PID USER" in clean_header and "%CPU" in clean_header:
            print(f"Found header line!")
            process_started = True
            continue
        
        if process_started and line.strip():
            # 清理ANSI转义序列
            clean_line = re.sub(r'\[[\d;]*[mK]', '', line)
            parts = clean_line.split()
            print(f"Process line parts: {parts}")
            
            if len(parts) >= 11:
                try:
                    pid = parts[0]
                    cpu_str = parts[8]  # %CPU列 (S列后面)
                    command = parts[-1] if len(parts) > 10 else "unknown"
                    
                    print(f"PID={pid}, CPU_str='{cpu_str}', Command={command}")
                    
                    # 处理CPU百分比
                    cpu_percent = 0.0
                    if cpu_str.replace('.', '').isdigit():
                        cpu_percent = float(cpu_str)
                    
                    if cpu_percent > performance["highest_cpu_percent"]:
                        performance["highest_cpu_pid"] = pid
                        performance["highest_cpu_percent"] = round(cpu_percent, 1)
                        performance["highest_cpu_process"] = command
                        print(f"找到最高CPU进程: PID={pid}, CPU={cpu_percent}%, Command={command}")
                    
                    # 只检查前几个进程（按CPU排序）
                    if performance["highest_cpu_percent"] > 0:
                        break
                        
                except (ValueError, IndexError) as e:
                    print(f"解析进程行失败: {line}, 错误: {e}")
                    continue
    
    return performance

# 测试样本数据 - 真实数据
sample_top_output = """Tasks: 374 total,   3 running, 369 sleeping,   0 stopped,   2 zombie
  Mem:  4006164K total,  3660916K used,   345248K free,    20868K buffers
 Swap:  2003076K total,  1313344K used,   689732K free,  1012956K cached
400%cpu  98%user   0%nice 207%sys  79%idle   0%iow  12%irq   5%sirq   0%host
[7m  PID USER         PR  NI VIRT  RES  SHR S[%CPU] %MEM     TIME+ ARGS            [0m
 1193 u0_a50       20   0  16G  79M  54M S  100   2.0 439:23.10 com.android.pro+
[1m8548 shell        20   0  10G 4.7M 3.9M R 35.7   0.1   0:00.18 top -d 0.5 -n 1[m
 8499 u0_a2        20   0 8.0K 8.0K    0 S 16.6   0.0   0:00.30 [isgservicemoni+
[1m8454 u0_a2        20   0 8.0K 8.0K    0 R 16.6   0.0   0:00.32 [isgservicemoni+[m
[1m8531 u0_a2        20   0 8.0K 8.0K    0 R 14.2   0.0   0:00.09 [isgservicemoni+[m
 4849 u0_a67       20   0  36G 414M 186M S 11.9  10.5  34:41.76 com.spotify.mus+"""

if __name__ == "__main__":
    print("=== 测试top命令解析逻辑 ===")
    result = parse_top_output(sample_top_output)
    print("\n📊 解析结果:")
    for key, value in result.items():
        print(f"  {key}: {value}")
    
    # 验证结果
    print("\n✅ 验证:")
    print(f"CPU使用率合理 (0-100%): {0 <= result['cpu_usage_percent'] <= 100}")
    print(f"内存使用率合理 (0-100%): {0 <= result['memory_usage_percent'] <= 100}")
    print(f"找到最高CPU进程: {result['highest_cpu_process'] is not None}")
    print(f"找到最高CPU进程PID: {result['highest_cpu_pid'] is not None}")