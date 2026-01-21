/**
 * 📝 格式化工具函数
 */

export function formatDateTime(date, format = 'YYYY-MM-DD HH:mm:ss') {
  if (!date) return '-'
  
  const d = new Date(date)
  const year = d.getFullYear()
  const month = String(d.getMonth() + 1).padStart(2, '0')
  const day = String(d.getDate()).padStart(2, '0')
  const hour = String(d.getHours()).padStart(2, '0')
  const minute = String(d.getMinutes()).padStart(2, '0')
  const second = String(d.getSeconds()).padStart(2, '0')
  
  return format
    .replace('YYYY', year)
    .replace('MM', month)
    .replace('DD', day)
    .replace('HH', hour)
    .replace('mm', minute)
    .replace('ss', second)
}

export function formatNumber(num, decimals = 2) {
  if (num === null || num === undefined) return '-'
  return Number(num).toFixed(decimals)
}

export function formatPercent(num, decimals = 1) {
  if (num === null || num === undefined) return '-'
  return (Number(num) * 100).toFixed(decimals) + '%'
}

export function formatDistance(meters) {
  if (!meters) return '0 m'
  
  if (meters >= 1000) {
    return (meters / 1000).toFixed(1) + ' km'
  }
  return Math.round(meters) + ' m'
}

// 🚀 新增：格式化速度
export function formatSpeed(speed, unit = 'knots') {
  if (speed === null || speed === undefined || speed === 0) return '0 节'
  
  const speedNum = Number(speed)
  
  switch (unit) {
    case 'knots':
    case 'kn':
      return speedNum.toFixed(1) + ' 节'
    case 'kmh':
    case 'km/h':
      return speedNum.toFixed(1) + ' km/h'
    case 'ms':
    case 'm/s':
      return speedNum.toFixed(1) + ' m/s'
    case 'mach':
      return 'Mach ' + speedNum.toFixed(2)
    default:
      return speedNum.toFixed(1) + ' 节'
  }
}

// 🌊 新增：格式化海拔/深度
export function formatAltitude(altitude) {
  if (altitude === null || altitude === undefined) return '-'
  
  const alt = Number(altitude)
  if (alt === 0) return '海平面'
  if (alt > 0) return `+${alt.toFixed(0)} m`
  return `${alt.toFixed(0)} m`
}

// 🎯 新增：格式化角度
export function formatAngle(angle, unit = 'degree') {
  if (angle === null || angle === undefined) return '-'
  
  const angleNum = Number(angle)
  
  switch (unit) {
    case 'degree':
    case 'deg':
      return angleNum.toFixed(1) + '°'
    case 'radian':
    case 'rad':
      return angleNum.toFixed(3) + ' rad'
    case 'bearing':
      // 转换为方位角格式 (0-360°)
      return (((angleNum % 360) + 360) % 360).toFixed(1) + '°'
    default:
      return angleNum.toFixed(1) + '°'
  }
}

// ⚡ 新增：格式化功率
export function formatPower(power, unit = 'kw') {
  if (power === null || power === undefined) return '-'
  
  const powerNum = Number(power)
  
  switch (unit) {
    case 'w':
    case 'watt':
      if (powerNum >= 1000000) {
        return (powerNum / 1000000).toFixed(1) + ' MW'
      }
      if (powerNum >= 1000) {
        return (powerNum / 1000).toFixed(1) + ' kW'
      }
      return powerNum.toFixed(0) + ' W'
    case 'kw':
    case 'kilowatt':
      if (powerNum >= 1000) {
        return (powerNum / 1000).toFixed(1) + ' MW'
      }
      return powerNum.toFixed(1) + ' kW'
    case 'hp':
    case 'horsepower':
      return powerNum.toFixed(1) + ' HP'
    default:
      return powerNum.toFixed(1) + ' kW'
  }
}

// 📏 新增：格式化重量
export function formatWeight(weight, unit = 'kg') {
  if (weight === null || weight === undefined) return '-'
  
  const weightNum = Number(weight)
  
  switch (unit) {
    case 'g':
    case 'gram':
      if (weightNum >= 1000000) {
        return (weightNum / 1000000).toFixed(1) + ' 吨'
      }
      if (weightNum >= 1000) {
        return (weightNum / 1000).toFixed(1) + ' kg'
      }
      return weightNum.toFixed(0) + ' g'
    case 'kg':
    case 'kilogram':
      if (weightNum >= 1000) {
        return (weightNum / 1000).toFixed(1) + ' 吨'
      }
      return weightNum.toFixed(1) + ' kg'
    case 'ton':
    case 'tonne':
      return weightNum.toFixed(1) + ' 吨'
    default:
      return weightNum.toFixed(1) + ' kg'
  }
}

// 🔥 新增：格式化温度
export function formatTemperature(temp, unit = 'celsius') {
  if (temp === null || temp === undefined) return '-'
  
  const tempNum = Number(temp)
  
  switch (unit) {
    case 'celsius':
    case 'c':
      return tempNum.toFixed(1) + '°C'
    case 'fahrenheit':
    case 'f':
      return tempNum.toFixed(1) + '°F'
    case 'kelvin':
    case 'k':
      return tempNum.toFixed(1) + ' K'
    default:
      return tempNum.toFixed(1) + '°C'
  }
}

