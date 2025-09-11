# routes/detect.py
from flask import Blueprint, request, jsonify, current_app
import os
from pathlib import Path
from typing import List, Dict, Any, Optional

bp_detect = Blueprint('detect', __name__)

_MODEL = None
_MODEL_NAMES = None
_DEVICE = None  # <= เก็บค่าที่เลือกได้

# ---------- utils: device ----------
def _pick_device() -> str:
    # 1) เคารพ YOLO_DEVICE ถ้าตั้งเป็นค่าเฉพาะเช่น '0' หรือ 'cpu'
    env = (os.environ.get('YOLO_DEVICE') or '').strip().lower()
    if env and env not in ('auto',):
        return env
    # 2) auto: ถ้ามี CUDA ใช้ GPU0, ไม่งั้น cpu
    try:
        import torch
        if torch.cuda.is_available():
            return '0'
    except Exception:
        pass
    # กันเคสตั้ง CUDA_VISIBLE_DEVICES=auto มาจากภายนอก
    if (os.environ.get('CUDA_VISIBLE_DEVICES') or '').strip().lower() == 'auto':
        os.environ.pop('CUDA_VISIBLE_DEVICES', None)
    return 'cpu'

# ---------- utils: uploads root ----------
def _uploads_root() -> Path:
    env_root = os.environ.get('UPLOAD_ROOT', '').strip()
    if env_root:
        return Path(env_root)
    return Path(current_app.root_path) / 'static' / 'uploads'

# ---------- utils: model path picker ----------
def _pick_model_path(app_root: Path) -> Optional[str]:
    """
    เลือก path โมเดลตามลำดับความสำคัญ:
      1) ENV: MODEL_PATH
      2) {root}/config/model/best(1).pt  และ  best (1).pt (มี/ไม่มีช่องว่าง)
      3) {root}/config/model/best.pt
      4) สำรอง: {root}/model/... (บางโปรเจกต์อาจวางไว้ตรงนี้)
    คืน path ที่มีจริงตัวแรก ถ้าไม่พบใดๆ คืน None
    """
    env_path = (os.environ.get('MODEL_PATH') or '').strip()

    candidates = [
        env_path,
        str((app_root / 'config' / 'model' / 'best(1).pt').resolve()),
        str((app_root / 'config' / 'model' / 'best (1).pt').resolve()),
        str((app_root / 'config' / 'model' / 'best.pt').resolve()),
        # สำรองโฟลเดอร์ model ที่ root เผื่อย้ายไฟล์ในอนาคต
        str((app_root / 'model' / 'best(1).pt').resolve()),
        str((app_root / 'model' / 'best (1).pt').resolve()),
        str((app_root / 'model' / 'best.pt').resolve()),
    ]

    for p in candidates:
        if p and Path(p).exists():
            current_app.logger.info(f"[DETECT] ✔ Using model file: {p}")
            return p

    # log ช่วยดีบักว่าหาไฟล์ที่ไหนบ้าง
    for p in candidates:
        if p:
            current_app.logger.warning(f"[DETECT] ✗ Not found: {p}")
    return None

# ---------- model loader ----------
def _load_model():
    global _MODEL, _MODEL_NAMES, _DEVICE
    if _MODEL is not None:
        return _MODEL

    from ultralytics import YOLO

    app_root = Path(current_app.root_path).resolve()
    model_path = _pick_model_path(app_root)
    if not model_path:
        msg = ("No model file found. Please set ENV MODEL_PATH or put model at "
               "`config/model/best.pt` (or `best(1).pt`).")
        current_app.logger.error(f"[DETECT] {msg}")
        raise FileNotFoundError(msg)

    _DEVICE = _pick_device()
    current_app.logger.info(f"[DETECT] Loading YOLO: {model_path} | device={_DEVICE}")
    m = YOLO(model_path)
    _MODEL = m
    _MODEL_NAMES = getattr(m, 'names', None)
    current_app.logger.info(
        f"[DETECT] YOLO loaded OK | classes="
        f"{len(_MODEL_NAMES) if isinstance(_MODEL_NAMES, dict) else _MODEL_NAMES}"
    )
    return _MODEL

def _class_name_from_id(idx: int) -> str:
    if isinstance(_MODEL_NAMES, dict):
        return _MODEL_NAMES.get(idx, str(idx))
    return str(idx)

# ---------- core predict ----------
def predict_on_paths(abs_paths: List[str], conf_thres: float = 0.25) -> List[Dict[str, Any]]:
    model = _load_model()
    # ใช้ _DEVICE ที่เลือกไว้เสมอ
    results = model.predict(
        abs_paths,
        verbose=False,
        conf=conf_thres,
        imgsz=int(os.environ.get('YOLO_IMGSZ', '640')),
        device=_DEVICE,                     # <<<<<<<<<< สำคัญ
    )

    out: List[Dict[str, Any]] = []
    for img_path, r in zip(abs_paths, results):
        preds = []
        if hasattr(r, 'boxes') and r.boxes is not None and len(r.boxes) > 0:
            for b in r.boxes:
                cls_id = int(b.cls[0].item()) if hasattr(b.cls[0], 'item') else int(b.cls[0])
                conf   = float(b.conf[0].item()) if hasattr(b.conf[0], 'item') else float(b.conf[0])
                preds.append({'class': _class_name_from_id(cls_id), 'confidence': conf})
        elif hasattr(r, 'probs') and r.probs is not None:
            import torch
            probs = r.probs
            if isinstance(probs, torch.Tensor):
                conf, cls_id = float(probs.max().item()), int(probs.argmax().item())
                preds.append({'class': _class_name_from_id(cls_id), 'confidence': conf})
        out.append({'image': img_path, 'preds': preds})
    return out

# ---------- routes ----------
@bp_detect.route('/labels', methods=['GET'])
def labels():
    try:
        _load_model()
    except FileNotFoundError as e:
        return jsonify({'success': False, 'error': 'model_not_found', 'message': str(e)}), 500

    if isinstance(_MODEL_NAMES, dict):
        return jsonify({'success': True, 'labels': _MODEL_NAMES})
    return jsonify({'success': True, 'labels': _MODEL_NAMES})

@bp_detect.route('', methods=['POST'])
def detect_batch():
    data = request.get_json(silent=True) or {}
    items = data.get('images') or data.get('paths') or []
    conf  = float(data.get('conf') or 0.25)
    if not isinstance(items, list) or not items:
        return jsonify({'success': False, 'error': 'no_images'}), 400

    root = _uploads_root()
    abs_paths = []
    for p in items:
        P = Path(str(p))
        if not P.is_absolute():
            P = (root / P).resolve()
        abs_paths.append(str(P))

    try:
        results = predict_on_paths(abs_paths, conf_thres=conf)
    except FileNotFoundError as e:
        return jsonify({'success': False, 'error': 'model_not_found', 'message': str(e)}), 500
    except Exception as e:
        current_app.logger.exception("[DETECT] Inference error")
        return jsonify({'success': False, 'error': 'inference_failed', 'message': str(e)}), 500

    return jsonify({'success': True, 'results': results})
