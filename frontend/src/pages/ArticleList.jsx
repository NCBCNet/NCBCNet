import { useEffect, useState, useCallback } from 'react'
import { useNavigate, useSearchParams } from 'react-router-dom'
import {
  List, Card, Row, Col, Input, Select, Tag, Typography, Spin, Pagination,
  Breadcrumb, Button, Space, Empty, message,
} from 'antd'
import {
  EyeOutlined, MessageOutlined, ClockCircleOutlined,
  PlusOutlined, SearchOutlined, FireOutlined, ClockCircleFilled,
} from '@ant-design/icons'
import api from '../services/api'
import { useAuth } from '../store/authStore'

const { Title, Text } = Typography

function ArticleList() {
  const navigate = useNavigate()
  const [searchParams, setSearchParams] = useSearchParams()
  const { isAuthenticated } = useAuth()

  const [articles, setArticles] = useState([])
  const [columns, setColumns] = useState([])
  const [loading, setLoading] = useState(true)
  const [total, setTotal] = useState(0)
  const [searchText, setSearchText] = useState(searchParams.get('search') || '')

  // 从 URL 参数读取
  const page = parseInt(searchParams.get('page') || '1', 10)
  const order = searchParams.get('order') || ''
  const columnId = searchParams.get('column') || ''
  const tag = searchParams.get('tag') || ''
  const search = searchParams.get('search') || ''

  const fetchArticles = useCallback(async () => {
    setLoading(true)
    try {
      const params = { page }
      if (search) params.search = search
      if (order) params.order = order
      if (columnId) params.column = columnId
      if (tag && tag !== 'None') params.tag = tag

      const res = await api.get('/articles/', { params })
      setArticles(res.data.results)
      setTotal(res.data.count)
    } catch {
      message.error('获取文章列表失败')
    } finally {
      setLoading(false)
    }
  }, [page, order, columnId, tag, search])

  const fetchColumns = useCallback(async () => {
    try {
      const res = await api.get('/articles/columns/')
      setColumns(res.data)
    } catch {
      // 栏目加载失败不影响主体
    }
  }, [])

  useEffect(() => {
    fetchArticles()
    fetchColumns()
  }, [fetchArticles, fetchColumns])

  const updateParams = (newParams) => {
    const params = new URLSearchParams(searchParams)
    Object.entries(newParams).forEach(([key, value]) => {
      if (value) params.set(key, value)
      else params.delete(key)
    })
    // 切换筛选条件时重置到第一页
    if ('search' in newParams || 'order' in newParams || 'column' in newParams || 'tag' in newParams) {
      params.set('page', '1')
    }
    setSearchParams(params)
  }

  const handleSearch = (value) => {
    updateParams({ search: value })
  }

  const handlePageChange = (p) => {
    updateParams({ page: String(p) })
    window.scrollTo({ top: 0, behavior: 'smooth' })
  }

  const formatTime = (timeStr) => {
    const now = new Date()
    const date = new Date(timeStr)
    const diff = (now - date) / 1000
    if (diff < 60) return '刚刚'
    if (diff < 3600) return `${Math.floor(diff / 60)} 分钟前`
    if (diff < 86400) return `${Math.floor(diff / 3600)} 小时前`
    if (diff < 2592000) return `${Math.floor(diff / 86400)} 天前`
    return date.toLocaleDateString('zh-CN')
  }

  return (
    <div>
      {/* 页面头部 */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 24 }}>
        <div>
          <Title level={3} style={{ margin: 0 }}>论坛</Title>
          <Text type="secondary">南城巴川教学交流论坛</Text>
        </div>
        {isAuthenticated && (
          <Button
            type="primary"
            icon={<PlusOutlined />}
            onClick={() => navigate('/article/article_create')}
            style={{ background: '#6f42c1', borderColor: '#6f42c1' }}
          >
            写文章
          </Button>
        )}
      </div>

      {/* 筛选栏 */}
      <Card style={{ marginBottom: 24, borderRadius: 8 }} styles={{ body: { padding: '16px 24px' } }}>
        <Row gutter={[16, 12]} align="middle">
          <Col>
            <Breadcrumb
              items={[
                {
                  title: (
                    <a onClick={() => updateParams({ order: '' })} style={!order ? { color: '#6f42c1', fontWeight: 600 } : {}}>
                      <ClockCircleFilled /> 最新
                    </a>
                  ),
                },
                {
                  title: (
                    <a onClick={() => updateParams({ order: 'total_views' })} style={order === 'total_views' ? { color: '#6f42c1', fontWeight: 600 } : {}}>
                      <FireOutlined /> 最热
                    </a>
                  ),
                },
              ]}
            />
          </Col>
          <Col flex="auto">
            <Input.Search
              placeholder="搜索文章..."
              allowClear
              defaultValue={search}
              onSearch={handleSearch}
              prefix={<SearchOutlined />}
              style={{ maxWidth: 280 }}
            />
          </Col>
          <Col>
            <Select
              placeholder="全部栏目"
              allowClear
              style={{ minWidth: 120 }}
              value={columnId || undefined}
              onChange={(val) => updateParams({ column: val || '' })}
            >
              {columns.map((col) => (
                <Select.Option key={col.id} value={String(col.id)}>{col.title}</Select.Option>
              ))}
            </Select>
          </Col>
        </Row>
      </Card>

      {/* 搜索结果提示 */}
      {search && (
        <div style={{ marginBottom: 16 }}>
          {articles.length > 0 ? (
            <Text>
              关于 <Text strong style={{ color: '#f5222d' }}>"{search}"</Text> 的搜索结果如下：
            </Text>
          ) : (
            <Text>
              暂无关于 <Text strong style={{ color: '#f5222d' }}>"{search}"</Text> 有关的文章。
            </Text>
          )}
        </div>
      )}

      {/* 文章列表 */}
      <Spin spinning={loading}>
        {articles.length === 0 && !loading ? (
          <Empty description="暂无文章" style={{ padding: 60 }} />
        ) : (
          <>
            <List
              dataSource={articles}
              split={false}
              renderItem={(article) => (
                <Card
                  style={{ marginBottom: 12, borderRadius: 8, cursor: 'pointer' }}
                  hoverable
                  styles={{ body: { padding: 20 } }}
                  onClick={() => navigate(`/article/article_detail/${article.id}`)}
                >
                  <Row gutter={16} align="top">
                    {article.avatar && typeof article.avatar === 'string' && (
                      <Col xs={24} sm={5} md={4}>
                        <img
                          src={article.avatar.startsWith('http') || article.avatar.startsWith('/') ? article.avatar : `/media/${article.avatar}`}
                          alt="avatar"
                          style={{ width: '100%', borderRadius: 12, maxHeight: 100, objectFit: 'cover' }}
                          onError={(e) => { e.target.style.display = 'none' }}
                        />
                      </Col>
                    )}
                    <Col xs={24} sm={article.avatar && typeof article.avatar === 'string' ? 19 : 24} md={article.avatar && typeof article.avatar === 'string' ? 20 : 24}>
                      <div style={{ marginBottom: 8 }}>
                        <Space size={8}>
                          {article.column && (
                            <Tag color="green" style={{ margin: 0 }}>{article.column.title}</Tag>
                          )}
                          {article.tags?.map((t) => (
                            <Tag key={t} style={{ color: '#888', margin: 0 }}>{t}</Tag>
                          ))}
                        </Space>
                      </div>
                      <Title level={4} style={{ margin: '0 0 8px', lineHeight: 1.4 }}>
                        {article.title}
                      </Title>
                      <div className="article-meta" style={{ marginTop: 12 }}>
                        <span><EyeOutlined /> {article.total_views}</span>
                        <span><MessageOutlined /> {article.comments_count}</span>
                        <span><ClockCircleOutlined /> {formatTime(article.created)}</span>
                        <span style={{ color: '#6f42c1' }}>{article.author?.username}</span>
                      </div>
                    </Col>
                  </Row>
                </Card>
              )}
            />
            <div style={{ textAlign: 'center', marginTop: 24 }}>
              <Pagination
                current={page}
                total={total}
                pageSize={10}
                onChange={handlePageChange}
                showSizeChanger={false}
                showTotal={(t) => `共 ${t} 篇文章`}
              />
            </div>
          </>
        )}
      </Spin>
    </div>
  )
}

export default ArticleList