import { useState } from 'react'
import {
  Badge, Button, Drawer, Empty, List, Progress, Tag, Typography,
} from 'antd'
import { ClearOutlined, CloudUploadOutlined } from '@ant-design/icons'
import { useUpload } from '../store/uploadStore'
import { formatEta, formatSize, formatSpeed } from '../utils/uploadProgress'

const { Text } = Typography

const STATUS = {
  uploading: { color: 'processing', label: '上传中' },
  processing: { color: 'processing', label: '处理中' },
  success: { color: 'success', label: '完成' },
  failed: { color: 'error', label: '失败' },
}

/** 右上角上传任务入口 + 集中查看抽屉。 */
function UploadPanel() {
  const { tasks, activeCount, clearFinished } = useUpload()
  const [open, setOpen] = useState(false)

  return (
    <>
      <Badge count={activeCount} size="small" offset={[-6, 4]}>
        <Button
          type="text"
          aria-label="上传任务"
          icon={<CloudUploadOutlined />}
          style={{ color: '#fff' }}
          onClick={() => setOpen(true)}
        />
      </Badge>

      <Drawer
        title="上传任务"
        placement="right"
        width={420}
        open={open}
        onClose={() => setOpen(false)}
        extra={tasks.length > 0 && (
          <Button type="text" size="small" icon={<ClearOutlined />} onClick={clearFinished}>
            清除已完成
          </Button>
        )}
      >
        {tasks.length === 0 ? (
          <Empty description="暂无上传任务" />
        ) : (
          <List
            dataSource={tasks}
            renderItem={(t) => {
              const st = STATUS[t.status] || STATUS.uploading
              return (
                <List.Item key={t.id}>
                  <div style={{ width: '100%' }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 6 }}>
                      <Text strong ellipsis={{ tooltip: t.fileName }} style={{ maxWidth: 230 }}>
                        {t.fileName}
                      </Text>
                      <Tag color={st.color}>{st.label}</Tag>
                    </div>
                    <Progress
                      percent={t.percent}
                      size="small"
                      status={t.status === 'failed' ? 'exception' : t.status === 'success' ? 'success' : 'active'}
                    />
                    {t.status === 'uploading' || t.status === 'processing' ? (
                      <Text type="secondary" style={{ fontSize: 12 }}>
                        {formatSpeed(t.speed)} · 剩余 {formatEta(t.eta)} · {formatSize(t.fileSize)}
                      </Text>
                    ) : t.status === 'failed' ? (
                      <Text type="danger" style={{ fontSize: 12 }}>{t.error}</Text>
                    ) : (
                      <Text type="secondary" style={{ fontSize: 12 }}>{formatSize(t.fileSize)}</Text>
                    )}
                  </div>
                </List.Item>
              )
            }}
          />
        )}
      </Drawer>
    </>
  )
}

export default UploadPanel
