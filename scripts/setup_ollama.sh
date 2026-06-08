#!/usr/bin/env bash
# macOS / Linux：安装并启动 Ollama，拉取 admin_config 中配置的 LLM 模型
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

MODEL="${TCM_LLM_MODEL:-deepseek-r1:1.5b}"

if ! command -v ollama >/dev/null 2>&1; then
  echo "→ 未检测到 ollama，尝试 Homebrew 安装..."
  if command -v brew >/dev/null 2>&1; then
    brew install ollama
  else
    echo "请手动安装: https://ollama.com/download"
    exit 1
  fi
fi

echo "→ 启动 Ollama 服务（若已在运行会跳过）..."
if ! curl -sf http://127.0.0.1:11434/api/tags >/dev/null 2>&1; then
  nohup ollama serve >/tmp/ollama-serve.log 2>&1 &
  sleep 2
fi

if python3 -c "import json; c=json.load(open('data/admin_config.json')); print(c.get('llm',{}).get('model',''))" 2>/dev/null | grep -q .; then
  MODEL="$(python3 -c "import json; print(json.load(open('data/admin_config.json')).get('llm',{}).get('model','$MODEL'))")"
fi

echo "→ 拉取模型: $MODEL"
ollama pull "$MODEL"

echo "→ 验证 LLM 连通性"
python3 scripts/setup_llm.py
echo "✓ 完成。请重启 python3 web_server.py 后测试诊断。"
