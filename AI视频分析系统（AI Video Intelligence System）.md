1. 项目定义
项目名称
AIVIS（AI Video Intelligence System）
2. 项目目标

构建一套：

上传视频 / 输入URL
↓
自动理解视频
↓
自动输出导演级分析报告

的 AI 多模态视频分析系统。

支持：

短视频
微短剧
TikTok
抖音
YouTube
B站
广告片
电影片段
纪录片
Vlog
3. 系统核心能力
3.1 内容理解

分析：

视频主题
选题方向
用户画像
情绪曲线
爆点结构
Hook设计
爽点
反转
CTA
3.2 导演分析

分析：

景别
运镜
构图
灯光
色彩
摄影风格
视觉语言
3.3 剪辑分析

分析：

剪辑频率
节奏变化
卡点
BGM同步
高潮区间
转场类型
3.4 运营分析

分析：

平台适配
标题策略
封面策略
评论情绪
热门标签
用户停留点
掉线点
3.5 AI复刻能力（后期）

生成：

“同结构新视频”
4. 系统总体架构
4.1 高层架构
Frontend
  ↓
API Gateway
  ↓
Task Queue
  ↓
Video Pipeline
  ↓
Multi-Agent Analysis Engine
  ↓
RAG Knowledge System
  ↓
Report Generator
  ↓
Dashboard / Export
5. 技术架构
5.1 前端

推荐：

技术	用途
Next.js	Web App
TailwindCSS	UI
shadcn/ui	组件
Zustand	状态管理
ReactFlow	Agent流程图
Video.js	视频播放器
5.2 后端

推荐：

技术	用途
FastAPI	API
Python	AI核心
Celery	异步任务
Redis	Queue
PostgreSQL	主数据库
MinIO/S3	视频存储
5.3 AI层

推荐：

模型	用途
Whisper Large-v3	ASR
GPT-5	综合分析
Claude	长上下文
Gemini	视频理解
Qwen2.5-VL	中文多模态
CLIP	图像语义
YOLOv11	目标检测
SAM2	视频分割
5.4 视频处理层

推荐：

工具	用途
FFmpeg	视频拆解
OpenCV	镜头分析
PySceneDetect	场景切换
Librosa	音频分析
6. 完整工作流
6.1 输入阶段

支持：

- mp4
- mov
- m3u8
- YouTube URL
- TikTok URL
- 抖音 URL
- B站 URL
6.2 视频预处理
6.2.1 视频拆帧
ffmpeg -i input.mp4 -vf fps=1 frames/frame_%04d.jpg

用途：

镜头识别
OCR
视觉Embedding
6.2.2 音频提取
ffmpeg -i input.mp4 audio.wav
6.2.3 字幕识别

Whisper：

result = whisper.transcribe(audio)

输出：

{
  "start": 12.4,
  "end": 15.8,
  "text": "你知道为什么她离开吗"
}
6.3 Scene Detection

使用：

PySceneDetect

检测：

镜头切换
场景变化
高潮区间

输出：

[
  {
    "start": 0.0,
    "end": 4.3
  }
]
6.4 多模态Embedding
视频向量

使用：

CLIP
VideoMAE
Qwen-VL Embedding

生成：

Frame Embedding
Scene Embedding
Video Embedding

存入：

Milvus / Weaviate / Qdrant
7. Multi-Agent 系统
7.1 Agent总体结构
Orchestrator Agent
 ├── Script Agent
 ├── Director Agent
 ├── Editing Agent
 ├── Emotion Agent
 ├── Marketing Agent
 ├── Visual Agent
 └── Recommendation Agent
8. Script Agent（编剧Agent）

分析：

三幕结构
起承转合
冲突
爽点
Hook
CTA
输入
{
  "subtitle": "...",
  "timeline": "...",
  "emotion_curve": "..."
}
输出
{
  "hook_type": "冲突式开场",
  "story_structure": "三段式",
  "climax_time": 42.1,
  "cta": "关注获取后续"
}
9. Director Agent（导演Agent）

