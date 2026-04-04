import { useEffect, useState } from 'react'
import { Card, Typography, Divider, Space, Button, Tag, Spin, Result } from 'antd'
import { LikeOutlined, EyeOutlined, ArrowLeftOutlined, LikeFilled } from '@ant-design/icons'
import { useParams, useNavigate } from 'react-router-dom'
import request from '../utils/request'

const { Title, Text } = Typography

function ArticleDetail() {
  const { id } = useParams()
  const navigate = useNavigate()
  const [article, setArticle] = useState(null)
  const [loading, setLoading] = useState(true)
  const [notFound, setNotFound] = useState(false)
  const [liking, setLiking] = useState(false)
  const [liked, setLiked] = useState(false)

  useEffect(() => {
    setLoading(true)
    setNotFound(false)
    request.get(`/article/api/detail/${id}/`)
      .then(res => setArticle(res.data))
      .catch(err => {
        if (err.response?.status === 404) setNotFound(true)
      })
      .finally(() => setLoading(false))
  }, [id])

  const handleLike = async () => {
    if (liked) return
    setLiking(true)
    try {
      const res = await request.post(`/article/api/like/${id}/`)
      setArticle(prev => ({ ...prev, likes: res.data.likes }))
      setLiked(true)
    } catch {
      // ignore
    } finally {
      setLiking(false)
    }
  }

  if (loading) {
    return (
      <div style={{ textAlign: 'center', padding: '60px 0' }}>
        <Spin size="large" />
      </div>
    )
  }

  if (notFound || !article) {
    return <Result status="404" title="文章不存在" extra={<Button onClick={() => navigate('/article')}>返回列表</Button>} />
  }

  return (
    <div style={{ maxWidth: 860, margin: '0 auto' }}>
      <Button icon={<ArrowLeftOutlined />} style={{ marginBottom: 16 }} onClick={() => navigate('/article')}>
        返回列表
      </Button>

      <Card>
        <Title level={1} style={{ marginBottom: 8 }}>{article.title}</Title>

        <Space wrap style={{ marginBottom: 16 }}>
          <Text type="secondary">作者：{article.author}</Text>
          <Text type="secondary">·</Text>
          <Text type="secondary">{new Date(article.created).toLocaleDateString('zh-CN')}</Text>
          {article.column && <Tag color="blue">{article.column}</Tag>}
          {article.tags?.map(tag => <Tag key={tag}>{tag}</Tag>)}
        </Space>

        <Space size="large" style={{ marginBottom: 16 }}>
          <Space>
            <EyeOutlined />
            <Text type="secondary">{article.total_views} 次浏览</Text>
          </Space>
          <Button
            icon={liked ? <LikeFilled style={{ color: '#1677ff' }} /> : <LikeOutlined />}
            onClick={handleLike}
            loading={liking}
            disabled={liked}
          >
            {article.likes} 点赞
          </Button>
        </Space>

        <Divider />

        <div
          className="article-content"
          dangerouslySetInnerHTML={{ __html: article.content }}
          style={{ lineHeight: 1.8, fontSize: 16 }}
        />
      </Card>
    </div>
  )
}

export default ArticleDetail
