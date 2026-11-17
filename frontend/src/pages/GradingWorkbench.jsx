import { useCallback, useEffect, useMemo, useState } from 'react'
import {
  Alert, Button, Card, Col, Empty, Form, Input, InputNumber, List,
  Row, Space, Spin, Statistic, Tag, Typography, message,
} from 'antd'
import {
  CheckCircleOutlined, ClockCircleOutlined, FormOutlined, ReloadOutlined,
} from '@ant-design/icons'
import { useAuth } from '../store/authStore'
import {
  claimAssignment, listMyAssignments, renewAssignmentLease, saveAssignmentDraft,
  submitAssignment,
} from '../services/gradingService'

const { Title, Text } = Typography

const STATUS_LABELS = {
  assigned: ['待领取', 'blue'],
  in_progress: ['评阅中', 'processing'],
  submitted: ['已提交', 'success'],
}

function GradingWorkbench() {
  const { isAuthenticated } = useAuth()
  const [assignments, setAssignments] = useState([])
  const [selected, setSelected] = useState(null)
  const [loading, setLoading] = useState(true)
  const [submitting, setSubmitting] = useState(false)
  const [form] = Form.useForm()

  const loadAssignments = useCallback(async () => {
    setLoading(true)
    try {
      const data = await listMyAssignments()
      setAssignments(data)
      setSelected((current) => current && data.find((item) => item.id === current.id) ? current : data[0] || null)
    } catch (error) {
      message.error(error.response?.data?.detail || '加载评卷任务失败')
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    if (!isAuthenticated) return undefined
    const timer = window.setTimeout(() => {
      loadAssignments()
    }, 0)
    return () => window.clearTimeout(timer)
  }, [isAuthenticated, loadAssignments])

  const counts = useMemo(() => ({
    total: assignments.length,
    pending: assignments.filter((item) => item.status === 'assigned').length,
    progress: assignments.filter((item) => item.status === 'in_progress').length,
    done: assignments.filter((item) => item.status === 'submitted').length,
  }), [assignments])

  const handleClaim = async () => {
    try {
      const updated = await claimAssignment(selected.id)
      setSelected(updated)
      setAssignments((items) => items.map((item) => item.id === updated.id ? updated : item))
      message.success('任务已领取')
    } catch (error) {
      message.error(error.response?.data?.detail || '领取任务失败')
    }
  }

  const handleSubmit = async (values) => {
    setSubmitting(true)
    try {
      const updated = await submitAssignment(selected.id, values)
      setAssignments((items) => items.map((item) => item.id === updated.id ? updated : item))
      setSelected(updated)
      form.resetFields()
      message.success('评分已提交')
    } catch (error) {
      message.error(error.response?.data?.detail || '提交评分失败')
    } finally {
      setSubmitting(false)
    }
  }

  useEffect(() => {
    if (!selected || selected.status !== 'in_progress') return undefined
    const timer = window.setInterval(async () => {
      try {
        await renewAssignmentLease(selected.id)
      } catch {
        message.warning('任务租约续期失败，请尽快提交当前评分')
      }
    }, 5 * 60 * 1000)
    return () => window.clearInterval(timer)
  }, [selected])

  const handleDraft = async (values) => {
    try {
      const updated = await saveAssignmentDraft(selected.id, values)
      setSelected(updated)
      setAssignments((items) => items.map((item) => item.id === updated.id ? updated : item))
      message.success('草稿已保存')
    } catch (error) {
      message.error(error.response?.data?.detail || '草稿保存失败')
    }
  }

  if (!isAuthenticated) {
    return <Alert type="warning" message="请先登录教师账号" showIcon />
  }

  if (loading) {
    return <div style={{ textAlign: 'center', padding: 80 }}><Spin size="large" /></div>
  }

  return (
    <div style={{ maxWidth: 1280, margin: '0 auto' }}>
      <Space style={{ width: '100%', justifyContent: 'space-between', marginBottom: 16 }}>
        <div>
          <Title level={3} style={{ marginBottom: 4 }}>教师评卷工作台</Title>
          <Text type="secondary">按题块评阅，提交后自动进入双评汇总或仲裁流程</Text>
        </div>
        <Button icon={<ReloadOutlined />} onClick={loadAssignments}>刷新</Button>
      </Space>

      <Row gutter={16} style={{ marginBottom: 16 }}>
        <Col xs={12} md={6}><Card><Statistic title="全部任务" value={counts.total} /></Card></Col>
        <Col xs={12} md={6}><Card><Statistic title="待领取" value={counts.pending} /></Card></Col>
        <Col xs={12} md={6}><Card><Statistic title="评阅中" value={counts.progress} /></Card></Col>
        <Col xs={12} md={6}><Card><Statistic title="已提交" value={counts.done} /></Card></Col>
      </Row>

      <Row gutter={16}>
        <Col xs={24} md={9}>
          <Card title="我的任务" bodyStyle={{ padding: 0 }}>
            {assignments.length === 0 ? <Empty description="暂无评卷任务" /> : (
              <List
                dataSource={assignments}
                renderItem={(item) => {
                  const [label, color] = STATUS_LABELS[item.status] || [item.status, 'default']
                  return (
                    <List.Item
                      onClick={() => setSelected(item)}
                      style={{
                        cursor: 'pointer',
                        padding: '14px 18px',
                        background: selected?.id === item.id ? '#f0f5ff' : undefined,
                      }}
                    >
                      <List.Item.Meta
                        avatar={item.status === 'submitted' ? <CheckCircleOutlined /> : <ClockCircleOutlined />}
                        title={`考号 ${item.candidate_no} · 第 ${item.question_number} 题`}
                        description={`第 ${item.round_no} 评`}
                      />
                      <Tag color={color}>{label}</Tag>
                    </List.Item>
                  )
                }}
              />
            )}
          </Card>
        </Col>
        <Col xs={24} md={15}>
          {selected ? (
            <Card title={`第 ${selected.question_number} 题 · 考号 ${selected.candidate_no}`}>
              <Space direction="vertical" size="large" style={{ width: '100%' }}>
                {selected.answer_block_image || selected.answer_sheet_image ? (
                  <img
                    src={selected.answer_block_image || selected.answer_sheet_image}
                    alt="答题区域"
                    style={{ maxWidth: '100%', maxHeight: 520, objectFit: 'contain', border: '1px solid #eee' }}
                  />
                ) : (
                  <Alert type="info" message="当前任务尚未绑定题块图像"                   description="扫描切割服务完成后，这里会展示脱敏后的题块。" />
                )}
                <Alert
                  type="warning"
                  showIcon
                  message="双评提示"
                  description="提交后系统会与另一位教师的评分比较；分差超过阈值时自动进入仲裁。"
                />
                {selected.status === 'assigned' && (
                  <Button type="primary" icon={<FormOutlined />} onClick={handleClaim}>领取任务</Button>
                )}
                {selected.status === 'in_progress' && (
                  <Form
                    form={form}
                    layout="vertical"
                    initialValues={{ score: selected.draft_score, comment: selected.draft_comment }}
                    onFinish={handleSubmit}
                  >
                    <Form.Item
                      name="score"
                      label={`评分（满分 ${selected.max_score}）`}
                      rules={[{ required: true, message: '请输入评分' }]}
                    >
                      <InputNumber min={0} max={Number(selected.max_score)} step={0.5} style={{ width: 180 }} />
                    </Form.Item>
                    <Form.Item name="comment" label="评语">
                      <Input.TextArea rows={4} placeholder="记录评分依据或异常说明" />
                    </Form.Item>
                    <Space>
                      <Button htmlType="button" onClick={() => handleDraft(form.getFieldsValue())}>保存草稿</Button>
                      <Button type="primary" htmlType="submit" loading={submitting}>提交评分</Button>
                    </Space>
                  </Form>
                )}
                {selected.status === 'submitted' && (
                  <Alert type="success" message={`已提交评分：${selected.score}`} description={selected.comment || '未填写评语'} />
                )}
              </Space>
            </Card>
          ) : <Card><Empty description="请选择左侧评卷任务" /></Card>}
        </Col>
      </Row>
    </div>
  )
}

export default GradingWorkbench
