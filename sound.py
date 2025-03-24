import sounddevice as sd
import numpy as np
from scipy.io.wavfile import write


if __name__ == "__main__":
    # 设置录音参数
    duration = 10  # 录音时长（秒）
    sample_rate = 44100  # 采样率
    device_info = sd.query_devices(kind='input')
    print("默认输入设备的声道数:", device_info['max_input_channels'])
    channels = device_info['max_input_channels']
    # 开始录音
    print("正在录音...")
    audio_data = sd.rec(int(duration * sample_rate), samplerate=sample_rate, channels=channels, dtype='float32')
    sd.wait()  # 等待录音完成

    # 保存录音为 WAV 文件
    output_file = "output.wav"
    write(output_file, sample_rate, (audio_data * 32767).astype(np.int16))  # 将浮点数转换为 16 位整数
    print(f"录音已保存到: {output_file}")