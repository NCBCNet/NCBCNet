import { useState } from 'react'
import { Form, Input, Button, Card, Typography, Alert, Space } from 'antd'
import { ArrowLeftOutlined, SendOutlined } from '@ant-design/icons'
import { useNavigate } from 'react-router-dom'
import request from '../utils/request'

const { Title, Text } = Typography
const { TextArea } = Input

function ArticleCreate() {
  const navigate = useNavigate()
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)

  const onFinish = async (values) => {
    setError(null)
    setLoading(true)
    try {
      const res = await request.post('/article/api/create/', values)
      if (res.data.success) {
        navigate(`/article/article_detail/${res.data.id}`)
      }
    } catch (err) {
      if (err.response?.status === 401) {
        setError('请先登录后再发布文章')
      } else {
        setError(err.response?.data?.error || '发布失败，请稍后重试')
      }
    } finally {
      setLoading(false)
    }
  }

  return (
    <div style={{ maxWidth: 860, margin: '0 auto' }}>
      <Space style={{ marginBottom: 16 }}>
        <Button icon={<ArrowLeftOutlined />} onClick={() => navigate('/article')}>返回</Button>
      </Space>

      <Card>
        <Title level={2} style={{ marginBottom: 24 }}>发布文章</Title>

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

        <Form onFinish={onFinish} layout="vertical" size="large">
          <Form.Item
            name="title"
            label="标题"
            rules={[
              { required: true, message: '请输入文章标题' },
              { max: 100, message: '标题不能超过 100 个字符' },
            ]}
          >
            <Input placeholder="请输入文章标题" />
          </Form.Item>

          <Form.Item
            name="content"
            label="正文（支持 Markdown）"
            rules={[{ required: true, message: '请输入文章内容' }]}
          >
            <TextArea rows={16} placeholder="请输入文章内容，支持 Markdown 格式" />
          </Form.Item>

          <Form.Item>
            <Space>
              <Button type="primary" htmlType="submit" loading={loading} icon={<SendOutlined />}>
                发布
              </Button>
              <Button onClick={() => navigate('/article')}>取消</Button>
            </Space>
          </Form.Item>
        </Form>
      </Card>
    </div>
  )
}

export default ArticleCreate
