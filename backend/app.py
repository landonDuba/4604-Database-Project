from flask import Flask, request, jsonify
from flask_cors import CORS
import mysql.connector
import os

app = Flask(__name__)
CORS(app)

# ── DB CONFIG ─────────────────────────────────────────────────────────────────
# Change these to match your MySQL credentials
DB_CONFIG = {
    "host": "localhost",
    "user": "root",
    "password": "password",
    "database": "fitness_db",
}

def get_db():
    return mysql.connector.connect(**DB_CONFIG)

def query(sql, params=(), fetchone=False, commit=False):
    conn = get_db()
    cur = conn.cursor(dictionary=True)
    cur.execute(sql, params)
    if commit:
        conn.commit()
        last_id = cur.lastrowid
        cur.close(); conn.close()
        return last_id
    result = cur.fetchone() if fetchone else cur.fetchall()
    cur.close(); conn.close()
    return result


# ── USERS ─────────────────────────────────────────────────────────────────────
@app.route("/api/users", methods=["GET"])
def get_users():
    return jsonify(query("SELECT * FROM USER ORDER BY user_id"))

@app.route("/api/users", methods=["POST"])
def create_user():
    d = request.json
    last_id = query(
        "INSERT INTO USER (email, password_hash, user_type, created_at) VALUES (%s,%s,%s,%s)",
        (d["email"], d["password_hash"], d["user_type"], d["created_at"]),
        commit=True
    )
    return jsonify({"user_id": last_id}), 201

@app.route("/api/users/<int:uid>", methods=["PUT"])
def update_user(uid):
    d = request.json
    query(
        "UPDATE USER SET email=%s, password_hash=%s, user_type=%s WHERE user_id=%s",
        (d["email"], d["password_hash"], d["user_type"], uid),
        commit=True
    )
    return jsonify({"success": True})

@app.route("/api/users/<int:uid>", methods=["DELETE"])
def delete_user(uid):
    try:
        # First, delete all meals for this user to avoid foreign key errors
        query("DELETE FROM MEAL WHERE user_id=%s", (uid,), commit=True)
        
        # Now delete the user
        query("DELETE FROM USER WHERE user_id=%s", (uid,), commit=True)
        return jsonify({"success": True})
    except mysql.connector.IntegrityError as e:
        # If some other FK error occurs
        return jsonify({"success": False, "error": str(e)}), 400


# ── MEALS ─────────────────────────────────────────────────────────────────────
@app.route("/api/meals", methods=["GET"])
def get_meals():
    return jsonify(query(
        "SELECT m.*, u.email FROM MEAL m JOIN USER u ON m.user_id=u.user_id ORDER BY m.meal_datetime DESC"
    ))

@app.route("/api/meals", methods=["POST"])
def create_meal():
    d = request.json
    last_id = query(
        "INSERT INTO MEAL (user_id, meal_datetime, meal_name, total_calories) VALUES (%s,%s,%s,%s)",
        (d["user_id"], d["meal_datetime"], d["meal_name"], d["total_calories"]), commit=True
    )
    return jsonify({"meal_id": last_id}), 201

@app.route("/api/meals/<int:mid>", methods=["PUT"])
def update_meal(mid):
    d = request.json
    query("UPDATE MEAL SET meal_datetime=%s, meal_name=%s, total_calories=%s WHERE meal_id=%s",
          (d["meal_datetime"], d["meal_name"], d["total_calories"], mid), commit=True)
    return jsonify({"success": True})

@app.route("/api/meals/<int:mid>", methods=["DELETE"])
def delete_meal(mid):
    query("DELETE FROM MEAL WHERE meal_id=%s", (mid,), commit=True)
    return jsonify({"success": True})


# ── FOOD ──────────────────────────────────────────────────────────────────────
@app.route("/api/foods", methods=["GET"])
def get_foods():
    return jsonify(query("SELECT * FROM FOOD ORDER BY food_name"))

@app.route("/api/foods", methods=["POST"])
def create_food():
    d = request.json
    last_id = query(
        "INSERT INTO FOOD (food_name, calories_per_serving, protein_g, carbs_g, fat_g, fiber_g) VALUES (%s,%s,%s,%s,%s,%s)",
        (d["food_name"], d["calories_per_serving"], d["protein_g"], d["carbs_g"], d["fat_g"], d.get("fiber_g")), commit=True
    )
    return jsonify({"food_id": last_id}), 201

@app.route("/api/foods/<int:fid>", methods=["PUT"])
def update_food(fid):
    d = request.json
    query("UPDATE FOOD SET food_name=%s, calories_per_serving=%s, protein_g=%s, carbs_g=%s, fat_g=%s, fiber_g=%s WHERE food_id=%s",
          (d["food_name"], d["calories_per_serving"], d["protein_g"], d["carbs_g"], d["fat_g"], d.get("fiber_g"), fid), commit=True)
    return jsonify({"success": True})

