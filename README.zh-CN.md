# video-director

**核心目标模型：Claude Opus 5.5 · 推荐搭配 Claude Code 使用**

[English](README.md) | **简体中文**

**video-director 是一套主要面向 Claude Opus 5.5（Claude Code）的代码视频制作 Skill**：引导模型使用 HTML、Canvas、SVG、Three.js、GSAP 或 Remotion 编写短视频，并逐帧渲染为 MP4。适用于产品发布片、宣传短片、讲解视频、数据故事、动态文字、角色与插画动画、循环动画以及社交媒体短视频。

这个 Skill 将 **Claude Opus 5.5** 视为导演与编程执行者：**用可量化的参数规划影片，以确定性的方式构建，再用检测工具检查不易凭主观观看或听觉判断的问题**。它包含阐明原因的制作原则、每个阶段都有检查关口的工作流，以及两套质量验证脚本。项目刻意没有附带可直接照搬的镜头素材库。

## 项目包含什么？

| 路径 | 内容 |
| --- | --- |
| [`video-director/SKILL.md`](video-director/SKILL.md) | 核心制作立场；每部影片的可调参数（时间基准、连续性、视觉风格、文字策略）；13 项原则；构建规范；需求简报结构和完成标准 |
| [`video-director/references/`](video-director/references/) | 制作模板（创意方案、时间轴、事实核对、交付报告）、实用制作参数、声音设计、QA 检查目录和评审评分标准 |
| [`video-director/scripts/`](video-director/scripts/) | `check_timeline.py` 在开始编写代码前检查时间轴方案；`qa_video.py` 检查渲染结果，包括开场文字的尺寸与对比度、首帧、闪烁、剪辑点、画面冻结、循环接缝、响度、静音片段和关键帧拼图 |
| [`video-director/evals/`](video-director/evals/) | 三组测试任务及其评分器 |
| [`METHODOLOGY.md`](METHODOLOGY.md) | 这套 Skill 的方法论研究：分析八个公开仓库，总结影响视频质量的关键因素 |

## 推荐模型：Claude Opus 5.5

**首选组合：Claude Code + Claude Opus 5.5。** 用户只需描述影片需求，Skill 即引导 Opus 5.5 逐步完成分镜规划、动画代码编写、逐帧渲染、质量检查和局部修复。具备相应代码执行能力的其他编程 Agent 也可以参考这套工作流，但**本项目重点面向 Claude Opus 5.5**。

这是一套指导编程模型制作和检查视频的 Skill，不附带模型服务或托管式视频生成接口。实际成片仍依赖运行环境中的开发、渲染和验证工具。

## 安装

在 Claude Code 中选择 **Claude Opus 5.5**，再把 Skill 文件夹复制到个人 Skill 目录，也可以复制到项目的 `.claude/skills/` 目录：

```bash
git clone https://github.com/win4r/video-director.git
```

```bash
cp -R video-director/video-director ~/.claude/skills/
```

在 Claude 应用中，可以将仓库内层的 `video-director/` 文件夹打包成 ZIP，然后作为自定义 Skill 上传。

**运行依赖：** QA 脚本需要 `ffmpeg` / `ffprobe`，以及安装了 `numpy`、`Pillow` 的 Python 3。使用 HTML 制作并渲染视频时，还需要 Node.js、Playwright 和 Chromium（也可以使用 Remotion）。`faster-whisper` 为可选依赖，用于检查旁白；配音可使用任意文字转语音（TTS）工具。

## 如何使用

在 Claude Code 中使用 **Claude Opus 5.5** 时，直接用自然语言描述想要的视频即可。即使只有一句简单需求，也可以触发这套制作工作流，例如：

- “为我们的 CLI 制作一段 15 秒的循环产品发布视频。所需信息都在 README 里。”
- “制作一段约 30 秒、16:9、带旁白的视频，讲解布隆过滤器（Bloom filter）的工作原理。”
- “根据 `subscribers.csv`，为我们的公开账号制作一段 20 秒的短视频（Reel），如实呈现数据。”

它还支持**审查和修复已有的代码动画**，例如“这段节奏太慢了”或“文字看不清楚”。

也可以手动运行检查脚本：

**1. 开始编写动画代码前，检查时间轴：**

```bash
python3 video-director/scripts/check_timeline.py timeline.json
```

**2. 视频渲染完成后，执行 QA：**

```bash
python3 video-director/scripts/qa_video.py film.mp4 --out qa/ --beats timeline.json
```

## 评测结果

每一轮都让三个测试任务在各个配置下分别执行一次。可以自动测量的断言由脚本检查；其余表现由不知道各影片来自哪个配置的盲测评审打分，并选出他们更愿意发布的视频。

| 轮次 | 对比对象 | 通过的断言 | 盲测偏好 | 成本 |
| --- | --- | --- | --- | --- |
| 第 1 轮 | 使用 Skill vs 不使用 Skill | 28/28 vs 25/28 | 2:1 偏好使用 Skill | 时间和 Token 消耗约为 2 倍 |
| 第 2 轮 | 当前版本 vs 第 1 轮版本 | 30/32 vs 26/32 | 3:0 偏好当前版本 | 两者大致相同 |

**第 1 轮**显示，Skill 能更好地发现制作基础问题，例如视频首帧为黑色、文字被 Reels 的说明区域遮挡、音量过低。但它仍暴露出两个不足：一条宣传标语直到第 11 秒才出现；一段讲解视频始终没有明确说出“false positive”（假阳性）。

**第 2 轮**针对这些问题加入了新规则：即使关闭声音，视频开头的吸引注意力内容（Hook）及行动号召（CTA，如有）也必须在前 3 秒内出现，并确保文字尺寸与对比度符合可测量的要求；观众可能搜索的关键术语既要被说出来，也要出现在画面中；数字还在变化时，不要让标签压在数字上。

**评测限制：** 每个配置只运行一次，因此这些结果只能作为趋势参考，不能当作具有充分重复验证的性能结论。角色动画、插画动画、局部修复和实时网页相关的规则是在第 2 轮之后加入的，**尚未接受上述评测**。这些结果也不能作为 Claude Opus 5.5 与其他模型之间的独立对照测试。

## 许可证

[MIT](LICENSE)
