# models.py - PCCS 标准化建模层
"""
PCCS (Perception, Control, Capability, State) 虚拟化资源建模
本模块定义了符合 PCCS 标准的资源抽象模型
"""

from dataclasses import dataclass, field, asdict
from typing import List, Dict, Any, Optional
from datetime import datetime
import json


# ============================================================================
# PCCS 四维度数据模型
# ============================================================================

@dataclass
class Perception:
    """感知 (Perception) - 资源能感知什么"""

    # 环境感知
    detection_range: float = 0.0  # 探测范围 (km)
    detection_types: List[str] = field(default_factory=list)  # 目标识别类型: ['air', 'surface', 'subsurface']
    tracking_capacity: int = 0  # 同时跟踪目标数量
    update_frequency: float = 1.0  # 态势更新频率 (Hz)

    # 自身状态感知
    position: Dict[str, float] = field(default_factory=lambda: {
        'longitude': 0.0,
        'latitude': 0.0,
        'altitude': 0.0
    })
    heading: float = 0.0  # 航向 (度)
    speed: float = 0.0  # 速度 (节)

    # 通信感知
    datalink_status: str = 'online'  # 数据链路状态: online/offline/degraded
    datalink_type: List[str] = field(default_factory=list)  # 数据链类型: ['Link16', 'HF', 'Satellite']
    communication_range: float = 0.0  # 通信范围 (km)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class Control:
    """控制 (Control) - 如何指挥它"""

    # 控制来源
    controller_id: Optional[str] = None  # 控制者标识 (指挥官ID或算法ID)
    control_authority: str = 'manual'  # 控制权限: manual/semi-auto/auto

    # 控制指令集
    available_commands: List[str] = field(default_factory=list)  # 可用指令列表
    # 常见指令: ['power_on', 'power_off', 'navigate', 'fire', 'detect', 'communicate']

    # 控制接口
    api_endpoint: str = ''  # API 端点
    control_protocol: str = 'REST'  # 控制协议: REST/MQTT/WebSocket
    message_format: str = 'json'  # 消息格式: json/xml/binary

    # 控制时限
    command_latency: float = 0.0  # 指令延迟 (秒)
    response_timeout: float = 30.0  # 响应超时 (秒)
    priority_level: int = 5  # 优先级 (1-10, 10最高)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class Capability:
    """能力 (Capability) - 它能干什么"""

    # 感知能力
    sensor_type: List[str] = field(default_factory=list)  # 传感器类型: ['radar', 'sonar', 'eo/ir']
    detection_capability: Dict[str, Any] = field(default_factory=dict)  # 探测能力详情

    # 执行能力 (作战能力)
    weapon_systems: List[Dict[str, Any]] = field(default_factory=list)  # 武器系统列表
    strike_range: float = 0.0  # 打击范围 (km)
    strike_types: List[str] = field(default_factory=list)  # 打击类型: ['anti-air', 'anti-surface', 'anti-submarine']
    firepower: int = 0  # 火力值 (相对评分)

    # 机动能力
    max_speed: float = 0.0  # 最大速度 (节)
    cruise_speed: float = 0.0  # 巡航速度 (节)
    endurance: float = 0.0  # 续航力 (小时或公里)
    maneuverability: str = 'medium'  # 机动性: low/medium/high

    # 通信能力
    bandwidth: float = 0.0  # 带宽 (Mbps)
    anti_jamming_level: int = 0  # 抗干扰等级 (1-10)
    encryption_support: bool = True  # 是否支持加密

    # 计算存储能力 (适用于无人系统)
    computing_power: float = 0.0  # 算力 (GFLOPS)
    storage_capacity: float = 0.0  # 存储容量 (GB)

    # 任务适配性 (关键：用于任务匹配)
    mission_types: List[str] = field(default_factory=list)  # 适合的任务类型: ['patrol', 'strike', 'air_defense', 'recon']
    effectiveness_scores: Dict[str, float] = field(default_factory=dict)  # 各任务类型效能评分 (0-1)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class State:
    """状态 (State) - 它现在怎么样"""

    # 工作状态
    operational_status: str = 'online'  # 在线状态: online/offline/maintenance/failure
    availability_status: str = 'available'  # 可用状态: available/busy/reserved
    mission_status: str = 'idle'  # 任务状态: idle/executing/completed
    health_level: float = 1.0  # 健康度 (0-1, 1为完全健康)

    # 网络状态
    network_latency: float = 0.0  # 网络延迟 (ms)
    packet_loss_rate: float = 0.0  # 丢包率 (0-1)
    connection_strength: float = 1.0  # 连接强度 (0-1)

    # 能量状态
    fuel_level: float = 1.0  # 燃油余量 (0-1)
    battery_level: float = 1.0  # 电池电量 (0-1, 适用于混合动力或无人系统)
    ammunition_level: float = 1.0  # 弹药余量 (0-1)

    # 资源消耗
    fuel_consumption_rate: float = 0.0  # 燃油消耗率 (L/h)
    power_consumption: float = 0.0  # 功率消耗 (kW)

    # 时间信息
    last_update_time: str = field(default_factory=lambda: datetime.now().isoformat())  # 最后更新时间
    uptime: float = 0.0  # 运行时间 (小时)
    next_maintenance_time: Optional[str] = None  # 下次维护时间

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


