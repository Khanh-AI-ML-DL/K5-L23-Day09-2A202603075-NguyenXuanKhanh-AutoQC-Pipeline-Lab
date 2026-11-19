# Báo cáo Day 09 — Nguyễn Xuân Khánh, 2A202603075



## 1. Kết luận trước
pipeline kết luận **Release / Hold / Rework**? Bao nhiêu ảnh vào, bao nhiêu ảnh ra dataset? Lý do chính (1–3 câu).
- pipline kết luận: **Release/Hold/Rework**. Nhận 205/224 ảnh, loại 19 ảnh, 6 ảnh bị lỗi rò rỉ test, 13 ảnh bị lỗi nhãn, 0 ảnh bị lỗi trùng. 
- Lý do chính: còn nhiều ảnh bị lỗi nhãn và rò rỉ test, cần người xem duyệt trước khi phát hành dataset.
- kết luận: HOLD — Không còn lỗi bắt buộc, nhưng 60/205 ảnh còn cảnh báo (tỉ lệ 29.27% >= ngưỡng 10.00%): chuyển người duyệt.; Đã bỏ qua cảnh báo của các ảnh người đã duyệt (80 ảnh).
## 2. Lỗi và phân việc
Lấy từ `02_error_list_v1` (gom theo mã lỗi). Cột "ai sửa": **máy** (autofix) hay **người** (hàng đợi); chỉ ghi những mã có mặt trong lô của bạn.

| Mã lỗi              | Số ảnh/dòng | Ai sửa (máy/người) | Vì sao                                                                                           |
|---------------------|------------:|--------------------|--------------------------------------------------------------------------------------------------|
| BAD_CLASS_ID        |           6 | Máy (autofix)               | Kiểm tra và đối chiếu ID lớp với danh sách class hợp lệ.                                         |
| BAD_CLASS_NAME      |           2 | Máy (autofix)               | Chuẩn hóa tên lớp theo danh sách nhãn đã định nghĩa                                              |
| BAD_FORMAT          |           3 | Máy (autofix)               | Chuyển đổi hoặc chuẩn hóa định dạng dữ liệu theo quy chuẩn.                                      |
| BAD_SIZE            |           3 | Máy  (autofix)              | Kiểm tra kích thước và loại bỏ hoặc xử lý ảnh không đạt điều kiện.                               |
| BOX_OUT_OF_IMAGE    |           8 | Máy  (autofix)              | Kiểm tra và giới hạn tọa độ Bounding Box trong phạm vi ảnh                                        |
| BOX_ZERO            |           4 | Người       (hàng đợi);       | Cần kiểm tra ảnh để xác định đối tượng thực tế và vẽ lại Bounding Box phù hợp.                   |
| CORRUPT_IMAGE       |           2 | Máy   (autofix)             | Phát hiện ảnh không đọc được và đưa vào danh sách loại bỏ.                                       |
| DUP_BOX             |           7 | Máy   (autofix)             | Phát hiện các Bounding Box trùng lặp và loại bỏ bản ghi dư thừa.                                 |
| DUP_IMAGE_EXACT     |           8 | Máy    (autofix)            | Phát hiện ảnh giống hệt nhau bằng mã MD5 và loại bỏ bản sao.                                     |
| DUP_IMAGE_NEAR      |           7 | Người     (hàng đợi);         | So sánh trực quan để xác định ảnh gần giống có thực sự là bản sao hay không.                     |
| LEAK_TEST           |          11 | Máy    (autofix)            | Phát hiện ảnh trùng giữa các tập dữ liệu và loại bỏ nguy cơ rò rỉ dữ liệu.                       |
| MISSING_LABEL_FILE  |           6 | Người    (hàng đợi);          | Quan sát ảnh và tạo file nhãn chính xác cho đối tượng.                                           |
| BOX_HUGE            |           3 | Người     (hàng đợi);         | Cần kiểm tra ảnh để xác định Bounding Box quá lớn có bao gồm nhiều vùng không liên quan hay không. |
| BOX_TINY            |           6 | Người     (hàng đợi);         | Cần quan sát đối tượng để xác định Bounding Box quá nhỏ có bỏ sót vùng cần gán nhãn hay không.   |
| CLASS_RARE          |           4 | Người    (hàng đợi);          | Cần đánh giá tính hợp lệ của lớp hiếm, tránh tự động xóa hoặc đổi nhãn dữ liệu.                  |
| EMPTY_LABEL         |          11 | Người    (hàng đợi);          | Cần kiểm tra ảnh để xác định ảnh thực sự không có đối tượng hay bị thiếu nhãn.                   |
| POSSIBLE_FALSE_POS  |          24 | Người   (hàng đợi);           | Cần xác minh đối tượng được gán nhãn có thực sự xuất hiện trong ảnh hay không.                   |
| POSSIBLE_LOOSE_BOX  |          11 | Người   (hàng đợi);           | Cần kiểm tra trực quan và điều chỉnh Bounding Box nếu vùng bao quá rộng.                         |
| POSSIBLE_MISSING    |          32 | Người   (hàng đợi);           | Cần kiểm tra ảnh để xác định có đối tượng chưa được gán nhãn hay không.                          |
| POSSIBLE_WRONG_CLASS |          13 | Người (hàng đợi);             | Cần đối chiếu đặc điểm hình ảnh với nhãn để xác định và sửa lớp bị gán sai.                      |

 vì sao `05_review_queue.csv` xếp ảnh đầu hàng như vậy?
 Với ngân sách 80 ảnh, người xem được bao nhiêu lỗi ngữ nghĩa : Xem được 35 lỗi

