import asyncio

import sounddevice as sd
import numpy as np
import time
import os

from automic import global_counter
from asr import AsrWsClient
from dc import discord

# 配置参数
SAMPLE_RATE = 16000  # 采样率
BLOCK_DURATION = 1  # 每次处理 1 秒音频
VOLUME_THRESHOLD = 0.1  # 音量阈值（调整以适应不同声音）
SILENCE_LIMIT = 3  # 5 秒无声音则停止录制
DEVICE_INDEX = 13
CHANNEL_INDEX = 1

recording_count = 1  # 录音文件计数
os.makedirs("recordings", exist_ok=True)  # 创建存储目录



def get_new_filename():
    """生成新的音频文件名，避免覆盖"""
    count = 1
    while True:
        file_path = f"recordings/recording_{count}.wav"
        if not os.path.exists(file_path):
            return file_path
        count += 1

async def process_audio(recv_queue):
    global_counter.increment()
    print("process_audio begin", global_counter.get())
    try:
        while True:
            result = await recv_queue.get()
            if result is None:
                break
            if 'result' not in result['payload_msg']:
                await asyncio.sleep(0.1)
                continue

            if 'utterances' in result['payload_msg']['result']:
                rr = result['payload_msg']['result']
                for vv in rr['utterances']:
                    if vv['definite']:
                        discord.call_webhook_api(rr['text'])
                        print(rr['text'])

                        # 保存录音文件

    except Exception as e:
        print(f"Unexpected error 222: {e}")
    global_counter.decrement()
    print("process_audio done", global_counter.get())


async def finish_tasks(task1, task2):
    """等待任务完成，但不阻塞主流程"""
    try:
        await asyncio.gather(task1, task2)
    except asyncio.CancelledError:
        print("任务被取消")
    print("任务完成", global_counter.get())

async def monitor_audio():
    while True:
        print("当前协程数",global_counter.get())
        silence_counter = 0
        recording = False
        recording = False
        audio_queue = asyncio.Queue()
        loop = asyncio.get_event_loop()
        last_sound_time = time.time()

        def callback(indata, frames, time_info, status):
            nonlocal silence_counter
            nonlocal recording
            nonlocal last_sound_time
            nonlocal audio_queue

            volume = np.linalg.norm(indata)
            current_time = time.time()
            if volume > VOLUME_THRESHOLD:
                last_sound_time = current_time
                if not recording:
                    print("开始录音...")
                    recording = True
                # recording_data.append(data_byte)
                pcm_data = (indata.copy() * 32768).astype(np.int16).tobytes()
                asyncio.run_coroutine_threadsafe(audio_queue.put(pcm_data), loop)

            elif recording and (current_time - last_sound_time > 3):
                print("\n5 秒无声音，停止录音")
                silence_counter = 4
                raise sd.CallbackStop()

        recv_queue = asyncio.Queue()
        client = AsrWsClient(audio_queue, recv_queue)
        task1 = asyncio.create_task(client.segment_data_processor())
        task2 = asyncio.create_task(process_audio(recv_queue))

        with sd.InputStream(callback=callback, blocksize=2048, samplerate=SAMPLE_RATE, channels=CHANNEL_INDEX, device=DEVICE_INDEX):
            print("开始监听监听中...")
            while silence_counter < 3:
                await asyncio.sleep(BLOCK_DURATION)
        await audio_queue.put(None)
        print("录音结束")
        asyncio.create_task(finish_tasks(task1, task2))

if __name__ == "__main__":
    asyncio.run(monitor_audio())