CREATE TABLE IF NOT EXISTS users (
    id UUID PRIMARY KEY,
    email TEXT UNIQUE NOT NULL,
    display_name TEXT,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS projects (
    id UUID PRIMARY KEY,
    user_id UUID REFERENCES users(id),
    title TEXT NOT NULL,
    description TEXT NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS analysis_tasks (
    id UUID PRIMARY KEY,
    project_id UUID REFERENCES projects(id),
    status TEXT NOT NULL,
    correlation_id UUID NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    started_at TIMESTAMP,
    finished_at TIMESTAMP
);

CREATE TABLE IF NOT EXISTS risk_items (
    id UUID PRIMARY KEY,
    task_id UUID REFERENCES analysis_tasks(id),
    category TEXT NOT NULL,
    title TEXT NOT NULL,
    probability TEXT NOT NULL,
    impact TEXT NOT NULL,
    score INTEGER NOT NULL,
    priority TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS report_metadata (
    id UUID PRIMARY KEY,
    task_id UUID REFERENCES analysis_tasks(id),
    storage_uri TEXT NOT NULL,
    format TEXT NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_analysis_tasks_status ON analysis_tasks(status);
CREATE INDEX IF NOT EXISTS idx_analysis_tasks_project_id ON analysis_tasks(project_id);
CREATE INDEX IF NOT EXISTS idx_risk_items_task_id ON risk_items(task_id);
CREATE INDEX IF NOT EXISTS idx_report_metadata_task_id ON report_metadata(task_id);