# ============================================================================
# PCCS 资源模型
# ============================================================================

@dataclass
class PCCSResource:
    """PCCS 标准化资源模型"""

    # 基础信息
    resource_id: int  # 资源ID (对应数据库中的 platform_id 或 equipment_id)
    resource_type: str  # 资源类型: 'platform' / 'equipment'
    name: str  # 资源名称
    category: str = ''  # 资源类别

    # PCCS 四维度
    perception: Perception = field(default_factory=Perception)
    control: Control = field(default_factory=Control)
    capability: Capability = field(default_factory=Capability)
    state: State = field(default_factory=State)

    # 元数据
    registration_time: str = field(default_factory=lambda: datetime.now().isoformat())
    last_modified_time: str = field(default_factory=lambda: datetime.now().isoformat())
    tags: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            'resource_id': self.resource_id,
            'resource_type': self.resource_type,
            'name': self.name,
            'category': self.category,
            'perception': self.perception.to_dict(),
            'control': self.control.to_dict(),
            'capability': self.capability.to_dict(),
            'state': self.state.to_dict(),
            'registration_time': self.registration_time,
            'last_modified_time': self.last_modified_time,
            'tags': self.tags
        }

    def to_json(self) -> str:
        """转换为 JSON 字符串"""
        return json.dumps(self.to_dict(), ensure_ascii=False, indent=2)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'PCCSResource':
        """从字典创建 PCCS 资源"""
        return cls(
            resource_id=data['resource_id'],
            resource_type=data['resource_type'],
            name=data['name'],
            category=data.get('category', ''),
            perception=Perception(**data.get('perception', {})),
            control=Control(**data.get('control', {})),
            capability=Capability(**data.get('capability', {})),
            state=State(**data.get('state', {})),
            registration_time=data.get('registration_time', datetime.now().isoformat()),
            last_modified_time=data.get('last_modified_time', datetime.now().isoformat()),
            tags=data.get('tags', [])
        )

    @classmethod
    def from_json(cls, json_str: str) -> 'PCCSResource':
        """从 JSON 字符串创建 PCCS 资源"""
        data = json.loads(json_str)
        return cls.from_dict(data)


# ============================================================================
# PCCS 资源池
# ============================================================================

class PCCSResourcePool:
    """PCCS 资源池 - 管理所有虚拟化资源"""

    def __init__(self):
        self.resources: Dict[str, PCCSResource] = {}  # key: resource_type:resource_id

    def register_resource(self, resource: PCCSResource) -> bool:
        """注册资源到资源池"""
        key = f"{resource.resource_type}:{resource.resource_id}"
        self.resources[key] = resource
        return True

    def unregister_resource(self, resource_type: str, resource_id: int) -> bool:
        """注销资源"""
        key = f"{resource_type}:{resource_id}"
        if key in self.resources:
            del self.resources[key]
            return True
        return False

    def get_resource(self, resource_type: str, resource_id: int) -> Optional[PCCSResource]:
        """获取资源"""
        key = f"{resource_type}:{resource_id}"
        return self.resources.get(key)

    def list_resources(self, resource_type: Optional[str] = None,
                      filters: Optional[Dict[str, Any]] = None) -> List[PCCSResource]:
        """列出资源"""
        result = list(self.resources.values())

        # 按资源类型过滤
        if resource_type:
            result = [r for r in result if r.resource_type == resource_type]

        # 按其他条件过滤
        if filters:
            for key, value in filters.items():
                if key == 'category':
                    result = [r for r in result if r.category == value]
                elif key == 'mission_type':
                    result = [r for r in result if value in r.capability.mission_types]
                elif key == 'availability':
                    result = [r for r in result if r.state.availability_status == value]

        return result

    def search_by_capability(self, mission_type: str, min_effectiveness: float = 0.5) -> List[PCCSResource]:
        """根据能力搜索资源 (用于任务匹配)"""
        result = []
        for resource in self.resources.values():
            # 检查任务类型匹配
            if mission_type in resource.capability.mission_types:
                # 检查效能评分
                effectiveness = resource.capability.effectiveness_scores.get(mission_type, 0.0)
                if effectiveness >= min_effectiveness:
                    # 检查可用性
                    if resource.state.availability_status == 'available':
                        result.append(resource)

        # 按效能评分排序
        result.sort(key=lambda r: r.capability.effectiveness_scores.get(mission_type, 0.0), reverse=True)
        return result

    def get_statistics(self) -> Dict[str, Any]:
        """获取资源池统计信息"""
        total = len(self.resources)
        platforms = len([r for r in self.resources.values() if r.resource_type == 'platform'])
        equipments = len([r for r in self.resources.values() if r.resource_type == 'equipment'])

        available = len([r for r in self.resources.values() if r.state.availability_status == 'available'])
        busy = len([r for r in self.resources.values() if r.state.availability_status == 'busy'])

        return {
            'total': total,
            'platforms': platforms,
            'equipments': equipments,
            'available': available,
            'busy': busy,
            'utilization_rate': (busy / total) if total > 0 else 0.0
        }


# 全局资源池实例
global_resource_pool = PCCSResourcePool()