## 3. Calibration (2 ngưỡng)
| Tham số | Khởi đầu | Đã chọn | Precision / Recall (trước → sau)                                                                                                                                            | Lý do (đánh đổi)                                 |
|---|---|---------|-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------|--------------------------------------------------|
| `duplicates.phash_dist` | 2 | 16      | DUP_IMAGE_EXACT 1.00 / 1.00 / 1.00  DUP_IMAGE_NEAR 1.00 / 0.50 / 0.67 -> duplicates.phash_dist=16     DUP_IMAGE_EXACT 1.00 / 1.00 / 1.00  DUP_IMAGE_NEAR 1.00 / 0.83 / 0.91 | Hiệu số Recall và F1                             |
| `second_opinion.conf` | 0.25 | 0.8     | WRONG_CLASS  0.56 / 0.83 / 0.67  MISSING      0.50 / 1.00 / 0.67  LOOSE_BOX    0.29 / 0.40 / 0.33  FALSE_POS    0.36 / 1.00 / 0.53     -> second_opinion.conf=0.8    WRONG_CLASS  1.00 / 0.83 / 0.91  MISSING      0.67 / 0.75 / 0.71  LOOSE_BOX    0.50 / 0.20 / 0.29  FALSE_POS    0.36 / 1.00 / 0.53                                  | Precision của các mục đầu tăng ưu tiên precision |

 **một chỗ calibration có thể đánh lừa bạn**, kèm bằng chứng từ dữ liệu của bạn (vd. mở xem vài cặp ảnh bị cho là trùng; số ảnh bị loại ở bước 1 có hợp lý không?).

## 4. Cửa chặn và điều pipeline KHÔNG bắt được
 (a) chứng minh gate chặn đúng: chạy `python -m pipeline.run --budget 0 --reports work/rep_nb --export-dir work/exp_nb` (không có người duyệt nên ảnh thiếu file nhãn còn nguyên), chỉ ra kết luận **Rework**, mã thoát 20 và việc **không xuất** dataset. (Đừng sửa tay `work/run/ds`: pipeline dựng lại thư mục này từ raw mỗi lần chạy.) (b) ≥ 2 điểm mù có bằng chứng (box lỏng nhẹ, nhầm lớp mà model lớn cũng nhầm, ảnh trùng biến đổi mạnh…).

**2 điểm mù**
- box lỏng nhẹ không bị bắt (POSSIBLE_LOOSE_BOX)
- ảnh trùng biến đổi mạnh (DUP_IMAGE_NEAR)

