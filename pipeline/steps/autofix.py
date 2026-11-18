"""BƯỚC 2/4 — Sửa tự động những lỗi bắt buộc mà máy sửa được AN TOÀN.   ★★

Test:  pytest tests/test_autofix.py -q

`fix(ds, issues, cfg) -> list[dict]`: duyệt `issues` (chỉ lỗi severity ERROR), sửa thẳng vào thư mục `ds`,
và trả về danh sách thay đổi; mỗi phần tử có khoá: image, line, action, before, after
(đây chính là file `03_fixes.csv` — bằng chứng pipeline đã làm gì, người có thể kiểm lại).

| code lỗi                                       | cách sửa                                    | action           |
|------------------------------------------------|---------------------------------------------|------------------|
| BAD_FORMAT, BAD_CLASS_ID, BOX_ZERO, DUP_BOX    | xoá dòng đó khỏi file nhãn                  | "drop_line"      |
| BOX_OUT_OF_IMAGE                               | cắt box về trong [0,1] (giữ nguyên lớp)     | "clip_box"       |
| MISSING_LABEL_FILE                             | KHÔNG sửa file (máy không thể bịa nhãn): ghi 1 dòng fix, before="(không có file)", after="chuyển người gán" | "needs_label" |
| BAD_CLASS_NAME                                 | ghi lại `names` trong data.yaml đúng `cfg["classes"]` | "rename_classes" |
| DUP_IMAGE_*, LEAK_TEST, CORRUPT_IMAGE, BAD_SIZE| xoá ảnh + nhãn khỏi `ds`                    | "remove_image"   |

Bẫy cần nghĩ tới (có test cho từng cái)
- Một file có NHIỀU dòng lỗi: số dòng trong `issues` là số dòng GỐC. Nếu xoá từng dòng một thì số dòng lệch.
  Gom theo file, rồi ghi lại MỘT lần.
- Sau khi cắt, box có thể không còn diện tích (nằm hẳn ngoài ảnh): lúc đó xoá dòng thay vì ghi box rỗng.
- Một dòng có 2 lỗi (vd. BOX_OUT_OF_IMAGE + DUP_BOX): xoá dòng thắng, chỉ ghi 1 fix `drop_line`, không ghi thêm `clip_box`. Dòng trống ở giữa file vẫn đếm vào số dòng gốc.
- Ảnh vừa bị xoá (DUP_IMAGE_*...) mà còn issue dòng của chính nó: bỏ qua êm, không được báo lỗi/chết.
- Không động tới lỗi WARN (cảnh báo là việc của người). Không sửa file ở `data/raw/` — chỉ sửa `ds`.
- Chạy lần 2 trên dữ liệu đã sửa phải không làm gì thêm (idempotent) — NGOẠI LỆ duy nhất: `needs_label` được ghi lại mỗi lần còn lỗi `MISSING_LABEL_FILE` (vì ảnh vẫn chưa có nhãn).

- `needs_label` KHÔNG tạo file nhãn rỗng (rỗng = "ảnh nền", khác với "chưa gán"). `review_queue` sẽ đẩy ảnh này lên đầu hàng đợi cho người.

Gợi ý: `yaml.safe_load / safe_dump`.
"""
from collections import defaultdict

import yaml

from ..common import ERROR, parse_yolo_line  # noqa: F401

DROP_CODES = {"BAD_FORMAT", "BAD_CLASS_ID", "BOX_ZERO", "DUP_BOX"}
REMOVE_CODES = {"LEAK_TEST", "CORRUPT_IMAGE", "BAD_SIZE"}


def _fix(image, line, action, before, after):
    return {"image": image, "line": line, "action": action, "before": before, "after": after}


def _is_remove(code):
    return code in REMOVE_CODES or code.startswith("DUP_IMAGE_")


def _clip(raw):
    """Cắt box về [0,1]; trả về dòng mới hoặc None nếu box không còn diện tích."""
    cls, cx, cy, w, h = parse_yolo_line(raw)
    x1, x2 = max(0.0, cx - w / 2), min(1.0, cx + w / 2)
    y1, y2 = max(0.0, cy - h / 2), min(1.0, cy + h / 2)
    if x2 - x1 <= 0 or y2 - y1 <= 0:
        return None
    return f"{int(cls)} {(x1 + x2) / 2:.6f} {(y1 + y2) / 2:.6f} {x2 - x1:.6f} {y2 - y1:.6f}"


def fix(ds, issues, cfg):
    errors = [i for i in issues if i.severity == ERROR]
    fixes, removed = [], set()

    # 1) Xoá ảnh + nhãn (mỗi ảnh một lần)
    for i in errors:
        if _is_remove(i.code) and i.image not in removed:
            removed.add(i.image)
            for p in list(ds.image_files()):
                if p.stem == i.image:
                    p.unlink(missing_ok=True)
            ds.label_path(i.image).unlink(missing_ok=True)
            fixes.append(_fix(i.image, None, "remove_image", i.code, "(đã xoá ảnh + nhãn)"))

    # 2) Ghi lại tên lớp trong data.yaml (một lần)
    if any(i.code == "BAD_CLASS_NAME" for i in errors):
        want = dict(enumerate(cfg["classes"]))
        before = ds.yaml_names()
        if before != want:
            yp = ds.yaml_path
            data = (yaml.safe_load(yp.read_text(encoding="utf-8")) if yp.exists() else None) or {}
            data["names"] = want
            yp.write_text(yaml.safe_dump(data, allow_unicode=True, sort_keys=False), encoding="utf-8")
            fixes.append(_fix("data.yaml", None, "rename_classes", str(before), str(want)))

    # 3) Thiếu file nhãn: không bịa nhãn, không tạo file rỗng
    for i in errors:
        if i.code == "MISSING_LABEL_FILE" and i.image not in removed:
            fixes.append(_fix(i.image, None, "needs_label", "(không có file)", "chuyển người gán"))

    # 4) Lỗi theo dòng: gom theo file (số dòng gốc), ghi lại MỘT lần
    per_file = defaultdict(lambda: defaultdict(set))
    for i in errors:
        if i.image in removed or not i.line:
            continue
        if i.code in DROP_CODES or i.code == "BOX_OUT_OF_IMAGE":
            per_file[i.image][i.line].add(i.code)

    for stem, per_line in per_file.items():
        lp = ds.label_path(stem)
        if not lp.exists():
            continue
        lines = lp.read_text(encoding="utf-8").splitlines()  # dòng trống vẫn đếm
        out, drop, changed = list(lines), set(), False
        for ln in sorted(per_line):
            if ln > len(lines):
                continue
            raw = lines[ln - 1]
            new = None
            if not (per_line[ln] & DROP_CODES):  # chỉ BOX_OUT_OF_IMAGE
                try:
                    new = _clip(raw)
                except (ValueError, TypeError):
                    new = None
            if new is None:
                drop.add(ln)
                fixes.append(_fix(stem, ln, "drop_line", raw, ""))
            else:
                out[ln - 1] = new
                fixes.append(_fix(stem, ln, "clip_box", raw, new))
            changed = True
        if changed:
            final = [t for n, t in enumerate(out, start=1) if n not in drop]
            lp.write_text("\n".join(final) + ("\n" if final else ""), encoding="utf-8")

    return fixes
