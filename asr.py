import asyncio
import gzip
import json
import time
import uuid
import wave
from io import BytesIO
import aiofiles
import websockets

from automic import global_counter

PROTOCOL_VERSION = 0b0001
DEFAULT_HEADER_SIZE = 0b0001

# Message Type:
FULL_CLIENT_REQUEST = 0b0001
AUDIO_ONLY_REQUEST = 0b0010
FULL_SERVER_RESPONSE = 0b1001
SERVER_ACK = 0b1011
SERVER_ERROR_RESPONSE = 0b1111

# Message Type Specific Flags
NO_SEQUENCE = 0b0000  # no check sequence
POS_SEQUENCE = 0b0001
NEG_SEQUENCE = 0b0010
NEG_WITH_SEQUENCE = 0b0011
NEG_SEQUENCE_1 = 0b0011

# Message Serialization
NO_SERIALIZATION = 0b0000
JSON = 0b0001

# Message Compression
NO_COMPRESSION = 0b0000
GZIP = 0b0001


def generate_header(
        message_type=FULL_CLIENT_REQUEST,
        message_type_specific_flags=NO_SEQUENCE,
        serial_method=JSON,
        compression_type=GZIP,
        reserved_data=0x00
):
    """
    protocol_version(4 bits), header_size(4 bits),
    message_type(4 bits), message_type_specific_flags(4 bits)
    serialization_method(4 bits) message_compression(4 bits)
    reserved （8bits) 保留字段
    """
    header = bytearray()
    header_size = 1
    header.append((PROTOCOL_VERSION << 4) | header_size)
    header.append((message_type << 4) | message_type_specific_flags)
    header.append((serial_method << 4) | compression_type)
    header.append(reserved_data)
    return header


def generate_before_payload(sequence: int):
    before_payload = bytearray()
    before_payload.extend(sequence.to_bytes(4, 'big', signed=True))  # sequence
    return before_payload


def parse_response(res):
    """
    protocol_version(4 bits), header_size(4 bits),
    message_type(4 bits), message_type_specific_flags(4 bits)
    serialization_method(4 bits) message_compression(4 bits)
    reserved （8bits) 保留字段
    header_extensions 扩展头(大小等于 8 * 4 * (header_size - 1) )
    payload 类似与http 请求体
    """
    protocol_version = res[0] >> 4
    header_size = res[0] & 0x0f
    message_type = res[1] >> 4
    message_type_specific_flags = res[1] & 0x0f
    serialization_method = res[2] >> 4
    message_compression = res[2] & 0x0f
    reserved = res[3]
    header_extensions = res[4:header_size * 4]
    payload = res[header_size * 4:]
    result = {
        'is_last_package': False,
    }
    payload_msg = None
    payload_size = 0
    if message_type_specific_flags & 0x01:
        # receive frame with sequence
        seq = int.from_bytes(payload[:4], "big", signed=True)
        result['payload_sequence'] = seq
        payload = payload[4:]

    if message_type_specific_flags & 0x02:
        # receive last package
        result['is_last_package'] = True

    if message_type == FULL_SERVER_RESPONSE:
        payload_size = int.from_bytes(payload[:4], "big", signed=True)
        payload_msg = payload[4:]
    elif message_type == SERVER_ACK:
        seq = int.from_bytes(payload[:4], "big", signed=True)
        result['seq'] = seq
        if len(payload) >= 8:
            payload_size = int.from_bytes(payload[4:8], "big", signed=False)
            payload_msg = payload[8:]
    elif message_type == SERVER_ERROR_RESPONSE:
        code = int.from_bytes(payload[:4], "big", signed=False)
        result['code'] = code
        payload_size = int.from_bytes(payload[4:8], "big", signed=False)
        payload_msg = payload[8:]
    if payload_msg is None:
        return result
    if message_compression == GZIP:
        payload_msg = gzip.decompress(payload_msg)
    if serialization_method == JSON:
        payload_msg = json.loads(str(payload_msg, "utf-8"))
    elif serialization_method != NO_SERIALIZATION:
        payload_msg = str(payload_msg, "utf-8")
    result['payload_msg'] = payload_msg
    result['payload_size'] = payload_size
    return result


