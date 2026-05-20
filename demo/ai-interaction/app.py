import os
from pathlib import Path

import numpy as np
import streamlit as st
from sentence_transformers import SentenceTransformer


# -----------------------------
# Basic project configuration
# -----------------------------

BASE_DIR = Path(__file__).parent
KNOWLEDGE_BASE_DIR = BASE_DIR / "sample_knowledge_base"

DEFAULT_MODEL_NAME = "Qwen3-235B-A22B-Instruct-2507"
EMBEDDING_MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"
LLM_MODEL_OPTIONS = [
    "Qwen3-235B-A22B-Instruct-2507",
    "Qwen3-Coder-480B-A35B-Instruct",
    "Qwen3-Next-80B-A3B-Thinking",
    "Qwen3-VL-30B-A3B-Instruct",
    "gpt-4.1-mini",
    "gpt-5-mini",
]


# -----------------------------
# Knowledge base loading
# -----------------------------

def load_knowledge_base(folder_path: Path) -> list[dict]:
    """Read all .txt and .md files from the local knowledge base folder."""
    documents = []

    for file_path in sorted(folder_path.glob("*")):
        if file_path.suffix.lower() not in [".txt", ".md"]:
            continue

        text = file_path.read_text(encoding="utf-8").strip()
        if text:
            documents.append(
                {
                    "source": file_path.name,
                    "text": text,
                }
            )

    return documents


def split_text_into_chunks(text: str, chunk_size: int = 350, overlap: int = 80) -> list[str]:
    """
    Split text into overlapping character chunks.

    This simple implementation is intentionally easy to understand:
    - chunk_size controls the maximum length of each chunk
    - overlap keeps a small amount of previous context in the next chunk
    """
    chunks = []
    start = 0
    safe_overlap = min(overlap, chunk_size - 1)

    while start < len(text):
        end = start + chunk_size
        chunk = text[start:end].strip()

        if chunk:
            chunks.append(chunk)

        start = end - safe_overlap

        # Safety guard: avoid an infinite loop if unusual values are passed in.
        if start < 0 or start >= len(text):
            break

    return chunks


def build_chunks(documents: list[dict], chunk_size: int, overlap: int) -> list[dict]:
    """Turn all documents into searchable chunks with source metadata."""
    all_chunks = []

    for document in documents:
        chunks = split_text_into_chunks(
            text=document["text"],
            chunk_size=chunk_size,
            overlap=overlap,
        )

        for index, chunk_text in enumerate(chunks, start=1):
            all_chunks.append(
                {
                    "chunk_id": f"{document['source']}#{index}",
                    "source": document["source"],
                    "chunk_index": index,
                    "text": chunk_text,
                }
            )

    return all_chunks


# -----------------------------
# Embedding and retrieval
# -----------------------------

@st.cache_resource
def load_embedding_model() -> SentenceTransformer:
    """
    Load the sentence-transformers model once.

    The first run may take a little time because the model needs to be downloaded.
    After that, Streamlit keeps it cached.
    """
    return SentenceTransformer(EMBEDDING_MODEL_NAME)


def normalize_vectors(vectors: np.ndarray) -> np.ndarray:
    """Normalize vectors so dot product becomes cosine similarity."""
    norms = np.linalg.norm(vectors, axis=1, keepdims=True)
    norms[norms == 0] = 1
    return vectors / norms


def retrieve_top_k_chunks(
    question: str,
    chunks: list[dict],
    embedding_model: SentenceTransformer,
    top_k: int,
) -> tuple[list[dict], np.ndarray, np.ndarray]:
    """
    Convert the question and chunks into embeddings, then rank chunks by similarity.

    Returns:
    - top ranked chunk records
    - question embedding
    - all chunk embeddings
    """
    chunk_texts = [chunk["text"] for chunk in chunks]

    question_embedding = embedding_model.encode([question], convert_to_numpy=True)
    chunk_embeddings = embedding_model.encode(chunk_texts, convert_to_numpy=True)

    normalized_question = normalize_vectors(question_embedding)
    normalized_chunks = normalize_vectors(chunk_embeddings)

    similarities = normalized_chunks @ normalized_question[0]
    ranked_indices = np.argsort(similarities)[::-1][:top_k]

    retrieved_chunks = []
    for rank, chunk_index in enumerate(ranked_indices, start=1):
        chunk = chunks[int(chunk_index)].copy()
        chunk["rank"] = rank
        chunk["similarity"] = float(similarities[chunk_index])
        retrieved_chunks.append(chunk)

    return retrieved_chunks, question_embedding, chunk_embeddings