// 💾 新增：格式化文件大小
export function formatFileSize(bytes) {
  if (!bytes || bytes === 0) return '0 B'
  
  const sizes = ['B', 'KB', 'MB', 'GB', 'TB']
  const i = Math.floor(Math.log(bytes) / Math.log(1024))
  
  return (bytes / Math.pow(1024, i)).toFixed(1) + ' ' + sizes[i]
}

// ⏱️ 新增：格式化持续时间
export function formatDuration(seconds) {
  if (!seconds || seconds === 0) return '0秒'
  
  const hours = Math.floor(seconds / 3600)
  const minutes = Math.floor((seconds % 3600) / 60)
  const secs = Math.floor(seconds % 60)
  
  if (hours > 0) {
    return `${hours}小时${minutes}分钟${secs}秒`
  } else if (minutes > 0) {
    return `${minutes}分钟${secs}秒`
  } else {
    return `${secs}秒`
  }
}

// 💰 新增：格式化货币
export function formatCurrency(amount, currency = 'CNY') {
  if (amount === null || amount === undefined) return '-'
  
  const amountNum = Number(amount)
  
  switch (currency) {
    case 'CNY':
    case 'RMB':
      if (amountNum >= 100000000) {
        return (amountNum / 100000000).toFixed(1) + '亿元'
      } else if (amountNum >= 10000) {
        return (amountNum / 10000).toFixed(1) + '万元'
      }
      return amountNum.toLocaleString('zh-CN') + '元'
    case 'USD':
      return '$' + amountNum.toLocaleString('en-US')
    case 'EUR':
      return '€' + amountNum.toLocaleString('de-DE')
    default:
      return amountNum.toLocaleString() + ' ' + currency
  }
}

// 🚢 新增：格式化装备类型
export function formatEquipmentType(type) {
  const typeMap = {
    'ship': '🚢 舰船',
    'submarine': '🟢 潜艇',
    'aircraft': '✈️ 飞机',
    'helicopter': '🚁 直升机',
    'missile': '🚀 导弹',
    'torpedo': '🎯 鱼雷',
    'radar': '📡 雷达',
    'sonar': '🔊 声呐',
    'weapon': '⚔️ 武器',
    'sensor': '👁️ 传感器',
    'communication': '📻 通信',
    'electronic': '💻 电子设备'
  }
  return typeMap[type] || type
}

export function formatEquipmentStatus(status) {
  const statusMap = {
    'active': '✅ 可用',
    'inactive': '⚪ 停用',
    'maintenance': '🔧 维护',
    'damaged': '❌ 损坏',
    'ready': '🟢 就绪',
    'busy': '🟡 忙碌',
    'offline': '🔴 离线'
  }
  return statusMap[status] || status
}

// 🎖️ 新增：格式化威胁等级
export function formatThreatLevel(level) {
  const levelMap = {
    'low': '🟢 低威胁',
    'medium': '🟡 中威胁',
    'high': '🟠 高威胁',
    'critical': '🔴 极高威胁',
    'unknown': '⚪ 未知'
  }
  return levelMap[level] || level
}

// 🎯 新增：格式化命中率
export function formatAccuracy(accuracy) {
  if (accuracy === null || accuracy === undefined) return '-'
  
  const acc = Number(accuracy)
  if (acc >= 0.9) return `🎯 ${formatPercent(acc)} (优秀)`
  if (acc >= 0.7) return `✅ ${formatPercent(acc)} (良好)`
  if (acc >= 0.5) return `⚠️ ${formatPercent(acc)} (一般)`
  return `❌ ${formatPercent(acc)} (较差)`
}

// 📊 新增：格式化优先级
export function formatPriority(priority) {
  const priorityMap = {
    'low': '🔵 低优先级',
    'normal': '🟢 普通',
    'high': '🟡 高优先级',
    'urgent': '🔴 紧急',
    'critical': '🚨 严重'
  }
  return priorityMap[priority] || priority
}

// 🌐 新增：格式化坐标
export function formatCoordinate(lat, lng, format = 'decimal') {
  if (lat === null || lat === undefined || lng === null || lng === undefined) {
    return '-'
  }
  
  switch (format) {
    case 'decimal':
      return `${Number(lat).toFixed(6)}, ${Number(lng).toFixed(6)}`
    case 'dms':
      // 度分秒格式
      return `${convertToDMS(lat, 'lat')}, ${convertToDMS(lng, 'lng')}`
    default:
      return `${Number(lat).toFixed(4)}, ${Number(lng).toFixed(4)}`
  }
}

// 辅助函数：转换为度分秒格式
function convertToDMS(coordinate, type) {
  const absolute = Math.abs(coordinate)
  const degrees = Math.floor(absolute)
  const minutes = Math.floor((absolute - degrees) * 60)
  const seconds = ((absolute - degrees - minutes / 60) * 3600).toFixed(1)
  
  const direction = type === 'lat' 
    ? (coordinate >= 0 ? 'N' : 'S')
    : (coordinate >= 0 ? 'E' : 'W')
  
  return `${degrees}°${minutes}'${seconds}"${direction}`
}

// 默认导出所有函数
export default {
  formatDateTime,
  formatNumber,
  formatPercent,
  formatDistance,
  formatSpeed,
  formatAltitude,
  formatAngle,
  formatPower,
  formatWeight,
  formatTemperature,
  formatFileSize,
  formatDuration,
  formatCurrency,
  formatEquipmentType,
  formatEquipmentStatus,
  formatThreatLevel,
  formatAccuracy,
  formatPriority,
  formatCoordinate
}
