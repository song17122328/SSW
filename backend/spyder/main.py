import requests
from bs4 import BeautifulSoup
import json  # 使用 json 库来处理 JSON 数据
import time
import re
import urllib.parse

# --- 配置区 ---

EQUIPMENT_LIST = [
    "尼米兹号航空母舰",
    "伊丽莎白女王号航空母舰",
    "库兹涅佐夫号航空母舰",
    "维克拉玛蒂亚号航空母舰",
    "戴高乐号航空母舰",
    "辽宁号航空母舰",
    "朱姆沃尔特号驱逐舰",
    "维克兰特号航空母舰 (IAC-I)",
    "威尔士亲王号航空母舰 (R09)",
    "阿利伯克级驱逐舰",
    "阿基坦级巡防舰",
    "西北风级两栖攻击舰",
    "弗吉尼亚级核潜艇",
    "朱姆沃尔特级驱逐舰",
    "45型驱逐舰",
    "元级潜艇",
    "凯旋级核潜艇",
    "F-22猛禽战斗机",
    "B-2幽灵战略轰炸机",
    "F-35闪电II战斗机",
    "F-16战隼战斗机",
    "F-14雄猫式战斗机",
    "A-10雷电二式攻击机",
    "C-130运输机",
    "MQ-9收割者侦察机",
    "AH-64阿帕契直升机",
    "E-3空中预警机"
]

# 修改输出文件名
OUTPUT_FILE = 'military_equipment_data.json'
BASE_URL = "https://zh.wikipedia.org/wiki/"
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/108.0.0.0 Safari/537.36'
}
MAX_RETRIES = 3
RETRY_DELAY = 3

# --- 爬虫核心代码 ---

def clean_text(text):
    """清理文本，去除引用标记和多余的空格"""
    return re.sub(r'\[.*?\]', '', text).strip()

def scrape_to_nested_dict(session, equipment_name):
    """
    爬取单个装备页面，将infobox数据提取为嵌套字典。
    """
    url = BASE_URL + urllib.parse.quote(equipment_name)
    print(f"正在处理: {equipment_name}")

    for attempt in range(MAX_RETRIES):
        try:
            response = session.get(url, headers=HEADERS, timeout=15)
            response.raise_for_status()

            soup = BeautifulSoup(response.text, 'html.parser')
            infobox = soup.select_one('table.infobox')

            if not infobox:
                print(f"  [警告] 在页面上未找到 '{equipment_name}' 的信息框。")
                return None

            # --- 核心逻辑：解析为嵌套字典 ---
            equipment_data = {}
            current_section_dict = None  # 指向当前正在填充的子字典

            for row in infobox.find_all('tr'):
                # 检查是否为分节标题行 (通常是只有一个th且colspan="2")
                header_cell = row.find('th')
                data_cell = row.find('td')

                if header_cell and not data_cell: # 这是一个分节标题
                    section_title = clean_text(header_cell.get_text())
                    if section_title:
                        # 为新分节创建一个空字典
                        equipment_data[section_title] = {}
                        # 将当前指针指向这个新的子字典
                        current_section_dict = equipment_data[section_title]
                
                # 检查是否为常规的键值对行
                elif header_cell and data_cell:
                    prop_name = clean_text(header_cell.get_text())
                    prop_value = clean_text(data_cell.get_text())
                    
                    if prop_name:
                        # 如果当前在某个分节内，则添加到子字典
                        if current_section_dict is not None:
                            current_section_dict[prop_name] = prop_value
                        # 否则，添加到顶层字典
                        else:
                            equipment_data[prop_name] = prop_value
            
            print(f"  [成功] 提取到数据并构建了字典结构。")
            return equipment_data

        except requests.exceptions.RequestException as e:
            print(f"  [错误] 请求 '{equipment_name}' 失败 (第 {attempt + 1}/{MAX_RETRIES} 次尝试): {e}")
            if attempt < MAX_RETRIES - 1:
                print(f"  将在 {RETRY_DELAY} 秒后重试...")
                time.sleep(RETRY_DELAY)
            else:
                print(f"  [严重] 所有重试均失败，跳过此项目。")
                return None
    return None

def main():
    """主函数，负责调度爬取任务和保存数据"""
    # 最终的大字典
    all_data_dict = {}
    
    with requests.Session() as session:
        for name in EQUIPMENT_LIST:
            scraped_data = scrape_to_nested_dict(session, name)
            
            if scraped_data:
                # 将爬取到的单个装备字典，以其名称为键，存入总字典
                all_data_dict[name] = scraped_data
            
            time.sleep(1)

    if not all_data_dict:
        print("\n未能爬取到任何数据，程序结束。")
        return

    # 将最终的大字典写入JSON文件
    try:
        with open(OUTPUT_FILE, 'w', encoding='utf-8') as jsonfile:
            # json.dump() 是关键函数
            # ensure_ascii=False 确保中文字符能被正确写入，而不是被转义成\uXXXX
            # indent=4 让JSON文件格式化，带缩进，非常易于阅读
            json.dump(all_data_dict, jsonfile, ensure_ascii=False, indent=4)
        
        print(f"\n任务完成！所有数据已成功保存到文件: {OUTPUT_FILE}")
        
    except IOError as e:
        print(f"\n[致命错误] 写入文件时发生错误: {e}")

if __name__ == "__main__":
    main()