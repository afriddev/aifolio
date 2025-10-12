CREATE TABLE 
        chunks(
            id UUID PRIMARY KEY DEFAULT uuid_generate_v4 (),
            text TEXT NOT NULL,
            embedding VECTOR(1024) NOT NULL
)

CREATE TABLE 
        questions(            
            id UUID PRIMARY KEY DEFAULT uuid_generate_v4 (),
            chunk_id UUID NOT NULL,
            text TEXT NOT NULL,
            embedding VECTOR(1024) NOT NULL
)




--     CREATE INDEX idx_chunkq_vec_hnsw
--     ON chunk_questions USING hnsw (embedding vector_cosine_ops)
-- WITH
--     (m = 16, ef_construction = 300
--     );