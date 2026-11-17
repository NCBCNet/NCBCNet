# 网上评卷系统（第一阶段）

`grading` 是独立的 Django 领域应用，复用项目现有的 Django/DRF、HttpOnly Cookie JWT 和对象存储配置。

评卷人使用 Django 原生 **“教师”组**。迁移会自动创建该组并授予 `gradingassignment.grade_answers`
权限；只有教师组成员才能查看、领取和提交评卷任务，管理员负责将用户加入该组。

## 核心流程

1. 管理员创建考试和题目，配置满分、题型及评分细则。
2. 扫描服务上传扫描批次，生成答题卡记录并绑定考号。
3. 分发服务按题目把答题卡切块后创建 `GradingAssignment`，每个评卷人只能看到自己的任务。
4. 评卷人领取任务并提交分数和评语；事务锁保证重复提交和并发回收安全。
5. 超时任务可回收到待评阅状态，重新由原分配人领取。
6. 所有提交写入 `GradingAuditLog`，答题卡在所有任务完成后自动变为 `completed`。

## 数据边界

- `Exam`：考试及生命周期。
- `Question`：题目、满分和评分细则。
- `ScanBatch`：原始扫描批次。
- `AnswerSheet`：考生答题卡及客观/主观分数。
- `GradingAssignment`：题块与评卷人的分发关系。
- `GradingAuditLog`：不可变操作审计记录。

## API

挂载前缀为 `/api/v1/grading/`：

- `GET/POST /exams/`
- `GET/PATCH /exams/{id}/`
- `GET /exams/{id}/statistics/`
- `GET/POST /exams/{id}/questions/`
- `GET/POST /exams/{id}/scan-batches/`
- `GET/POST /exams/{id}/answer-sheets/`
- `POST /exams/{id}/assignments/distribute/`
- `GET /assignments/me/`
- `POST /assignments/{id}/claim/`
- `POST /assignments/{id}/submit/`
- `POST /assignments/reclaim/`（管理员）

第一阶段提供可靠的领域模型和评卷回收闭环；第二阶段在此基础上加入扫描识别、双评仲裁和 React 评卷工作台。

## 第二阶段已实现

- `RecognitionJob`：扫描批次识别任务、处理状态、图像尺寸、方向和质量结果。
- `ArbitrationCase`：双评分差超阈值后自动生成仲裁案件，管理员提交最终分。
- 双评分发：默认每个主观题分配两名教师，可配置分差阈值。
- 教师工作台：`/grading/workbench`，支持任务刷新、领取、图像查看、评分、评语和提交。
- 新增接口：
  - `POST/GET /scan-batches/{id}/recognize/`
  - `POST /scan-batches/{id}/recognize/retry/`（管理员）
  - `GET /arbitrations/`
  - `POST /arbitrations/{id}/resolve/`

## 第三阶段已开始实现

- `ExamTemplate`：保存定位点、题块坐标和 OMR 区域模板。
- `ScanPage`：将扫描批次拆成页，保存页级图像、尺寸、质量、OCR/OMR 结果。
- `AnswerBlock`：按模板从页图像中切割题块，供教师任务使用。
- 支持图片和 ZIP 图片批次拆分。
- 识别接口支持 `?async=true` 使用 RQ；Redis 不可用时自动同步兜底。
- 新增接口：
  - `GET/PUT /exams/{id}/template/`
  - `GET /scan-batches/{id}/pages/`
  - `GET /answer-blocks/`

当前 OCR/OMR 使用可替换适配器占位实现，下一步接入真实 OCR/OMR 引擎和 OpenCV 模板定位。

## 第四至第六阶段核心接口

- `PATCH /assignments/{id}/draft/`：保存评分草稿。
- `POST /assignments/{id}/lease/`：续租评卷任务。
- `POST /exams/{id}/snapshots/`：生成成绩快照。
- `GET /exams/{id}/snapshots/`：查询成绩快照。
- `POST /exams/{id}/release/`：申请成绩发布。
- `GET /release-approvals/`：管理员查看发布审批。
- `POST /release-approvals/{id}/decide/`：审批或驳回发布。
- `POST /release-approvals/{id}/publish/`：发布成绩并关闭考试。
- `GET /quality-reviews/`：管理员查看质检任务。
- `POST /quality-reviews/{id}/review/`：完成质检。
- `GET /metrics/`：管理员查看扫描、评卷、仲裁、质检和成绩发布指标。
- `GET /exams/{id}/scores/export/`：管理员导出已发布成绩 CSV；未发布成绩不会导出。
- `GET /exams/{id}/scores/?candidate_no=...`：考试创建者或管理员查询已发布成绩，可按考号筛选。
- `POST /release-approvals/{id}/revoke/`：管理员撤回已发布成绩，快照恢复为锁定状态并停止导出。
- `GET /teacher-profiles/`、`PATCH /teacher-profiles/{id}/`：管理员查看和更新教师科目、题号范围、并发上限及启用状态。
- `GET /audit-logs/?action=...`：管理员查看最近 100 条评卷审计日志，可按操作类型筛选。
- `GET /recognition-jobs/failed/`、`POST /scan-batches/{id}/recognize/retry/`：管理员查看失败识别任务并触发受最大重试次数保护的重试。
- `GET/POST /exams/{id}/candidates/`：维护考试考生名册，考生通过唯一考号和条码绑定答题卡。
- `POST /exams/{id}/candidates/import/`：批量导入 JSON `candidates` 数组或 UTF-8 CSV（字段：`candidate_no,barcode,name`）。

