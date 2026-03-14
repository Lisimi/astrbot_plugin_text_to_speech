# astrbot_plugin_text_to_speech

基于 AstrBot 的文字转语音插件（GPT‑SoVITS + GenieTTS / Gradio）。

本插件会将 AstrBot 生成的文字消息（长度在配置范围内）自动转换为语音并返回给用户，支持在多平台（QQ、Telegram、Discord 等）中使用。

---

## ✅ 主要功能

- 监听 AstrBot 生成的回复文本
- 调用外部 SoVITS + GPT 语音生成服务（通过 Gradio API）生成语音
- 自动将文字组件替换为 `Record` 语音组件并返回
- 提供命令 `voicegen-test <文本>` 供手动测试语音生成

---

## 📦 依赖

- Python 3.8+
- AstrBot (插件框架)
- `gradio_client`
- `requests`

安装依赖：

```bash
pip install -r requirements.txt
```

---

## ⚙️ 配置

插件配置项（在 AstrBot 插件配置处或 `config.yaml` 中填写）：

| 配置项 | 说明 | 默认值 |
| --- | --- | --- |
| `api_host` | 语音生成服务所在机器 IP | `192.168.0.203` |
| `api_port` | 语音生成服务 Gradio 接口端口 | `9872` |
| `windows_http_port` | 语音生成服务静态文件下载端口（Gradio 端口） | `9800` |
| `sovits_model` | SoVITS 模型路径（相对于语音服务的模型目录） | `SoVITS_weights_v3/Qingyi_e2_s46_l32.pth` |
| `gpt_model` | GPT 说话方式模型路径 | `GPT_weights_v3/Qingyi-e10.ckpt` |
| `ref_audio` | 参考音频 URL（用于保持声音一致性） | `http://192.168.0.203:9800/output/slicer_opt/Qingyi.wav_0001504320_0001702080.wav` |
| `prompt_text` | 参考音频对应的文本 | `嗯。如果不是因为店长深谙电影知识，我可能会错过这个细节也未可知。` |
| `min_text_length` | 最小触发语音生成的文本长度 | `10` |
| `max_text_length` | 最大触发语音生成的文本长度 | `80` |

> ✅ 配置项也定义在 `_conf_schema.json` 中，可用于 AstrBot 的可视配置界面。

---

## 🚀 使用说明

### 1. 启动语音生成服务（必需）

该插件依赖一个运行中的 SoVITS/GenieTTS（Gradio）服务。
请确保在 `api_host:api_port` 上可访问，并且该服务可以返回音频文件（通过 `windows_http_port` 访问临时文件）。

示例：
- Gradio 接口（API）：`http://<api_host>:<api_port>/`（用于模型切换 / 生成）
- 静态文件下载：`http://<api_host>:<windows_http_port>/TEMP/gradio/...`

### 2. 安装插件到 AstrBot

将本仓库放入 AstrBot 插件目录，并在 AstrBot 插件配置中启用本插件。

### 3. 测试语音生成

在任何支持的聊天平台中发送：

```
voicegen-test 你好，测试文本。
```

成功时会收到一个音频文件（`audio.wav`）。

---

## 📂 输出文件

生成的音频会保存到：

```
outputVideo/<platform_id>/<session_id>/audio.wav
```

例如：
```
outputVideo/QQ_bot/EFF950C5DA97AD1C682A8C41CBD1DBEC/audio.wav
```

---

## 🛠️ 开发与调试

- 关键代码入口：`main.py`（AstrBot Star）
- 语音调用逻辑：`voice_generator.py` + `sovits_tts.py`

如果出现“语音生成失败”或“下载失败”，请检查：
1. `api_host`/`api_port` 是否可连通
2. `windows_http_port` 是否正确且可以访问到 Gradio 的 `TEMP/gradio` 目录
3. `ref_audio` URL 是否有效

---

## 作者 & 许可证

- 作者：Lisimi
- 许可证：MIT（详见 `LICENSE`）
