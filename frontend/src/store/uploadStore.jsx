import { createContext, useCallback, useContext, useRef, useState } from 'react'
import api from '../services/api'
import { computeUploadProgress } from '../utils/uploadProgress'

const UploadContext = createContext(null)

/**
 * 全局上传任务中心：集中管理所有上传任务，
 * 供右上角「上传任务」面板集中查看（状态/进度/速度/剩余时间）。
 */
export function UploadProvider({ children }) {
  const [tasks, setTasks] = useState([])
  const idRef = useRef(0)
  const samplesRef = useRef({})

  const updateTask = useCallback((id, patch) => {
    setTasks((prev) => prev.map((t) => (t.id === id ? { ...t, ...patch } : t)))
  }, [])

  /**
   * 上传一个文件，登记为一个任务并返回 Promise。
   * 始终 resolve，返回 { id, ok }：ok 表示上传是否成功（含服务器处理完成）。
   * 状态流转：uploading(传输中) → processing(已传完，服务器处理中) → success / failed
   */
  const uploadFile = useCallback((file, folderId) => {
    const id = ++idRef.current
    samplesRef.current[id] = []

    setTasks((prev) => [
      {
        id,
        fileName: file.name,
        fileSize: file.size,
        status: 'uploading',
        percent: 0,
        speed: 0,
        eta: 0,
        error: null,
      },
      ...prev,
    ])

    const formData = new FormData()
    formData.append('file', file)
    if (folderId) formData.append('folder', folderId)

    return api
      .post('/files/upload/', formData, {
        onUploadProgress: (event) => {
          const { percent, speed, eta } = computeUploadProgress(event, {
            current: samplesRef.current[id],
          })
          const sent = event.total > 0 && event.loaded >= event.total
          updateTask(id, { percent, speed, eta, status: sent ? 'processing' : 'uploading' })
        },
      })
      .then(() => {
        updateTask(id, { status: 'success', percent: 100 })
        return { id, ok: true }
      })
      .catch((err) => {
        updateTask(id, { status: 'failed', error: err.response?.data?.message || '上传失败' })
        return { id, ok: false }
      })
  }, [updateTask])

  const clearFinished = useCallback(() => {
    setTasks((prev) => prev.filter((t) => t.status === 'uploading' || t.status === 'processing'))
  }, [])

  const activeCount = tasks.filter(
    (t) => t.status === 'uploading' || t.status === 'processing',
  ).length

  return (
    <UploadContext.Provider value={{ tasks, uploadFile, clearFinished, activeCount }}>
      {children}
    </UploadContext.Provider>
  )
}

export function useUpload() {
  const ctx = useContext(UploadContext)
  if (!ctx) {
    throw new Error('useUpload must be used within an UploadProvider')
  }
  return ctx
}

export default UploadContext
