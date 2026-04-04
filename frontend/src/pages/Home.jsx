import { useEffect, useState } from 'react'
import { Card, Typography, Row, Col, Spin, List, Tag } from 'antd'
import {
  FileTextOutlined,
  UserOutlined,
  FolderOutlined,
  WifiOutlined,
} from '@ant-design/icons'
import request from '../utils/request'

const { Title, Paragraph, Text } = Typography

const features = [
  { icon: <FileTextOutlined style={{ fontSize: 24, color: '#1677ff' }} />, title: '文章管理', desc: '支持 Markdown 和富文本编辑，发布和管理文章' },
  { icon: <UserOutlined style={{ fontSize: 24, color: '#52c41a' }} />, title: '用户系统', desc: '注册登录、个人资料管理、账户安全' },
  { icon: <FolderOutlined style={{ fontSize: 24, color: '#fa8c16' }} />, title: '文件管理', desc: '上传下载文件，支持文件夹层级管理和共享' },
  { icon: <WifiOutlined style={{ fontSize: 24, color: '#722ed1' }} />, title: '实时通信', desc: '基于 WebSocket 的实时消息与通知' },
]

function Home() {
  const [data, setData] = useState(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    request.get('/server/')
      .then(res => setData(res.data))
      .catch(() => setData(null))
      .finally(() => setLoading(false))
  }, [])

  if (loading) {
    return (
      <div style={{ textAlign: 'center', padding: '60px 0' }}>
        <Spin size="large" />
      </div>
    )
  }

  return (
    <div>
      <Card
        style={{ marginBottom: 24, background: 'linear-gradient(135deg, #1677ff 0%, #4096ff 100%)', border: 'none' }}
        styles={{ body: { padding: '48px 32px' } }}
      >
        <Title level={1} style={{ color: '#fff', margin: 0 }}>
          {data?.welcome_msg || '欢迎来到 NCBCNet'}
        </Title>
        <Paragraph style={{ color: 'rgba(255,255,255,0.85)', fontSize: 16, marginTop: 12, marginBottom: 0 }}>
          南城广播网 — 基于 Django + React 的综合信息平台
        </Paragraph>
      </Card>

      <Title level={3}>平台功能</Title>
      <Row gutter={[16, 16]}>
        {features.map(f => (
          <Col xs={24} sm={12} lg={6} key={f.title}>
            <Card hoverable styles={{ body: { textAlign: 'center', padding: '24px 16px' } }}>
              <div style={{ marginBottom: 12 }}>{f.icon}</div>
              <Text strong style={{ fontSize: 16 }}>{f.title}</Text>
              <Paragraph type="secondary" style={{ marginTop: 8, marginBottom: 0 }}>{f.desc}</Paragraph>
            </Card>
          </Col>
        ))}
      </Row>

      <Card style={{ marginTop: 24 }} title="技术栈">
        <Row gutter={[8, 8]}>
          {['Django', 'Daphne', 'Channels', 'React 19', 'Ant Design', 'Axios', 'Vite', 'MySQL', 'Redis', 'Nginx'].map(t => (
            <Col key={t}><Tag color="blue">{t}</Tag></Col>
          ))}
        </Row>
      </Card>
    </div>
  )
}

export default Home
