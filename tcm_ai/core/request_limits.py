"""HTTP 请求体与上传相关上限。"""

# base64 字符上限（约 6MB 解码后图像）
MAX_DIAGNOSE_IMAGE_B64_CHARS = 8 * 1024 * 1024
