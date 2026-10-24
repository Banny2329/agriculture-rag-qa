"""文本分块：按标点切句后合并为约 chunk_size 长度的块，块间保留 overlap 字符防语义断裂。"""
import re

_SENT_SPLIT = re.compile(r"(?<=[。！？；\n])")


def chunk_text(text: str, chunk_size: int = 500, overlap: int = 50) -> list[str]:
    """将整页文本切成若干块。chunk_size 为块的目标字符数。"""
    chunks: list[str] = []
    current: list[str] = []
    current_len = 0

    sentences = [s.strip() for s in _SENT_SPLIT.split(text) if s.strip()]

    for sent in sentences:
        # 超长单句（如连续表格/无标点段落）直接硬切
        while len(sent) > chunk_size:
            if current:
                chunks.append("".join(current))
                tail = "".join(current)[-overlap:]
                current, current_len = [tail], len(tail)
            chunks.append(sent[:chunk_size])
            sent = sent[chunk_size:]

        if current_len + len(sent) > chunk_size:
            # 收尾当前块，并用其末尾 overlap 字符作为下一块开头
            chunks.append("".join(current))
            tail = "".join(current)[-overlap:]
            current, current_len = ([tail] if tail else []), len(tail)
        current.append(sent)
        current_len += len(sent)

    if current:
        chunks.append("".join(current))
    return chunks
