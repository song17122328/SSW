#!/usr/bin/env python3
# init_pccs_pool.py - PCCS 资源池初始化脚本
"""
本脚本用于从数据库中加载平台和装备数据，并转换为 PCCS 标准模型
注册到全局资源池中
"""

import sqlite3
from models import global_resource_pool
from pccs_adapter import PCCSAdapter


def init_pccs_resource_pool(db_path='military_data.db'):
    """
    初始化 PCCS 资源池

    Args:
        db_path: 数据库路径

    Returns:
        (platform_count, equipment_count): 加载的资源数量
    """
    print("\n" + "="*60)
    print("  🔄 正在初始化 PCCS 资源池...")
    print("="*60)

    try:
        # 连接数据库
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        db = conn.cursor()

        # 创建适配器
        adapter = PCCSAdapter()

        # 清空现有资源池
        global_resource_pool.resources.clear()
        print("  ✓ 已清空现有资源池")

        # 加载平台资源
        print("\n  [1/2] 正在加载平台资源...")
        platforms = db.execute('SELECT * FROM platforms').fetchall()
        platform_count = 0
        platform_errors = []

        for platform_row in platforms:
            try:
                platform_data = dict(platform_row)

                # 获取平台关联的装备
                equipments_rows = db.execute('''
                    SELECT e.* FROM equipments e
                    JOIN platform_equipment_link pe ON e.id = pe.equipment_id
                    WHERE pe.platform_id = ?
                ''', (platform_data['id'],)).fetchall()

                equipments = [dict(r) for r in equipments_rows]

                # 转换为 PCCS 资源
                pccs_resource = adapter.convert_platform_to_pccs(platform_data, equipments)

                # 注册到资源池
                if global_resource_pool.register_resource(pccs_resource):
                    platform_count += 1

                    # 打印进度
                    if platform_count % 10 == 0:
                        print(f"    - 已加载 {platform_count} 个平台...")

            except Exception as e:
                platform_errors.append(f"平台 {platform_data.get('name', 'Unknown')} (ID: {platform_data.get('id')}): {e}")
                continue

        print(f"  ✓ 成功加载 {platform_count} 个平台资源")
        if platform_errors:
            print(f"  ⚠ {len(platform_errors)} 个平台加载失败")
            for err in platform_errors[:5]:  # 只显示前5个错误
                print(f"    - {err}")

        # 加载装备资源
        print("\n  [2/2] 正在加载装备资源...")
        equipments = db.execute('SELECT * FROM equipments').fetchall()
        equipment_count = 0
        equipment_errors = []

        for equipment_row in equipments:
            try:
                equipment_data = dict(equipment_row)

                # 转换为 PCCS 资源
                pccs_resource = adapter.convert_equipment_to_pccs(equipment_data)

                # 注册到资源池
                if global_resource_pool.register_resource(pccs_resource):
                    equipment_count += 1

                    # 打印进度
                    if equipment_count % 50 == 0:
                        print(f"    - 已加载 {equipment_count} 个装备...")

            except Exception as e:
                equipment_errors.append(f"装备 {equipment_data.get('name', 'Unknown')} (ID: {equipment_data.get('id')}): {e}")
                continue

        print(f"  ✓ 成功加载 {equipment_count} 个装备资源")
        if equipment_errors:
            print(f"  ⚠ {len(equipment_errors)} 个装备加载失败")
            for err in equipment_errors[:5]:  # 只显示前5个错误
                print(f"    - {err}")

        # 关闭数据库连接
        conn.close()

        # 打印统计信息
        stats = global_resource_pool.get_statistics()
        print("\n" + "="*60)
        print("  📊 PCCS 资源池统计信息")
        print("="*60)
        print(f"  总资源数:     {stats['total']}")
        print(f"  平台资源:     {stats['platforms']}")
        print(f"  装备资源:     {stats['equipments']}")
        print(f"  可用资源:     {stats['available']}")
        print(f"  忙碌资源:     {stats['busy']}")
        print(f"  利用率:       {stats['utilization_rate']:.1%}")

        # 按任务类型统计
        print("\n  📋 按任务类型统计:")
        all_resources = global_resource_pool.list_resources()
        for mission_type in ['patrol', 'strike', 'air_defense', 'recon']:
            count = len([r for r in all_resources if mission_type in r.capability.mission_types])
            print(f"    - {mission_type:15s}: {count} 个资源")

        print("="*60)
        print("  ✅ PCCS 资源池初始化完成!\n")

        return platform_count, equipment_count

    except Exception as e:
        print(f"\n  ❌ 初始化失败: {e}")
        import traceback
        traceback.print_exc()
        return 0, 0


