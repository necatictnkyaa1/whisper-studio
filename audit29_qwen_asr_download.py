"""Resmî sabit sürümden yerel ASR karşılaştırma modeli; ses yüklemez."""
import os,time,json,hashlib
from pathlib import Path
os.environ['HF_HUB_DISABLE_XET']='1'
from huggingface_hub import snapshot_download
revision='bcd2b5b7f32b480ab5790554cfa8347f246a14f3'
root=Path('models/qwen3-asr-1.7b-compare')
snapshot_download('Qwen/Qwen3-ASR-1.7B-hf',revision=revision,local_dir=root,
 allow_patterns=['*.json','*.jinja','*.safetensors'],max_workers=3)
path=root/'model.safetensors';digest=hashlib.file_digest(path.open('rb'),'sha256').hexdigest()
assert path.stat().st_size==4076193080
assert digest=='2db53c7d81bd9b8cbc6a074e89be2c968a0d373fb4ee68bb1b1e14f7042dfee1'
(root/'verified.json').write_text(json.dumps({'revision':revision,'sha256':digest}),encoding='utf-8')
print('VERIFIED',digest,flush=True)
