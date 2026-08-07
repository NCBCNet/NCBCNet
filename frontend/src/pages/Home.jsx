import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { Carousel, Card, Row, Col, Typography, Button, Spin, Space } from 'antd'
import {
  ReadOutlined,
  CloudOutlined,
  TeamOutlined,
  SafetyOutlined,
  RightOutlined,
} from '@ant-design/icons'
import api from '../services/api'

const { Title, Paragraph, Text } = Typography

const features = [
  {
    icon: <ReadOutlined style={{ fontSize: 36, color: '#6f42c1' }} />,
    title: '教学论坛',
    desc: '分享知识、讨论问题，支持 Markdown 编辑和代码高亮',
    link: '/article',
  },
  {
    icon: <CloudOutlined style={{ fontSize: 36, color: '#6f42c1' }} />,
    title: '云上网盘',
    desc: '文件存储与共享，支持文件夹管理和在线预览',
    link: '/file_up/file_list',
  },
  {
    icon: <TeamOutlined style={{ fontSize: 36, color: '#6f42c1' }} />,
    title: '用户社区',
    desc: '建立个人资料，与同学老师互动交流',
    link: '/usermanage/login',
  },
  {
    icon: <SafetyOutlined style={{ fontSize: 36, color: '#6f42c1' }} />,
    title: '安全可靠',
    desc: 'HTTPS 加密传输、权限管理、数据安全保障',
    link: '/server/about',
  },
]

function Home() {
  const navigate = useNavigate()
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    // 模拟数据加载
    const timer = setTimeout(() => setLoading(false), 300)
    return () => clearTimeout(timer)
  }, [])

  if (loading) {
    return (
      <div style={{ textAlign: 'center', padding: 80 }}>
        <Spin size="large" />
      </div>
    )
  }

  return (
    <div>
      {/* 轮播图 */}
      <Carousel autoplay autoplaySpeed={5000} style={{ borderRadius: 12, overflow: 'hidden', marginBottom: 40 }}>
        <div>
          <div style={{
            height: 360,
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            background: 'linear-gradient(135deg, #6f42c1 0%, #9b72cf 100%)',
            color: '#fff',
            textAlign: 'center',
          }}>
            <div>
              <Title level={1} style={{ color: '#fff', margin: 0 }}>NCNet 南城网</Title>
              <Paragraph style={{ color: 'rgba(255,255,255,0.85)', fontSize: 18, marginTop: 16 }}>
                南城巴川自己的教学交流论坛
              </Paragraph>
              <Button
                type="primary"
                size="large"
                ghost
                onClick={() => navigate('/article')}
                style={{ borderColor: '#fff', color: '#fff' }}
              >
                进入论坛 <RightOutlined />
              </Button>
            </div>
          </div>
        </div>
        <div>
          <div style={{
            height: 360,
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            background: 'linear-gradient(135deg, #1a1a2e 0%, #16213e 100%)',
            color: '#fff',
            textAlign: 'center',
          }}>
            <div>
              <Title level={2} style={{ color: '#fff' }}>山重水复疑无路</Title>
              <Title level={2} style={{ color: '#fff', marginTop: 0 }}>柳暗花明又一村</Title>
              <Text style={{ color: 'rgba(255,255,255,0.7)' }}>—— 陆游《游山西村》</Text>
            </div>
          </div>
        </div>
        <div>
          <div style={{
            height: 360,
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            background: 'linear-gradient(135deg, #0f3443 0%, #34e89e 100%)',
            color: '#fff',
            textAlign: 'center',
          }}>
            <div>
              <Title level={2} style={{ color: '#fff' }}>云上网盘</Title>
              <Paragraph style={{ color: 'rgba(255,255,255,0.85)', fontSize: 16, marginTop: 16 }}>
                安全便捷的文件管理，随时随地存取您的资料
              </Paragraph>
              <Button
                type="primary"
                size="large"
                ghost
                onClick={() => navigate('/file_up/file_list')}
                style={{ borderColor: '#fff', color: '#fff' }}
              >
                前往云盘 <RightOutlined />
              </Button>
            </div>
          </div>
        </div>
      </Carousel>

      {/* 功能特性 */}
      <div style={{ marginBottom: 40 }}>
        <Title level={3} style={{ textAlign: 'center', marginBottom: 32 }}>平台功能</Title>
        <Row gutter={[24, 24]}>
          {features.map((item, index) => (
            <Col xs={24} sm={12} lg={6} key={index}>
              <Card
                hoverable
                style={{ textAlign: 'center', borderRadius: 12, height: '100%' }}
                onClick={() => navigate(item.link)}
              >
                <div style={{ marginBottom: 16 }}>{item.icon}</div>
                <Title level={4}>{item.title}</Title>
                <Paragraph type="secondary">{item.desc}</Paragraph>
              </Card>
            </Col>
          ))}
        </Row>
      </div>

      {/* 欢迎信息 */}
      <Card style={{ textAlign: 'center', borderRadius: 12, background: '#f9f8ff' }}>
        <Title level={3}>Hello NCNet！</Title>
        <Paragraph type="secondary" style={{ fontSize: 16 }}>
          欢迎来到 NCBCNet —— 南城巴川的教学交流平台
        </Paragraph>
        <Space size="large">
          <Button type="primary" onClick={() => navigate('/usermanage/register')} style={{ background: '#6f42c1', borderColor: '#6f42c1' }}>
            立即注册
          </Button>
          <Button onClick={() => navigate('/server/about')}>了解更多</Button>
        </Space>
      </Card>
    </div>
  )
}

export default Home