# -----------------------------
# Prompt and answer generation
# -----------------------------

def build_final_prompt(question: str, retrieved_chunks: list[dict]) -> str:
    """Create the exact prompt that will be sent to the LLM."""
    context_text = "\n\n".join(
        [
            f"[Chunk {chunk['rank']} | {chunk['chunk_id']} | similarity={chunk['similarity']:.4f}]\n{chunk['text']}"
            for chunk in retrieved_chunks
        ]
    )

    return f"""你是一个负责教学的 AI 助手。
请只根据下面检索到的知识库内容回答用户问题。
如果知识库内容不足以回答，请明确说明“不确定”，不要编造。

【检索到的知识库内容】
{context_text}

【用户问题】
{question}

【回答要求】
1. 用中文回答。
2. 先给出简洁定义。
3. 再用 2-4 个要点解释。
4. 最后说明答案主要参考了哪些 chunk。
"""


def build_mock_answer(question: str, retrieved_chunks: list[dict]) -> str:
    """
    Create a local mock answer when no API key is available.

    This is not a real LLM answer. It simply stitches together retrieved chunks so
    students can still see how retrieval helps generation.
    """
    sources = ", ".join([chunk["chunk_id"] for chunk in retrieved_chunks])
    context_preview = "\n\n".join(
        [f"- {chunk['text']}" for chunk in retrieved_chunks]
    )

    return f"""当前没有检测到 API Key，因此进入 mock answer 模式。

用户问题：{question}

根据检索到的相关 chunk，可以整理出以下参考回答：

{context_preview}

参考 chunk：{sources}
"""


def get_llm_api_key() -> str | None:
    """Support both OpenAI-style and third-party platform environment names."""
    return os.getenv("OPENAI_API_KEY") or os.getenv("API_KEY")


def get_llm_base_url() -> str | None:
    """Read an OpenAI-compatible API base URL if the platform provides one."""
    return (
        os.getenv("OPENAI_BASE_URL")
        or os.getenv("BASE_URL")
        or os.getenv("API_URL")
    )


def call_openai_api(prompt: str, model_name: str) -> str:
    """
    Call an OpenAI-compatible Chat Completions API.

    Many third-party model platforms support OpenAI-compatible
    /chat/completions, but do not support OpenAI's newer Responses API.
    Chat Completions is therefore the safer interface for this teaching demo.

    Supported environment variables:
    - OPENAI_API_KEY or API_KEY
    - OPENAI_BASE_URL or BASE_URL or API_URL
    """
    from openai import OpenAI

    api_key = get_llm_api_key()
    base_url = get_llm_base_url()

    client = OpenAI(
        api_key=api_key,
        base_url=base_url,
    )
    response = client.chat.completions.create(
        model=model_name,
        messages=[
            {
                "role": "user",
                "content": prompt,
            }
        ],
        temperature=0.2,
    )

    return response.choices[0].message.content or ""


# -----------------------------
# Streamlit UI
# -----------------------------

st.set_page_config(
    page_title="RAG 可视化教学 Demo",
    page_icon="🧠",
    layout="wide",
)

st.title("RAG 可视化教学 Demo")
st.caption("用最少框架展示 Retrieval-Augmented Generation 的核心流程")

