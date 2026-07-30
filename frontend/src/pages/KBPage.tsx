import { useState, useEffect } from 'react';
import {
  Typography,
  Card,
  Table,
  Button,
  Upload,
  Modal,
  Tag,
  Space,
  Popconfirm,
  message,
  Statistic,
  Row,
  Col,
} from 'antd';
import {
  UploadOutlined,
  DeleteOutlined,
  FilePdfOutlined,
  FileWordOutlined,
  FileTextOutlined,
  FileExcelOutlined,
  ReloadOutlined,
} from '@ant-design/icons';
import type { UploadFile } from 'antd';
import apiClient from '../api/client';

const { Title } = Typography;

interface DocumentInfo {
  id: string;
  filename: string;
  original_name: string;
  file_type: string;
  file_size: number | null;
  status: string;
  chunk_count: number;
  error_message: string | null;
  uploaded_by: string | null;
  created_at: string;
  updated_at: string;
}

interface KBStats {
  total_documents: number;
  total_chunks: number;
  total_storage_bytes: number;
  documents_by_status: Record<string, number>;
  documents_by_type: Record<string, number>;
}

const fileIcons: Record<string, React.ReactNode> = {
  pdf: <FilePdfOutlined style={{ color: '#ff4d4f' }} />,
  docx: <FileWordOutlined style={{ color: '#1677ff' }} />,
  txt: <FileTextOutlined />,
  md: <FileTextOutlined />,
  csv: <FileExcelOutlined style={{ color: '#52c41a' }} />,
  html: <FileTextOutlined />,
};

const statusColors: Record<string, string> = {
  uploading: 'processing',
  parsing: 'processing',
  chunking: 'processing',
  embedding: 'processing',
  ready: 'success',
  failed: 'error',
};

const statusLabels: Record<string, string> = {
  uploading: '上传中',
  parsing: '解析中',
  chunking: '分块中',
  embedding: '嵌入中',
  ready: '就绪',
  failed: '失败',
};

