"""CHECK 2 — Dòng nhãn YOLO: sai định dạng, ID lớp lạ, box tràn ảnh, box rỗng, box lặp.   (Script 2 trong slide)   ★★

Test:  pytest tests/test_label_format.py -q

Mỗi dòng nhãn: `id cx cy w h` (5 số, toạ độ 0–1). Trả về list[Issue]; `Issue.line` = số dòng (đếm từ 1).

| code             | severity | khi nào                                                                  |
|------------------|----------|--------------------------------------------------------------------------|
| BAD_FORMAT       | ERROR    | không đúng 5 cột số (dùng `parse_yolo_line`, bắt `ValueError`)           |
| BAD_CLASS_ID     | ERROR    | id lớp ngoài 0..len(ds.classes)-1                                        |
| BOX_ZERO         | ERROR    | w <= 0 hoặc h <= 0                                                       |
| BOX_OUT_OF_IMAGE | ERROR    | mép box vượt [0,1] quá `cfg["label_format"]["overflow_tol"]`; extra={"overflow": mức tràn} |
| DUP_BOX          | ERROR    | cùng lớp với một dòng TRƯỚC ĐÓ và IoU > `dup_box_iou`; báo ở dòng SAU    |
| BOX_TINY         | WARN     | cạnh ngắn của box (px) < `min_box_px`  (cần `ds.image_size(stem)`)       |
| BOX_HUGE         | WARN     | w*h > `max_box_frac`                                                     |

Gợi ý
- Mép trái = x - w/2, mép phải = x + w/2 (xem câu hỏi "dòng YOLO nào lỗi?" trong slide).
- Một dòng hỏng (BAD_FORMAT, BAD_CLASS_ID, BOX_ZERO) thì `continue`, đừng kiểm tiếp hình học của dòng đó.
- Dòng thiếu cột làm script của slide dừng giữa chừng: đây là lý do phải `try/except`.
- `iou_xywh(a, b)` có sẵn trong common.py.
- Ngưỡng nằm trong `cfg["label_format"]` — đừng viết cứng số vào code.
"""

from ..common import ERROR, WARN, Issue, iou_xywh, parse_yolo_line  # noqa: F401

CHECK = "label_format"


def _numbered(ds, stem):
    """Danh sách (số dòng gốc, nội dung) của file nhãn; [] nếu không có file."""
    out = []
    for item in ds.read_label_lines(stem) or []:
        out.append(tuple(item) if isinstance(item, (tuple, list)) else (len(out) + 1, item))
    return out


def run(ds, cfg):
    c = cfg["label_format"]
    tol, dup_iou = c["overflow_tol"], c["dup_box_iou"]
    min_px, max_frac = c["min_box_px"], c["max_box_frac"]
    n_cls = len(ds.classes)
    issues = []

    def add(code, sev, stem, ln, msg, extra=None):
        issues.append(Issue(CHECK, sev, code, stem, msg, line=ln, extra=extra or {}))

    for p in ds.image_files():
        stem = p.stem
        rows = _numbered(ds, stem)
        if not rows:
            continue
        try:
            W, H = ds.image_size(stem)
        except Exception:
            W = H = None

        kept = []  # (lớp, box) các dòng hình học hợp lệ đã gặp, để dò DUP_BOX
        for ln, raw in rows:
            if not raw.strip():
                continue
            try:
                cls, cx, cy, w, h = parse_yolo_line(raw)
            except (ValueError, TypeError):
                add("BAD_FORMAT", ERROR, stem, ln, f"dòng nhãn không đúng 5 cột số: {raw.strip()!r}")
                continue
            if cls < 0 or cls >= n_cls:
                add("BAD_CLASS_ID", ERROR, stem, ln, f"id lớp {cls} ngoài 0..{n_cls - 1}")
                continue
            if w <= 0 or h <= 0:
                add("BOX_ZERO", ERROR, stem, ln, f"box rỗng (w={w}, h={h})")
                continue

            overflow = max(0.0, -(cx - w / 2), (cx + w / 2) - 1, -(cy - h / 2), (cy + h / 2) - 1)
            if overflow > tol:
                add("BOX_OUT_OF_IMAGE", ERROR, stem, ln, f"box tràn ảnh {overflow:.4f}", {"overflow": overflow})

            box = (cx, cy, w, h)
            for pcls, pbox in kept:
                if pcls == cls:
                    v = iou_xywh(pbox, box)
                    if v > dup_iou:
                        add("DUP_BOX", ERROR, stem, ln, f"box lặp với một dòng trước (IoU={v:.3f})", {"iou": v})
                        break
            kept.append((cls, box))

            if W and H and min(w * W, h * H) < min_px:
                add("BOX_TINY", WARN, stem, ln, f"box quá nhỏ ({min(w * W, h * H):.1f}px)")
            if w * h > max_frac:
                add("BOX_HUGE", WARN, stem, ln, f"box chiếm {w * h:.1%} ảnh")
    return issues