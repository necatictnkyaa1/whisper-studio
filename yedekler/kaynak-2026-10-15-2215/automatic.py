"""Donanıma göre kalite seçimi ve kontrollü geri dönüş."""
import ctypes
import gc
import json
import os
import subprocess
from dataclasses import dataclass, asdict
from pathlib import Path

@dataclass(frozen=True)
class Hardware:
    ram_mb: int = 0
    available_mb: int = 0
    gpu_free_mb: int = 0
    cuda: bool = False

@dataclass(frozen=True)
class Profile:
    model: str
    device: str

def inspect_hardware():
    total = available = free = 0
    if os.name == 'nt':
        class Memory(ctypes.Structure):
            _fields_ = [('length', ctypes.c_ulong), ('load', ctypes.c_ulong),
                        ('total', ctypes.c_ulonglong), ('available', ctypes.c_ulonglong),
                        ('page_total', ctypes.c_ulonglong), ('page_available', ctypes.c_ulonglong),
                        ('virtual_total', ctypes.c_ulonglong), ('virtual_available', ctypes.c_ulonglong),
                        ('extended', ctypes.c_ulonglong)]
        memory = Memory()
        memory.length = ctypes.sizeof(Memory)
        if ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(memory)):
            total, available = memory.total // 1048576, memory.available // 1048576
    cuda = False
    try:
        import ctranslate2
        cuda = ctranslate2.get_cuda_device_count() > 0 and 'float16' in ctranslate2.get_supported_compute_types('cuda')
        if cuda:
            result = subprocess.run(['nvidia-smi', '-i', '0', '--query-gpu=memory.free', '--format=csv,noheader,nounits'],
                                    capture_output=True, text=True, timeout=8,
                                    creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0))
            if result.returncode == 0:
                free = int(result.stdout.strip().splitlines()[0])
    except (OSError, ValueError, RuntimeError, subprocess.SubprocessError):
        pass
    return Hardware(total, available, free, cuda)

def profiles(hardware):
    result = []
    # RAM ve VRAM için pay bırakılır; teorik en büyük model zorlanmaz.
    if hardware.cuda:
        if hardware.gpu_free_mb >= 10000 and hardware.available_mb >= 6000:
            result.append(Profile('large-v3', 'cuda'))
        if hardware.gpu_free_mb >= 4500 and hardware.available_mb >= 3500:
            result.append(Profile('turbo', 'cuda'))
        if hardware.gpu_free_mb >= 2000 or hardware.gpu_free_mb == 0:
            result.append(Profile('small', 'cuda'))
    cpu_model = 'small' if hardware.available_mb >= 2500 else 'base'
    result.append(Profile(cpu_model, 'cpu'))
    return result

def resource_error(error):
    message = str(error).casefold()
    return any(word in message for word in ('out of memory', 'cuda', 'cublas', 'cudnn',
                                            'driver', 'not enough memory', 'memory allocation', 'bad_alloc'))

def cached(model):
    names = {'large-v3': 'models--Systran--faster-whisper-large-v3',
             'turbo': 'models--mobiuslabsgmbh--faster-whisper-large-v3-turbo',
             'small': 'models--Systran--faster-whisper-small',
             'base': 'models--Systran--faster-whisper-base',
             'tiny': 'models--Systran--faster-whisper-tiny'}
    folder = Path(__file__).resolve().parent / 'models' / names[model] / 'snapshots'
    return any((p / 'config.json').is_file() and (p / 'tokenizer.json').is_file()
               for p in folder.glob('*') if (p / 'model.bin').is_file())

def run_automatic(path, offline, on_segment, on_status, cancelled, target_language, runner):
    on_status('Bilgisayarın kontrol ediliyor · kalite ve hız otomatik ayarlanıyor')
    hardware = inspect_hardware()
    candidates = profiles(hardware)
    if offline:
        candidates = [p for p in candidates if cached(p.model)]
        if not candidates and cached('tiny'):
            candidates = [Profile('tiny', 'cpu')]
        if not candidates:
            raise RuntimeError('İnternetsiz çalışma için gerekli dosyalar henüz hazır değil. İnternetsiz çalışma seçeneğini kapatıp ilk indirmeyi tamamla.')
    report_path = Path(__file__).resolve().parent / 'automatic-selection.json'
    report = {'hardware': asdict(hardware), 'attempts': []}
    emitted = 0
    def emit(segment, progress):
        nonlocal emitted
        emitted += 1
        on_segment(segment, progress)
    for index, profile in enumerate(candidates):
        if cancelled():
            return
        report['attempts'].append(asdict(profile))
        try:
            report_path.write_text(json.dumps(report, indent=2), encoding='utf-8')
        except OSError:
            pass
        try:
            return runner(path, profile.model, None, profile.device, offline, emit, on_status,
                          cancelled, target_language=target_language)
        except Exception as error:
            # Üretilmiş metin varken baştan başlatmak tekrar eden bölümler üretir.
            if emitted or index == len(candidates) - 1 or not resource_error(error):
                raise
            gc.collect()
            on_status('Bu çalışma yolu kullanılamadı · bilgisayarına uygun alternatif deneniyor')
