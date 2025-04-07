import asyncio

from amazon_transcribe.handlers import TranscriptResultStreamHandler
from amazon_transcribe.model import TranscriptEvent
import os
from amazon_transcribe.client import TranscribeStreamingClient
import boto3
from botocore.exceptions import NoCredentialsError, PartialCredentialsError, ClientError
import json

REGION = "us-east-1"
with open("aws.json") as f:
    config = json.load(f)
os.environ["AWS_ACCESS_KEY_ID"] =  config["access_key_id"]
os.environ["AWS_SECRET_ACCESS_KEY"] = config["secret_access_key"]
os.environ["AWS_DEFAULT_REGION"] = REGION


def check_aws_credentials():
    try:
        # 使用 STS 获取当前身份
        client = boto3.client('sts')
        identity = client.get_caller_identity()

        print("✅ AWS 凭证有效")
        print("账户 ID:", identity['Account'])
        print("用户 ARN:", identity['Arn'])
        return True
    except NoCredentialsError:
        print("❌ 未找到 AWS 凭证（NoCredentialsError）")
    except PartialCredentialsError:
        print("❌ 凭证不完整（PartialCredentialsError）")
    except ClientError as e:
        print("❌ AWS 客户端错误:", e.response['Error']['Message'])
    except Exception as e:
        print("❌ 未知错误:", str(e))

    return False



LANGUAGE_CODE = "en-US"
SAMPLE_RATE = 16000




class MyEventHandler(TranscriptResultStreamHandler):
    def __init__(self, stream, recv_queue):
        super().__init__(stream)
        self.last_sent_text = ""
        self.recv_queue = recv_queue

    async def handle_transcript_event(self, transcript_event: TranscriptEvent):
        for result in transcript_event.transcript.results:
            if result.is_partial:
                continue
            if result.alternatives:
                text = result.alternatives[0].transcript.strip()
                if text and text != self.last_sent_text:
                    self.last_sent_text = text
                    await self.recv_queue.put(text)



class AwsAsrClient:
    def __init__(self, send_queue, recv_queue, **kwargs):
        self.send_queue = send_queue
        self.recv_queue = recv_queue

    async def write_audio(self, stream):
        while True:
            chunk = await self.send_queue.get()
            if chunk is not None:
                await stream.input_stream.send_audio_event(audio_chunk=chunk)
            else:
                await stream.input_stream.end_stream()
                break

    async def doing(self):
        chunk = await self.send_queue.get()
        if chunk is None:
            return

        client = TranscribeStreamingClient(region=REGION)
        stream = await client.start_stream_transcription(
            language_code=LANGUAGE_CODE,
            media_sample_rate_hz=SAMPLE_RATE,
            media_encoding="pcm"
        )
        await stream.input_stream.send_audio_event(audio_chunk=chunk)

        await asyncio.gather(
            self.write_audio(stream),
            MyEventHandler(stream.output_stream, self.recv_queue).handle_events()
        )
        await self.recv_queue.put(None)

if __name__ == "__main__":
    check_aws_credentials()