export default function KBPage() {
  const [documents, setDocuments] = useState<DocumentInfo[]>([]);
  const [stats, setStats] = useState<KBStats | null>(null);
  const [loading, setLoading] = useState(false);
  const [uploadOpen, setUploadOpen] = useState(false);
  const [uploadFile, setUploadFile] = useState<UploadFile | null>(null);
  const [uploading, setUploading] = useState(false);

  const loadData = async () => {
    setLoading(true);
    try {
      const [docsRes, statsRes] = await Promise.all([
        apiClient.get('/kb/documents?page_size=100'),
        apiClient.get('/kb/stats'),
      ]);
      setDocuments(docsRes.data.documents);
      setStats(statsRes.data);
    } catch {
      // ignore
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  const handleUpload = async () => {
    if (!uploadFile) return;
    setUploading(true);
    try {
      const formData = new FormData();
      formData.append('file', uploadFile as unknown as File);
      await apiClient.post('/kb/documents/upload', formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
      });
      message.success('文档上传成功，正在后台处理...');
      setUploadOpen(false);
      setUploadFile(null);
      setTimeout(() => loadData(), 2000);
    } catch (err: unknown) {
      const detail = (err as { response?: { data?: { error?: { message?: string } } } })?.response?.data?.error?.message;
      message.error(detail || '上传失败');
    } finally {
      setUploading(false);
    }
  };

  const handleDelete = async (id: string) => {
    try {
      await apiClient.delete(`/kb/documents/${id}`);
      message.success('文档已删除');
      loadData();
    } catch {
      message.error('删除失败');
    }
  };

  const columns = [
    {
      title: '文件名',
      dataIndex: 'original_name',
      key: 'name',
      render: (name: string, record: DocumentInfo) => (
        <Space>
          {fileIcons[record.file_type] || <FileTextOutlined />}
          {name}
        </Space>
      ),
    },
    {
      title: '类型',
      dataIndex: 'file_type',
      key: 'type',
      width: 80,
    },
    {
      title: '大小',
      dataIndex: 'file_size',
      key: 'size',
      width: 100,
      render: (size: number | null) =>
        size ? `${(size / 1024).toFixed(1)} KB` : '-',
    },
    {
      title: '块数',
      dataIndex: 'chunk_count',
      key: 'chunks',
      width: 80,
    },
    {
      title: '状态',
      dataIndex: 'status',
      key: 'status',
      width: 100,
      render: (status: string) => (
        <Tag color={statusColors[status] || 'default'}>
          {statusLabels[status] || status}
        </Tag>
      ),
    },
    {
      title: '上传时间',
      dataIndex: 'created_at',
      key: 'created',
      width: 180,
      render: (t: string) => new Date(t).toLocaleString('zh-CN'),
    },
    {
      title: '操作',
      key: 'actions',
      width: 80,
      render: (_: unknown, record: DocumentInfo) => (
        <Popconfirm
          title="确定删除此文档？删除后关联的所有知识库内容将无法检索。"
          onConfirm={() => handleDelete(record.id)}
        >
          <Button type="text" danger icon={<DeleteOutlined />} size="small" />
        </Popconfirm>
      ),
    },
  ];

  return (
    <div style={{ padding: 24, maxWidth: 1200, margin: '0 auto' }}>
      <Title level={3} style={{ marginBottom: 24 }}>
        知识库管理
      </Title>

      {/* Stats */}
      {stats && (
        <Row gutter={16} style={{ marginBottom: 24 }}>
          <Col span={6}>
            <Card size="small">
              <Statistic title="文档总数" value={stats.total_documents} prefix="📄" />
            </Card>
          </Col>
          <Col span={6}>
            <Card size="small">
              <Statistic title="知识块数" value={stats.total_chunks} prefix="✂️" />
            </Card>
          </Col>
          <Col span={6}>
            <Card size="small">
              <Statistic
                title="存储大小"
                value={(stats.total_storage_bytes / 1024 / 1024).toFixed(1)}
                suffix="MB"
                prefix="💾"
              />
            </Card>
          </Col>
          <Col span={6}>
            <Card size="small">
              <Statistic
                title="就绪文档"
                value={stats.documents_by_status.ready || 0}
                suffix={`/ ${stats.total_documents}`}
                prefix="✅"
              />
            </Card>
          </Col>
        </Row>
      )}

      {/* Toolbar */}
      <Card
        style={{ marginBottom: 16 }}
        styles={{ body: { padding: '12px 24px' } }}
      >
        <Space>
          <Button type="primary" icon={<UploadOutlined />} onClick={() => setUploadOpen(true)}>
            上传文档
          </Button>
          <Button icon={<ReloadOutlined />} onClick={loadData} loading={loading}>
            刷新
          </Button>
        </Space>
        <Tag style={{ marginLeft: 16 }}>支持 PDF / DOCX / CSV / TXT / MD / HTML，最大 20MB</Tag>
      </Card>

      {/* Table */}
      <Card>
        <Table
          dataSource={documents}
          columns={columns}
          rowKey="id"
          loading={loading}
          pagination={{ pageSize: 20 }}
          locale={{ emptyText: '暂无文档，请点击"上传文档"添加知识库内容' }}
        />
      </Card>

      {/* Upload Modal */}
      <Modal
        title="上传文档"
        open={uploadOpen}
        onOk={handleUpload}
        onCancel={() => {
          setUploadOpen(false);
          setUploadFile(null);
        }}
        confirmLoading={uploading}
        okText="开始上传"
        cancelText="取消"
      >
        <Upload
          beforeUpload={(file) => {
            const allowed = ['pdf', 'docx', 'csv', 'txt', 'md', 'html'];
            const ext = file.name.split('.').pop()?.toLowerCase() || '';
            if (!allowed.includes(ext)) {
              message.error(`不支持的文件类型: .${ext}`);
              return false;
            }
            if (file.size > 20 * 1024 * 1024) {
              message.error('文件大小不能超过 20MB');
              return false;
            }
            setUploadFile(file);
            return false; // prevent auto-upload
          }}
          onRemove={() => setUploadFile(null)}
          fileList={uploadFile ? [uploadFile] : []}
          maxCount={1}
        >
          <Button icon={<UploadOutlined />}>选择文件</Button>
        </Upload>
        {uploadFile && (
          <div style={{ marginTop: 8 }}>
            <Typography.Text>已选择: {uploadFile.name}</Typography.Text>
          </div>
        )}
      </Modal>
    </div>
  );
}
