/**
 * 上传进度计算工具：根据 axios onUploadProgress 事件计算
 * 百分比、实时速度（bytes/s）与剩余时间（秒）。
 */

/**
 * 计算上传进度。
 * @param {object} event - axios onUploadProgress 事件（{ loaded, total }）
 * @param {React.MutableRefObject<Array>} samplesRef - 用于保存最近采样的 ref（数组）
 * @returns {{ percent: number, speed: number, eta: number }}
 */
export function computeUploadProgress(event, samplesRef) {
  const loaded = event.loaded || 0
  const total = event.total || 0
  const percent = total > 0 ? Math.round((loaded / total) * 100) : 0

  const now = Date.now()
  const samples = samplesRef.current || []
  samples.push({ loaded, t: now })
  // 仅保留最近 1 秒的采样，用于计算瞬时速度
  while (samples.length && now - samples[0].t > 1000) samples.shift()

  let speed = 0
  if (samples.length >= 2) {
    const first = samples[0]
    const last = samples[samples.length - 1]
    const dt = (last.t - first.t) / 1000
    if (dt > 0) speed = (last.loaded - first.loaded) / dt
  }

  const eta = speed > 0 && total > 0 ? Math.ceil((total - loaded) / speed) : 0
  return { percent, speed, eta }
}

/**
 * 格式化字节数为人类可读大小。
 * @param {number} bytes
 * @returns {string}
 */
export function formatSize(bytes) {
  if (!bytes || bytes <= 0) return '0 B'
  const units = ['B', 'KB', 'MB', 'GB', 'TB']
  const i = Math.min(Math.floor(Math.log(bytes) / Math.log(1024)), units.length - 1)
  const value = bytes / Math.pow(1024, i)
  return `${value >= 100 ? Math.round(value) : value.toFixed(1)} ${units[i]}`
}

/**
 * 格式化上传速度。
 * @param {number} bytesPerSec
 * @returns {string}
 */
export function formatSpeed(bytesPerSec) {
  return `${formatSize(bytesPerSec)}/s`
}

/**
 * 格式化剩余时间。
 * @param {number} seconds
 * @returns {string}
 */
export function formatEta(seconds) {
  if (!seconds || seconds <= 0) return '--'
  if (seconds < 60) return `${seconds} 秒`
  const m = Math.floor(seconds / 60)
  const s = seconds % 60
  return s > 0 ? `${m} 分 ${s} 秒` : `${m} 分钟`
}
