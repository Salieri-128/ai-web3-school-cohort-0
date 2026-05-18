# AI × Web3 School 学习仓库

这是我的 **AI × Web3 School** 公开学习仓库，用来沉淀：
- 学习计划
- 每日打卡草稿
- 任务拆解
- 小实验与 PoW（proof of work）
- Handbook feedback
- Hackathon 项目过程记录

## 相关链接
- Handbook：https://aiweb3.school/zh/handbook/
- Learning Agent Prompt：https://aiweb3.school/learning-agent.zh.txt
- WCB 课程页：https://web3career.build/zh/programs/AI-Web3-School
- WCB Learning 页：https://web3career.build/zh/programs/AI-Web3-School#tab=learning
- WCB Agent API 文档：https://web3career.build/llms.txt

## 仓库目录
- `profile.md`：我的学习画像与目标
- `learning-plan.md`：当前阶段学习计划
- `daily/`：每日学习记录与打卡草稿
- `tasks/`：任务拆解与待办
- `experiments/`：实验、脚本、demo、失败记录
- `handbook-feedback/`：对 Handbook 的问题与建议反馈
- `hackathon/`：Hackathon 方向、想法、原型、里程碑
- `submissions/`：外部提交记录、证明链接、交付快照
- `templates/`：每日笔记、任务笔记、反馈模板

## 隐私与安全提醒
这个仓库默认是 **public**。不要提交以下内容：
- API key / token
- 助记词 / 私钥 / keystore
- 未公开联系方式
- 内部会议链接
- 含个人敏感信息的数据

如果需要接入 WCB Agent API，请把 secret 仅保存在本地环境变量或 Hermes secrets 中，例如：`WCB_AGENT_SECRET_API_KEY`。

## 当前学习策略
因为我的画像是：**AI 基础新手 + Web3 有基础 + 会基础脚本 + 每天 2 小时 + 目标偏开发 / Hackathon**，所以当前策略是：
1. 先补最小 AI 基础闭环（LLM / Prompt / Context / RAG / Agent）
2. 尽快进入 AI × Web3 Bridge（Wallet / Tool Use / Agent Workflow / Security）
3. 保持每天有可公开沉淀的输出，不只看文档

## 提交约定
每次有学习变更时：
1. 更新对应文件
2. 检查 `git status --short`
3. 确认后再 commit / push

推荐提交信息：
- `docs: add day 01 learning notes`
- `docs: update learning plan`
- `feat: add first wallet experiment`
- `docs: add handbook feedback on context section`
