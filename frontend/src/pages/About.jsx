import { Card, Typography, Row, Col, List, Tag, Divider } from 'antd'
import {
  GithubOutlined,
  CloudServerOutlined,
  CodeOutlined,
  DatabaseOutlined,
} from '@ant-design/icons'

const { Title, Paragraph, Text } = Typography

const techStack = {
  backend: ['Django 5.1', 'Daphne (ASGI)', 'Django Channels', 'Django REST Framework', 'MySQL / SQLite', 'Redis', 'Celery'],
  frontend: ['React 19', 'Ant Design', 'Vite', 'React Router', 'Axios'],
  deployment: ['Nginx', 'Supervisor', 'Docker', 'systemd', 'SSL/TLS'],
}

function About() {
  return (
    <div>
      <Card style={{ marginBottom: 24, background: 'linear-gradient(135deg, #001529 0%, #003a8c 100%)', border: 'none' }}
        styles={{ body: { padding: '40px 32px' } }}>
        <Title level={1} style={{ color: '#fff', margin: 0 }}>关于 NCBCNet</Title>
        <Paragraph style={{ color: 'rgba(255,255,255,0.75)', fontSize: 16, marginTop: 12, marginBottom: 0 }}>
          南城广播网 — 面向学校的综合信息与资源管理平台
        </Paragraph>
      </Card>

      <Row gutter={24}>
        <Col xs={24} md={16}>
          <Card title="项目介绍" style={{ marginBottom: 24 }}>
            <Paragraph>
              NCBCNet 是一套采用前后端分离架构开发的综合 Web 应用，后端基于 <Text strong>Django + Daphne</Text>，
              前端基于 <Text strong>React + Ant Design</Text>，支持文章发布、文件管理、用户系统及实时通信等功能。
            </Paragraph>
            <Paragraph>
              系统通过 <Text code>Django Channels</Text> 实现 WebSocket 支持，可进行实时消息推送；
              文件管理模块支持目录层级、在线预览与文件共享；文章模块支持 Markdown 格式与富文本编辑。
            </Paragraph>
          </Card>

          <Card title="功能列表">
            <List
              size="small"
              dataSource={[
                '文章管理：发布、编辑、删除，支持 Markdown 渲染',
                '用户系统：注册、登录、个人资料管理',
                '文件管理：上传/下载，文件夹层级，文件共享',
                '评论系统：基于 django-mptt 的嵌套评论',
                '实时通知：WebSocket 推送',
                '搜索功能：django-haystack 全文检索',
              ]}
              renderItem={item => (
                <List.Item>
                  <Text>{item}</Text>
                </List.Item>
              )}
            />
          </Card>
        </Col>

        <Col xs={24} md={8}>
          <Card title={<><CloudServerOutlined /> 后端</>} style={{ marginBottom: 16 }}>
            <Row gutter={[6, 6]}>
              {techStack.backend.map(t => <Col key={t}><Tag color="blue">{t}</Tag></Col>)}
            </Row>
          </Card>

          <Card title={<><CodeOutlined /> 前端</>} style={{ marginBottom: 16 }}>
            <Row gutter={[6, 6]}>
              {techStack.frontend.map(t => <Col key={t}><Tag color="green">{t}</Tag></Col>)}
            </Row>
          </Card>

          <Card title={<><DatabaseOutlined /> 部署</>}>
            <Row gutter={[6, 6]}>
              {techStack.deployment.map(t => <Col key={t}><Tag color="orange">{t}</Tag></Col>)}
            </Row>
          </Card>
        </Col>
      </Row>
    </div>
  )
}

export default About
