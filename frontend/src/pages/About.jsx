import { Card, Typography, Row, Col, Tag, Divider, Timeline } from 'antd'
import {
  GithubOutlined,
  SafetyOutlined,
  CloudServerOutlined,
  CodeOutlined,
  TeamOutlined,
  BookOutlined,
} from '@ant-design/icons'

const { Title, Paragraph, Text } = Typography

const techStack = [
  { name: 'Django 6.0', type: '后端框架', color: '#092e20' },
  { name: 'Daphne 4.2', type: 'ASGI 服务器', color: '#6f42c1' },
  { name: 'DRF 3.16', type: 'API 框架', color: '#a30000' },
  { name: 'MySQL 8.0', type: '数据库', color: '#4479a1' },
  { name: 'Redis 7', type: '缓存', color: '#dc382d' },
  { name: 'React 19', type: '前端框架', color: '#61dafb' },
  { name: 'Ant Design 6', type: 'UI 库', color: '#1677ff' },
  { name: 'Nginx', type: '反向代理', color: '#009639' },
  { name: 'Docker', type: '容器化', color: '#2496ed' },
]

function About() {
  return (
    <div style={{ maxWidth: 900, margin: '0 auto' }}>
      <div className="page-header" style={{ textAlign: 'center', marginBottom: 32 }}>
        <Title level={2}>关于 NCBCNet</Title>
        <Paragraph type="secondary" style={{ fontSize: 16 }}>
          南城巴川自己的教学交流论坛 —— 南城网
        </Paragraph>
      </div>

      {/* 项目介绍 */}
      <Card style={{ marginBottom: 24, borderRadius: 8 }}>
        <Title level={4}><BookOutlined /> 项目简介</Title>
        <Paragraph style={{ fontSize: 15, lineHeight: 1.8 }}>
          NCBCNet（南城网）是一个面向南城巴川学校的综合性教学交流平台。
          平台提供文章发布与管理、文件云存储与共享、用户互动交流等核心功能，
          旨在为师生打造一个便捷、高效的在线教学辅助环境。
        </Paragraph>
        <Paragraph style={{ fontSize: 15, lineHeight: 1.8 }}>
          项目采用前后端分离架构，后端基于 Django + Daphne 构建，
          前端使用 React + Ant Design 开发，并通过 Docker 容器化部署，
          保证了系统的可维护性和可扩展性。
        </Paragraph>
      </Card>

      {/* 核心功能 */}
      <Card style={{ marginBottom: 24, borderRadius: 8 }}>
        <Title level={4}><CodeOutlined /> 核心功能</Title>
        <Row gutter={[16, 16]}>
          <Col span={12}>
            <Card size="small" style={{ borderRadius: 8 }}>
              <Text strong>📝 文章系统</Text>
              <Paragraph type="secondary" style={{ margin: '8px 0 0', fontSize: 13 }}>
                支持 Markdown 编辑、代码高亮、标签分类、栏目管理
              </Paragraph>
            </Card>
          </Col>
          <Col span={12}>
            <Card size="small" style={{ borderRadius: 8 }}>
              <Text strong>💬 评论互动</Text>
              <Paragraph type="secondary" style={{ margin: '8px 0 0', fontSize: 13 }}>
                支持无限嵌套回复、富文本编辑器、@提及功能
              </Paragraph>
            </Card>
          </Col>
          <Col span={12}>
            <Card size="small" style={{ borderRadius: 8 }}>
              <Text strong>📁 云上网盘</Text>
              <Paragraph type="secondary" style={{ margin: '8px 0 0', fontSize: 13 }}>
                树形文件夹管理、文件共享、大文件上传、断点续传
              </Paragraph>
            </Card>
          </Col>
          <Col span={12}>
            <Card size="small" style={{ borderRadius: 8 }}>
              <Text strong>👤 用户系统</Text>
              <Paragraph type="secondary" style={{ margin: '8px 0 0', fontSize: 13 }}>
                注册登录、资料管理、头像上传、权限控制
              </Paragraph>
            </Card>
          </Col>
        </Row>
      </Card>

      {/* 技术栈 */}
      <Card style={{ marginBottom: 24, borderRadius: 8 }}>
        <Title level={4}><CloudServerOutlined /> 技术栈</Title>
        <div style={{ display: 'flex', flexWrap: 'wrap', gap: 8 }}>
          {techStack.map((tech, index) => (
            <Tag key={index} color={tech.color} style={{ padding: '4px 12px', fontSize: 14, borderRadius: 4 }}>
              {tech.name}
            </Tag>
          ))}
        </div>
      </Card>

      {/* 项目里程碑 */}
      <Card style={{ borderRadius: 8 }}>
        <Title level={4}><GithubOutlined /> 项目信息</Title>
        <div style={{ display: 'flex', gap: 16, flexWrap: 'wrap' }}>
          <Card size="small" style={{ flex: 1, minWidth: 180, borderRadius: 8, textAlign: 'center' }}>
            <Title level={3} style={{ color: '#6f42c1', margin: 0 }}>AGPL-3.0</Title>
            <Text type="secondary">开源许可证</Text>
          </Card>
          <Card size="small" style={{ flex: 1, minWidth: 180, borderRadius: 8, textAlign: 'center' }}>
            <Title level={3} style={{ color: '#6f42c1', margin: 0 }}>v0.5.8</Title>
            <Text type="secondary">当前版本</Text>
          </Card>
          <Card size="small" style={{ flex: 1, minWidth: 180, borderRadius: 8, textAlign: 'center' }}>
            <Title level={3} style={{ color: '#6f42c1', margin: 0 }}>2024-2026</Title>
            <Text type="secondary">开发周期</Text>
          </Card>
        </div>
      </Card>
    </div>
  )
}

export default About