-- ────────────── 1️⃣ Populate 20 sample users ──────────────
INSERT INTO USER (email, password_hash, user_type, created_at) VALUES
('user1@example.com','hash1','standard',NOW()),
('user2@example.com','hash2','standard',NOW()),
('user3@example.com','hash3','standard',NOW()),
('user4@example.com','hash4','standard',NOW()),
('user5@example.com','hash5','standard',NOW()),
('user6@example.com','hash6','standard',NOW()),
('user7@example.com','hash7','standard',NOW()),
('user8@example.com','hash8','standard',NOW()),
('user9@example.com','hash9','standard',NOW()),
('user10@example.com','hash10','standard',NOW()),
('user11@example.com','hash11','standard',NOW()),
('user12@example.com','hash12','standard',NOW()),
('user13@example.com','hash13','standard',NOW()),
('user14@example.com','hash14','standard',NOW()),
('user15@example.com','hash15','standard',NOW()),
('user16@example.com','hash16','standard',NOW()),
('user17@example.com','hash17','standard',NOW()),
('user18@example.com','hash18','standard',NOW()),
('user19@example.com','hash19','standard',NOW()),
('user20@example.com','hash20','standard',NOW());

-- ────────────── 2️⃣ Populate 20 sample meals ──────────────
INSERT INTO MEAL (meal_name, meal_datetime, total_calories, user_id) VALUES
('Breakfast', NOW(), 350, 1),
('Lunch', NOW(), 600, 2),
('Dinner', NOW(), 500, 3),
('Snack', NOW(), 200, 4),
('Breakfast', NOW(), 300, 5),
('Lunch', NOW(), 650, 6),
('Dinner', NOW(), 550, 7),
('Snack', NOW(), 150, 8),
('Breakfast', NOW(), 400, 9),
('Lunch', NOW(), 700, 10),
('Dinner', NOW(), 500, 11),
('Snack', NOW(), 220, 12),
('Breakfast', NOW(), 360, 13),
('Lunch', NOW(), 620, 14),
('Dinner', NOW(), 530, 15),
('Snack', NOW(), 180, 16),
('Breakfast', NOW(), 380, 17),
('Lunch', NOW(), 640, 18),
('Dinner', NOW(), 510, 19),
('Snack', NOW(), 200, 20);

-- ────────────── 3️⃣ Populate 20 sample workouts ──────────────
INSERT INTO WORKOUT (workout_name, duration_min, user_id) VALUES
('Running',30,1),('Cycling',45,2),('Yoga',60,3),('Swimming',40,4),
('Weights',50,5),('Pilates',30,6),('Running',35,7),('Cycling',50,8),
('Yoga',55,9),('Swimming',45,10),('Weights',60,11),('Pilates',30,12),
('Running',25,13),('Cycling',40,14),('Yoga',60,15),('Swimming',50,16),
('Weights',45,17),('Pilates',35,18),('Running',30,19),('Cycling',40,20);

-- ────────────── 4️⃣ Populate 20 sample progress records ──────────────
INSERT INTO PROGRESS (date_logged, weight_kg, user_id) VALUES
('2026-04-01',70,1),('2026-04-01',65,2),('2026-04-01',80,3),('2026-04-01',75,4),
('2026-04-01',68,5),('2026-04-01',72,6),('2026-04-01',78,7),('2026-04-01',74,8),
('2026-04-01',69,9),('2026-04-01',71,10),('2026-04-01',73,11),('2026-04-01',76,12),
('2026-04-01',70,13),('2026-04-01',67,14),('2026-04-01',79,15),('2026-04-01',81,16),
('2026-04-01',72,17),('2026-04-01',74,18),('2026-04-01',75,19),('2026-04-01',77,20);