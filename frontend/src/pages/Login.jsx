import { useState } from 'react'
import { Form, Input, Button, Card, Typography, Alert, Space } from 'antd'
import { UserOutlined, LockOutlined } from '@ant-design/icons'
import { useNavigate, Link } from 'react-router-dom'
import request from '../utils/request'

const { Title, Text } = Typography

function Login({ setUser }) {
  const navigate = useNavigate()
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)

  const onFinish = async (values) => {
    setError(null)
    setLoading(true)
    try {
      const res = await request.post('/usermanage/login/', values)
      if (res.data.success) {
        if (setUser) {
          const userRes = await request.get('/usermanage/api/user/')
          if (userRes.data.authenticated) setUser(userRes.data)
        }
        navigate('/')
      } else {
        setError(res.data.message || '登录失败，请检查用户名和密码')
      }
    } catch (err) {
      setError(err.response?.data?.message || '登录失败，请稍后重试')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div style={{ display: 'flex', justifyContent: 'center', padding: '40px 0' }}>
      <Card style={{ width: '100%', maxWidth: 420 }}>
        <Space direction="vertical" style={{ width: '100%' }} size="large">
          <div style={{ textAlign: 'center' }}>
            <Title level={2} style={{ marginBottom: 4 }}>登录</Title>
            <Text type="secondary">欢迎回到 NCBCNet</Text>
          </div>

          {error && <Alert message={error} type="error" showIcon closable onClose={() => setError(null)} />}

          <Form onFinish={onFinish} layout="vertical" size="large">
            <Form.Item
              name="username"
              rules={[{ required: true, message: '请输入用户名' }]}
            >
              <Input prefix={<UserOutlined />} placeholder="用户名" />
            </Form.Item>

            <Form.Item
              name="password"
              rules={[{ required: true, message: '请输入密码' }]}
            >
              <Input.Password prefix={<LockOutlined />} placeholder="密码" />
            </Form.Item>

            <Form.Item>
              <Button type="primary" htmlType="submit" loading={loading} block>
                登录
              </Button>
            </Form.Item>
          </Form>

          <div style={{ textAlign: 'center' }}>
            <Text type="secondary">还没有账号？ </Text>
            <Link to="/usermanage/register">立即注册</Link>
          </div>
        </Space>
      </Card>
    </div>
  )
}

export default Login
