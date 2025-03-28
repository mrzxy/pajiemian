from google.cloud import speech_v1p1beta1 as speech
import os

def transcribe_audio(file_path):

    os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = 'gkey.json'

    # 创建 SpeechClient 实例
    client = speech.SpeechClient()

    # 读取音频文件
    with open(file_path, "rb") as audio_file:
        content = audio_file.read()

    # 配置音频和识别参数
    audio = speech.RecognitionAudio(content=content)
    config = speech.RecognitionConfig(
        encoding=speech.RecognitionConfig.AudioEncoding.LINEAR16,
        sample_rate_hertz=16000,  # 根据音频文件调整
        language_code="zh-CN",  # 中文普通话
    )

    # 调用 API 进行识别
    response = client.recognize(config=config, audio=audio)

    # 输出识别结果
    for result in response.results:
        print("Transcript: {}".format(result.alternatives[0].transcript))

if __name__ == "__main__":
    # 设置环境变量（如果未在外部设置）

    # 调用函数，传入音频文件路径
    transcribe_audio("path/to/your/audio.wav")