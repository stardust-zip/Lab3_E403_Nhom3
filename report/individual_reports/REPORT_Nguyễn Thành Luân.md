# Individual Report: Lab 3 - Chatbot vs ReAct Agent

- **Student Name**: Nguyen Thanh Luan
- **Student ID**: 2A202600204
- **Date**: 2026-04-06

---

## I. Technical Contribution (15 Points)

Trong chu kỳ lab này, đóng góp chính của tôi tập trung vào: vẽ flowchart cho vòng lặp ReAct, lựa chọn và tinh chỉnh bộ test case đánh giá, cập nhật trace sau mỗi lần chạy, và tổng hợp kết quả vào báo cáo cuối.

- **Modules / Artifacts Contributed**:
  - Flowchart và trực quan hóa logic: [report/group_report/flowcharts.md](../group_report/flowcharts.md)
  - Cập nhật test case và trace theo từng bước: [report/group_report/trace.md](../group_report/trace.md)
  - Tổng hợp đầu ra test để đối chiếu: [logs/test_results_new.json](../../logs/test_results_new.json)
  - Báo cáo kỹ thuật và phân tích của nhóm: [report/group_report/GROUP_REPORT_Nhom3.md](../group_report/GROUP_REPORT_Nhom3.md)
  - Đối chiếu với tiêu chí đánh giá: [EVALUATION.md](../../EVALUATION.md), [SCORING.md](../../SCORING.md)

- **Mối liên hệ với vòng lặp ReAct**:
  - Tôi chuyển hóa luồng Thought -> Action -> Observation -> Final Answer thành flowchart để nhóm nhìn rõ điểm dừng và điểm có thể lỗi.
  - Tôi thiết kế 5 test case có tính bao phủ (hỏi sự kiện đơn giản, liệt kê, tìm theo ràng buộc, tính giá combo có khuyến mãi, và từ chối ngoài phạm vi).
  - Tôi cập nhật trace sau mỗi lần rerun để phản ánh đúng quy trình agent, đồng thời điều chỉnh kết quả mong đợi khi hành vi thay đổi giữa v1 và v2.
  - Tôi liên kết bằng chứng trace với kết luận cuối cùng trong báo cáo (tỷ lệ thành công, đổi-đối giữa chi phí-chất lượng, và nguyên nhân gốc rễ).

---

## II. Debugging Case Study (10 Points)

Tôi phân tích lỗi logic quan trọng: tính tổng tiền combo kèm mã khuyến mãi ở Test Case 4.

- **Problem Description**:
  - Câu hỏi: Mua iPhone 17 Pro + ốp lưng + kính cường lực, áp dụng mã HSSV2026.
  - Quan sát ở v1: tổng tiền cuối tính sai vì luồng suy luận chưa áp dụng ổn định quy tắc tính giá cho toàn bộ thành phần trong giỏ hàng.

- **Diagnosis**:
  - Nguyên nhân gốc chủ yếu đến từ chất lượng suy luận ở tầng prompt, không phải lỗi runtime.
  - v1 thiếu few-shot hướng dẫn đủ mạnh cho bài toán nhiều món + mã giảm giá, nên quy trình suy luận kém ổn định ở các case tính giá phức tạp.
  - Vấn đề biểu hiện dưới dạng lệch logic nghiệp vụ, không phải exception parser/tool.

- **Solution**:
  - Nâng cấp prompt v2 với ví dụ minh họa rõ ràng cho combo + giảm giá và mẫu trả lời ngoài phạm vi.
  - Bổ sung parser action và guardrail mạnh hơn (nhiều pattern parse, gợi ý retry, xử lý action trùng lặp) để tăng độ ổn định quãng đường suy luận.
  - Chạy lại bộ test và cập nhật trace/kết quả để xác minh cải tiến trước khi chốt kết luận báo cáo.

---

## III. Personal Insights: Chatbot vs ReAct (10 Points)

Dựa trên kết quả đo lường và trace của lab, tôi rút ra các nhận định sau:

1.  **Reasoning**: How did the `Thought` block help the agent compared to a direct Chatbot answer?
  - Khối Thought giúp phân rã yêu cầu phức tạp thành các bước nhỏ có thể thực thi, đồng thời bắt buộc grounding qua tool. Đây là lý do chính giúp agent vượt chatbot ở bài toán tìm kiếm có ràng buộc và tính giá.
2.  **Reliability**: In which cases did the Agent actually perform *worse* than the Chatbot?
  - Ở các câu hỏi sự kiện đơn giản, chatbot nhanh và tiết kiệm token hơn nhưng vẫn đúng (ví dụ: iPhone thuộc hãng nào). ReAct tạo thêm độ trễ/token không cần thiết với đề bài dễ.
3.  **Observation**: How did the environment feedback (observations) influence the next steps?
  - Observation là tín hiệu điều khiển cho action tiếp theo. Khi observation rõ ràng và grounded, agent hội tụ tốt. Khi quy trình bị lặp hoặc mơ hồ, cần guardrail và ví dụ để ép kết thúc an toàn.

Nhận xét bổ sung:
- ReAct không phải lúc nào cũng "tốt hơn"; nó tốt hơn khi bài toán cần grounding và kết hợp nhiều bước.
- Trace chất lượng cao quan trọng ngang với câu trả lời đúng vì nó cho thấy chính xác điểm suy luận lệch khỏi quy tắc nghiệp vụ.
- Chất lượng tài liệu hóa (flowchart + trace + RCA) giúp nhóm lặp nhanh hơn và giảm debug mơ hồ.

---

## IV. Future Improvements (5 Points)

Để mở rộng prototype này lên mức production:

- **Scalability**:
  - Chuyển logic tồn kho và khuyến mãi từ mock tĩnh sang backend API có giao dịch.
  - Thêm cơ chế cache cho các tool call lặp lại và tra cứu giá.
  - Đưa vào workflow orchestration cho tác vụ dài (planner-executor hoặc graph-based agent flow).

- **Safety**:
  - Ràng buộc schema tool chặt chẽ hơn và xác thực quy tắc nghiệp vụ ngay tại tầng tool (không chỉ dựa vào prompt).
  - Bổ sung policy check trước khi trả ra giá cuối.
  - Duy trì cảnh báo bất thường dựa trên telemetry cho mẫu loop/hallucination action.

- **Performance**:
  - Dynamic routing: dùng chatbot cho intent đơn giản, dùng ReAct cho intent cần grounding/nhiều bước.
  - Nén prompt và chỉ truy xuất các ví dụ liên quan.
  - Đánh giá offline theo lô trong CI để phát hiện hồi quy trên 5 test case chuẩn.
