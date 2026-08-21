import { useCallback, useEffect, useMemo, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import {
  Breadcrumb, Button, Card, Col, Empty, Input, List, Modal, Row,
  Space, Spin, Statistic, Tag, Tooltip, Tree, Typography, Upload, message,
} from 'antd'
import {
  CloudUploadOutlined, DeleteOutlined, DownloadOutlined, FileOutlined,
  FolderAddOutlined, FolderOutlined, HddOutlined, InboxOutlined, LinkOutlined,
} from '@ant-design/icons'
import api from '../services/api'
import { useAuth } from '../store/authStore'
import { useUpload } from '../store/uploadStore'
import { formatSize } from '../utils/uploadProgress'

const { Title, Text } = Typography
const { Dragger } = Upload

const ROOT_TREE_KEY = 'folder-root'

function FileList() {
  const navigate = useNavigate()
  const { user } = useAuth()
  const { uploadFile } = useUpload()

  // 当前浏览路径（从根目录开始的文件夹链），currentFolderId 由路径末位推导
  const [folderPath, setFolderPath] = useState([])
  const [folders, setFolders] = useState([])
  const [files, setFiles] = useState([])
  const [loading, setLoading] = useState(true)

  // 共享文件（其他用户共享的）
  const [sharedFiles, setSharedFiles] = useState([])
  const [sharedLoading, setSharedLoading] = useState(false)

  // 文件夹树
  const [treeData, setTreeData] = useState([])
  const [treeExpandedKeys, setTreeExpandedKeys] = useState([])

  // 新建文件夹弹窗
  const [createModalOpen, setCreateModalOpen] = useState(false)
  const [newFolderName, setNewFolderName] = useState('')
  const [creating, setCreating] = useState(false)

  // 上传状态（进度/速度/剩余时间统一由 uploadStore 的上传任务中心展示）
  const [uploading, setUploading] = useState(false)

  const currentFolderId = folderPath.length > 0 ? folderPath[folderPath.length - 1].id : null

  // ---------- 数据加载 ----------

  const fetchFolderContents = useCallback(async (path) => {
    setLoading(true)
    const folderId = path.length > 0 ? path[path.length - 1].id : null
    try {
      const params = {}
      if (folderId) params.folder = folderId
      const [foldersRes, filesRes] = await Promise.all([
        api.get('/folders/', { params: folderId ? { parent: folderId } : {} }),
        api.get('/files/', { params }),
      ])
      setFolders(foldersRes.data)
      setFiles(filesRes.data)
    } catch {
      message.error('加载文件列表失败')
    } finally {
      setLoading(false)
    }
  }, [])

  const fetchSharedFiles = useCallback(async () => {
    setSharedLoading(true)
    try {
      const res = await api.get('/files/shared/')
      setSharedFiles(res.data)
    } catch {
      // 共享文件加载失败不阻塞主列表
    } finally {
      setSharedLoading(false)
    }
  }, [])

  const navigateToPath = useCallback((path) => {
    setFolderPath(path)
    fetchFolderContents(path)
  }, [fetchFolderContents])

  // ---------- 文件夹树 ----------

  const fetchTreeChildren = useCallback(async (parentId, parentPath = []) => {
    const res = await api.get('/folders/', { params: parentId ? { parent: parentId } : {} })
    return res.data.map((f) => {
      const path = [...parentPath, { id: f.id, name: f.name }]
      return {
        title: f.name,
        key: `folder-${f.id}`,
        folderId: f.id,
        path,
        isLeaf: !f.has_children,
        children: [],
      }
    })
  }, [])

  const updateTreeNodeChildren = (nodes, key, children) =>
    nodes.map((node) => {
      if (node.key === key) return { ...node, children }
      if (node.children && node.children.length > 0) {
        return { ...node, children: updateTreeNodeChildren(node.children, key, children) }
      }
      return node
    })

  const buildTree = useCallback(async () => {
    try {
      const children = await fetchTreeChildren(null, [])
      setTreeData([{
        title: '我的云盘',
        key: ROOT_TREE_KEY,
        folderId: null,
        path: [],
        isLeaf: false,
        children,
      }])
    } catch {
      // 文件夹树加载失败不影响主列表
    }
  }, [fetchTreeChildren])

  const handleTreeLoadData = useCallback(async (node) => {
    const children = await fetchTreeChildren(node.folderId ?? null, node.path || [])
    setTreeData((prev) => updateTreeNodeChildren(prev, node.key, children))
  }, [fetchTreeChildren])

  const handleTreeSelect = useCallback((keys, info) => {
    if (!info.node || info.selected === false) return
    const node = info.node
    const targetId = node.folderId ?? null
    if (targetId === currentFolderId) return
    navigateToPath(node.path || [])
  }, [currentFolderId, navigateToPath])

  // ---------- 初始化 ----------

  useEffect(() => {
    fetchFolderContents([])
    fetchSharedFiles()
    buildTree()
  }, [fetchFolderContents, fetchSharedFiles, buildTree])

  // ---------- 文件夹操作 ----------

  const handleCreateFolder = async () => {
    const name = newFolderName.trim()
    if (!name) {
      message.warning('请输入文件夹名称')
      return
    }
    setCreating(true)
    try {
      const payload = { name }
      if (currentFolderId) payload.parent = currentFolderId
      await api.post('/folders/', payload)
      message.success('文件夹创建成功')
      setCreateModalOpen(false)
      setNewFolderName('')
      fetchFolderContents(folderPath)
      buildTree()
    } catch (err) {
      message.error(err.response?.data?.message || '创建文件夹失败')
    } finally {
      setCreating(false)
    }
  }

  const handleDeleteFolder = (folder) => {
    Modal.confirm({
      title: '确认删除文件夹',
      content: `确定要删除文件夹「${folder.name}」吗？其中的文件将一并删除，此操作不可撤销。`,
      okText: '确认删除',
      okType: 'danger',
      cancelText: '取消',
      onOk: async () => {
        try {
          await api.delete(`/folders/${folder.id}/delete/`)
          message.success('文件夹已删除')
          fetchFolderContents(folderPath)
          buildTree()
        } catch (err) {
          message.error(err.response?.data?.message || '删除文件夹失败')
        }
      },
    })
  }

  // ---------- 文件操作 ----------

  const handleDeleteFile = (file) => {
    Modal.confirm({
      title: '确认删除文件',
      content: `确定要删除文件「${file.original_name}」吗？此操作不可撤销。`,
      okText: '确认删除',
      okType: 'danger',
      cancelText: '取消',
      onOk: async () => {
        try {
          await api.delete(`/files/${file.id}/delete/`)
          message.success('文件已删除')
          fetchFolderContents(folderPath)
          fetchSharedFiles()
        } catch (err) {
          message.error(err.response?.data?.message || '删除文件失败')
        }
      },
    })
  }

  const handleToggleShare = async (file) => {
    try {
      const res = await api.post(`/files/${file.id}/share/`)
      setFiles((prev) => prev.map((f) => (f.id === file.id ? { ...f, share: res.data.share } : f)))
      message.success(res.data.message || '共享状态已更新')
    } catch (err) {
      message.error(err.response?.data?.message || '操作失败')
    }
  }

  const handleDownload = async (file) => {
    try {
      const res = await api.get(`/files/${file.id}/download-url/`)
      const { url } = res.data
      // 签名下载链接即授权凭证，直接用 <a> 触发下载（服务端返回 Content-Disposition: attachment）
      const link = document.createElement('a')
      link.href = url
      link.target = '_blank'
      link.rel = 'noopener noreferrer'
      document.body.appendChild(link)
      link.click()
      document.body.removeChild(link)
    } catch (err) {
      message.error(err.response?.data?.message || '获取下载链接失败')
    }
  }

  // ---------- 上传 ----------

  const handleUpload = async ({ file, onSuccess, onError }) => {
    setUploading(true)
    const { ok } = await uploadFile(file, currentFolderId)
    setUploading(false)
    if (ok) {
      message.success(`文件「${file.name}」上传成功`)
      onSuccess?.()
      fetchFolderContents(folderPath)
      fetchSharedFiles()
    } else {
      message.error(`文件「${file.name}」上传失败`)
      onError?.()
    }
  }

  // ---------- 派生数据 ----------

  const totalSize = useMemo(
    () => files.reduce((sum, f) => sum + (Number(f.file_size) || 0), 0),
    [files],
  )

  const breadcrumbItems = [
    {
      title: <a onClick={() => navigateToPath([])}>全部文件</a>,
    },
    ...folderPath.map((f, i) => ({
      title: <a onClick={() => navigateToPath(folderPath.slice(0, i + 1))}>{f.name}</a>,
    })),
  ]

  const currentTreeKey = currentFolderId ? `folder-${currentFolderId}` : ROOT_TREE_KEY

  const isOwner = (file) => user?.id != null && file.owner === user.id

  // ---------- 渲染 ----------

  return (
    <div>
      {/* 页面头部 */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: 12, marginBottom: 24 }}>
        <div>
          <Title level={3} style={{ margin: 0 }}>云盘</Title>
          <Text type="secondary">文件存储与共享</Text>
        </div>
        <Space>
          <Button icon={<FolderAddOutlined />} onClick={() => setCreateModalOpen(true)}>
            新建文件夹
          </Button>
          <Button
            type="primary"
            icon={<CloudUploadOutlined />}
            onClick={() => navigate('/file_up/file_upload')}
            style={{ background: '#6f42c1', borderColor: '#6f42c1' }}
          >
            上传文件
          </Button>
        </Space>
      </div>

      <Row gutter={[16, 16]}>
        {/* 左侧：文件夹树 + 快速上传 */}
        <Col xs={24} lg={6}>
          <Card
            title="文件夹"
            style={{ marginBottom: 16, borderRadius: 8 }}
            styles={{ body: { padding: '8px 12px', maxHeight: 360, overflow: 'auto' } }}
          >
            <Tree
              showLine
              treeData={treeData}
              expandedKeys={treeExpandedKeys}
              onExpand={(keys) => setTreeExpandedKeys(keys)}
              loadData={handleTreeLoadData}
              selectedKeys={[currentTreeKey]}
              onSelect={handleTreeSelect}
              defaultExpandAll
            />
          </Card>

          <Card title="快速上传" style={{ borderRadius: 8 }} styles={{ body: { padding: 12 } }}>
            <Dragger
              multiple={false}
              showUploadList={false}
              disabled={uploading}
              customRequest={handleUpload}
            >
              <p className="ant-upload-drag-icon">
                <InboxOutlined style={{ color: '#6f42c1' }} />
              </p>
              <p className="ant-upload-text">点击或拖拽文件到此处上传</p>
              <p className="ant-upload-hint">
                上传到：{currentFolderId ? folderPath.map((f) => f.name).join(' / ') : '根目录'}
              </p>
            </Dragger>
            {uploading && (
              <div style={{ marginTop: 12 }}>
                <Text type="secondary" style={{ fontSize: 12 }}>
                  上传中… 进度与速度见右上角「上传任务」
                </Text>
              </div>
            )}
          </Card>
        </Col>

        {/* 右侧：面包屑 + 统计 + 文件网格 + 共享文件 */}
        <Col xs={24} lg={18}>
          <Breadcrumb items={breadcrumbItems} style={{ marginBottom: 16 }} />

          {/* 统计卡片 */}
          <Row gutter={[16, 16]} style={{ marginBottom: 16 }}>
            <Col xs={8}>
              <Card style={{ borderRadius: 8 }} styles={{ body: { padding: '16px 20px' } }}>
                <Statistic title="文件夹" value={folders.length} prefix={<FolderOutlined style={{ color: '#6f42c1' }} />} />
              </Card>
            </Col>
            <Col xs={8}>
              <Card style={{ borderRadius: 8 }} styles={{ body: { padding: '16px 20px' } }}>
                <Statistic title="文件" value={files.length} prefix={<FileOutlined style={{ color: '#6f42c1' }} />} />
              </Card>
            </Col>
            <Col xs={8}>
              <Card style={{ borderRadius: 8 }} styles={{ body: { padding: '16px 20px' } }}>
                <Statistic title="总大小" value={totalSize} prefix={<HddOutlined style={{ color: '#6f42c1' }} />} formatter={() => formatSize(totalSize)} />
              </Card>
            </Col>
          </Row>

          {/* 文件夹 / 文件网格 */}
          <Spin spinning={loading}>
            {folders.length === 0 && files.length === 0 ? (
              <Empty description="此文件夹为空" style={{ padding: 60 }} />
            ) : (
              <div className="file-grid">
                {folders.map((folder) => (
                  <Card
                    key={folder.id}
                    hoverable
                    onClick={() => navigateToPath([...folderPath, { id: folder.id, name: folder.name }])}
                    style={{ borderRadius: 8 }}
                    styles={{ body: { padding: '16px 12px' } }}
                    actions={[
                      <Tooltip title="删除文件夹" key="delete">
                        <DeleteOutlined
                          style={{ color: '#ff4d4f' }}
                          onClick={(e) => {
                            e.stopPropagation()
                            handleDeleteFolder(folder)
                          }}
                        />
                      </Tooltip>,
                    ]}
                  >
                    <div style={{ textAlign: 'center', cursor: 'pointer' }}>
                      <FolderOutlined style={{ fontSize: 40, color: '#6f42c1' }} />
                      <div style={{ marginTop: 8 }}>
                        <Text strong ellipsis={{ tooltip: folder.name }} style={{ maxWidth: '100%', display: 'block' }}>
                          {folder.name}
                        </Text>
                      </div>
                      <Text type="secondary" style={{ fontSize: 12 }}>
                        {folder.created_at?.slice(0, 10) || ''}
                      </Text>
                    </div>
                  </Card>
                ))}

                {files.map((file) => (
                  <Card
                    key={file.id}
                    hoverable
                    style={{ borderRadius: 8 }}
                    styles={{ body: { padding: '16px 12px' } }}
                    actions={[
                      <Tooltip title="下载" key="download">
                        <DownloadOutlined onClick={() => handleDownload(file)} />
                      </Tooltip>,
                      ...(isOwner(file)
                        ? [
                            <Tooltip title={file.share ? '取消共享' : '共享文件'} key="share">
                              <LinkOutlined
                                style={{ color: file.share ? '#6f42c1' : undefined }}
                                onClick={() => handleToggleShare(file)}
                              />
                            </Tooltip>,
                            <Tooltip title="删除" key="delete">
                              <DeleteOutlined
                                style={{ color: '#ff4d4f' }}
                                onClick={() => handleDeleteFile(file)}
                              />
                            </Tooltip>,
                          ]
                        : []),
                    ]}
                  >
                    <div style={{ textAlign: 'center' }}>
                      <FileOutlined style={{ fontSize: 40, color: '#6f42c1' }} />
                      <div style={{ marginTop: 8 }}>
                        <Text strong ellipsis={{ tooltip: file.original_name }} style={{ maxWidth: '100%', display: 'block' }}>
                          {file.original_name}
                        </Text>
                      </div>
                      <div>
                        <Text type="secondary" style={{ fontSize: 12 }}>
                          {file.file_size_display || formatSize(file.file_size)}
                        </Text>
                        {file.share && (
                          <Tag color="purple" style={{ marginLeft: 6, fontSize: 12 }}>已共享</Tag>
                        )}
                      </div>
                    </div>
                  </Card>
                ))}
              </div>
            )}
          </Spin>

          {/* 共享文件 */}
          <Card
            title="共享文件"
            style={{ marginTop: 24, borderRadius: 8 }}
            extra={<Text type="secondary" style={{ fontSize: 12 }}>其他用户共享给你的文件</Text>}
          >
            <Spin spinning={sharedLoading}>
              {sharedFiles.length === 0 ? (
                <Empty description="暂无其他用户共享的文件" />
              ) : (
                <List
                  dataSource={sharedFiles}
                  renderItem={(file) => (
                    <List.Item
                      actions={[
                        <Button
                          key="download"
                          type="link"
                          size="small"
                          icon={<DownloadOutlined />}
                          onClick={() => handleDownload(file)}
                        >
                          下载
                        </Button>,
                      ]}
                    >
                      <List.Item.Meta
                        avatar={<FileOutlined style={{ fontSize: 24, color: '#6f42c1' }} />}
                        title={file.original_name}
                        description={
                          <Space size={12}>
                            <span>分享者：{file.owner_username}</span>
                            <span>{file.file_size_display || formatSize(file.file_size)}</span>
                            <span>{file.uploaded_at?.slice(0, 10) || ''}</span>
                          </Space>
                        }
                      />
                    </List.Item>
                  )}
                />
              )}
            </Spin>
          </Card>
        </Col>
      </Row>

      {/* 新建文件夹弹窗 */}
      <Modal
        title="新建文件夹"
        open={createModalOpen}
        onOk={handleCreateFolder}
        confirmLoading={creating}
        onCancel={() => {
          setCreateModalOpen(false)
          setNewFolderName('')
        }}
        okText="创建"
        cancelText="取消"
        okButtonProps={{ style: { background: '#6f42c1', borderColor: '#6f42c1' } }}
      >
        <Input
          placeholder="请输入文件夹名称"
          value={newFolderName}
          onChange={(e) => setNewFolderName(e.target.value)}
          onPressEnter={handleCreateFolder}
          maxLength={50}
          autoFocus
        />
        <Text type="secondary" style={{ fontSize: 12, display: 'block', marginTop: 8 }}>
          将创建在：{currentFolderId ? folderPath.map((f) => f.name).join(' / ') : '根目录'}
        </Text>
      </Modal>
    </div>
  )
}

export default FileList