@app.route("/api/foods/<int:fid>", methods=["DELETE"])
def delete_food(fid):
    query("DELETE FROM FOOD WHERE food_id=%s", (fid,), commit=True)
    return jsonify({"success": True})


# ── WORKOUTS ──────────────────────────────────────────────────────────────────
@app.route("/api/workouts", methods=["GET"])
def get_workouts():
    return jsonify(query(
        "SELECT w.*, u.email FROM WORKOUT w JOIN USER u ON w.user_id=u.user_id ORDER BY w.workout_datetime DESC"
    ))

@app.route("/api/workouts", methods=["POST"])
def create_workout():
    d = request.json
    last_id = query(
        "INSERT INTO WORKOUT (user_id, workout_datetime, duration_min, total_calories_burned) VALUES (%s,%s,%s,%s)",
        (d["user_id"], d["workout_datetime"], d["duration_min"], d.get("total_calories_burned")), commit=True
    )
    return jsonify({"workout_id": last_id}), 201

@app.route("/api/workouts/<int:wid>", methods=["PUT"])
def update_workout(wid):
    d = request.json
    query("UPDATE WORKOUT SET workout_datetime=%s, duration_min=%s, total_calories_burned=%s WHERE workout_id=%s",
          (d["workout_datetime"], d["duration_min"], d.get("total_calories_burned"), wid), commit=True)
    return jsonify({"success": True})

@app.route("/api/workouts/<int:wid>", methods=["DELETE"])
def delete_workout(wid):
    query("DELETE FROM WORKOUT WHERE workout_id=%s", (wid,), commit=True)
    return jsonify({"success": True})


# ── EXERCISES ─────────────────────────────────────────────────────────────────
@app.route("/api/exercises", methods=["GET"])
def get_exercises():
    return jsonify(query("SELECT * FROM EXERCISE ORDER BY exercise_name"))

@app.route("/api/exercises", methods=["POST"])
def create_exercise():
    d = request.json
    last_id = query(
        "INSERT INTO EXERCISE (exercise_name, muscle_group, calories_per_unit) VALUES (%s,%s,%s)",
        (d["exercise_name"], d["muscle_group"], d.get("calories_per_unit")), commit=True
    )
    return jsonify({"exercise_id": last_id}), 201

@app.route("/api/exercises/<int:eid>", methods=["PUT"])
def update_exercise(eid):
    d = request.json
    query("UPDATE EXERCISE SET exercise_name=%s, muscle_group=%s, calories_per_unit=%s WHERE exercise_id=%s",
          (d["exercise_name"], d["muscle_group"], d.get("calories_per_unit"), eid), commit=True)
    return jsonify({"success": True})

@app.route("/api/exercises/<int:eid>", methods=["DELETE"])
def delete_exercise(eid):
    query("DELETE FROM EXERCISE WHERE exercise_id=%s", (eid,), commit=True)
    return jsonify({"success": True})


# ── PROGRESS ──────────────────────────────────────────────────────────────────
@app.route("/api/progress", methods=["GET"])
def get_progress():
    return jsonify(query(
        "SELECT p.*, u.email FROM PROGRESS p JOIN USER u ON p.user_id=u.user_id ORDER BY p.progress_date DESC"
    ))

@app.route("/api/progress", methods=["POST"])
def create_progress():
    d = request.json
    last_id = query(
        "INSERT INTO PROGRESS (user_id, progress_date, body_weight, body_fat_percent, notes) VALUES (%s,%s,%s,%s,%s)",
        (d["user_id"], d["progress_date"], d.get("body_weight"), d.get("body_fat_percent"), d.get("notes")), commit=True
    )
    return jsonify({"progress_id": last_id}), 201

@app.route("/api/progress/<int:pid>", methods=["PUT"])
def update_progress(pid):
    d = request.json
    query("UPDATE PROGRESS SET progress_date=%s, body_weight=%s, body_fat_percent=%s, notes=%s WHERE progress_id=%s",
          (d["progress_date"], d.get("body_weight"), d.get("body_fat_percent"), d.get("notes"), pid), commit=True)
    return jsonify({"success": True})

@app.route("/api/progress/<int:pid>", methods=["DELETE"])
def delete_progress(pid):
    query("DELETE FROM PROGRESS WHERE progress_id=%s", (pid,), commit=True)
    return jsonify({"success": True})


if __name__ == "__main__":
    app.run(debug=True, port=5000)