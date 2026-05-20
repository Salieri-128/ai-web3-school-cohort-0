# RAG 可视化教学 Demo

这是一个用于教学的 RAG（Retrieval-Augmented Generation，检索增强生成）可视化 Demo。

它不是商业产品，也没有使用 LangChain、Pinecone、ChromaDB、Redis 等复杂框架。项目目标是让初学者看清楚最底层的 RAG 流程：

1. 用户输入问题
2. 本地知识库切分成 chunk
3. 使用 sentence-transformers 生成 embedding
4. 使用 numpy 计算 cosine similarity
5. 选出 top-k 相似 chunk
6. 组装最终 prompt
7. 调用 LLM 或使用 mock answer 生成回答

## 项目结构

```text
ai-interaction/
├── app.py
├── requirements.txt
├── README.md
└── sample_knowledge_base/
    ├── reentrancy.txt
    ├── dao.txt
    └── rag.txt
```

## 如何安装

建议使用 Python 3.10 或更高版本。

```bash
cd demo/ai-interaction
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

第一次运行时，`sentence-transformers` 会下载 embedding 模型，可能需要一点时间。

## 如何运行

```bash
streamlit run app.py
```

运行后，浏览器会打开 Streamlit 页面。你可以输入例如：

- 什么是重入攻击？
- 什么是 DAO？
- 什么是 RAG？

## API Key 设置

如果没有设置 API Key，项目会自动进入 mock answer 模式，直接基于检索到的 chunk 拼接一个回答，方便离线教学。

如果你使用 OpenAI 官方 API，可以设置：

```bash
export OPENAI_API_KEY="你的 API Key"
streamlit run app.py
```

如果你使用 OpenAI-compatible 的第三方大模型平台，可以设置：

```bash
export API_KEY="你的 API Key"
export BASE_URL="https://llmapi.paratera.com/v1"
streamlit run app.py
```

如果平台文档给出的地址已经包含 `/v1`，就照文档填写；如果文档只给到域名，例如 `https://llmapi.paratera.com`，但运行时报 `404` 或 `Not Found`，通常需要尝试在末尾加上 `/v1`。

程序会按顺序读取这些环境变量：

- API Key：`OPENAI_API_KEY` 或 `API_KEY`
- Base URL：`OPENAI_BASE_URL`、`BASE_URL` 或 `API_URL`

页面侧边栏默认提供这些文本生成模型：

- `Qwen3-235B-A22B-Instruct-2507`
- `Qwen3-Coder-480B-A35B-Instruct`
- `Qwen3-Next-80B-A3B-Thinking`
- `Qwen3-VL-30B-A3B-Instruct`

也保留了 `gpt-4.1-mini` 和 `gpt-5-mini` 选项，方便切回 OpenAI 官方 API。

注意：截图里的 `GLM-Embedding-2`、`GLM-Embedding-3` 是 embedding 模型，不适合用来生成最终文字回答。`GLM-CogView3-Flash`、`Doubao-Seedream-3.0-T2I`、`MiniMax-I2V-01-Live` 更偏图像或视频生成，也不适合本 demo 的 Step 5 文本回答。

项目使用新版 OpenAI Python SDK，但调用的是兼容性更好的 Chat Completions API：

```python
from openai import OpenAI

client = OpenAI(
    api_key="你的 API Key",
    base_url="https://llmapi.paratera.com/v1",
)
response = client.chat.completions.create(
    model="Qwen3-235B-A22B-Instruct-2507",
    messages=[
        {
            "role": "user",
            "content": prompt,
        }
    ],
)
print(response.choices[0].message.content)
```

## RAG 工作原理解释

RAG 的全称是 Retrieval-Augmented Generation，也就是“检索增强生成”。

普通 LLM 回答问题时，主要依赖模型参数中已有的知识。RAG 会先从外部知识库中找资料，再把资料和用户问题一起交给 LLM。

本项目中的 RAG 流程如下：

### Step 1 用户输入

用户输入一个自然语言问题，例如“什么是重入攻击？”。

### Step 2 Chunk 切分

系统读取 `sample_knowledge_base/` 中的 `.txt` 文件，并把长文本切成较小的片段，也就是 chunk。

切 chunk 的原因是：

- embedding 模型更适合处理较短文本
- 检索时可以找到更精确的内容
- prompt 中不用塞入整篇文档

### Step 3 Embedding 检索结果

系统使用 `sentence-transformers/all-MiniLM-L6-v2` 把问题和每个 chunk 都转换成向量。

然后用 cosine similarity 计算问题向量和 chunk 向量之间的相似度。相似度越高，说明 chunk 越可能与问题相关。

### Step 4 最终 Prompt

系统把 top-k 相似 chunk 和用户问题组合成最终 prompt。

这个 prompt 会明确告诉 LLM：

- 只能根据检索到的知识库内容回答
- 如果资料不足，要说明不确定
- 回答要简洁并说明参考了哪些 chunk

### Step 5 AI 回答

如果存在 API Key，系统会调用大模型 API 生成最终回答。

如果没有 key，系统会使用 mock answer 模式，把检索到的 chunk 拼接成一个教学用回答。

## 哪部分由 AI 完成

在设置了 API Key 的情况下，AI 主要完成：

- 阅读最终 prompt
- 根据 retrieved chunks 组织自然语言回答
- 用更易懂的方式解释概念

在没有 API key 的 mock answer 模式下，没有真正调用 LLM。

## 哪部分由人工完成

人工主要完成：

- 准备知识库文件
- 决定 chunk 大小和 overlap
- 选择 top-k 数量
- 检查检索结果是否合理
- 判断最终回答是否准确

RAG 并不是让 AI 自动知道所有事实，而是让人把可靠资料整理好，再让 AI 基于这些资料回答。

## 教学建议

你可以尝试调整侧边栏参数，观察结果变化：

- chunk 太大：检索结果可能包含太多无关内容
- chunk 太小：上下文可能不完整
- overlap 太小：上下文衔接可能断裂
- top-k 太少：资料可能不足
- top-k 太多：prompt 可能变长且混入噪声

这个 Demo 的重点不是做一个强大的聊天机器人，而是帮助你看见 RAG 内部每一步发生了什么。