with st.sidebar:
    st.header("参数设置")

    chunk_size = st.slider(
        "Chunk 大小",
        min_value=150,
        max_value=800,
        value=350,
        step=50,
    )

    chunk_overlap = st.slider(
        "Chunk overlap",
        min_value=0,
        max_value=200,
        value=80,
        step=20,
    )

    top_k = st.slider(
        "Top-k 检索数量",
        min_value=1,
        max_value=5,
        value=3,
        step=1,
    )

    model_name = st.selectbox(
        "LLM 模型",
        options=LLM_MODEL_OPTIONS,
        index=LLM_MODEL_OPTIONS.index(DEFAULT_MODEL_NAME),
    )

    custom_model_name = st.text_input(
        "自定义模型名（可选）",
        value="",
        placeholder="例如：Qwen3-235B-A22B-Instruct-2507",
    ).strip()
    if custom_model_name:
        model_name = custom_model_name

    api_key = get_llm_api_key()
    base_url = get_llm_base_url()
    has_api_key = bool(api_key)

    if has_api_key:
        st.info(f"已检测到 API Key。Base URL：{base_url or 'OpenAI 官方默认地址'}")
    else:
        st.info("未检测到 API Key，将使用 mock answer。")


documents = load_knowledge_base(KNOWLEDGE_BASE_DIR)
chunks = build_chunks(documents, chunk_size=chunk_size, overlap=chunk_overlap)

if not documents:
    st.error("没有找到知识库文件。请检查 sample_knowledge_base 文件夹。")
    st.stop()

if not chunks:
    st.error("知识库文件存在，但没有成功切出 chunk。")
    st.stop()


st.subheader("Step 1 用户输入")

example_questions = [
    "什么是重入攻击？",
    "什么是 DAO？",
    "什么是 RAG？",
]

selected_example = st.selectbox("选择一个示例问题", example_questions)
question = st.text_input("也可以输入自己的问题", value=selected_example)

run_button = st.button("运行 RAG 流程", type="primary")


if run_button:
    st.divider()

    st.subheader("Step 2 Chunk 切分")
    st.write(f"当前知识库共读取 `{len(documents)}` 个文件，切分出 `{len(chunks)}` 个 chunk。")

    with st.expander("查看所有 chunk", expanded=True):
        for chunk in chunks:
            st.markdown(f"**{chunk['chunk_id']}**")
            st.code(chunk["text"], language="markdown")

    st.divider()

    st.subheader("Step 3 Embedding 检索结果")

    with st.spinner("正在加载 embedding 模型并计算相似度..."):
        embedding_model = load_embedding_model()
        retrieved_chunks, question_embedding, chunk_embeddings = retrieve_top_k_chunks(
            question=question,
            chunks=chunks,
            embedding_model=embedding_model,
            top_k=top_k,
        )

    st.write(
        f"问题 embedding 维度：`{question_embedding.shape[1]}`；"
        f"chunk embedding 数量：`{chunk_embeddings.shape[0]}`。"
    )

    for chunk in retrieved_chunks:
        st.markdown(
            f"**Top {chunk['rank']} | 相似度：`{chunk['similarity']:.4f}` | 来源：`{chunk['chunk_id']}`**"
        )
        st.code(chunk["text"], language="markdown")

    st.divider()

    st.subheader("Step 4 最终 Prompt")

    final_prompt = build_final_prompt(question, retrieved_chunks)
    st.code(final_prompt, language="markdown")

    st.divider()

    st.subheader("Step 5 AI 回答")

    if has_api_key:
        with st.spinner(f"正在调用 OpenAI API：{model_name} ..."):
            try:
                answer = call_openai_api(final_prompt, model_name)
                st.success("OpenAI API 调用成功")
            except Exception as error:
                answer = (
                    "OpenAI API 调用失败，已自动切换到 mock answer 模式。\n\n"
                    f"错误信息：{error}\n\n"
                    + build_mock_answer(question, retrieved_chunks)
                )
                st.warning("OpenAI API 调用失败")
    else:
        answer = build_mock_answer(question, retrieved_chunks)

    st.markdown(answer)
else:
    st.info("点击“运行 RAG 流程”后，会依次展示 chunk、embedding 检索、prompt 和回答。")
