import { Avatar, Button, Typography } from 'antd'
import { UserOutlined, HeartFilled } from '@ant-design/icons'
import DOMPurify from 'dompurify'

const { Text } = Typography

/**
 * 单条评论（递归渲染子评论）。
 * 纯展示组件：回复动作通过 onReply(comment) 抛给父级处理（登录校验等）。
 */
function CommentItem({ comment, depth = 0, onReply }) {
  return (
    <div style={{ marginLeft: depth > 0 ? 40 : 0, marginTop: 16 }}>
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
          <Button type="link" size="small" onClick={() => onReply?.(comment)}>
            回复
          </Button>
        </div>
      </div>
      {comment.children?.map((child) => (
        <CommentItem key={child.id} comment={child} depth={depth + 1} onReply={onReply} />
      ))}
    </div>
  )
}

/**
 * 递归评论树。
 * @param {Array} comments - 评论列表（含 children 嵌套）
 * @param {Function} onReply - 点击“回复”时的回调，参数为评论对象
 */
function CommentTree({ comments = [], onReply }) {
  return comments.map((comment) => (
    <CommentItem key={comment.id} comment={comment} onReply={onReply} />
  ))
}

export default CommentTree
