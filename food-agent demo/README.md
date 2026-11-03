# Food Agent

一个以手机为主要使用设备的饮食记录 MVP。用户用自然语言记录饮食，应用会：

- 识别常见食物和大致分量
- 估算热量、蛋白质、碳水、脂肪和膳食纤维
- 将记录保存到 SQLite
- 汇总当天饮食并给出下一餐建议
- Ollama 本地 AI（免费、无需 API Key）
- 可选的 OpenAI Responses API 在线解析

> 本项目只提供一般性饮食信息，不替代医生或注册营养师。涉及疾病、孕期、饮食障碍或严重过敏时，请咨询专业人士。

## 启动

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -e '.[dev]'
streamlit run app.py
```

浏览器打开 `http://127.0.0.1:8501`。项目默认只监听本机地址，不向局域网公开饮食记录。

## 免费本地 AI

安装 Ollama 后下载模型：

```bash
ollama pull qwen3:4b
```

应用会自动连接 `http://localhost:11434`，不需要 API Key。可在 `.env` 中更换模型：

```env
AI_PROVIDER=auto
OLLAMA_MODEL=qwen3:4b
```

模型不可用时，应用会自动退回本地规则解析。

## 可选 OpenAI API

需要使用 OpenAI 在线模型时：

```bash
cp .env.example .env
```

然后在 `.env` 中填写 `OPENAI_API_KEY`。不要把 `.env` 提交到 Git。

## 测试

```bash
pytest
ruff check .
```
