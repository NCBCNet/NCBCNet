import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import {
  Button, Card, Select, Space, Typography, Upload, message,
} from 'antd'
import { ArrowLeftOutlined, InboxOutlined } from '@ant-design/icons'
import api from '../services/api'
import { useUpload } from '../store/uploadStore'

const { Title, Text } = Typography
const { Dragger } = Upload

function FileUpload() {
  const navigate = useNavigate()
  const { uploadFile } = useUpload()
  const [folders, setFolders] = useState([])
  const [folderId, setFolderId] = useState(undefined)
  const [uploading, setUploading] = useState(false)

  // 载入顶层文件夹供选择（嵌套选择请进入云盘对应文件夹后使用快速上传）
  useEffect(() => {
    api.get('/folders/')
      .then((res) => setFolders(res.data))
      .catch(() => {})
  }, [])

  const handleUpload = async ({ file, onSuccess, onError }) => {
    setUploading(true)
    const { ok } = await uploadFile(file, folderId)
    setUploading(false)
    if (ok) {
      message.success(`「${file.name}」上传成功`)
      onSuccess?.()
      navigate('/file_up/file_list')
    } else {
      message.error(`「${file.name}」上传失败`)
      onError?.()
    }
  }

  return (
    <div style={{ maxWidth: 720, margin: '0 auto' }}>
      <Button
        type="link"
        icon={<ArrowLeftOutlined />}
        style={{ padding: 0, marginBottom: 16 }}
        onClick={() => navigate('/file_up/file_list')}
      >
        返回云盘
      </Button>
      <Title level={3}>上传文件</Title>
      <Text type="secondary">上传到云盘，单个文件最大 2GB</Text>

      <Card style={{ marginTop: 16, borderRadius: 8 }}>
        <Space direction="vertical" style={{ width: '100%' }} size={16}>
          <div>
            <Text strong>目标文件夹</Text>
            <Select
              style={{ width: '100%', marginTop: 8 }}
              placeholder="根目录"
              allowClear
              value={folderId}
              onChange={setFolderId}
              options={folders.map((f) => ({ label: f.name, value: f.id }))}
            />
          </div>

          <Dragger
            multiple={false}
            disabled={uploading}
            showUploadList={false}
            customRequest={handleUpload}
          >
            <p className="ant-upload-drag-icon">
              <InboxOutlined style={{ color: '#6f42c1' }} />
            </p>
            <p className="ant-upload-text">点击或拖拽文件到此处上传</p>
            <p className="ant-upload-hint">支持大文件流式上传，将上传到所选文件夹</p>
          </Dragger>

          {uploading && (
            <Text type="secondary" style={{ fontSize: 12 }}>
              上传中… 进度与速度见右上角「上传任务」
            </Text>
          )}
        </Space>
      </Card>
    </div>
  )
}

export default FileUpload
