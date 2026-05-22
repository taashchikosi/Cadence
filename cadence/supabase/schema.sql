-- Enable pgvector for semantic search
CREATE EXTENSION IF NOT EXISTS vector;

-- User profiles (linked to Supabase Auth)
CREATE TABLE IF NOT EXISTS user_profiles (
    id UUID PRIMARY KEY REFERENCES auth.users(id) ON DELETE CASCADE,
    role_type TEXT,
    self_identified_failure_pattern TEXT,
    typical_week_structure TEXT,
    top_3_active_goals TEXT,
    voice_preference TEXT DEFAULT 'female',
    response_mode TEXT DEFAULT 'text',
    onboarding_complete BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Daily logs
CREATE TABLE IF NOT EXISTS daily_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE,
    date DATE NOT NULL,
    execution_score INTEGER CHECK (execution_score BETWEEN 1 AND 10),
    friction_tag TEXT,
    deep_work_blocks TEXT DEFAULT '0',
    free_text TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Tasks linked to daily logs
CREATE TABLE IF NOT EXISTS tasks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    daily_log_id UUID REFERENCES daily_logs(id) ON DELETE CASCADE,
    user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE,
    description TEXT NOT NULL,
    status TEXT DEFAULT 'planned',
    is_planned BOOLEAN DEFAULT TRUE
);

-- Monday weekly inputs
CREATE TABLE IF NOT EXISTS weekly_monday_inputs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE,
    week_start_date DATE NOT NULL,
    priority_1 TEXT,
    priority_2 TEXT,
    priority_3 TEXT,
    priority_4 TEXT,
    priority_5 TEXT,
    estimated_deep_work_hours REAL,
    predicted_main_derailer TEXT,
    conversation_log JSONB DEFAULT '[]',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(user_id, week_start_date)
);

-- Friday weekly reviews
CREATE TABLE IF NOT EXISTS weekly_friday_reviews (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE,
    week_start_date DATE NOT NULL,
    priority_1_status TEXT,
    priority_2_status TEXT,
    priority_3_status TEXT,
    priority_4_status TEXT,
    priority_5_status TEXT,
    deep_work_hours REAL DEFAULT 0,
    admin_hours REAL DEFAULT 0,
    meetings_hours REAL DEFAULT 0,
    reactive_work_hours REAL DEFAULT 0,
    learning_hours REAL DEFAULT 0,
    low_leverage_hours REAL DEFAULT 0,
    weekly_execution_score INTEGER,
    reflection_text TEXT,
    conversation_log JSONB DEFAULT '[]',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(user_id, week_start_date)
);

-- Computed weekly metrics
CREATE TABLE IF NOT EXISTS weekly_metrics (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE,
    week_start_date DATE NOT NULL,
    priority_completion_rate REAL,
    deep_work_frequency REAL,
    friction_pattern_index JSONB,
    execution_score_trend JSONB,
    deferral_rate REAL,
    planning_accuracy REAL,
    avg_execution_score REAL,
    calculated_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(user_id, week_start_date)
);

-- AI generated reviews
CREATE TABLE IF NOT EXISTS ai_reviews (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE,
    week_start_date DATE NOT NULL,
    diagnosis TEXT,
    evidence TEXT,
    intervention TEXT,
    maturity_label TEXT,
    raw_response TEXT,
    patterns_detected JSONB DEFAULT '[]',
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- RAG knowledge base chunks
CREATE TABLE IF NOT EXISTS knowledge_chunks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    book_title TEXT NOT NULL,
    chunk_text TEXT NOT NULL,
    embedding VECTOR(384),
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Conversation sessions
CREATE TABLE IF NOT EXISTS conversation_sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE,
    session_type TEXT NOT NULL,
    week_start_date DATE,
    messages JSONB DEFAULT '[]',
    extracted_data JSONB DEFAULT '{}',
    status TEXT DEFAULT 'active',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Row Level Security
ALTER TABLE user_profiles ENABLE ROW LEVEL SECURITY;
ALTER TABLE daily_logs ENABLE ROW LEVEL SECURITY;
ALTER TABLE tasks ENABLE ROW LEVEL SECURITY;
ALTER TABLE weekly_monday_inputs ENABLE ROW LEVEL SECURITY;
ALTER TABLE weekly_friday_reviews ENABLE ROW LEVEL SECURITY;
ALTER TABLE weekly_metrics ENABLE ROW LEVEL SECURITY;
ALTER TABLE ai_reviews ENABLE ROW LEVEL SECURITY;
ALTER TABLE conversation_sessions ENABLE ROW LEVEL SECURITY;

-- RLS Policies (users only see their own data)
CREATE POLICY "Users manage own profile" ON user_profiles FOR ALL USING (auth.uid() = id);
CREATE POLICY "Users manage own logs" ON daily_logs FOR ALL USING (auth.uid() = user_id);
CREATE POLICY "Users manage own tasks" ON tasks FOR ALL USING (auth.uid() = user_id);
CREATE POLICY "Users manage own monday" ON weekly_monday_inputs FOR ALL USING (auth.uid() = user_id);
CREATE POLICY "Users manage own friday" ON weekly_friday_reviews FOR ALL USING (auth.uid() = user_id);
CREATE POLICY "Users manage own metrics" ON weekly_metrics FOR ALL USING (auth.uid() = user_id);
CREATE POLICY "Users manage own reviews" ON ai_reviews FOR ALL USING (auth.uid() = user_id);
CREATE POLICY "Users manage own sessions" ON conversation_sessions FOR ALL USING (auth.uid() = user_id);
CREATE POLICY "Knowledge base readable by all" ON knowledge_chunks FOR SELECT USING (TRUE);

-- Index for vector similarity search
CREATE INDEX IF NOT EXISTS knowledge_chunks_embedding_idx
    ON knowledge_chunks USING ivfflat (embedding vector_cosine_ops)
    WITH (lists = 100);
