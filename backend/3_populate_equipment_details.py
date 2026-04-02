#!/usr/bin/env python3
# 3_populate_equipment_details.py - 为装备填充基本详细信息
import sqlite3
import json

DB_NAME = 'military_data.db'

# 装备详细信息模板
def generate_equipment_details(name, type_code, category_text):
    """根据装备类型生成基本的详细信息"""

    # 基础信息
    details = {
        "概况": {
            "名称": name,
            "分类": category_text,
            "类型代码": type_code
        },
        "技术数据": {}
    }

    # 根据类型代码添加具体参数
    if type_code == 'S':  # Sense (感知)
        if '雷达' in category_text:
            details["技术数据"] = {
                "探测距离": "根据型号而定",
                "频率范围": "X/S/C 波段",
                "目标容量": "多目标跟踪",
                "扫描模式": "机械扫描/相控阵"
            }
        elif '声呐' in category_text:
            details["技术数据"] = {
                "探测距离": "中远程",
                "工作频率": "中低频",
                "工作模式": "主动/被动",
                "目标识别": "声纹识别"
            }
        elif '光电' in category_text or '红外' in category_text:
            details["技术数据"] = {
                "探测距离": "视距范围",
                "波段": "可见光/红外",
                "跟踪模式": "自动跟踪",
                "稳定系统": "三轴稳定"
            }
        else:
            details["技术数据"] = {
                "探测能力": "环境感知",
                "工作模式": "主动/被动",
                "数据输出": "数字信号"
            }

    elif type_code == 'C':  # Command (控制)
        if '数据链' in category_text:
            details["技术数据"] = {
                "传输速率": "高速数据链",
                "通信距离": "远程",
                "加密等级": "军用级",
                "网络拓扑": "战术网络"
            }
        elif '电子战' in category_text or '对抗' in category_text:
            details["技术数据"] = {
                "干扰频段": "宽频段",
                "干扰功率": "高功率",
                "工作模式": "主动/被动",
                "对抗能力": "多威胁对抗"
            }
        elif '诱饵' in category_text:
            details["技术数据"] = {
                "诱饵类型": "箔条/红外/角反射器",
                "发射距离": "中远程",
                "持续时间": "根据型号",
                "载弹量": "多发"
            }
        else:
            details["技术数据"] = {
                "控制能力": "指挥控制",
                "通信协议": "标准军用协议",
                "响应时间": "毫秒级"
            }

    elif type_code == 'A':  # Act (执行)
        if '导弹' in name or '导弹' in category_text:
            details["技术数据"] = {
                "射程": "根据型号",
                "制导方式": "主动/半主动雷达",
                "弹头类型": "高爆破片",
                "速度": "超音速/亚音速",
                "打击能力": "空中/水面/水下目标"
            }
        elif '鱼雷' in name or '鱼雷' in category_text:
            details["技术数据"] = {
                "射程": "中远程",
                "制导方式": "声自导/线导",
                "速度": "高速/超高速",
                "弹头威力": "高爆"
            }
        elif '火炮' in category_text or '炮' in name:
            details["技术数据"] = {
                "口径": "根据型号",
                "射程": "中远程",
                "射速": "根据型号",
                "弹药类型": "多种"
            }
        else:
            details["技术数据"] = {
                "作战能力": "打击/防御",
                "有效距离": "根据型号",
                "命中精度": "高精度"
            }

    return details

def main():
    """为所有装备填充详细信息"""
    print("=== 开始填充装备详细信息 ===\n")

    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    # 获取所有装备
    cursor.execute('SELECT id, name, type_code, category_text FROM equipments')
    equipments = cursor.fetchall()

    print(f"找到 {len(equipments)} 个装备，正在生成详细信息...\n")

    updated_count = 0
    for equipment in equipments:
        eq_id = equipment['id']
        name = equipment['name']
        type_code = equipment['type_code']
        category_text = equipment['category_text']

        # 生成详细信息
        details = generate_equipment_details(name, type_code, category_text)
        details_json = json.dumps(details, ensure_ascii=False)

        # 更新数据库
        cursor.execute(
            'UPDATE equipments SET details = ? WHERE id = ?',
            (details_json, eq_id)
        )

        updated_count += 1
        if updated_count % 10 == 0:
            print(f"  已处理 {updated_count} 个装备...")

    conn.commit()
    conn.close()

    print(f"\n✓ 成功为 {updated_count} 个装备填充了详细信息！")
    print("\n示例：")
    print("  - 雷达装备包含：探测距离、频率范围、目标容量等")
    print("  - 导弹装备包含：射程、制导方式、速度等")
    print("  - 数据链装备包含：传输速率、通信距离、加密等级等")

if __name__ == '__main__':
    main()
