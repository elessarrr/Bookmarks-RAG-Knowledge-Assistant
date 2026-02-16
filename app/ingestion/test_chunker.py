from app.ingestion.chunker import chunk_text

def test_chunk_short_text():
    text = "This is a short text. It should fit in one chunk."
    chunks = chunk_text(text, chunk_size=100, overlap=10)
    assert len(chunks) == 1
    assert chunks[0].text == text
    assert chunks[0].chunk_index == 0

def test_chunk_respects_token_limit():
    # Create a long text with distinct sentences
    sentences = [f"This is sentence number {i}." for i in range(50)]
    text = " ".join(sentences)
    
    # Approx 5 words per sentence. 50 sentences = 250 words.
    # Chunk size 50 words. Should get ~5 chunks.
    chunks = chunk_text(text, chunk_size=50, overlap=0)
    
    assert len(chunks) > 1
    for chunk in chunks:
        # Crude token count (words)
        word_count = len(chunk.text.split())
        # It won't be exact, but shouldn't exceed significantly
        assert word_count <= 60  # Allow some buffer for sentence completion

def test_chunk_overlap():
    text = "Sentence one. Sentence two. Sentence three. Sentence four. Sentence five."
    # Chunk size small enough to force split
    # "Sentence one." is 2 words. 5 sentences = 10 words.
    # If chunk_size is 4, we should definitely split.
    chunks = chunk_text(text, chunk_size=4, overlap=2) 
    
    assert len(chunks) > 1
    # Check if end of chunk 0 overlaps with start of chunk 1
    # Note: Logic depends on implementation (sliding window of sentences)
    # If overlap is 5 tokens, and sentences are short, we expect shared sentences.
    
    chunk0_text = chunks[0].text
    chunk1_text = chunks[1].text
    
    # There should be some common text
    common = set(chunk0_text.split()) & set(chunk1_text.split())
    assert len(common) > 0

def test_no_mid_sentence_splits():
    long_sentence = "This is a very long sentence that should hopefully stay together in one piece and not be split in the middle unless it is absolutely larger than the chunk size itself which is unlikely here."
    text = f"Short one. {long_sentence} Short two."
    
    chunks = chunk_text(text, chunk_size=20, overlap=5)
    
    # The long sentence might force a chunk boundary check.
    # We want to ensure the long sentence appears intact in at least one chunk (or across chunks but not cut mid-word/mid-sentence if possible, though strict token limits might force it).
    # Our requirement says "no mid-sentence splits".
    
    found_intact = False
    for chunk in chunks:
        if long_sentence in chunk.text:
            found_intact = True
            break
    
    assert found_intact

def test_empty_text():
    chunks = chunk_text("")
    assert chunks == []
