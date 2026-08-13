#
#  Copyright 2024 The InfiniFlow Authors. All Rights Reserved.
#
#  Licensed under the Apache License, Version 2.0 (the "License");
#  you may not use this file except in compliance with the License.
#  You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
#  Unless required by applicable law or agreed to in writing, software
#  distributed under the License is distributed on an "AS IS" BASIS,
#  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#  See the License for the specific language governing permissions and
#  limitations under the License.
#

import infinity.rag_tokenizer

# === SHBVN CUSTOMIZATION START ===
# Vietnamese-aware tokenization: the upstream splitter is ASCII-only and
# shatters accented Latin into per-letter tokens ("đ i ề u"), killing the
# BM25/keyword leg for Vietnamese. Tokenization logic lives in shbvn_core;
# this file only routes Vietnamese-bearing text to it. shbvn_core ships
# separately from this fork (workspace dev install / offline bundle):
# when it is absent the hook must vanish and upstream behavior stay
# intact, so a missing package downgrades to no Vietnamese routing
# instead of killing rag.nlp at import.
try:
    from shbvn_core.nlp import (
        contains_vietnamese,
        fine_grained_vietnamese,
        tokenize_mixed,
    )
except ImportError:
    contains_vietnamese = None
    fine_grained_vietnamese = None
    tokenize_mixed = None
# === SHBVN CUSTOMIZATION END ===


class RagTokenizer(infinity.rag_tokenizer.RagTokenizer):
    def tokenize(self, line: str) -> str:
        from common import settings  # moved from the top of the file to avoid circular import

        if settings.DOC_ENGINE_INFINITY:
            return line
        else:
            # === SHBVN CUSTOMIZATION START ===
            if contains_vietnamese is not None and contains_vietnamese(line):
                return tokenize_mixed(line, fallback=super().tokenize)
            # === SHBVN CUSTOMIZATION END ===
            return super().tokenize(line)

    def fine_grained_tokenize(self, tks: str) -> str:
        from common import settings  # moved from the top of the file to avoid circular import

        if settings.DOC_ENGINE_INFINITY:
            return tks
        else:
            # === SHBVN CUSTOMIZATION START ===
            if contains_vietnamese is not None and contains_vietnamese(tks):
                return fine_grained_vietnamese(tks, fallback=super().fine_grained_tokenize)
            # === SHBVN CUSTOMIZATION END ===
            return super().fine_grained_tokenize(tks)


def is_chinese(s):
    return infinity.rag_tokenizer.is_chinese(s)


def is_number(s):
    return infinity.rag_tokenizer.is_number(s)


def is_alphabet(s):
    return infinity.rag_tokenizer.is_alphabet(s)


def naive_qie(txt):
    return infinity.rag_tokenizer.naive_qie(txt)


tokenizer = RagTokenizer()
tokenize = tokenizer.tokenize
fine_grained_tokenize = tokenizer.fine_grained_tokenize
tag = tokenizer.tag
freq = tokenizer.freq
tradi2simp = tokenizer._tradi2simp
strQ2B = tokenizer._strQ2B
