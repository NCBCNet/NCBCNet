import { useEffect, useState, useCallback } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import {
  Typography, Spin, Tag, Button, Space, Divider, Input, message,
  Modal, Row, Col, Card, Avatar, Affix, Tooltip, Empty,
} from 'antd'
import {
  EyeOutlined, HeartOutlined, HeartFilled, DeleteOutlined,
  EditOutlined, UserOutlined, ArrowLeftOutlined,
  ClockCircleOutlined, CommentOutlined,
} from '@ant-design/icons'
import DOMPurify from 'dompurify'
import api from '../services/api'
import { useAuth } from '../store/authStore'

const { Title, Text, Paragraph } = Typography
const { TextArea } = Input

function ArticleDetail() {
  const { id } = useParams()
  const navigate = useNavigate()
  const { user, isAuthenticated } = useAuth()

  const [article, setArticle] = useState(null)
  const [loading, setLoading] = useState(true)
  const [likes, setLikes] = useState(0)
  const [liked, setLiked] = useState(false)

  // 评论相关
  const [comments, setComments] = useState([])
  const [commentText, setCommentText] = useState('')
  const [submitting, setSubmitting] = useState(false)
  const [replyTo, setReplyTo] = useState(null) // { id, username }

  const fetchArticle = useCallback(async () => {
    setLoading(true)
    try {
      const res = await api.get(`/articles/${id}/`)
      setArticle(res.data)
      setLikes(res.data.likes)
      setComments(res.data.comments || [])
    } catch {
      message.error('加载文章失败')
    } finally {
      setLoading(false)
    }
  }, [id])

  useEffect(() => {
    fetchArticle()
  }, [fetchArticle])

  // 点赞
  const handleLike = async () => {
    if (!isAuthenticated) {
      message.warning('请先登录')
      navigate('/usermanage/login')
      return
    }
    try {
      const res = await api.post(`/articles/${id}/like/`)
      setLikes(res.data.likes)
      setLiked(true)
    } catch {
      message.error('点赞失败')
    }
  }

  // 删除文章
  const handleDelete = () => {
    Modal.confirm({
      title: '确认删除',
      content: '确定要删除这篇文章吗？此操作不可撤销。',
      okText: '确认删除',
      okType: 'danger',
      cancelText: '取消',
      onOk: async () => {
        try {
          await api.delete(`/articles/${id}/delete/`)
          message.success('文章已删除')
          navigate('/article')
        } catch {
          message.error('删除失败')
        }
      },
    })
  }

  // 发表评论
  const handleSubmitComment = async () => {
    if (!commentText.trim()) {
      message.warning('请输入评论内容')
      return
    }
    setSubmitting(true)
    try {
      if (replyTo) {
        await api.post(`/articles/${id}/comments/${replyTo.id}/reply/`, { content: commentText })
      } else {
        await api.post(`/articles/${id}/comments/`, { content: commentText })
      }
      message.success('评论成功')
      setCommentText('')
      setReplyTo(null)
      fetchArticle() // 重新加载评论
    } catch {
      message.error('评论发表失败')
    } finally {
      setSubmitting(false)
    }
  }

  const handleReply = (comment) => {
    if (!isAuthenticated) {
      message.warning('请先登录')
      navigate('/usermanage/login')
      return
    }
    setReplyTo({ id: comment.id, username: comment.user?.username })
    // 滚动到评论框
    window.scrollTo({ top: document.body.scrollHeight, behavior: 'smooth' })
  }

  const cancelReply = () => {
    setReplyTo(null)
    setCommentText('')
  }

  // 递归渲染评论
  const renderComment = (comment, depth = 0) => (
    <div key={comment.id} style={{ marginLeft: depth > 0 ? 40 : 0, marginTop: 16 }}>
      <div style={{
        padding: '12px 16px',
        background: depth > 0 ? '#fafafa' : '#fff',
        borderRadius: 8,
        border: '1px solid #f0f0f0',
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 8 }}>
          <Avatar size={24} icon={<UserOutlined />} style={{ backgroundColor: '#6f42c1' }} />
          <Text strong style={{ color: '#6f42c1' }}>{comment.user?.username}</Text>
          {comment.reply_to && (
            <>
              <Text type="secondary" style={{ fontSize: 13 }}>
                <HeartFilled style={{ color: '#6f42c1', fontSize: 10 }} /> 回复
              </Text>
              <Text strong style={{ color: '#6f42c1' }}>{comment.reply_to?.username}</Text>
            </>
          )}
          <Text type="secondary" style={{ fontSize: 12 }}>{comment.created}</Text>
        </div>
        <div dangerouslySetInnerHTML={{ __html: DOMPurify.sanitize(comment.content) }} />
        <div style={{ marginTop: 8 }}>
          <Button type="link" size="small" onClick={() => handleReply(comment)}>
            回复
          </Button>
        </div>
      </div>
      {comment.children?.map((child) => renderComment(child, depth + 1))}
    </div>
  )

  if (loading) {
    return <div style={{ textAlign: 'center', padding: 80 }}><Spin size="large" /></div>
  }

  if (!article) {
    return <Empty description="文章不存在" style={{ padding: 80 }} />
  }

  const isAuthor = user?.id === article.author?.id

  return (
    <Row gutter={24}>
      {/* 主内容区 */}
      <Col xs={24} lg={17}>
        {/* 返回按钮 */}
        <Button
          type="link"
          icon={<ArrowLeftOutlined />}
          style={{ padding: 0, marginBottom: 16 }}
          onClick={() => navigate('/article')}
        >
          返回论坛
        </Button>

        {/* 文章标题 */}
        <Title level={2} style={{ marginTop: 0, marginBottom: 16 }}>{article.title}</Title>

        {/* 元信息 */}
        <Card style={{ marginBottom: 24, borderRadius: 8, background: '#f9f0ff' }} styles={{ body: { padding: '12px 20px' } }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: 8 }}>
            <Space>
              <Avatar icon={<UserOutlined />} style={{ backgroundColor: '#6f42c1' }} />
              <Text strong>{article.author?.username}</Text>
              {isAuthor && (
                <>
                  <Button type="link" size="small" icon={<EditOutlined />} onClick={() => navigate(`/article/article_edit/${id}`)}>
                    编辑
                  </Button>
                  <Button type="link" size="small" icon={<DeleteOutlined />} danger onClick={handleDelete}>
                    删除
                  </Button>
                </>
              )}
            </Space>
            <Space>
              <Text type="secondary"><EyeOutlined /> {article.total_views}</Text>
              <Text type="secondary"><ClockCircleOutlined /> {article.created?.slice(0, 10)}</Text>
            </Space>
          </div>
        </Card>

        {/* 文章内容 */}
        <div
          className="article-content"
          dangerouslySetInnerHTML={{ __html: DOMPurify.sanitize(article.content_html) }}
        />

        {/* 标签 */}
        {article.tags?.length > 0 && (
          <div style={{ marginTop: 24 }}>
            {article.tags.map((t) => (
              <Tag key={t} style={{ marginBottom: 4 }}>{t}</Tag>
            ))}
          </div>
        )}

        {/* 点赞 */}
        <div style={{ textAlign: 'center', marginTop: 32 }}>
          <Button
            size="large"
            icon={liked ? <HeartFilled /> : <HeartOutlined />}
            onClick={handleLike}
            style={{
              borderColor: '#6f42c1',
              color: liked ? '#fff' : '#6f42c1',
              background: liked ? '#6f42c1' : '#fff',
              borderRadius: 24,
              padding: '4px 28px',
              height: 44,
            }}
          >
            <span style={{ marginLeft: 4 }}>{likes}</span>
          </Button>
        </div>

        <Divider />

        {/* 评论部分 */}
        <div id="comments">
          <Title level={4}><CommentOutlined /> 评论 ({comments.length})</Title>

          {/* 评论输入框 */}
          {isAuthenticated ? (
            <Card style={{ marginBottom: 24, borderRadius: 8 }} styles={{ body: { padding: 16 } }}>
              {replyTo && (
                <div style={{ marginBottom: 8 }}>
                  <Text type="secondary">回复 @{replyTo.username}：</Text>
                  <Button type="link" size="small" onClick={cancelReply} style={{ padding: 0 }}>
                    取消回复
                  </Button>
                </div>
              )}
              <TextArea
                rows={3}
                value={commentText}
                onChange={(e) => setCommentText(e.target.value)}
                placeholder={replyTo ? `回复 @${replyTo.username}...` : '写下你的评论...'}
              />
              <div style={{ marginTop: 12, textAlign: 'right' }}>
                <Button
                  type="primary"
                  loading={submitting}
                  onClick={handleSubmitComment}
                  style={{ background: '#6f42c1', borderColor: '#6f42c1' }}
                >
                  发表评论
                </Button>
              </div>
            </Card>
          ) : (
            <Card style={{ marginBottom: 24, borderRadius: 8, textAlign: 'center' }} styles={{ body: { padding: 16 } }}>
              <Text type="secondary">
                请 <a onClick={() => navigate('/usermanage/login')} style={{ color: '#6f42c1' }}>登录</a> 后发表评论
              </Text>
            </Card>
          )}

          {/* 评论列表 */}
          {comments.length === 0 ? (
            <Empty description="暂无评论，快来抢沙发吧！" />
          ) : (
            comments.map((comment) => renderComment(comment))
          )}
        </div>
      </Col>

      {/* 目录侧边栏 */}
      <Col xs={24} lg={7}>
        <Affix offsetTop={80}>
          <Card
            title="目录"
            size="small"
            style={{ borderRadius: 8, marginTop: 8 }}
            styles={{ body: { maxHeight: 'calc(100vh - 200px)', overflow: 'auto', padding: '12px 16px' } }}
          >
            <div
              className="article-toc"
              dangerouslySetInnerHTML={{ __html: DOMPurify.sanitize(article.toc || '') }}
            />
          </Card>
        </Affix>
      </Col>
    </Row>
  )
}

export default ArticleDetail