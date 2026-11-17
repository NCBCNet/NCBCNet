import { useCallback, useEffect, useState } from 'react'
import {
  Button, Card, Col, Descriptions, Empty, Image, InputNumber, Row, Space, Spin,
  Statistic, Switch, Table, Tag, Typography, message,
} from 'antd'
import {
  CheckOutlined, CloseOutlined, ReloadOutlined, SafetyCertificateOutlined,
} from '@ant-design/icons'
import {
  decideRelease, getGradingMetrics, listArbitrations, listQualityReviews,
  listReleaseApprovals, listTeacherProfiles, listAuditLogs, publishRelease, revokeRelease,
  resolveArbitration, reviewQuality, exportExamScores, updateTeacherProfile,
  listFailedRecognitionJobs, retryRecognition,
  listScanPageReviewQueue, reviewScanPage,
} from '../services/gradingService'

const { Title, Text } = Typography

function GradingOperations() {
  const [loading, setLoading] = useState(true)
  const [metrics, setMetrics] = useState(null)
  const [arbitrations, setArbitrations] = useState([])
  const [reviews, setReviews] = useState([])
  const [approvals, setApprovals] = useState([])
  const [teacherProfiles, setTeacherProfiles] = useState([])
  const [auditLogs, setAuditLogs] = useState([])
  const [failedRecognitionJobs, setFailedRecognitionJobs] = useState([])
  const [scanReviewPages, setScanReviewPages] = useState([])
  const [arbitrationScores, setArbitrationScores] = useState({})
  const [busy, setBusy] = useState(false)

  const load = useCallback(async () => {
    setLoading(true)
    try {
      const [metricsData, arbitrationData, reviewData, approvalData, profileData, auditData, failedJobs, scanPages] = await Promise.all([
        getGradingMetrics(), listArbitrations(), listQualityReviews(), listReleaseApprovals(),
        listTeacherProfiles(), listAuditLogs(), listFailedRecognitionJobs(), listScanPageReviewQueue(),
      ])
      setMetrics(metricsData)
      setArbitrations(arbitrationData)
      setReviews(reviewData)
      setApprovals(approvalData)
      setTeacherProfiles(profileData)
      setAuditLogs(auditData)
      setFailedRecognitionJobs(failedJobs)
      setScanReviewPages(scanPages)
    } catch (error) {
      message.error(error.response?.data?.detail || '加载运营数据失败，请确认当前账号是管理员')
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    const timer = window.setTimeout(load, 0)
    return () => window.clearTimeout(timer)
  }, [load])

  const action = async (callback) => {
    setBusy(true)
    try {
      await callback()
      await load()
      message.success('操作成功')
    } catch (error) {
      message.error(error.response?.data?.detail || '操作失败')
    } finally {
      setBusy(false)
    }
  }

  const downloadScores = async (examId) => {
    try {
      const response = await exportExamScores(examId)
      const url = window.URL.createObjectURL(response.data)
      const link = document.createElement('a')
      link.href = url
      link.download = `exam-${examId}-scores.csv`
      link.click()
      window.URL.revokeObjectURL(url)
    } catch (error) {
      message.error(error.response?.data?.detail || '导出成绩失败')
    }
  }

  if (loading) return <div style={{ textAlign: 'center', padding: 80 }}><Spin size="large" /></div>

  const assignmentCounts = metrics?.assignments || {}
  const jobCounts = metrics?.scan_jobs || {}
  const teacherLoads = metrics?.teacher_load || []
  const defaultArbitrationScore = (item) => {
    const scores = (item.assignment_scores || [])
      .map((score) => Number(score.score))
      .filter((score) => Number.isFinite(score))
    return scores.length
      ? scores.reduce((total, score) => total + score, 0) / scores.length
      : 0
  }

  return (
    <div style={{ maxWidth: 1280, margin: '0 auto' }}>
      <Space style={{ width: '100%', justifyContent: 'space-between', marginBottom: 16 }}>
        <div>
          <Title level={3} style={{ marginBottom: 4 }}>评卷运营控制台</Title>
          <Text type="secondary">识别、评卷、质检、仲裁和成绩发布统一监控</Text>
        </div>
        <Button icon={<ReloadOutlined />} onClick={load}>刷新</Button>
      </Space>

      <Row gutter={[16, 16]}>
        <Col xs={12} md={6}><Card><Statistic title="考试" value={metrics?.exams || 0} /></Card></Col>
        <Col xs={12} md={6}><Card><Statistic title="扫描批次" value={metrics?.scan_batches || 0} /></Card></Col>
        <Col xs={12} md={6}><Card><Statistic title="待仲裁" value={metrics?.open_arbitrations || 0} /></Card></Col>
        <Col xs={12} md={6}><Card><Statistic title="待质检" value={metrics?.pending_quality_reviews || 0} /></Card></Col>
        <Col xs={12} md={6}><Card><Statistic title="失败识别" value={metrics?.failed_recognition_jobs || 0} /></Card></Col>
        <Col xs={12} md={6}><Card><Statistic title="待复核扫描页" value={metrics?.pending_scan_page_reviews || 0} /></Card></Col>
        <Col xs={12} md={6}><Card><Statistic title="启用教师" value={metrics?.enabled_teachers || 0} /></Card></Col>
        <Col xs={12} md={6}><Card><Statistic title="审计事件" value={metrics?.audit_events || 0} /></Card></Col>
      </Row>

      <Row gutter={[16, 16]} style={{ marginTop: 16 }}>
        <Col xs={24} md={12}>
          <Card title="扫描任务状态">
            <Descriptions column={2} size="small">
              <Descriptions.Item label="排队">{jobCounts.queued || 0}</Descriptions.Item>
              <Descriptions.Item label="处理中">{jobCounts.processing || 0}</Descriptions.Item>
              <Descriptions.Item label="已完成">{jobCounts.completed || 0}</Descriptions.Item>
              <Descriptions.Item label="失败">{jobCounts.failed || 0}</Descriptions.Item>
            </Descriptions>
          </Card>

          <Card title="教师画像与分发配置" style={{ marginTop: 16 }}>
            {teacherProfiles.length === 0 ? <Empty description="暂无教师画像配置" /> : (
              <Table rowKey="id" dataSource={teacherProfiles} pagination={false} columns={[
                { title: '教师', dataIndex: 'user' },
                {
                  title: '当前负载',
                  render: (_, item) => {
                    const load = teacherLoads.find((entry) => entry.profile_id === item.id)
                    return load ? `${load.active_assignments}/${load.max_active_assignments}` : '-'
                  },
                },
                { title: '科目', dataIndex: 'subjects', render: (value) => value?.join('、') || '-' },
                { title: '题号范围', dataIndex: 'question_numbers', render: (value) => value?.join('、') || '-' },
                { title: '并发上限', dataIndex: 'max_active_assignments' },
                { title: '启用', dataIndex: 'enabled', render: (value, item) => (
                  <Switch
                    checked={value}
                    disabled={busy}
                    onChange={(checked) => action(() => updateTeacherProfile(item.id, { enabled: checked }))}
                  />
                ) },
              ]} />
            )}
          </Card>
        </Col>
        <Col xs={24} md={12}>
          <Card title="评卷任务状态">
            <Descriptions column={2} size="small">
              <Descriptions.Item label="待评阅">{assignmentCounts.assigned || 0}</Descriptions.Item>
              <Descriptions.Item label="评阅中">{assignmentCounts.in_progress || 0}</Descriptions.Item>
              <Descriptions.Item label="已提交">{assignmentCounts.submitted || 0}</Descriptions.Item>
              <Descriptions.Item label="已过期">{assignmentCounts.expired || 0}</Descriptions.Item>
            </Descriptions>
          </Card>
        </Col>
      </Row>

      <Card title="待仲裁案件" style={{ marginTop: 16 }}>
        {arbitrations.length === 0 ? <Empty description="暂无待仲裁案件" /> : (
          <Table rowKey="id" dataSource={arbitrations} pagination={false} columns={[
            { title: '答题卡', dataIndex: 'answer_sheet' },
            { title: '题目', dataIndex: 'question' },
            { title: '评分', render: (_, item) => item.assignment_scores?.map((score) => (
              <Tag key={score.assignment_id}>{score.score ?? '-'} 分</Tag>
            )) },
            {
              title: '最终分数',
              render: (_, item) => (
                <InputNumber
                  min={0}
                  max={Number(item.assignment_scores?.[0]?.max_score || 999999)}
                  precision={2}
                  value={arbitrationScores[item.id] ?? defaultArbitrationScore(item)}
                  disabled={busy}
                  onChange={(value) => setArbitrationScores((current) => ({
                    ...current,
                    [item.id]: value,
                  }))}
                />
              ),
            },
            { title: '操作', render: (_, item) => (
              <Button
                type="primary"
                size="small"
                disabled={busy}
                onClick={() => action(() => resolveArbitration(item.id, {
                  final_score: arbitrationScores[item.id] ?? defaultArbitrationScore(item),
                  resolution_comment: '管理员人工确认仲裁分数',
                }))}
              >
                提交仲裁分数
              </Button>
            ) },
          ]} />
        )}
      </Card>

      <Card title="待质检任务" style={{ marginTop: 16 }}>
        {reviews.length === 0 ? <Empty description="暂无待质检任务" /> : (
          <Table rowKey="id" dataSource={reviews} pagination={false} columns={[
            { title: '评卷任务', dataIndex: 'assignment' },
            { title: '操作', render: (_, item) => (
              <Space>
                <Button icon={<CheckOutlined />} size="small" onClick={() => action(() => reviewQuality(item.id, { status: 'passed' }))}>通过</Button>
                <Button danger icon={<CloseOutlined />} size="small" onClick={() => action(() => reviewQuality(item.id, { status: 'failed' }))}>退回</Button>
              </Space>
            ) },
          ]} />
        )}
      </Card>

      <Card title="成绩发布审批" style={{ marginTop: 16 }}>
        {approvals.length === 0 ? <Empty description="暂无发布申请" /> : (
          <Table rowKey="id" dataSource={approvals} pagination={false} columns={[
            { title: '考试', dataIndex: 'exam' },
            { title: '状态', dataIndex: 'status', render: (value) => <Tag>{value}</Tag> },
            { title: '操作', render: (_, item) => (
              <Space>
                {item.status === 'pending' && (
                  <>
                    <Button icon={<SafetyCertificateOutlined />} size="small" onClick={() => action(() => decideRelease(item.id, { approved: true }))}>批准</Button>
                    <Button danger size="small" onClick={() => action(() => decideRelease(item.id, { approved: false, comment: '管理员驳回发布申请' }))}>驳回</Button>
                  </>
                )}
                {item.status === 'approved' && (
                  <Button type="primary" size="small" onClick={() => action(() => publishRelease(item.id))}>发布成绩</Button>
                )}
                {item.status === 'published' && (
                  <>
                    <Button size="small" onClick={() => downloadScores(item.exam)}>导出成绩</Button>
                    <Button danger size="small" onClick={() => action(() => revokeRelease(item.id))}>撤回发布</Button>
                  </>
                )}
              </Space>
            ) },
          ]} />
        )}
      </Card>

      <Card title="最近审计日志" style={{ marginTop: 16 }}>
        {auditLogs.length === 0 ? <Empty description="暂无审计日志" /> : (
          <Table rowKey="id" dataSource={auditLogs} pagination={false} columns={[
            { title: '时间', dataIndex: 'created_at' },
            { title: '操作人', dataIndex: 'actor' },
            { title: '操作', dataIndex: 'action' },
            { title: '对象', render: (_, item) => `${item.object_type}#${item.object_id}` },
          ]} />
        )}
      </Card>

      <Card title="失败识别任务" style={{ marginTop: 16 }}>
        {failedRecognitionJobs.length === 0 ? <Empty description="暂无失败识别任务" /> : (
          <Table rowKey="id" dataSource={failedRecognitionJobs} pagination={false} columns={[
            { title: '批次', dataIndex: 'batch' },
            { title: '错误', dataIndex: 'error_message', ellipsis: true },
            { title: '重试次数', render: (_, item) => `${item.retry_count}/${item.max_retries}` },
            { title: '操作', render: (_, item) => (
              <Button
                size="small"
                disabled={busy || item.retry_count >= item.max_retries}
                onClick={() => action(() => retryRecognition(item.batch))}
              >
                重试识别
              </Button>
            ) },
          ]} />
        )}
      </Card>

      <Card title="扫描页人工复核队列" style={{ marginTop: 16 }}>
        {scanReviewPages.length === 0 ? <Empty description="暂无待复核扫描页" /> : (
          <Table rowKey="id" dataSource={scanReviewPages} pagination={false} columns={[
            {
              title: '扫描页',
              render: (_, item) => (
                <Space>
                  {item.normalized_image && <Image width={56} src={item.normalized_image} />}
                  <span>批次 {item.batch} / 第 {item.page_no} 页</span>
                </Space>
              ),
            },
            { title: '质量原因', dataIndex: 'quality_reasons', render: (value) => value?.join('、') || '-' },
            { title: '条码', render: (_, item) => item.barcode_result?.binding?.status || item.barcode_result?.status || '-' },
            { title: 'OCR', render: (_, item) => item.ocr_result?.status || '-' },
            { title: 'OMR', render: (_, item) => item.omr_result?.status || '-' },
            { title: '操作', render: (_, item) => (
              <Space>
                <Button
                  type="primary"
                  size="small"
                  disabled={busy}
                  onClick={() => action(() => reviewScanPage(item.id, { status: 'normalized', comment: '管理员复核通过' }))}
                >
                  复核通过
                </Button>
                <Button
                  danger
                  size="small"
                  disabled={busy}
                  onClick={() => action(() => reviewScanPage(item.id, { status: 'review', comment: '保留人工复核' }))}
                >
                  保留复核
                </Button>
              </Space>
            ) },
          ]} />
        )}
      </Card>
    </div>
  )
}

export default GradingOperations
