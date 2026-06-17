# pccs_adapter.py - PCCS 数据适配器
"""
本模块负责将现有的 platforms 和 equipments 数据转换为 PCCS 标准模型
包含智能推断和映射逻辑
"""

import json
import re
from typing import Dict, Any, List, Optional, Tuple
from models import (
    PCCSResource, Perception, Control, Capability, State,
    global_resource_pool
)


class PCCSAdapter:
    """PCCS 数据适配器 - 将传统数据转换为 PCCS 模型"""

    # 任务类型映射
    MISSION_TYPE_MAP = {
        'patrol': '巡逻',
        'strike': '打击',
        'air_defense': '反导',
        'recon': '侦察'
    }

    # 装备类型到感知能力的映射
    EQUIPMENT_PERCEPTION_MAP = {
        '雷达': {
            'sensor_type': 'radar',
            'detection_types': ['air', 'surface'],
            'detection_range_multiplier': 1.0
        },
        '声呐': {
            'sensor_type': 'sonar',
            'detection_types': ['subsurface'],
            'detection_range_multiplier': 0.3
        },
        '光电': {
            'sensor_type': 'eo/ir',
            'detection_types': ['air', 'surface'],
            'detection_range_multiplier': 0.5
        }
    }

    # 装备类型到能力的映射
    EQUIPMENT_CAPABILITY_MAP = {
        '导弹': {
            'strike_type': 'missile',
            'firepower_base': 80,
            'range_multiplier': 1.0
        },
        '火炮': {
            'strike_type': 'gun',
            'firepower_base': 40,
            'range_multiplier': 0.2
        },
        '鱼雷': {
            'strike_type': 'torpedo',
            'firepower_base': 90,
            'range_multiplier': 0.3
        }
    }

    def __init__(self):
        """初始化适配器"""
        pass

    def extract_numeric_value(self, text: str, unit: Optional[str] = None) -> float:
        """从文本中提取数值"""
        if not text or not isinstance(text, str):
            return 0.0

        # 移除中文字符和单位
        text = re.sub(r'[^\d.,]+', '', text)
        if not text:
            return 0.0

        try:
            # 尝试提取第一个数字
            numbers = re.findall(r'\d+\.?\d*', text.replace(',', ''))
            if numbers:
                return float(numbers[0])
        except (ValueError, IndexError):
            pass

        return 0.0

    def parse_platform_details(self, details_json: str) -> Dict[str, Any]:
        """解析平台详情 JSON"""
        if not details_json:
            return {}

        try:
            return json.loads(details_json)
        except json.JSONDecodeError:
            return {}

    def infer_mission_types_from_platform(self, platform_data: Dict[str, Any],
                                         equipments: List[Dict[str, Any]]) -> Tuple[List[str], Dict[str, float]]:
        """
        根据平台类型和装备推断适合的任务类型
        返回: (任务类型列表, 效能评分字典)
        """
        category = platform_data.get('category', '').lower()
        mission_types = []
        effectiveness_scores = {}

        # 根据平台类别初步判断
        if '航母' in category or 'carrier' in category:
            mission_types = ['strike', 'air_defense', 'patrol']
            effectiveness_scores = {'strike': 0.95, 'air_defense': 0.9, 'patrol': 0.85}

        elif '驱逐舰' in category or 'destroyer' in category:
            mission_types = ['air_defense', 'strike', 'patrol']
            effectiveness_scores = {'air_defense': 0.9, 'strike': 0.85, 'patrol': 0.8}

        elif '护卫舰' in category or 'frigate' in category:
            mission_types = ['patrol', 'air_defense', 'strike']
            effectiveness_scores = {'patrol': 0.9, 'air_defense': 0.75, 'strike': 0.7}

        elif '潜艇' in category or 'submarine' in category:
            mission_types = ['strike', 'recon', 'patrol']
            effectiveness_scores = {'strike': 0.9, 'recon': 0.85, 'patrol': 0.8}

        elif '侦察' in category or 'recon' in category or '预警' in category:
            mission_types = ['recon', 'patrol']
            effectiveness_scores = {'recon': 0.95, 'patrol': 0.8}

        else:
            # 默认：根据装备推断
            mission_types = ['patrol']
            effectiveness_scores = {'patrol': 0.6}

        # 根据装备进一步调整
        has_air_defense = any('防空' in eq.get('name', '') or '导弹' in eq.get('category_text', '') for eq in equipments)
        has_strike = any('打击' in eq.get('name', '') or '导弹' in eq.get('name', '') for eq in equipments)
        has_sensor = any('雷达' in eq.get('category_text', '') or '声呐' in eq.get('category_text', '') for eq in equipments)

        if has_air_defense and 'air_defense' not in mission_types:
            mission_types.append('air_defense')
            effectiveness_scores['air_defense'] = 0.7

        if has_strike and 'strike' not in mission_types:
            mission_types.append('strike')
            effectiveness_scores['strike'] = 0.7

        if has_sensor and 'recon' not in mission_types:
            mission_types.append('recon')
            effectiveness_scores['recon'] = 0.7

        return mission_types, effectiveness_scores

    def build_perception_from_platform(self, platform_data: Dict[str, Any],
                                       equipments: List[Dict[str, Any]]) -> Perception:
        """从平台数据构建 Perception"""
        details = self.parse_platform_details(platform_data.get('details', '{}'))

        # 提取探测范围（从雷达装备中推断）
        detection_range = 0.0
        detection_types = []
        tracking_capacity = 0

        for eq in equipments:
            category = eq.get('category_text', '')
            if '雷达' in category:
                # 简化：根据雷达类型估算探测范围
                if '远程' in eq.get('name', '') or '预警' in eq.get('name', ''):
                    detection_range = max(detection_range, 400.0)
                    tracking_capacity += 50
                elif '中程' in eq.get('name', ''):
                    detection_range = max(detection_range, 200.0)
                    tracking_capacity += 30
                else:
                    detection_range = max(detection_range, 100.0)
                    tracking_capacity += 20

                if 'air' not in detection_types:
                    detection_types.append('air')
                if 'surface' not in detection_types:
                    detection_types.append('surface')

            elif '声呐' in category:
                detection_range = max(detection_range, 50.0)
                if 'subsurface' not in detection_types:
                    detection_types.append('subsurface')
                tracking_capacity += 10

        # 数据链类型（基于平台级别推断）
        datalink_types = ['Link16'] if '驱逐舰' in platform_data.get('category', '') or '航母' in platform_data.get('category', '') else ['HF']

        return Perception(
            detection_range=detection_range,
            detection_types=detection_types,
            tracking_capacity=tracking_capacity,
            update_frequency=1.0,
            position={'longitude': 0.0, 'latitude': 0.0, 'altitude': 0.0},
            heading=0.0,
            speed=0.0,
            datalink_status='online',
            datalink_type=datalink_types,
            communication_range=500.0 if 'Link16' in datalink_types else 200.0
        )

    def build_control_from_platform(self, platform_data: Dict[str, Any]) -> Control:
        """从平台数据构建 Control"""
        platform_id = platform_data.get('id', 0)

        # 定义可用指令集
        available_commands = [
            'navigate',      # 导航
            'detect',        # 探测
            'communicate',   # 通信
            'fire',          # 开火
            'defend'         # 防御
        ]

        return Control(
            controller_id=None,
            control_authority='manual',
            available_commands=available_commands,
            api_endpoint=f'/api/pccs/control/{platform_id}',
            control_protocol='REST',
            message_format='json',
            command_latency=0.5,
            response_timeout=30.0,
            priority_level=5
        )

    def build_capability_from_platform(self, platform_data: Dict[str, Any],
                                       equipments: List[Dict[str, Any]]) -> Capability:
        """从平台数据构建 Capability"""
        details = self.parse_platform_details(platform_data.get('details', '{}'))
        tech_data = details.get('技术数据', {})

        # 提取速度
        max_speed = self.extract_numeric_value(tech_data.get('最高速度', '30'))
        cruise_speed = max_speed * 0.7 if max_speed > 0 else 20.0

        # 提取续航力
        endurance_text = tech_data.get('续航力', '1000')
        endurance = self.extract_numeric_value(endurance_text)
        if endurance == 0:
            endurance = 5000.0  # 默认值

        # 分析武器系统
        weapon_systems = []
        strike_range = 0.0
        strike_types = []
        firepower = 0

        for eq in equipments:
            eq_name = eq.get('name', '')
            category = eq.get('category_text', '')

            if '导弹' in category or '导弹' in eq_name:
                # 推断导弹射程
                if '远程' in eq_name or '巡航' in eq_name:
                    weapon_range = 1000.0
                    weapon_power = 90
                elif '中程' in eq_name:
                    weapon_range = 200.0
                    weapon_power = 70
                else:
                    weapon_range = 50.0
                    weapon_power = 60

                weapon_systems.append({
                    'name': eq_name,
                    'type': 'missile',
                    'range': weapon_range,
                    'firepower': weapon_power
                })

                strike_range = max(strike_range, weapon_range)
                firepower += weapon_power

                # 确定打击类型
                if '防空' in eq_name or '空空' in eq_name:
                    if 'anti-air' not in strike_types:
                        strike_types.append('anti-air')
                if '反舰' in eq_name or '舰舰' in eq_name:
                    if 'anti-surface' not in strike_types:
                        strike_types.append('anti-surface')
                if '反潜' in eq_name:
                    if 'anti-submarine' not in strike_types:
                        strike_types.append('anti-submarine')

            elif '火炮' in category or '炮' in eq_name:
                weapon_systems.append({
                    'name': eq_name,
                    'type': 'gun',
                    'range': 20.0,
                    'firepower': 40
                })
                strike_range = max(strike_range, 20.0)
                firepower += 40

        # 传感器类型
        sensor_types = []
        for eq in equipments:
            category = eq.get('category_text', '')
            if '雷达' in category and 'radar' not in sensor_types:
                sensor_types.append('radar')
            elif '声呐' in category and 'sonar' not in sensor_types:
                sensor_types.append('sonar')
            elif '光电' in category and 'eo/ir' not in sensor_types:
                sensor_types.append('eo/ir')

        # 推断任务类型和效能
        mission_types, effectiveness_scores = self.infer_mission_types_from_platform(
            platform_data, equipments
        )

        return Capability(
            sensor_type=sensor_types,
            detection_capability={
                'radar': {'range': 400.0} if 'radar' in sensor_types else {},
                'sonar': {'range': 50.0} if 'sonar' in sensor_types else {}
            },
            weapon_systems=weapon_systems,
            strike_range=strike_range,
            strike_types=strike_types,
            firepower=firepower,
            max_speed=max_speed,
            cruise_speed=cruise_speed,
            endurance=endurance,
            maneuverability='medium',
            bandwidth=100.0,
            anti_jamming_level=7,
            encryption_support=True,
            computing_power=0.0,
            storage_capacity=0.0,
            mission_types=mission_types,
            effectiveness_scores=effectiveness_scores
        )

    def build_state_from_platform(self, platform_data: Dict[str, Any]) -> State:
        """从平台数据构建 State"""
        status = platform_data.get('status', '可用')

        # 映射状态
        operational_status = 'online' if status == '可用' else 'offline'
        availability_status = 'available' if status == '可用' else 'maintenance'

        return State(
            operational_status=operational_status,
            availability_status=availability_status,
            mission_status='idle',
            health_level=1.0 if status == '可用' else 0.5,
            network_latency=10.0,
            packet_loss_rate=0.01,
            connection_strength=0.95,
            fuel_level=1.0,
            battery_level=1.0,
            ammunition_level=1.0,
            fuel_consumption_rate=100.0,
            power_consumption=5000.0,
            next_maintenance_time=None
        )

    def convert_platform_to_pccs(self, platform_data: Dict[str, Any],
                                 equipments: List[Dict[str, Any]]) -> PCCSResource:
        """
        将平台数据转换为 PCCS 资源

        Args:
            platform_data: 平台数据字典
            equipments: 平台关联的装备列表

        Returns:
            PCCSResource 实例
        """
        resource = PCCSResource(
            resource_id=platform_data['id'],
            resource_type='platform',
            name=platform_data['name'],
            category=platform_data.get('category', ''),
            perception=self.build_perception_from_platform(platform_data, equipments),
            control=self.build_control_from_platform(platform_data),
            capability=self.build_capability_from_platform(platform_data, equipments),
            state=self.build_state_from_platform(platform_data),
            tags=[platform_data.get('country', ''), platform_data.get('model_type', '')]
        )

        return resource

    def convert_equipment_to_pccs(self, equipment_data: Dict[str, Any]) -> PCCSResource:
        """
        将装备数据转换为 PCCS 资源

        Args:
            equipment_data: 装备数据字典

        Returns:
            PCCSResource 实例
        """
        category = equipment_data.get('category_text', '')

        # 为装备构建简化的 PCCS 模型
        perception = Perception(
            detection_range=100.0 if '雷达' in category else 0.0,
            detection_types=['air'] if '雷达' in category else []
        )

        control = Control(
            available_commands=['power_on', 'power_off', 'operate'],
            api_endpoint=f'/api/pccs/control/equipment/{equipment_data["id"]}',
            control_protocol='REST'
        )

        # 根据装备类型设置能力
        strike_range = 0.0
        firepower = 0
        mission_types = []

        if '导弹' in category:
            strike_range = 200.0
            firepower = 80
            mission_types = ['strike', 'air_defense']
        elif '火炮' in category:
            strike_range = 20.0
            firepower = 40
            mission_types = ['strike']
        elif '雷达' in category:
            mission_types = ['recon', 'patrol']

        capability = Capability(
            sensor_type=['radar'] if '雷达' in category else [],
            strike_range=strike_range,
            firepower=firepower,
            mission_types=mission_types,
            effectiveness_scores={mt: 0.7 for mt in mission_types}
        )

        state = State(
            operational_status='online',
            availability_status='available' if equipment_data.get('status') == '可用' else 'maintenance',
            mission_status='idle',
            health_level=1.0
        )

        resource = PCCSResource(
            resource_id=equipment_data['id'],
            resource_type='equipment',
            name=equipment_data['name'],
            category=category,
            perception=perception,
            control=control,
            capability=capability,
            state=state,
            tags=[equipment_data.get('type_code', '')]
        )

        return resource

    def batch_convert_platforms(self, platforms_with_equipments: List[Tuple[Dict, List[Dict]]]) -> List[PCCSResource]:
        """
        批量转换平台为 PCCS 资源

        Args:
            platforms_with_equipments: [(platform_data, equipments), ...]

        Returns:
            PCCS 资源列表
        """
        results = []
        for platform_data, equipments in platforms_with_equipments:
            try:
                resource = self.convert_platform_to_pccs(platform_data, equipments)
                results.append(resource)
            except Exception as e:
                print(f"转换平台 {platform_data.get('name')} 失败: {e}")
                continue

        return results

    def register_to_pool(self, resources: List[PCCSResource]) -> int:
        """
        将资源批量注册到全局资源池

        Returns:
            成功注册的资源数量
        """
        count = 0
        for resource in resources:
            if global_resource_pool.register_resource(resource):
                count += 1
        return count