def read_wav_info(data: bytes = None) -> (int, int, int, int, bytes):
    with BytesIO(data) as _f:
        wave_fp = wave.open(_f, 'rb')
        nchannels, sampwidth, framerate, nframes = wave_fp.getparams()[:4]
        wave_bytes = wave_fp.readframes(nframes)
    return nchannels, sampwidth, framerate, nframes, wave_bytes


def judge_wav(ori_date):
    if len(ori_date) < 44:
        return False
    if ori_date[0:4] == b"RIFF" and ori_date[8:12] == b"WAVE":
        return True
    return False


class AsrWsClient:
    def __init__(self, send_queue, recv_queue, **kwargs):
        """
        :param config: config
        """
        self.send_queue = send_queue
        self.recv_queue = recv_queue
        self.success_code = 1000  # success code, default is 1000
        self.seg_duration = int(kwargs.get("seg_duration", 100))
        self.ws_url = kwargs.get("ws_url", "wss://openspeech.bytedance.com/api/v3/sauc/bigmodel")
        self.uid = kwargs.get("uid", "test")
        self.format = kwargs.get("format", "pcm")
        self.rate = kwargs.get("rate", 16000)
        self.bits = kwargs.get("bits", 16)
        self.channel = kwargs.get("channel", 1)
        self.codec = kwargs.get("codec", "raw")
        self.auth_method = kwargs.get("auth_method", "none")
        self.hot_words = kwargs.get("hot_words", None)
        self.streaming = kwargs.get("streaming", True)
        self.mp3_seg_size = kwargs.get("mp3_seg_size", 1000)
        self.req_event = 1

    def construct_request(self, reqid, data=None):
        req = {
            "user": {
                "uid": self.uid,
            },
            "audio": {
                'format': self.format,
                "sample_rate": self.rate,
                "bits": self.bits,
                "channel": self.channel,
                "codec": self.codec,
            },
            "request": {
                "model_name": "bigmodel",
                "enable_punc": True,
                "result_type": "single",
                # "vad_segment_duration": 800,
            }
        }
        return req

    @staticmethod
    def slice_data(data: bytes, chunk_size: int) -> (list, bool):
        data_len = len(data)
        offset = 0
        while offset + chunk_size < data_len:
            yield data[offset: offset + chunk_size], False
            offset += chunk_size
        else:
            yield data[offset: data_len], True

    async def send_data(self, ws, seq, chunk, last):
        if len(chunk) > 0:
            payload_bytes = gzip.compress(chunk)
        else:
            payload_bytes = gzip.compress(b' ')

        audio_only_request = bytearray(generate_header(message_type=AUDIO_ONLY_REQUEST,
                                                       message_type_specific_flags=POS_SEQUENCE))
        if last:
            audio_only_request = bytearray(generate_header(message_type=AUDIO_ONLY_REQUEST,
                                                           message_type_specific_flags=NEG_WITH_SEQUENCE))
        audio_only_request.extend(generate_before_payload(sequence=seq))
        audio_only_request.extend((len(payload_bytes)).to_bytes(4, 'big'))  # payload size(4 bytes)
        req_str = ' '.join(format(byte, '02x') for byte in audio_only_request)
        # print("seq", seq, "req", req_str)
        audio_only_request.extend(payload_bytes)  # payload
        await ws.send(audio_only_request)
        res =  await ws.recv()
        return res

    async def segment_data_processor(self):
        global_counter.increment()
        reqid = str(uuid.uuid4())
        seq = 1
        request_params = self.construct_request(reqid)
        payload_bytes = str.encode(json.dumps(request_params))
        payload_bytes = gzip.compress(payload_bytes)
        full_client_request = bytearray(generate_header(message_type_specific_flags=POS_SEQUENCE))
        full_client_request.extend(generate_before_payload(sequence=seq))
        full_client_request.extend((len(payload_bytes)).to_bytes(
            4, 'big'))  # payload size(4 bytes)
        req_str = ' '.join(format(byte, '02x') for byte in full_client_request)
        # print(f"{time.time()}, seq", seq, "req", req_str)
        full_client_request.extend(payload_bytes)  # payload
        header = {}
        # print("reqid", reqid)
        # header["X-Tt-Logid"] = reqid
        header["X-Api-Resource-Id"] = "volc.bigasr.sauc.duration"
        header["X-Api-Access-Key"] = "vLrS1QgMAwV0-PR5e3-ZqQMwx61ktt6Q"
        header["X-Api-App-Key"] = "8042709829"
        header["X-Api-Request-Id"] = reqid
        try:
            first_chunk = await self.send_queue.get()
            if first_chunk is None:
                await self.recv_queue.put(None)
                return

            async with websockets.connect(self.ws_url, extra_headers=header, max_size=1000000000) as ws:
                await ws.send(full_client_request)
                res = await ws.recv()
                result = parse_response(res)
                print("******************")
                print("sauc result", result)
                print("******************")

                seq = 2
                # send first chunk
                res = await self.send_data(ws, seq, first_chunk, False)
                result = parse_response(res)
                await self.recv_queue.put(result)

                print("listeing queue...")
                while True:
                    last = False
                    chunk = await self.send_queue.get()
                    if chunk is None:
                        last = True
                        chunk = []
                        # if no compression, comment this line
                    seq += 1
                    if last:
                        print("send 最后一个包")
                        seq = -seq
                    start = time.time()

                    res = await self.send_data(ws, seq, chunk, last)

                    # print(res)
                    # res_str = ' '.join(format(byte, '02x') for byte in res)
                    # print(res_str)
                    result = parse_response(res)
                    await self.recv_queue.put(result)

                    # if 'utterances' in result['payload_msg']['result']:
                    #     rr = result['payload_msg']['result']
                    #     for vv in rr['utterances']:
                    #         if vv['definite']:
                    #             print(rr['text'])
                    # print(f"{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')}, seq", seq, "res", json.dumps(result))
                    # if 'payload_msg' in result and result['payload_msg']['code'] != self.success_code:
                    #     return result
                    if last:
                        await self.recv_queue.put(None)
                        break
                    if self.streaming:
                        await asyncio.sleep(0.01)

        except websockets.exceptions.WebSocketException as e:
            print(f"WebSocket connection failed: {e}")
            if hasattr(e, "status_code"):
                print(f"Response status code: {e.status_code}")
            if hasattr(e, "headers"):
                print(f"Response headers: {e.headers}")
            if hasattr(e, "response") and hasattr(e.response, "text"):
                print(f"Response body: {e.response.text}")
        except Exception as e:
            print(f"Unexpected error: {e}")

        global_counter.increment()


async def execute(self):
    async with aiofiles.open(self.audio_path, mode="rb") as _f:
        data = await _f.read()
    audio_data = bytes(data)
    if self.format == "mp3":
        segment_size = self.mp3_seg_size
        return await self.segment_data_processor(audio_data, segment_size)
    if self.format == "wav":
        nchannels, sampwidth, framerate, nframes, wav_len = read_wav_info(audio_data)
        size_per_sec = nchannels * sampwidth * framerate
        segment_size = int(size_per_sec * self.seg_duration / 1000)
        return await self.segment_data_processor(audio_data, segment_size)
    if self.format == "pcm":
        segment_size = int(self.rate * 2 * self.channel * self.seg_duration / 500)
        return await self.segment_data_processor(audio_data, segment_size)
    else:
        raise Exception("Unsupported format")


def execute_one(audio_item, **kwargs):
    asr_http_client = AsrWsClient(
        **kwargs
    )
    result = asyncio.run(asr_http_client.execute())
    return {"result": result}


def test_stream():
    print("测试流式")
    result = execute_one(
        {
            'id': 1,
            "path": "/Users/zxy/Downloads/wen/output.wav"
        }
    )
    print(result)


if __name__ == '__main__':
    test_stream()
