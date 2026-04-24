-- ══════════════════════════════════════════════════════════════
--  FitTrack Schema Fix
--  Run this once to align your DB with the Flask app.
--  Safe to run even if some columns already exist.
-- ══════════════════════════════════════════════════════════════

-- ── 1. USER ───────────────────────────────────────────────────
--  Fix: primary key needs AUTO_INCREMENT
--  Fix: user_type values in sample data are 'standard'; app uses 'regular'
ALTER TABLE USER MODIFY COLUMN user_id INT NOT NULL AUTO_INCREMENT;

UPDATE USER SET user_type = 'regular' WHERE user_type = 'standard';


-- ── 2. MEAL ───────────────────────────────────────────────────
--  Fix: primary key needs AUTO_INCREMENT
ALTER TABLE MEAL MODIFY COLUMN meal_id INT NOT NULL AUTO_INCREMENT;


-- ── 3. WORKOUT ────────────────────────────────────────────────
--  Fix: primary key needs AUTO_INCREMENT
--  Fix: rename workout_name → no equivalent needed (app doesn't use it), add missing columns
ALTER TABLE WORKOUT MODIFY COLUMN workout_id INT NOT NULL AUTO_INCREMENT;

-- Add workout_datetime if missing (use existing data as a placeholder)
ALTER TABLE WORKOUT ADD COLUMN IF NOT EXISTS workout_datetime DATETIME DEFAULT NOW();

-- Add total_calories_burned if missing
ALTER TABLE WORKOUT ADD COLUMN IF NOT EXISTS total_calories_burned INT DEFAULT NULL;

-- Backfill workout_datetime from created_at or just set to now for existing rows
UPDATE WORKOUT SET workout_datetime = NOW() WHERE workout_datetime IS NULL;


-- ── 4. PROGRESS ───────────────────────────────────────────────
--  Fix: primary key needs AUTO_INCREMENT
--  Fix: rename date_logged → progress_date, weight_kg → body_weight
--  Fix: add missing columns body_fat_percent, notes
ALTER TABLE PROGRESS MODIFY COLUMN progress_id INT NOT NULL AUTO_INCREMENT;

-- Rename date_logged → progress_date (skip if already done)
ALTER TABLE PROGRESS CHANGE COLUMN date_logged progress_date DATE NOT NULL;

-- Rename weight_kg → body_weight (stored as lbs in app, but just renaming the column)
ALTER TABLE PROGRESS CHANGE COLUMN weight_kg body_weight DECIMAL(5,2) DEFAULT NULL;

-- Add missing columns
ALTER TABLE PROGRESS ADD COLUMN IF NOT EXISTS body_fat_percent DECIMAL(4,2) DEFAULT NULL;
ALTER TABLE PROGRESS ADD COLUMN IF NOT EXISTS notes TEXT DEFAULT NULL;


-- ── 5. EXERCISE ───────────────────────────────────────────────
--  Fix: primary key needs AUTO_INCREMENT (if table exists)
ALTER TABLE EXERCISE MODIFY COLUMN exercise_id INT NOT NULL AUTO_INCREMENT;


-- ── 6. FOOD ───────────────────────────────────────────────────
--  Fix: primary key needs AUTO_INCREMENT (if table exists)
ALTER TABLE FOOD MODIFY COLUMN food_id INT NOT NULL AUTO_INCREMENT;


-- ══════════════════════════════════════════════════════════════
--  Verify — run these SELECTs to confirm everything looks right
-- ══════════════════════════════════════════════════════════════
-- SHOW COLUMNS FROM USER;
-- SHOW COLUMNS FROM MEAL;
-- SHOW COLUMNS FROM WORKOUT;
-- SHOW COLUMNS FROM PROGRESS;
-- SHOW COLUMNS FROM EXERCISE;
-- SHOW COLUMNS FROM FOOD;