import os
from gradio_client import Client, file

class SoVITSTTS:
    def __init__(self, api_url="http://localhost:9872/"):
        try:
            self.client = Client(api_url)
            self.available = True
        except Exception as e:
            # 捕获连接失败，不抛异常
            self.client = None
            self.available = False
            print(f"[SoVITSTTS] 无法连接语音服务器: {e}")

    def set_sovits_model(self, sovits_path, prompt_language="中文", text_language="中文"):
        return self.client.predict(
            sovits_path=sovits_path,
            prompt_language=prompt_language,
            text_language=text_language,
            api_name="/change_sovits_weights"
        )

    def set_gpt_model(self, gpt_path):
        return self.client.predict(
            gpt_path=gpt_path,
            api_name="/change_gpt_weights"
        )

    def synthesize(self, ref_audio, prompt_text, text,
                   prompt_language="中文", text_language="中文",
                   how_to_cut="凑四句一切", top_k=15, top_p=1, temperature=1,
                   ref_free=False, speed=1, if_freeze=False, inp_refs=None,
                   sample_steps=32, if_sr=False, pause_second=0.3):
        return self.client.predict(
            ref_wav_path=file(ref_audio),
            prompt_text=prompt_text,
            prompt_language=prompt_language,
            text=text,
            text_language=text_language,
            how_to_cut=how_to_cut,
            top_k=top_k,
            top_p=top_p,
            temperature=temperature,
            ref_free=ref_free,
            speed=speed,
            if_freeze=if_freeze,
            inp_refs=inp_refs,
            sample_steps=sample_steps,
            if_sr=if_sr,
            pause_second=pause_second,
            api_name="/get_tts_wav"
        )
