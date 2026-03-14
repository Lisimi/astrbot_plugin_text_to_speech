import os
import requests
from pathlib import Path
from astrbot.api import logger
from data.plugins.astrbot_plugin_text_to_speech.sovits_tts import SoVITSTTS

class VoiceGenerator:
    def __init__(self, api_url="http://192.168.0.203:9872/", windows_base_url="http://192.168.0.203:9800/"):
        self.tts = SoVITSTTS(api_url=api_url)
        self.windows_base_url = windows_base_url

    def set_models(self, sovits_model, gpt_model):
        try:
            self.tts.set_sovits_model(sovits_model)
            self.tts.set_gpt_model(gpt_model)
        except Exception as e:
            logger.error(f"[VoiceGenerator] 模型加载失败: {e}")
            return False

    def generate_voice(self, ref_audio, prompt_text, text, save_dir):
        try:
            output_file = self.tts.synthesize(ref_audio=ref_audio, prompt_text=prompt_text, text=text)
        except Exception as e:
            logger.error(f"[VoiceGenerator] 语音生成服务器连接失败: {e}")
            return False   # 🚨 关键：连接失败时返回 False

        try:
            # 解析 Windows 路径
            win_path = os.path.basename(output_file).split("file=")[-1]
            parts = win_path.split("\\")
            subdir, filename = parts[-2], parts[-1]

            # 拼接下载链接
            base_url = self.windows_base_url + "TEMP/gradio"
            audio_url = f"{base_url}/{subdir}/{filename}"
            logger.info(f"[VoiceGenerator] 下载链接: {audio_url}")

            os.makedirs(save_dir, exist_ok=True)
            save_path = os.path.join(save_dir, filename)

            if os.path.exists(save_path):
                os.remove(save_path)
                logger.info(f"[VoiceGenerator] 已删除旧文件: {save_path}")

            resp = requests.get(audio_url, stream=True, timeout=5)
            if resp.status_code == 200:
                with open(save_path, "wb") as f:
                    for chunk in resp.iter_content(chunk_size=8192):
                        f.write(chunk)
                logger.info(f"[VoiceGenerator] 语音已保存到: {save_path}")
                return save_path
            else:
                logger.error(f"[VoiceGenerator] 下载失败，状态码: {resp.status_code}")
                return False
        except Exception as e:
            logger.error(f"[VoiceGenerator] 下载失败: {e}")
            return False