**gate chặn đúng**
- [00:55:02] Bước 1/5  Nhận dữ liệu (ảnh hỏng, kích thước, trùng, rò rỉ test)
- [00:55:03]           nhận 193/224 ảnh, loại 31
- [00:55:03] Bước 4/5  QC tự động — vòng 1 (nhãn thô)
- [00:55:03]           36 lỗi bắt buộc, 104 cảnh báo
- [00:55:03] Bước 4/5  Sửa tự động lỗi bắt buộc (ảnh chưa có nhãn -> chuyển người gán)
- [00:55:03]           35 thay đổi -> 03_fixes.csv
- [00:55:03] Bước 4/5  QC tự động — vòng 2 (sau sửa tự động)
- [00:55:03]           6 lỗi bắt buộc còn lại; hàng đợi người duyệt: 98 ảnh
- [00:55:03] Bước 3/5  Người duyệt (MÔ PHỎNG) — ngân sách 0 ảnh
- [00:55:03] Bước 4/5  QC tự động — vòng 3 (sau người duyệt) + cửa chặn
- [00:55:04]           6 sửa tự động sau người duyệt -> 03b_fixes_after_review.csv
- [00:55:04]           kết luận: REWORK — Còn 6 lỗi bắt buộc (ERROR) chưa xử lý: phải sửa trước khi phát hành.
- [00:55:04] Bước 5/5  KHÔNG xuất: còn lỗi bắt buộc (Rework) — trả về bước 3
- [00:55:04] xong trong 2.0s
- **mã thoát: 20**


## 5. Train: raw vs clean (tùy chọn, chấm riêng)
Chưa train: ghi "chưa chạy" và lý do, rồi bỏ qua phần còn lại của mục này. Nếu đã train: dán bảng từ `submission/results/comparison.md` (model, epoch, seed, số ảnh train mỗi biến thể).

 biến thể | #ảnh train | số seed | map50 (TB ± độ lệch) | map50_95 (TB ± độ lệch) | precision (TB ± độ lệch) | recall (TB ± độ lệch) |
|---|---|---|---|---|---|---|
| raw | 224 | 2 | 0.726 ± 0.000 | 0.512 ± 0.004 | 0.764 ± 0.061 | 0.649 ± 0.028 |
| clean | 193 | 2 | 0.730 ± 0.008 | 0.517 ± 0.007 | 0.767 ± 0.021 | 0.642 ± 0.009 |

Chênh mAP50 (clean − raw) = **+0.004**.

- Chênh mAP50 (clean − raw) = **-0.004**.**độ lệch chuẩn giữa các seed**; 
- kết luận **trung thực** (nằm trong nhiễu thì nói là chưa kết luận được); ≥ 2 giả thuyết giải thích (ảnh trùng/rò rỉ test trong `raw`, nhãn máy còn lại trong `clean`, test chỉ 100 ảnh…) và cách kiểm. : Chưa đủ cơ sở để khẳng định Clean tốt hơn Raw hoặc Raw tốt hơn Clean.

Mặc dù Raw đạt mAP50 trung bình 0.722, cao hơn Clean 0.718, nhưng mức chênh lệch chỉ là 0.004, trong khi độ lệch chuẩn giữa các seed lần lượt là 0.013 và 0.023.
## 6. Quyết định và ghi chú AI

**(a) quyết định cuối; nếu Hold/Rework cần làm gì để thành Release?**
-  kết luận: RELEASE — Không còn lỗi bắt buộc; 13/193 ảnh còn cảnh báo (tỉ lệ 6.74% < ngưỡng 10.00%): có thể phát hành.; Đã bỏ qua cảnh báo của các ảnh người đã duyệt (80 ảnh).
- 

**(b) Dùng AI viết code?** 
- Dùng clude code AI 

**Ghi 3 dòng:  prompt chính, cách bạn kiểm code AI, 1 lần AI sai. Không dùng: ghi "không dùng".**
  - Viết 4 file pipeline:  label_format.py  second_opinion.py gate.py autofix.py theo logic các file liên quan và theo hướng dẫn slide.


*(Thưởng +2, tùy chọn)* CVAT: lọc `width < 20`, ảnh/số box khớp, đối chiếu `BOX_TINY` (xem docs/CVAT_FILTER.md), 1 câu về `can_review`.
