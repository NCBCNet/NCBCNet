import { useEffect, useState } from 'react'
import { Card, Result, Spin, Tag, Typography } from 'antd'
import { CheckCircleFilled, CloseCircleFilled } from '@ant-design/icons'
import api from '../services/api'

const { Title, Text } = Typography

const COMPONENT_LABELS = {
  database: '数据库',
  cache: '缓存',
  storage: '媒体存储',
}

function Health() {
  const [data, setData] = useState(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    api.get('/health/components/')
      .then((res) => setData(res.data))
      .catch(() => setData({ status: 'error', components: {} }))
      .finally(() => setLoading(false))
  }, [])

  if (loading) {
    return <div style={{ textAlign: 'center', padding: 80 }}><Spin size="large" /></div>
  }

  const components = data?.components || {}
  const overall = data?.status

  return (
    <div style={{ maxWidth: 720, margin: '0 auto' }}>
      <Title level={3} style={{ marginBottom: 8 }}>网站状态</Title>
      <Text type="secondary">各模块实时健康状态</Text>

      <Result
        status={overall === 'ok' ? 'success' : 'error'}
        title={overall === 'ok' ? '所有组件运行正常' : '部分组件异常'}
        style={{ padding: '24px 0 0' }}
      />

      <Card title="组件状态" style={{ borderRadius: 8, marginTop: 16 }}>
        {Object.entries(COMPONENT_LABELS).map(([key, label]) => {
          const c = components[key]
          const ok = c?.status === 'ok'
          return (
            <div
              key={key}
              style={{
                display: 'flex',
                justifyContent: 'space-between',
                alignItems: 'center',
                padding: '14px 4px',
                borderBottom: '1px solid #f0f0f0',
              }}
            >
              <Text strong>{label}</Text>
              <span>
                <Tag
                  color={ok ? 'green' : 'red'}
                  icon={ok ? <CheckCircleFilled /> : <CloseCircleFilled />}
                  style={{ marginRight: 0 }}
                >
                  {c?.message || '未知'}
                </Tag>
                {c?.latency_ms != null && (
                  <Text type="secondary" style={{ fontSize: 12, marginLeft: 8 }}>
                    {c.latency_ms} ms
                  </Text>
                )}
              </span>
            </div>
          )
        })}
      </Card>
    </div>
  )
}

export default Health
