-- Schema for class_dataset.csv (student intake responses)
--
-- Entities:
--   students              one row per student (scalar attributes)
--   tools                 each distinct tool, stored once
--   availability_slots    each distinct availability option, stored once
--
-- Relationships:
--   students <-> tools               many-to-many  -> bridge table student_tools
--   students <-> availability_slots  many-to-many  -> bridge table student_availability
--
-- `tools` and `availability` hold several semicolon-separated values per cell
-- in the CSV, so they are split out into their own tables instead of text columns.

-- Drop in reverse dependency order (bridges first) so the file can be re-run.
DROP TABLE IF EXISTS student_availability;
DROP TABLE IF EXISTS student_tools;
DROP TABLE IF EXISTS availability_slots;
DROP TABLE IF EXISTS tools;
DROP TABLE IF EXISTS students;

-- Parent tables -------------------------------------------------------------

CREATE TABLE students (
    student_id             SERIAL PRIMARY KEY,          -- generated; names can repeat
    netid                  TEXT NOT NULL,
    name                   TEXT NOT NULL,
    school_year            TEXT,
    intro_programming      TEXT,
    skill_programming      SMALLINT CHECK (skill_programming     BETWEEN 1 AND 5),
    skill_data_stats       SMALLINT CHECK (skill_data_stats      BETWEEN 1 AND 5),
    skill_frontend_design  SMALLINT CHECK (skill_frontend_design BETWEEN 1 AND 5),
    skill_business_pitch   SMALLINT CHECK (skill_business_pitch  BETWEEN 1 AND 5),
    working_style          TEXT,
    interests              TEXT,
    semester_goal          TEXT,
    submitted_at           TIMESTAMPTZ                  -- timestamp with timezone, not text
);

CREATE TABLE tools (
    id    SERIAL PRIMARY KEY,
    name  TEXT NOT NULL UNIQUE
);

CREATE TABLE availability_slots (
    id    SERIAL PRIMARY KEY,
    name  TEXT NOT NULL UNIQUE
);

-- Bridge tables (many-to-many) ---------------------------------------------

CREATE TABLE student_tools (
    student_id  INT NOT NULL REFERENCES students(student_id) ON DELETE CASCADE,
    tool_id     INT NOT NULL REFERENCES tools(id)            ON DELETE CASCADE,
    PRIMARY KEY (student_id, tool_id)
);

CREATE TABLE student_availability (
    student_id  INT NOT NULL REFERENCES students(student_id)    ON DELETE CASCADE,
    slot_id     INT NOT NULL REFERENCES availability_slots(id)  ON DELETE CASCADE,
    PRIMARY KEY (student_id, slot_id)
);
