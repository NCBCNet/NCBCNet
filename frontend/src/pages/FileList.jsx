import { useEffect, useState } from 'react'
import { Table, Button, Space, Popconfirm, Typography, Spin, Empty, message } from 'antd'
import { UploadOutlined, DeleteOutlined, DownloadOutlined, ReloadOutlined } from '@ant-design/icons'
import { useNavigate } from 'react-router-dom'
import request from '../utils/request'

const { Title } = Typography

function FileList() {
  const navigate = useNavigate()
  const [files, setFiles] = useState([])
  const [loading, setLoading] = useState(true)
  const [deletingId, setDeletingId] = useState(null)

  const fetchFiles = () => {
    setLoading(true)
    request.get('/file_up/api/list/')
      .then(res => setFiles(res.data))
      .catch(() => setFiles([]))
      .finally(() => setLoading(false))
  }

  useEffect(() => { fetchFiles() }, [])

  const handleDelete = async (id) => {
    setDeletingId(id)
    try {
      await request.delete(`/file_up/api/delete/${id}/`)
      message.success('文件已删除')
      setFiles(prev => prev.filter(f => f.id !== id))
    } catch {
      message.error('删除失败，请稍后重试')
    } finally {
      setDeletingId(null)
    }
  }

  const columns = [
    {
      title: '文件名',
      dataIndex: 'original_name',
      key: 'original_name',
      ellipsis: true,
    },
    {
      title: '大小',
      dataIndex: 'file_size_display',
      key: 'file_size_display',
      width: 100,
    },
    {
      title: '文件夹',
      dataIndex: 'folder',
      key: 'folder',
      width: 120,
      render: val => val || '根目录',
    },
    {
      title: '上传时间',
      dataIndex: 'uploaded_at',
      key: 'uploaded_at',
      width: 180,
      render: val => new Date(val).toLocaleString('zh-CN'),
    },
    {
      title: '操作',
      key: 'actions',
      width: 160,
      render: (_, record) => (
        <Space>
          <Button
            size="small"
            icon={<DownloadOutlined />}
            href={`/file_up/file_download/${record.id}/`}
            target="_blank"
            rel="noopener noreferrer"
          >
            下载
          </Button>
          <Popconfirm
            title="确认删除该文件？"
            okText="删除"
            cancelText="取消"
            onConfirm={() => handleDelete(record.id)}
          >
            <Button
              size="small"
              danger
              icon={<DeleteOutlined />}
              loading={deletingId === record.id}
            >
              删除
            </Button>
          </Popconfirm>
        </Space>
      ),
    },
  ]

  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16 }}>
        <Title level={2} style={{ margin: 0 }}>文件管理</Title>
        <Space>
          <Button icon={<ReloadOutlined />} onClick={fetchFiles}>刷新</Button>
          <Button type="primary" icon={<UploadOutlined />} onClick={() => navigate('/file_up/file_upload')}>
            上传文件
          </Button>
        </Space>
      </div>

      <Table
        dataSource={files}
        columns={columns}
        rowKey="id"
        loading={loading}
        locale={{ emptyText: <Empty description="暂无文件" /> }}
        pagination={{ pageSize: 20, showTotal: total => `共 ${total} 个文件` }}
      />
    </div>
  )
}

export default FileList
