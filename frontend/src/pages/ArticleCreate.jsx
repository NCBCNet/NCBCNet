import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import {
  Card, Form, Input, Select, Button, Upload, message, Typography, Space,
} from 'antd'
import {
  PlusOutlined, InboxOutlined, ArrowLeftOutlined,
} from '@ant-design/icons'
import MDEditor from '@uiw/react-md-editor'
import api from '../services/api'
import { useAuth } from '../store/authStore'

const { Title, Text } = Typography
const { Dragger } = Upload

function ArticleCreate() {
  const navigate = useNavigate()
  const { isAuthenticated } = useAuth()
  const [form] = Form.useForm()
  const [loading, setLoading] = useState(false)
  const [columns, setColumns] = useState([])
  const [content, setContent] = useState('')

  useEffect(() => {
    if (!isAuthenticated) {
      message.warning('请先登录')
      navigate('/usermanage/login')
      return
    }
    fetchColumns()
  }, [isAuthenticated, navigate])

  const fetchColumns = async () => {
    try {
      const res = await api.get('/articles/columns/')
      setColumns(res.data)
    } catch {
      // ignore
    }
  }

  const onFinish = async (values) => {
    if (!content.trim()) {
      message.warning('请输入文章内容')
      return
    }
    setLoading(true)
    try {
      const formData = new FormData()
      formData.append('title', values.title)
      formData.append('content', content)
      if (values.column) formData.append('column', values.column)
      if (values.tags) formData.append('tags', values.tags)
      if (values.avatar?.file?.originFileObj) {
        formData.append('avatar', values.avatar.file.originFileObj)
      }

      const res = await api.post('/articles/create/', formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
      })
      message.success('文章发布成功！')
      navigate(`/article/article_detail/${res.data.id}`)
    } catch (err) {
      const errData = err.response?.data
      if (errData) {
        const msgs = Object.values(errData).flat().join('；')
        message.error(msgs || '发布失败')
      } else {
        message.error('发布失败，请检查网络')
      }
    } finally {
      setLoading(false)
    }
  }

  return (
    <div style={{ maxWidth: 900, margin: '0 auto' }}>
      <Button
        type="link"
        icon={<ArrowLeftOutlined />}
        style={{ padding: 0, marginBottom: 16 }}
        onClick={() => navigate('/article')}
      >
        返回论坛
      </Button>

      <Title level={3} style={{ marginBottom: 24 }}>写文章</Title>

      <Form
        form={form}
        layout="vertical"
        onFinish={onFinish}
      >
        <Card style={{ marginBottom: 24, borderRadius: 8 }}>
          <Form.Item
            name="title"
            label="文章标题"
            rules={[{ required: true, message: '请输入文章标题' }]}
          >
            <Input placeholder="输入文章标题..." size="large" />
          </Form.Item>

          <Form.Item label="标题图" name="avatar">
            <Dragger
              accept="image/*"
              maxCount={1}
              beforeUpload={() => false}
              showUploadList={{ showPreviewIcon: false }}
            >
              <p className="ant-upload-drag-icon">
                <InboxOutlined />
              </p>
              <p className="ant-upload-text">点击或拖拽图片到此区域上传标题图</p>
            </Dragger>
          </Form.Item>

          <Space size={16} style={{ width: '100%' }} wrap>
            <Form.Item name="column" label="栏目" style={{ minWidth: 180 }}>
              <Select placeholder="请选择栏目..." allowClear>
                {columns.map((col) => (
                  <Select.Option key={col.id} value={col.id}>{col.title}</Select.Option>
                ))}
              </Select>
            </Form.Item>

            <Form.Item name="tags" label="标签" style={{ minWidth: 300 }}>
              <Input placeholder="多个标签用逗号分隔" />
            </Form.Item>
          </Space>
        </Card>

        {/* Markdown 编辑器 */}
        <Card style={{ marginBottom: 24, borderRadius: 8 }} title="文章内容">
          <Form.Item style={{ marginBottom: 0 }}>
            <MDEditor
              value={content}
              onChange={setContent}
              height={500}
              preview="edit"
              style={{ borderRadius: 6 }}
            />
          </Form.Item>
        </Card>

        <div style={{ textAlign: 'right' }}>
          <Button
            style={{ marginRight: 12 }}
            onClick={() => navigate('/article')}
          >
            取消
          </Button>
          <Button
            type="primary"
            htmlType="submit"
            loading={loading}
            icon={<PlusOutlined />}
            style={{ background: '#6f42c1', borderColor: '#6f42c1' }}
          >
            发布文章
          </Button>
        </div>
      </Form>
    </div>
  )
}

export default ArticleCreate