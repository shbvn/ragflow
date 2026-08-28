#
#  SHBVN fork test: the mechanical "Nguồn:" source-line hook in
#  dialog_service (SHBVN CUSTOMIZATION markers) and the streaming delivery
#  contract it relies on. The label-extraction logic itself is tested in
#  shbvn_core; here the fork-side wiring is what must not regress:
#  the hook binds against shbvn_core, understands the raw ES chunk field
#  names it is called with, and the extra streamed delta survives into the
#  persisted conversation message.
#

import time
import types

import api.db.services.dialog_service as dialog_service
from api.db.services.conversation_service import structure_answer

RAW_CHUNKS = [
    {
        "docnm_kwd": "01-quy-dinh-giao-dich-tien-mat.docx",
        "content_with_weight": (
            "Điều 4. Hạn mức thu chi của giao dịch viên\n"
            "1. Hạn mức giao dịch trong ngày tối đa là 200.000.000 VNĐ."
        ),
    },
]


def test_hook_binds_when_shbvn_core_is_present():
    assert dialog_service._shbvn_source_line is not None


def test_hook_reads_raw_es_chunk_fields():
    # decorate_answer passes kbinfos["chunks"] untouched, so the builder must
    # accept docnm_kwd / content_with_weight rather than the formatted names
    line = dialog_service._shbvn_source_line(
        "Hạn mức là 200.000.000 VNĐ [ID:0].", RAW_CHUNKS
    )
    assert line == (
        "Nguồn: 01-quy-dinh-giao-dich-tien-mat.docx — "
        "Điều 4. Hạn mức thu chi của giao dịch viên"
    )


def test_uncited_answer_produces_no_line():
    assert dialog_service._shbvn_source_line("Không trích dẫn.", RAW_CHUNKS) == ""


def _conv():
    return types.SimpleNamespace(
        message=[{"role": "user", "content": "câu hỏi", "id": "q1",
                  "created_at": time.time()}],
        reference=[{}],
    )


def test_streamed_source_delta_survives_into_persisted_message():
    # the hook ships the source line as one extra non-final delta because the
    # final streaming payload carries an empty answer by upstream contract;
    # structure_answer must append the delta and the final must keep it
    conv = _conv()
    for delta in ("Hạn mức là 200 triệu [ID:0].", "\n\nNguồn: 01-quy-dinh-giao-dich-tien-mat.docx — Điều 4."):
        structure_answer(
            conv,
            {"answer": delta, "reference": {}, "final": False},
            "m1", "s1",
        )
    structure_answer(
        conv,
        {"answer": "", "reference": {"chunks": [], "doc_aggs": []}, "final": True},
        "m1", "s1",
    )
    assistant = conv.message[-1]
    assert assistant["role"] == "assistant"
    assert assistant["content"].endswith("Nguồn: 01-quy-dinh-giao-dich-tien-mat.docx — Điều 4.")
    assert assistant["content"].startswith("Hạn mức là 200 triệu")