def check_pccs_resource(resource_type='platform', resource_id=1):
    """
    检查单个资源的 PCCS 模型

    Args:
        resource_type: 资源类型 (platform/equipment)
        resource_id: 资源ID
    """
    resource = global_resource_pool.get_resource(resource_type, resource_id)

    if resource is None:
        print(f"\n❌ 资源 {resource_type}:{resource_id} 未找到")
        return

    print("\n" + "="*60)
    print(f"  PCCS 资源详情: {resource.name}")
    print("="*60)

    print("\n[基础信息]")
    print(f"  资源ID:       {resource.resource_id}")
    print(f"  资源类型:     {resource.resource_type}")
    print(f"  名称:         {resource.name}")
    print(f"  类别:         {resource.category}")

    print("\n[1] Perception (感知)")
    p = resource.perception
    print(f"  探测范围:     {p.detection_range} km")
    print(f"  探测类型:     {', '.join(p.detection_types)}")
    print(f"  跟踪容量:     {p.tracking_capacity} 个目标")
    print(f"  数据链类型:   {', '.join(p.datalink_type)}")
    print(f"  通信范围:     {p.communication_range} km")

    print("\n[2] Control (控制)")
    c = resource.control
    print(f"  控制权限:     {c.control_authority}")
    print(f"  可用指令:     {', '.join(c.available_commands)}")
    print(f"  API端点:      {c.api_endpoint}")
    print(f"  指令延迟:     {c.command_latency} 秒")
    print(f"  优先级:       {c.priority_level}/10")

    print("\n[3] Capability (能力)")
    cap = resource.capability
    print(f"  传感器类型:   {', '.join(cap.sensor_type)}")
    print(f"  武器系统:     {len(cap.weapon_systems)} 种")
    print(f"  打击范围:     {cap.strike_range} km")
    print(f"  打击类型:     {', '.join(cap.strike_types)}")
    print(f"  火力值:       {cap.firepower}")
    print(f"  最大速度:     {cap.max_speed} 节")
    print(f"  续航力:       {cap.endurance} km")
    print(f"  适合任务:     {', '.join(cap.mission_types)}")
    print(f"  效能评分:")
    for mt, score in cap.effectiveness_scores.items():
        print(f"    - {mt:15s}: {score:.2f}")

    print("\n[4] State (状态)")
    s = resource.state
    print(f"  工作状态:     {s.operational_status}")
    print(f"  可用状态:     {s.availability_status}")
    print(f"  任务状态:     {s.mission_status}")
    print(f"  健康度:       {s.health_level:.0%}")
    print(f"  燃油余量:     {s.fuel_level:.0%}")
    print(f"  弹药余量:     {s.ammunition_level:.0%}")
    print(f"  网络延迟:     {s.network_latency} ms")
    print(f"  连接强度:     {s.connection_strength:.0%}")

    print("\n" + "="*60 + "\n")


if __name__ == '__main__':
    import sys

    # 初始化资源池
    platform_count, equipment_count = init_pccs_resource_pool()

    # 如果提供了参数，则显示示例资源
    if len(sys.argv) > 1:
        if sys.argv[1] == '--check':
            resource_type = sys.argv[2] if len(sys.argv) > 2 else 'platform'
            resource_id = int(sys.argv[3]) if len(sys.argv) > 3 else 1
            check_pccs_resource(resource_type, resource_id)
        elif sys.argv[1] == '--stats':
            # 显示统计信息（已在初始化时显示）
            pass
    else:
        # 默认显示第一个平台的 PCCS 信息
        if platform_count > 0:
            print("\n💡 提示: 使用以下命令查看详细信息:")
            print("  python init_pccs_pool.py --check platform 1")
            print("  python init_pccs_pool.py --check equipment 1")
