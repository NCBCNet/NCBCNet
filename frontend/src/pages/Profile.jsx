import { useEffect, useState } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import {
  Card, Form, Input, Button, Upload, Avatar, Typography,
  message, Spin, Descriptions, Divider, Space,
} from 'antd'
import { UserOutlined, PhoneOutlined, EditOutlined, MailOutlined } from '@ant-design/icons'
import { useAuth } from '../store/authStore'
import api from '../services/api'

const { Title, Text } = Typography

function Profile() {
  const { id } = useParams()
  const navigate = useNavigate()
  const { user, isAuthenticated, updateProfile } = useAuth()
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)
  const [profileData, setProfileData] = useState(null)
  const [form] = Form.useForm()
  const [avatarUrl, setAvatarUrl] = useState(null)

  useEffect(() => {
    if (!isAuthenticated) {
      message.warning('请先登录')
      navigate('/usermanage/login')
      return
    }

    const fetchProfile = async () => {
      try {
        const res = await api.get('/auth/me/')
        setProfileData(res.data)
        setAvatarUrl(res.data.profile?.avatar)
        form.setFieldsValue({
          username: res.data.username,
          email: res.data.email,
          phone: res.data.profile?.phone || '',
          bio: res.data.profile?.bio || '',
        })
      } catch {
        message.error('获取用户信息失败')
      } finally {
        setLoading(false)
      }
    }
    fetchProfile()
  }, [id, isAuthenticated, navigate, form])

  const onFinish = async (values) => {
    setSaving(true)
    try {
      await updateProfile({
        email: values.email,
        profile: {
          phone: values.phone,
          bio: values.bio,
        },
      })
      message.success('资料更新成功！')
    } catch {
      message.error('更新失败，请重试')
    } finally {
      setSaving(false)
    }
  }

  const handleAvatarChange = async (info) => {
    if (info.file.status === 'uploading') return

    const formData = new FormData()
    formData.append('avatar', info.file.originFileObj || info.file)

    try {
      const res = await api.patch('/auth/me/', formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
      })
      const newAvatar = res.data.profile?.avatar
      if (newAvatar) {
        setAvatarUrl(newAvatar)
        message.success('头像更新成功！')
      }
    } catch {
      message.error('头像上传失败')
    }
  }

  if (loading) {
    return (
      <div style={{ textAlign: 'center', padding: 80 }}>
        <Spin size="large" />
      </div>
    )
  }

  return (
    <div style={{ maxWidth: 800, margin: '0 auto' }}>
      <div className="page-header">
        <Title level={3}>个人资料</Title>
        <Text type="secondary">管理您的账号信息和个人资料</Text>
      </div>

      {/* 头像和基本信息卡片 */}
      <Card style={{ marginBottom: 24, borderRadius: 8 }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 24 }}>
          <Upload
            showUploadList={false}
            customRequest={({ onSuccess }) => onSuccess()}
            onChange={handleAvatarChange}
            accept="image/*"
          >
            <Avatar
              size={96}
              src={avatarUrl ? avatarUrl.startsWith('http') ? avatarUrl : `/media/${avatarUrl}` : null}
              icon={<UserOutlined />}
              style={{
                cursor: 'pointer',
                border: '2px dashed #d9d9d9',
                backgroundColor: '#f5f5f5',
              }}
            />
            <div style={{ textAlign: 'center', marginTop: 4 }}>
              <Text type="secondary" style={{ fontSize: 12 }}>点击更换</Text>
            </div>
          </Upload>
          <div>
            <Title level={4} style={{ margin: 0 }}>{profileData?.username || '用户'}</Title>
            <Text type="secondary">
              <MailOutlined style={{ marginRight: 4 }} />
              {profileData?.email || '未设置邮箱'}
            </Text>
            <br />
            <Text type="secondary" style={{ fontSize: 13 }}>
              注册时间：{profileData?.date_joined || '-'}
            </Text>
          </div>
        </div>
      </Card>

      {/* 编辑表单 */}
      <Card title={<span><EditOutlined /> 编辑资料</span>} style={{ borderRadius: 8 }}>
        <Form
          form={form}
          layout="vertical"
          onFinish={onFinish}
          style={{ maxWidth: 500 }}
        >
          <Form.Item name="username" label="用户名">
            <Input disabled prefix={<UserOutlined />} />
          </Form.Item>

          <Form.Item
            name="email"
            label="邮箱"
            rules={[{ type: 'email', message: '请输入有效的邮箱地址' }]}
          >
            <Input prefix={<MailOutlined />} placeholder="请输入邮箱" />
          </Form.Item>

          <Form.Item name="phone" label="电话">
            <Input prefix={<PhoneOutlined />} placeholder="请输入电话" />
          </Form.Item>

          <Form.Item name="bio" label="个人简介">
            <Input.TextArea rows={4} placeholder="介绍一下自己..." maxLength={500} showCount />
          </Form.Item>

          <Form.Item>
            <Button
              type="primary"
              htmlType="submit"
              loading={saving}
              style={{ background: '#6f42c1', borderColor: '#6f42c1' }}
            >
              保存修改
            </Button>
          </Form.Item>
        </Form>
      </Card>
    </div>
  )
}

export default Profile