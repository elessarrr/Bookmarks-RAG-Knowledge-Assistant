from dataclasses import dataclass
from typing import List
import nltk

@dataclass
class Chunk:
    text: str
    chunk_index: int
    start_char_idx: int
    end_char_idx: int

def chunk_text(text: str, chunk_size: int = 400, overlap: int = 50) -> List[Chunk]:
    """
    Splits text into chunks of approximately `chunk_size` tokens (estimated by words/chars).
    Respects sentence boundaries using nltk.
    """
    if not text.strip():
        return []

    try:
        nltk.data.find('tokenizers/punkt')
    except LookupError:
        nltk.download('punkt', quiet=True)
        nltk.download('punkt_tab', quiet=True) # Ensure punkt_tab is also downloaded if needed by newer nltk

    sentences = nltk.sent_tokenize(text)
    
    chunks: List[Chunk] = []
    current_chunk_sentences: List[str] = []
    current_chunk_len = 0
    
    # We use a sliding window approach with sentences
    # But since sentences vary wildly in length, we accumulate until we hit chunk_size
    # Then we backtrack for overlap if needed.
    
    # Actually, simpler approach for "accumulate until token count reaches chunk size":
    # 1. Iterate sentences.
    # 2. Add sentence to current buffer.
    # 3. If buffer exceeds chunk_size, emit chunk.
    # 4. For next chunk, keep last N sentences that sum up to `overlap` size.
    
    # Let's map sentences to their approximate token counts first to make it easier
    sent_data = []
    current_char_idx = 0
    
    for sent in sentences:
        # Simple word split for token count estimation
        # Real tokenizers (tiktoken/bert) are slower, this is "good enough" for RAG usually
        token_count = len(sent.split())
        start = text.find(sent, current_char_idx)
        # If not found (shouldn't happen with exact match), fallback
        if start == -1: 
            start = current_char_idx
        
        end = start + len(sent)
        current_char_idx = end
        
        sent_data.append({
            "text": sent,
            "tokens": token_count,
            "start": start,
            "end": end
        })

    i = 0
    chunk_idx = 0
    
    while i < len(sent_data):
        current_tokens = 0
        chunk_sentences: List[dict] = []
        chunk_start_idx = sent_data[i]["start"]
        
        # Start new chunk
        j = i
        while j < len(sent_data):
            sent = sent_data[j]
            # If adding this sentence keeps us under chunk_size OR it's the very first sentence of the chunk
            # (we don't want to skip a sentence just because it's longer than chunk_size alone)
            if current_tokens + sent["tokens"] <= chunk_size or not chunk_sentences:
                chunk_sentences.append(sent)
                current_tokens += sent["tokens"]
                j += 1
            else:
                break
        
        # Create chunk object
        chunk_text_str = " ".join([s["text"] for s in chunk_sentences])
        chunk_end_idx = chunk_sentences[-1]["end"]
        
        chunks.append(Chunk(
            text=chunk_text_str,
            chunk_index=chunk_idx,
            start_char_idx=chunk_start_idx,
            end_char_idx=chunk_end_idx
        ))
        chunk_idx += 1
        
        # Calculate where to start next chunk (overlap)
        # We want to go back from j until we cover `overlap` tokens
        if j >= len(sent_data):
            break
            
        overlap_tokens = 0
        next_start_i = j
        
        # Walk backwards from the sentence that caused the break (sent_data[j])
        # to find how many previous sentences we should include in the next chunk
        # But wait, overlap is usually "previous chunk's tail". 
        # So we look at chunk_sentences (which are 0 to j-1)
        # We want the *next* chunk to start such that it repeats the last `overlap` tokens of *this* chunk.
        
        k = len(chunk_sentences) - 1
        while k >= 0:
            overlap_tokens += chunk_sentences[k]["tokens"]
            if overlap_tokens >= overlap:
                # We found enough overlap. 
                # The next chunk should start at this sentence index (i + k)
                # But we want to ensure we advance at least by 1 sentence to avoid infinite loops
                # if the overlap is huge or sentence is huge.
                next_start_i = i + k
                break
            k -= 1
        
        # Ensure progress
        if next_start_i <= i:
            next_start_i = i + 1
            
        i = next_start_i

    return chunks
