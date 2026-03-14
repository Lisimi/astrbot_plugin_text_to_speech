import asyncio
from pathlib import Path
from astrbot.api.event import AstrMessageEvent
from astrbot.api.star import Context, Star, register
from astrbot.api import logger
import astrbot.api.message_components as Comp
from astrbot.core.star.register import register_on_decorating_result as on_decorating_result
from astrbot.core.star.register import register_command as command
from data.plugins.astrbot_plugin_text_to_speech.voice_generator import VoiceGenerator



@register(
    "voice-generator-plugin",
    "Lisimi",
    "支持 GPT-SoVITS 的文字转语音插件",
    "1.0.0"
)
class VoiceGeneratorStar(Star):
    def __init__(self, context: Context, config: dict):
        super().__init__(context)
        self.config = config
        self.sovits_model = config.get("sovits_model", "SoVITS_weights_v3/Qingyi_e2_s46_l32.pth")
        self.gpt_model = config.get("gpt_model", "GPT_weights_v3/Qingyi-e10.ckpt")
        self.max_text_length = config.get("max_text_length", 80)
        self.min_text_length = config.get("min_text_length", 10)
        self.ref_audio = config.get("ref_audio", "http://192.168.0.203:9800/output/slicer_opt/Qingyi.wav_0001504320_0001702080.wav")
        self.prompt_text = config.get("prompt_text", "嗯。如果不是因为店长深谙电影知识，我可能会错过这个细节也未可知。")
        host = config.get("api_host", "localhost")
        port = config.get("api_port", 8000)
        self.api_url = f"http://{host}:{port}/"
        windows_http_port = config.get("windows_http_port", 9800)
        self.windows_base_url = f"http://{host}:{windows_http_port}/"

        self.vg = VoiceGenerator(api_url=self.api_url, windows_base_url=self.windows_base_url)
        if not self.vg.tts.available:
            return
        if self.sovits_model and self.gpt_model:
            self.vg.set_models(self.sovits_model, self.gpt_model)
        

    async def _generate_audio(self, text: str, save_dir: str) -> str:
        return self.vg.generate_voice(
            ref_audio=self.ref_audio,
            prompt_text=self.prompt_text,
            text=text,
            save_dir=save_dir
        )

    @on_decorating_result()
    async def on_decorating_result(self, event: AstrMessageEvent):
        result = event.get_result()
        #logger.info(f"[VoiceGeneratorStar] event 可用属性: {dir(event)}")
        platform_id = event.session.platform_id
        session_id = event.get_session_id()
        save_dir = str(Path(__file__).parent / "outputVideo" / platform_id / session_id)
        logger.info(f"[VoiceGeneratorStar] 插件已加载，保存目录: {save_dir}")

        if not result or not result.chain:
            return
        full_text = " ".join([comp.text for comp in result.chain if isinstance(comp, Comp.Plain)]).strip()
        if len(full_text) < self.min_text_length or len(full_text) > self.max_text_length:
            return
        try:
            audio_path = await self._generate_audio(full_text, save_dir)
            if audio_path is False:
                logger.error("[VoiceGeneratorStar] 语音生成失败，服务器不可用")
                return
            # 清除文字组件，只保留语音
            result.chain = [comp for comp in result.chain if not isinstance(comp, Comp.Plain)]
            result.chain.insert(0, Comp.Record(file=save_dir + "/audio.wav", url=save_dir + "/audio.wav"))
            logger.info(f"[VoiceGeneratorStar] 成功生成语音: {audio_path}")
        except Exception as e:
            logger.error(f"[VoiceGeneratorStar] 插件处理失败: {e}")

    @command(command_name="voicegen-test", description="测试语音生成")
    async def test_cmd(self, event: AstrMessageEvent, text: str = ""):
        if not text.strip():
            yield event.plain_result("用法: voicegen-test <文本>")
            return
        try:
            path = await self._generate_audio(text.strip())
            yield event.chain_result([Comp.Record(file=path, url=path)])
        except Exception as e:
            yield event.plain_result(f"❌ {e}")
