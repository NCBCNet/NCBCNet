import { useEffect, useState } from 'react'
import { List, Card, Button, Typography, Input, Space, Spin, Empty, Pagination, Tag, Select } from 'antd'
import { PlusOutlined, EyeOutlined, LikeOutlined, SearchOutlined } from '@ant-design/icons'
import { useNavigate } from 'react-router-dom'
import request from '../utils/request'

const { Title, Text, Paragraph } = Typography

function ArticleList() {
  const navigate = useNavigate()
  const [articles, setArticles] = useState([])
  const [loading, setLoading] = useState(true)
  const [total, setTotal] = useState(0)
  const [currentPage, setCurrentPage] = useState(1)
  const [search, setSearch] = useState('')
  const [searchInput, setSearchInput] = useState('')
  const [order, setOrder] = useState('')

  const fetchArticles = (page = 1, searchVal = search, orderVal = order) => {
    setLoading(true)
    const params = { page, search: searchVal, order: orderVal }
    request.get('/article/api/list/', { params })
      .then(res => {
        setArticles(res.data.results || [])
        setTotal(res.data.count || 0)
        setCurrentPage(page)
      })
      .catch(() => {
        setArticles([])
        setTotal(0)
      })
      .finally(() => setLoading(false))
  }

  useEffect(() => { fetchArticles() }, [])

  const handleSearch = () => {
    setSearch(searchInput)
    fetchArticles(1, searchInput, order)
  }

  const handleOrderChange = (val) => {
    setOrder(val)
    fetchArticles(1, search, val)
  }

  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16 }}>
        <Title level={2} style={{ margin: 0 }}>文章列表</Title>
        <Button type="primary" icon={<PlusOutlined />} onClick={() => navigate('/article/article_create')}>
          发布文章
        </Button>
      </div>

      <Space style={{ marginBottom: 16 }} wrap>
        <Input
          placeholder="搜索文章…"
          value={searchInput}
          onChange={e => setSearchInput(e.target.value)}
          onPressEnter={handleSearch}
          suffix={<SearchOutlined onClick={handleSearch} style={{ cursor: 'pointer' }} />}
          style={{ width: 240 }}
        />
        <Select
          value={order || undefined}
          placeholder="排序方式"
          allowClear
          style={{ width: 140 }}
          onChange={handleOrderChange}
          options={[
            { value: '', label: '最新发布' },
            { value: 'total_views', label: '最多浏览' },
          ]}
        />
      </Space>

      <Spin spinning={loading}>
        {articles.length === 0 && !loading ? (
          <Empty description="暂无文章" />
        ) : (
          <List
            dataSource={articles}
            renderItem={article => (
              <List.Item key={article.id} style={{ padding: 0, marginBottom: 12 }}>
                <Card
                  hoverable
                  style={{ width: '100%' }}
                  onClick={() => navigate(`/article/article_detail/${article.id}`)}
                >
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
                    <div style={{ flex: 1 }}>
                      <Title level={4} style={{ margin: 0, marginBottom: 4 }}>{article.title}</Title>
                      <Space size="small" style={{ marginBottom: 8 }}>
                        <Text type="secondary">作者：{article.author}</Text>
                        <Text type="secondary">·</Text>
                        <Text type="secondary">{new Date(article.created).toLocaleDateString('zh-CN')}</Text>
                      </Space>
                      <Paragraph type="secondary" ellipsis={{ rows: 2 }} style={{ margin: 0 }}>
                        {article.content_preview}
                      </Paragraph>
                    </div>
                    <Space direction="vertical" align="end" style={{ marginLeft: 16, flexShrink: 0 }}>
                      <Space>
                        <EyeOutlined />
                        <Text type="secondary">{article.total_views}</Text>
                      </Space>
                      <Space>
                        <LikeOutlined />
                        <Text type="secondary">{article.likes}</Text>
                      </Space>
                    </Space>
                  </div>
                </Card>
              </List.Item>
            )}
          />
        )}
      </Spin>

      {total > 10 && (
        <div style={{ textAlign: 'right', marginTop: 16 }}>
          <Pagination
            current={currentPage}
            total={total}
            pageSize={10}
            showSizeChanger={false}
            onChange={page => fetchArticles(page)}
          />
        </div>
      )}
    </div>
  )
}

export default ArticleList