扫描识别结果包含条码识别字段；当 OpenCV 和 pyzbar 均可用时，系统先尝试 OpenCV QR，再回退到 pyzbar，以覆盖一维码和二维码。未安装识别依赖时会明确返回 `unavailable` 并进入人工复核，不会伪造考生身份。

扫描页会持久化关联到具体答题卡，同一考生的多页扫描可以归并到同一答题卡；题块切割优先使用扫描页自身关联，避免同批不同考生之间串页。

阶段 2 识别参数通过环境变量配置：`GRADING_OCR_LANG`（默认 `eng`）、`GRADING_OCR_MIN_CONFIDENCE`（默认 `0.85`）、`GRADING_OMR_MIN_MARK_RATIO`（默认 `0.1`）和 `GRADING_OMR_MIN_MARGIN`（默认 `0.15`）。低于阈值或选项差值过小的 OCR/OMR 结果会标记为需要人工复核。

真实识别部署清单：

- OCR：Python `pytesseract`、系统 Tesseract，以及对应语言包（中文场景至少安装 `chi_sim`）。
- OMR/二维码：`opencv-python-headless` 和 `numpy`。
- 一维码/兼容二维码：`pyzbar` 及系统 `libzbar`。
- PDF：`pymupdf`。

当前项目依赖已固定 `numpy==2.5.5`、`opencv-python-headless==5.0.0.93`、`pytesseract==0.3.13`、`PyMuPDF==2.1` 和 `pyzbar==0.1.9`；系统仍需安装 Tesseract 中文语言包和 `libzbar`。

当前验证环境已安装 Tesseract 5.3.4、`pytesseract==0.3.13` 和 `chi_sim`，已用打印文本样本验证识别出 `CANDIDATE 12345`；该样本置信度为 `0.81`，按默认 `0.85` 门禁仍会进入人工复核，符合安全策略。

当前环境同时已验证 pyzbar 读取 `PYZBAR-CHECK` 二维码，以及 PyMuPDF 将一页 PDF 渲染为识别页。

模板 `alignment_markers` 可配置四个按左上、右上、右下、左下顺序排列的定位点（支持 `{"x": ..., "y": ...}` 或 `[x, y]`），识别时使用 OpenCV 透视变换到 `page_width/page_height`；定位点不完整或引擎不可用时保留 EXIF 校正后的原图并标记为 fallback。

扫描页会持久化 `barcode_result` 和 `alignment_result`，运营或人工复核接口可直接查看条码、校正状态、引擎和置信度，不依赖批次任务结果快照。

安装前必须用考试扫描样本验证识别准确率、置信度阈值和模板坐标；未完成样本验收前只能使用人工复核模式。

分发任务时会校验教师画像：科目非空时必须匹配考试科目，题号范围非空时必须包含目标题号；没有符合条件或可用容量不足会明确返回错误。

成绩发布申请、审批、发布和撤回都会写入 `GradingAuditLog`，记录操作人、对象和业务备注。

前端管理入口为 `/grading/operations`，教师入口为 `/grading/workbench`。运营入口只显示给管理员可用的后端数据，非管理员访问 API 会返回 403。

扫描批次支持单页图片、ZIP 图片包和多页 TIFF；PDF 扫描需要在部署环境安装 `pymupdf`（导入名 `fitz`），否则任务会以明确错误失败，不会伪造识别结果。

## 运维命令

```bash
python manage.py reclaim_grading_assignments --timeout-minutes 30
python manage.py retry_recognition --limit 100
python manage.py retry_recognition --batch-id 123
```

建议使用 cron、RQ Scheduler 或容器定时任务周期执行回收和失败重试。
