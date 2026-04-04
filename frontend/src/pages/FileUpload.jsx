import { useState } from 'react'
import { Upload, Button, Card, Typography, Space, Alert, Progress } from 'antd'
import { InboxOutlined, ArrowLeftOutlined } from '@ant-design/icons'
import { useNavigate } from 'react-router-dom'
import request from '../utils/request'

const { Title, Text } = Typography
const { Dragger } = Upload

function FileUpload() {
  const navigate = useNavigate()
  const [fileList, setFileList] = useState([])
  const [uploading, setUploading] = useState(false)
  const [error, setError] = useState(null)
  const [success, setSuccess] = useState(null)

  const handleUpload = async () => {
    if (fileList.length === 0) {
      setError('请先选择文件')
      return
    }
    setError(null)
    setSuccess(null)
    setUploading(true)

    const formData = new FormData()
    fileList.forEach(f => formData.append('file', f))

    try {
      const res = await request.post('/file_up/file_upload/', formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
      })
      if (res.data.success) {
        setSuccess(`文件 "${res.data.file_name}" 上传成功！`)
        setFileList([])
        setTimeout(() => navigate('/file_up/file_list'), 1500)
      } else {
        setError(res.data.message || '上传失败，请重试')
      }
    } catch (err) {
      setError(err.response?.data?.message || '上传失败，请稍后重试')
    } finally {
      setUploading(false)
    }
  }

  const draggerProps = {
    multiple: false,
    beforeUpload: (file) => {
      setFileList([file])
      return false
    },
    onRemove: () => setFileList([]),
    fileList: fileList.map(f => ({ uid: f.name, name: f.name, status: 'done' })),
  }

  return (
    <div style={{ maxWidth: 600, margin: '0 auto' }}>
      <Space style={{ marginBottom: 16 }}>
        <Button icon={<ArrowLeftOutlined />} onClick={() => navigate('/file_up/file_list')}>返回</Button>
      </Space>

      <Card>
        <Title level={2} style={{ marginBottom: 24 }}>上传文件</Title>

        {success && (
          <Alert message={success} type="success" showIcon style={{ marginBottom: 16 }} />
        )}
        {error && (
          <Alert
            message={error}
            type="error"
            showIcon
            closable
            style={{ marginBottom: 16 }}
            onClose={() => setError(null)}
          />
        )}

        <Dragger {...draggerProps} style={{ marginBottom: 16 }}>
          <p className="ant-upload-drag-icon">
            <InboxOutlined style={{ fontSize: 48, color: '#1677ff' }} />
          </p>
          <p className="ant-upload-text">点击或拖拽文件到此区域上传</p>
          <p className="ant-upload-hint">支持单个文件上传</p>
        </Dragger>

        {fileList.length > 0 && (
          <div style={{ marginBottom: 16 }}>
            <Text type="secondary">已选择：{fileList[0].name}</Text>
          </div>
        )}

        <Space>
          <Button
            type="primary"
            onClick={handleUpload}
            loading={uploading}
            disabled={fileList.length === 0}
          >
            {uploading ? '上传中…' : '开始上传'}
          </Button>
          <Button onClick={() => navigate('/file_up/file_list')}>取消</Button>
        </Space>
      </Card>
    </div>
  )
}

export default FileUpload
