-- Enable pgvector for embeddings
CREATE EXTENSION IF NOT EXISTS vector;

-- Enable UUID generation
CREATE EXTENSION IF NOT EXISTS pgcrypto;

-- Verify extensions
DO $$
BEGIN
  RAISE NOTICE 'Extensions installed: vector, pgcrypto';
END $$;