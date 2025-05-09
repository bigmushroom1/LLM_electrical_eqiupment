from ollama import chat
from py2neo import Graph
from sentence_transformers import SentenceTransformer
import numpy as np
from openai import OpenAI

client = OpenAI(
    api_key="",
    base_url="https://api.deepseek.com"
)

def call_deepseek_chat(messages, model="deepseek-chat"):
    response = client.chat.completions.create(
        model=model,
        messages=messages,
        temperature=0.7,
    )
    return response.choices[0].message.content.strip()

graph = Graph('http://localhost:7474', auth=('', ''), name='')

triples = graph.run(
    "MATCH (n)-[r]->(m) RETURN n.name AS subj, type(r) AS rel, m.name AS obj"
).data()
docs = [f"{t['subj']} {t['rel']} {t['obj']}" for t in triples]

embed_model = SentenceTransformer("./data/all-MiniLM-L6-v2")
embeddings = embed_model.encode(docs, convert_to_numpy=True)

emb_norms = np.linalg.norm(embeddings, axis=1, keepdims=True)

def retrieve_context(question: str, k: int = 5) -> str:

    # 4.1 计算问题 embedding
    q_emb = embed_model.encode([question], convert_to_numpy=True)  # (1, D)
    q_norm = np.linalg.norm(q_emb, axis=1, keepdims=True)         # (1, 1)
    # 4.2 计算余弦相似度： (embeddings · q_emb.T) / (||emb|| * ||q||)
    sims = (embeddings @ q_emb.T).squeeze() / (emb_norms.squeeze() * q_norm.squeeze())
    # 4.3 取 top-k 最大相似度索引
    topk_idx = np.argpartition(-sims, k-1)[:k]
    # 4.4 按相似度排序并返回对应 docs
    topk_sorted = topk_idx[np.argsort(-sims[topk_idx])]
    return "\n".join(docs[i] for i in topk_sorted)

def main():
    history = []
    print("DeepSeekR1 知识问答——输入 exit 或 quit 退出。\n")

    while True:
        question = input("请输入你的问题：").strip()
        if question.lower() in ("exit", "quit"):
            print("已退出。")
            break

        context = retrieve_context(question, k=5)
        system_msg = {
            "role": "system",
            "content": f"以下是与你的问题最相关的知识：\n{context}"
        }

        messages = [system_msg] + history + [{"role": "user", "content": question}]
        answer = call_deepseek_chat(messages, model="deepseek-chat")

        print("\n" + answer + "\n" + "-" * 50 + "\n")
        history.append({"role": "user",    "content": question})
        history.append({"role": "assistant","content": answer})

if __name__ == "__main__":
    main()
