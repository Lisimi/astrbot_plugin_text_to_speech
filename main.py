import asyncio
import os
from pathlib import Path
from astrbot.api.event import AstrMessageEvent
from astrbot.api.star import Context, Star, register
from astrbot.api import logger
import astrbot.api.message_components as Comp
from astrbot.core.star.register import register_on_decorating_result as on_decorating_result
from astrbot.core.star.register import register_command as command
from data.plugins.astrbot_plugin_text_to_speech.voice_generator import SoVITSClient

import re

@register(
    "voice-generator-plugin",
    "Lisimi",
    "支持 GPT-SoVITS 的文字转语音插件",
    "1.0.0"
)
class VoiceGeneratorStar(Star):
    def __init__(self, context: Context, config: dict):
        """
        初始化语音生成插件
        
        Args:
            context: AstrBot 上下文
            config: 插件配置字典
        """
        super().__init__(context)
        self.config = config
        
        self.sovits_model = config.get("sovits_model", "SoVITS_weights/qingyi_e8_s104.pth")
        self.gpt_model = config.get("gpt_model", "GPT_weights/qingyi-e15.ckpt")
        self.max_text_length = config.get("max_text_length", 80)
        self.min_text_length = config.get("min_text_length", 10)
        self.ref_audio = config.get("ref_audio", "ref_audio/Qingyi.wav_0001504320_0001702080.wav")
        self.prompt_text = config.get("prompt_text", "嗯。如果不是因为店长深谙电影知识，我可能会错过这个细节也未可知。")
        self.base_url = config.get("base_url", "http://192.168.0.105:9880")
        
        self.clean_patterns = config.get(
            "clean_patterns", 
            [r"\(.*?\)",
            r"\[.*?\]",
            r"\<.*?\>",
            r"\*.*?\*",
        ])
        
        self.client = SoVITSClient(base_url=self.base_url)
        
        if not self.client.available:
            logger.error("[VoiceGeneratorStar] 语音服务器不可用，插件将无法正常工作")
        else:
            if self.sovits_model:
                result = self.client.set_sovits_model(self.sovits_model)
                if result is False:
                    logger.error("[VoiceGeneratorStar] SoVITS 模型加载失败")
            if self.gpt_model:
                result = self.client.set_gpt_model(self.gpt_model)
                if result is False:
                    logger.error("[VoiceGeneratorStar] GPT 模型加载失败")


    def _clean_text(self, text: str) -> str:
        """
        清理文本中的特殊标记
        
        Args:
            text: 原始文本
            
        Returns:
            str: 清理后的文本
        """
        for pattern in self.clean_patterns:
            text = re.sub(pattern, "", text)
        return text.strip()

    async def _generate_audio(self, text: str, save_dir: str) -> str:
        """
        生成语音文件
        
        Args:
            text: 要转换的文本
            save_dir: 保存目录
            
        Returns:
            str/bool: 成功返回文件路径，失败返回 False
        """
        os.makedirs(save_dir, exist_ok=True)
        output_path = os.path.join(save_dir, "audio.wav")
        
        return self.client.tts(
            text=text,
            text_lang="zh",
            ref_audio_path=self.ref_audio,
            prompt_text=self.prompt_text,
            prompt_lang="zh",
            output_file=output_path
        )

    @on_decorating_result()
    async def on_decorating_result(self, event: AstrMessageEvent):
        """
        监听消息结果事件，自动将文本转换为语音
        
        Args:
            event: AstrBot 消息事件
        """
        result = event.get_result()
        
        if not result or not result.chain:
            return
            
        platform_id = event.session.platform_id
        session_id = event.get_session_id()
        save_dir = str(Path(__file__).parent / "outputVideo" / platform_id / session_id)
        logger.info(f"[VoiceGeneratorStar] 语音保存目录: {save_dir}")

        if not self.client.available:
            logger.warning("[VoiceGeneratorStar] 语音服务器不可用，跳过语音生成")
            return

        full_text = " ".join([comp.text for comp in result.chain if isinstance(comp, Comp.Plain)]).strip()
        if not full_text:
            return
        full_text = self._clean_text(full_text)
        
        if len(full_text) < self.min_text_length or len(full_text) > self.max_text_length:
            return
            
        try:
            audio_path = await self._generate_audio(full_text, save_dir)
            if audio_path is False:
                logger.error("[VoiceGeneratorStar] 语音生成失败，服务器不可用")
                return
            result.chain = [comp for comp in result.chain if not isinstance(comp, Comp.Plain)]
            result.chain.insert(0, Comp.Record(file=save_dir + "/audio.wav", url=save_dir + "/audio.wav"))
            logger.info(f"[VoiceGeneratorStar] 成功生成语音: {audio_path}")
        except Exception as e:
            logger.error(f"[VoiceGeneratorStar] 插件处理失败: {e}")

    @command(command_name="voicegen-test", description="测试语音生成")
    async def test_cmd(self, event: AstrMessageEvent, text: str = ""):
        """
        测试语音生成命令
        
        Args:
            event: AstrBot 消息事件
            text: 要转换的测试文本
        """
        if not text.strip():
            yield event.plain_result("用法: voicegen-test <文本>")
            return
            
        if not self.client.available:
            yield event.plain_result("❌ 语音服务器不可用")
            return
            
        try:
            save_dir = str(Path(__file__).parent / "outputVideo" / event.session.platform_id / event.get_session_id())
            path = await self._generate_audio(text, save_dir)

            if path is False:
                yield event.plain_result("❌ 语音生成失败")
                return
                
            yield event.chain_result([Comp.Record(file=path, url=path)])
        except Exception as e:
            yield event.plain_result(f"❌ {e}")
