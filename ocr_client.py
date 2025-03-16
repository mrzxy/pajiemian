
import json
import os
import types
from tencentcloud.common import credential
from tencentcloud.common.profile.client_profile import ClientProfile
from tencentcloud.common.profile.http_profile import HttpProfile
from tencentcloud.common.exception.tencent_cloud_sdk_exception import TencentCloudSDKException
from tencentcloud.ocr.v20181119 import ocr_client, models

def mock_detect_text(file_name):
    with (open(os.path.join("case", file_name), "r") as f):
        body =  f.read()
        return json.loads(body)

def detect_text(img_base64):
    try:
        cred = credential.Credential("xx", "xx")
        # 实例化一个http选项，可选的，没有特殊需求可以跳过
        httpProfile = HttpProfile()
        httpProfile.endpoint = "ocr.tencentcloudapi.com"

        # 实例化一个client选项，可选的，没有特殊需求可以跳过
        clientProfile = ClientProfile()
        clientProfile.httpProfile = httpProfile
        # 实例化要请求产品的client对象,clientProfile是可选的
        client = ocr_client.OcrClient(cred, "ap-guangzhou", clientProfile)

        # 实例化一个请求对象,每个接口都会对应一个request对象
        req = models.GeneralAccurateOCRRequest()
        params = {
            "ImageBase64": img_base64,
            "IsPdf": True,
            "EnableImageCrop": False,
            "PdfPageNumber": 1,
        }
        req.from_json_string(json.dumps(params))

        # 返回的resp是一个GeneralAccurateOCRResponse的实例，与请求对象对应
        resp = client.QuestionOCR(req)
        return json.loads(resp.to_json_string())

    except TencentCloudSDKException as err:
        print(err)
        return None