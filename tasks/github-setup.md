# GitHub 仓库创建与连接

## 当前状态
- 本地目录已初始化：`~/ai-web3-school-cohort-0`
- 本地 Git 已初始化：`main`
- Git 用户：`Jesse <xjia2304@gmail.com>`
- `gh` 状态：未安装
- 远程 GitHub repo：尚未创建

## 推荐步骤
### 1. 安装 GitHub CLI
```bash
brew install gh
```

### 2. 登录 GitHub
```bash
gh auth login
```
建议选择：
- GitHub.com
- HTTPS
- Login with a web browser

### 3. 验证登录
```bash
gh auth status
```

### 4. 创建远程仓库并自动连接本地目录
在 `~/ai-web3-school-cohort-0` 目录下运行：
```bash
gh repo create ai-web3-school-cohort-0 \
  --public \
  --description "Personal learning journal and proof-of-work for AI x Web3 School" \
  --source . \
  --remote origin \
  --push
```

## 提醒
- 这是 public repo，不要提交敏感信息
- 不要把 GitHub 密码、token、验证码发给 Agent
- commit / push 前先看 `git status --short`
