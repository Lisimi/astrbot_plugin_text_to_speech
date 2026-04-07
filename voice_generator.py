import os
import requests
from astrbot.api import logger


class SoVITSClient:
    """SoVITS API 客户端，用于与 GPT-SoVITS 服务端交互"""
    
    def __init__(self, base_url="http://127.0.0.1:9880"):
        """
        初始化客户端
        
        Args:
            base_url: SoVITS API 服务地址，默认为本地地址
        """
        self.base_url = base_url
        self.available = self._check_connection()

    def _check_connection(self) -> bool:
        """
        检查服务器是否可用
        
        Returns:
            bool: 服务器可用返回 True，否则返回 False
        """
        try:
            resp = requests.get(f"{self.base_url}/", timeout=3)
            logger.info(f"[SoVITSClient] 成功连接到语音服务器: {self.base_url}")
            return True
        except Exception as e:
            logger.error(f"[SoVITSClient] 无法连接语音服务器: {e}")
            return False

    def set_sovits_model(self, sovits_path: str):
        """
        切换 SoVITS 模型
        
        Args:
            sovits_path: SoVITS 模型权重文件路径
            
        Returns:
            dict/bool: 成功返回响应 JSON，失败返回 False
        """
        try:
            resp = requests.get(
                f"{self.base_url}/set_sovits_weights",
                params={"weights_path": sovits_path},
                timeout=10
            )
            result = resp.json()
            logger.info(f"[SoVITSClient] SoVITS 模型切换成功: {sovits_path}")
            return result
        except Exception as e:
            logger.error(f"[SoVITSClient] SoVITS 模型切换失败: {e}")
            return False

    def set_gpt_model(self, gpt_path: str):
        """
        切换 GPT 模型
        
        Args:
            gpt_path: GPT 模型权重文件路径
            
        Returns:
            dict/bool: 成功返回响应 JSON，失败返回 False
        """
        try:
            resp = requests.get(
                f"{self.base_url}/set_gpt_weights",
                params={"weights_path": gpt_path},
                timeout=10
            )
            result = resp.json()
            logger.info(f"[SoVITSClient] GPT 模型切换成功: {gpt_path}")
            return result
        except Exception as e:
            logger.error(f"[SoVITSClient] GPT 模型切换失败: {e}")
            return False

    def tts(
        self,
        text: str,
        text_lang: str,
        ref_audio_path: str,
        prompt_text: str,
        prompt_lang: str,
        output_file: str = "output.wav",
        media_type: str = "wav",
        text_split_method: str = "cut4",
        batch_size: int = 1,
        top_k: int = 15,
        top_p: float = 1.0,
        temperature: float = 1.0,
        ref_free: bool = False,
        speed: float = 1.0,
        if_freeze: bool = False,
        sample_steps: int = 32,
        if_sr: bool = False,
        pause_second: float = 0.3
    ) -> str:
        """
        文本转语音并保存到文件
        
        Args:
            text: 要转换的文本
            text_lang: 文本语言 (zh/en/ja等)
            ref_audio_path: 参考音频路径
            prompt_text: 参考音频对应的文本
            prompt_lang: 提示文本语言
            output_file: 输出文件路径
            media_type: 输出媒体类型 (wav/mp3等)
            text_split_method: 文本切分方法
            batch_size: 批处理大小
            top_k: top_k 采样参数
            top_p: top_p 采样参数
            temperature: 温度参数
            ref_free: 是否不使用参考音频
            speed: 语速
            if_freeze: 是否冻结
            sample_steps: 采样步数
            if_sr: 是否超分辨率
            pause_second: 句间停顿秒数
            
        Returns:
            str/bool: 成功返回输出文件路径，失败返回 False
        """
        if not self.available:
            logger.error("[SoVITSClient] 服务器不可用，无法生成语音")
            return False
            
        payload = {
            "text": text,
            "text_lang": text_lang,
            "ref_audio_path": ref_audio_path,
            "prompt_lang": prompt_lang,
            "prompt_text": prompt_text,
            "media_type": media_type,
            "text_split_method": text_split_method,
            "batch_size": batch_size,
            "top_k": top_k,
            "top_p": top_p,
            "temperature": temperature,
            "ref_free": ref_free,
            "speed": speed,
            "if_freeze": if_freeze,
            "sample_steps": sample_steps,
            "if_sr": if_sr,
            "pause_second": pause_second
        }
        
        try:
            resp = requests.post(
                f"{self.base_url}/tts",
                json=payload,
                timeout=120
            )
            
            if resp.status_code != 200:
                logger.error(f"[SoVITSClient] TTS 请求失败，状态码: {resp.status_code}")
                return False
                
            os.makedirs(os.path.dirname(output_file), exist_ok=True)
            with open(output_file, "wb") as f:
                f.write(resp.content)
            logger.info(f"[SoVITSClient] 语音已保存到: {output_file}")
            return output_file
            
        except requests.exceptions.Timeout:
            logger.error("[SoVITSClient] TTS 请求超时")
            return False
        except Exception as e:
            logger.error(f"[SoVITSClient] 语音生成失败: {e}")
            return False