分析：

景别
运镜
镜头时长
光影
色彩
摄影风格
输出
{
  "camera_style": "手持跟拍",
  "avg_shot_duration": 1.2,
  "dominant_colors": ["#FFB800"]
}
10. Editing Agent（剪辑Agent）

分析：

BPM同步
剪辑频率
高潮节奏
转场类型
快慢变化
核心指标
指标	说明
ASL	平均镜头长度
Beat Match	卡点率
Jump Density	高频剪辑
Retention Rhythm	留存节奏
11. Emotion Agent

生成：

用户情绪曲线
输出
[
  {
    "time": 12,
    "emotion": "紧张"
  }
]
12. Marketing Agent

分析：

爆款概率
平台适配
标签
标题结构
评论情绪
输出
{
  "platform": "TikTok",
  "viral_score": 87,
  "target_audience": "18-24女性"
}
13. 导演级分析报告生成
13.1 输出结构
一、视频概览
视频类型：情感短剧
核心主题：背叛与复仇
目标平台：抖音
二、选题分析

分析：

是否热点
用户共鸣
情绪价值
爆点类型
三、剧本分析

分析：

Hook
冲突
反转
爽点
结尾CTA
四、镜头分析

分析：

运镜
景别
机位
光线
色彩
五、剪辑分析

分析：

节奏曲线
高潮区间
BGM同步
镜头长度
六、运营分析

分析：

平台适配
完播率预测
掉线点
评论引导
七、AI建议

生成：

如何提升10%完播率
14. 数据结构设计
14.1 Video表
CREATE TABLE videos (
  id UUID PRIMARY KEY,
  title TEXT,
  duration FLOAT,
  platform TEXT,
  created_at TIMESTAMP
);
14.2 Scene表
CREATE TABLE scenes (
  id UUID PRIMARY KEY,
  video_id UUID,
  start_time FLOAT,
  end_time FLOAT,
  embedding VECTOR
);
14.3 Analysis表
CREATE TABLE analyses (
  id UUID PRIMARY KEY,
  video_id UUID,
  report JSONB
);
15. RAG知识系统
15.1 视频知识库

持续爬取：

TikTok爆款
抖音爆款
Shorts爆款

建立：

视频DNA数据库
15.2 存储内容

包括：

Hook
节奏
色彩
镜头
评论
完播率
标签
16. 视频DNA系统（核心竞争力）

目标：

建立：

视频成功公式

例如：

“3秒冲突”
+
“1.2秒平均镜头”
+
“高频字幕”
=
高留存
17. API设计
17.1 上传视频
POST /api/v1/video/upload
17.2 创建分析任务
POST /api/v1/analyze
17.3 获取分析结果
GET /api/v1/report/{id}
18. LangGraph 工作流
Upload Node
  ↓
Preprocess Node
  ↓
ASR Node
  ↓
Scene Detection Node
  ↓
Embedding Node
  ↓
Agent Analysis Node
  ↓
RAG Compare Node
  ↓
Report Node
19. GPU部署建议
最低配置
RTX 4090 × 1
64GB RAM
推荐配置
A100 × 2
128GB RAM
20. 成本控制
推荐架构
本地模型负责：
Whisper
YOLO
CLIP
Scene Detection
云API负责：
GPT-5
Claude
Gemini
21. 商业化方向
SaaS模式

按：

视频时长
分析深度
Agent数量

收费。

企业版

服务：

MCN
广告公司
品牌方
短剧公司
API平台

开放：

Video Intelligence API
22. 第二阶段（高级能力）
AI复刻

自动生成：

“相同节奏不同内容”
AI导演助手

实时指导：

镜头应该怎么拍
AI爆款预测

预测：

视频火的概率
23. 最终产品形态

不是：

AI剪辑工具

而是：

AI视频理解操作系统

即：

AI understands video