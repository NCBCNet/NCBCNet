import { useState, useEffect } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import {
  Card, Form, Input, Select, Button, Upload, message, Typography, Space, Spin,
} from 'antd'
import {
  SaveOutlined, InboxOutlined, ArrowLeftOutlined,
} from '@ant-design/icons'
import MDEditor from '@uiw/react-md-editor'
import api from '../services/api'
import { useAuth } from '../store/authStore'

const { Title } = Typography
const { Dragger } = Upload

function ArticleEdit() {
  const { id } = useParams()
  const navigate = useNavigate()
  const { isAuthenticated } = useAuth()
  const [form] = Form.useForm()
  const [loading, setLoading] = useState(false)
  const [fetching, setFetching] = useState(true)
  const [columns, setColumns] = useState([])
  const [content, setContent] = useState('')

  useEffect(() => {
    if (!isAuthenticated) {
      message.warning('请先登录')
      navigate('/usermanage/login')
      return
    }
    fetchArticle()
    fetchColumns()
  }, [id, isAuthenticated, navigate])

  const fetchArticle = async () => {
    try {
      const res = await api.get(`/articles/${id}/`)
      const article = res.data
      form.setFieldsValue({
        title: article.title,
        column: article.column?.id || undefined,
        tags: article.tags?.join(', ') || '',
      })
      setContent(article.content)
    } catch {
      message.error('文章不存在或无权编辑')
      navigate('/article')
    } finally {
      setFetching(false)
    }
  }

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

      await api.put(`/articles/${id}/update/`, formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
      })
      message.success('文章更新成功！')
      navigate(`/article/article_detail/${id}`)
    } catch (err) {
      const errData = err.response?.data
      if (errData) {
        const msgs = Object.values(errData).flat().join('；')
        message.error(msgs || '更新失败')
      } else {
        message.error('更新失败，请检查网络')
      }
    } finally {
      setLoading(false)
    }
  }

  if (fetching) {
    return <div style={{ textAlign: 'center', padding: 80 }}><Spin size="large" /></div>
  }

  return (
    <div style={{ maxWidth: 900, margin: '0 auto' }}>
      <Button
        type="link"
        icon={<ArrowLeftOutlined />}
        style={{ padding: 0, marginBottom: 16 }}
        onClick={() => navigate(`/article/article_detail/${id}`)}
      >
        返回文章
      </Button>

      <Title level={3} style={{ marginBottom: 24 }}>编辑文章</Title>

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

          <Form.Item label="标题图（留空则保持原图）" name="avatar">
            <Dragger
              accept="image/*"
              maxCount={1}
              beforeUpload={() => false}
              showUploadList={{ showPreviewIcon: false }}
            >
              <p className="ant-upload-drag-icon">
                <InboxOutlined />
              </p>
              <p className="ant-upload-text">点击或拖拽新图片替换标题图</p>
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
            onClick={() => navigate(`/article/article_detail/${id}`)}
          >
            取消
          </Button>
          <Button
            type="primary"
            htmlType="submit"
            loading={loading}
            icon={<SaveOutlined />}
            style={{ background: '#6f42c1', borderColor: '#6f42c1' }}
          >
            保存修改
          </Button>
        </div>
      </Form>
    </div>
  )
}

export default ArticleEdit