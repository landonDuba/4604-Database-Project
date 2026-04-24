from flask import Flask, request, jsonify, session
from flask_cors import CORS
import mysql.connector
import bcrypt

app = Flask(__name__)
app.secret_key = "change-this-to-a-random-secret"
app.config.update(SESSION_COOKIE_SAMESITE="Lax")

CORS(app, supports_credentials=True, origins=["http://127.0.0.1:5500"])

ADMIN_CODE = "fittrack-admin-2024"

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


# ── AUTH HELPERS ──────────────────────────────────────────────────────────────
def login_required(f):
    from functools import wraps
    @wraps(f)
    def decorated(*args, **kwargs):
        if "user_id" not in session:
            return jsonify({"error": "Unauthorized"}), 401
        return f(*args, **kwargs)
    return decorated

def admin_required(f):
    from functools import wraps
    @wraps(f)
    def decorated(*args, **kwargs):
        if "user_id" not in session:
            return jsonify({"error": "Unauthorized"}), 401
        if session.get("user_type") != "admin":
            return jsonify({"error": "Admin access required"}), 403
        return f(*args, **kwargs)
    return decorated


# ── AUTH ROUTES ───────────────────────────────────────────────────────────────
@app.route("/api/auth/register", methods=["POST"])
def register():
    d = request.json
    email = d.get("email", "").strip().lower()
    password = d.get("password", "")
    admin_code = d.get("admin_code", "")
    if not email or not password:
        return jsonify({"error": "Email and password are required"}), 400
    if len(password) < 6:
        return jsonify({"error": "Password must be at least 6 characters"}), 400
    existing = query("SELECT user_id FROM USER WHERE email=%s", (email,), fetchone=True)
    if existing:
        return jsonify({"error": "An account with that email already exists"}), 409
    user_type = "admin" if admin_code == ADMIN_CODE else "regular"
    pw_hash = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()
    from datetime import date
    user_id = query(
        "INSERT INTO USER (email, password_hash, user_type, created_at) VALUES (%s,%s,%s,%s)",
        (email, pw_hash, user_type, date.today().isoformat()), commit=True
    )
    session["user_id"] = user_id
    session["email"] = email
    session["user_type"] = user_type
    return jsonify({"user_id": user_id, "email": email, "user_type": user_type}), 201


@app.route("/api/auth/login", methods=["POST"])
def login():
    d = request.json
    email = d.get("email", "").strip().lower()
    password = d.get("password", "")
    if not email or not password:
        return jsonify({"error": "Email and password are required"}), 400
    user = query("SELECT * FROM USER WHERE email=%s", (email,), fetchone=True)
    if not user or not bcrypt.checkpw(password.encode(), user["password_hash"].encode()):
        return jsonify({"error": "Invalid email or password"}), 401
    session["user_id"] = user["user_id"]
    session["email"] = user["email"]
    session["user_type"] = user["user_type"]
    return jsonify({"user_id": user["user_id"], "email": user["email"], "user_type": user["user_type"]})


@app.route("/api/auth/logout", methods=["POST"])
def logout():
    session.clear()
    return jsonify({"success": True})


@app.route("/api/auth/me", methods=["GET"])
def me():
    if "user_id" not in session:
        return jsonify({"error": "Not logged in"}), 401
    return jsonify({"user_id": session["user_id"], "email": session["email"], "user_type": session["user_type"]})


@app.route("/api/auth/change-password", methods=["POST"])
@login_required
def change_password():
    d = request.json
    current = d.get("current_password", "")
    new_pw = d.get("new_password", "")
    if not current or not new_pw:
        return jsonify({"error": "Both fields are required"}), 400
    if len(new_pw) < 6:
        return jsonify({"error": "New password must be at least 6 characters"}), 400
    user = query("SELECT * FROM USER WHERE user_id=%s", (session["user_id"],), fetchone=True)
    if not bcrypt.checkpw(current.encode(), user["password_hash"].encode()):
        return jsonify({"error": "Current password is incorrect"}), 401
    new_hash = bcrypt.hashpw(new_pw.encode(), bcrypt.gensalt()).decode()
    query("UPDATE USER SET password_hash=%s WHERE user_id=%s", (new_hash, session["user_id"]), commit=True)
    return jsonify({"success": True})


# ── USERS ─────────────────────────────────────────────────────────────────────
@app.route("/api/users", methods=["GET"])
@admin_required
def get_users():
    return jsonify(query("SELECT user_id, email, user_type, created_at FROM USER ORDER BY user_id"))

@app.route("/api/users/create", methods=["POST"])
@admin_required
def admin_create_user():
    d = request.json
    email = d.get("email", "").strip().lower()
    password = d.get("password", "")
    user_type = d.get("user_type", "regular")
    if not email or not password:
        return jsonify({"error": "Email and password are required"}), 400
    if len(password) < 6:
        return jsonify({"error": "Password must be at least 6 characters"}), 400
    existing = query("SELECT user_id FROM USER WHERE email=%s", (email,), fetchone=True)
    if existing:
        return jsonify({"error": "An account with that email already exists"}), 409
    pw_hash = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()
    from datetime import date
    user_id = query(
        "INSERT INTO USER (email, password_hash, user_type, created_at) VALUES (%s,%s,%s,%s)",
        (email, pw_hash, user_type, date.today().isoformat()), commit=True
    )
    return jsonify({"user_id": user_id}), 201

@app.route("/api/users/<int:uid>", methods=["PUT"])
@admin_required
def update_user(uid):
    d = request.json
    query("UPDATE USER SET email=%s, user_type=%s WHERE user_id=%s", (d["email"], d["user_type"], uid), commit=True)
    return jsonify({"success": True})

@app.route("/api/users/<int:uid>", methods=["DELETE"])
@admin_required
def delete_user(uid):
    if uid == session["user_id"]:
        return jsonify({"error": "Cannot delete your own account"}), 400
    query("DELETE FROM USER WHERE user_id=%s", (uid,), commit=True)
    return jsonify({"success": True})


# ── EXERCISES (admin write, all read) ─────────────────────────────────────────
@app.route("/api/exercises", methods=["GET"])
@login_required
def get_exercises():
    return jsonify(query("SELECT * FROM EXERCISE ORDER BY exercise_name"))

@app.route("/api/exercises", methods=["POST"])
@admin_required
def create_exercise():
    d = request.json
    last_id = query(
        "INSERT INTO EXERCISE (exercise_name, muscle_group, calories_per_unit) VALUES (%s,%s,%s)",
        (d["exercise_name"], d.get("muscle_group"), d.get("calories_per_unit")), commit=True
    )
    return jsonify({"exercise_id": last_id}), 201

@app.route("/api/exercises/<int:eid>", methods=["PUT"])
@admin_required
def update_exercise(eid):
    d = request.json
    query("UPDATE EXERCISE SET exercise_name=%s, muscle_group=%s, calories_per_unit=%s WHERE exercise_id=%s",
          (d["exercise_name"], d.get("muscle_group"), d.get("calories_per_unit"), eid), commit=True)
    return jsonify({"success": True})

@app.route("/api/exercises/<int:eid>", methods=["DELETE"])
@admin_required
def delete_exercise(eid):
    query("DELETE FROM EXERCISE WHERE exercise_id=%s", (eid,), commit=True)
    return jsonify({"success": True})


# ── MEALS ─────────────────────────────────────────────────────────────────────
@app.route("/api/meals", methods=["GET"])
@login_required
def get_meals():
    if session.get("user_type") == "admin":
        meals = query(
            "SELECT m.*, u.email FROM MEAL m JOIN USER u ON m.user_id=u.user_id ORDER BY m.meal_datetime DESC"
        )
    else:
        user_id = request.args.get("user_id", session["user_id"])
        if str(user_id) != str(session["user_id"]):
            return jsonify({"error": "Forbidden"}), 403
        meals = query(
            "SELECT m.*, u.email FROM MEAL m JOIN USER u ON m.user_id=u.user_id WHERE m.user_id=%s ORDER BY m.meal_datetime DESC",
            (user_id,)
        )
    for meal in meals:
        meal["foods"] = query(
            """SELECT mf.food_id, mf.quantity_servings, f.food_name,
                      f.calories_per_serving, f.protein_g, f.carbs_g, f.fat_g
               FROM MEAL_FOOD mf JOIN FOOD f ON mf.food_id=f.food_id
               WHERE mf.meal_id=%s""",
            (meal["meal_id"],)
        )
    return jsonify(meals)


@app.route("/api/meals", methods=["POST"])
@login_required
def create_meal():
    d = request.json
    user_id = session["user_id"] if session.get("user_type") != "admin" else d.get("user_id", session["user_id"])
    foods = d.get("foods", [])
    if not d.get("meal_name") or not d.get("meal_datetime"):
        return jsonify({"error": "Meal name and datetime required"}), 400
    if len(foods) == 0:
        return jsonify({"error": "Add at least one food"}), 400
    if len(foods) > 5:
        return jsonify({"error": "Maximum 5 foods per meal"}), 400

    total_cal = 0
    for item in foods:
        food = query("SELECT calories_per_serving FROM FOOD WHERE food_id=%s", (item["food_id"],), fetchone=True)
        if food and food["calories_per_serving"]:
            total_cal += food["calories_per_serving"] * float(item["quantity_servings"])

    conn = get_db()
    cur = conn.cursor(dictionary=True)
    try:
        cur.execute(
            "INSERT INTO MEAL (user_id, meal_datetime, meal_name, total_calories) VALUES (%s,%s,%s,%s)",
            (user_id, d["meal_datetime"], d["meal_name"], round(total_cal, 1))
        )
        meal_id = cur.lastrowid
        for item in foods:
            cur.execute(
                "INSERT INTO MEAL_FOOD (meal_id, food_id, quantity_servings) VALUES (%s,%s,%s)",
                (meal_id, item["food_id"], item["quantity_servings"])
            )
        conn.commit()
    except Exception as e:
        conn.rollback()
        cur.close(); conn.close()
        return jsonify({"error": str(e)}), 500
    cur.close(); conn.close()
    return jsonify({"meal_id": meal_id, "total_calories": round(total_cal, 1)}), 201


@app.route("/api/meals/<int:mid>", methods=["PUT"])
@login_required
def update_meal(mid):
    d = request.json
    if session.get("user_type") != "admin":
        meal = query("SELECT user_id FROM MEAL WHERE meal_id=%s", (mid,), fetchone=True)
        if not meal or meal["user_id"] != session["user_id"]:
            return jsonify({"error": "Forbidden"}), 403
    foods = d.get("foods", [])
    if len(foods) == 0:
        return jsonify({"error": "Add at least one food"}), 400
    if len(foods) > 5:
        return jsonify({"error": "Maximum 5 foods per meal"}), 400

    total_cal = 0
    for item in foods:
        food = query("SELECT calories_per_serving FROM FOOD WHERE food_id=%s", (item["food_id"],), fetchone=True)
        if food and food["calories_per_serving"]:
            total_cal += food["calories_per_serving"] * float(item["quantity_servings"])

    conn = get_db()
    cur = conn.cursor(dictionary=True)
    try:
        cur.execute(
            "UPDATE MEAL SET meal_datetime=%s, meal_name=%s, total_calories=%s WHERE meal_id=%s",
            (d["meal_datetime"], d["meal_name"], round(total_cal, 1), mid)
        )
        cur.execute("DELETE FROM MEAL_FOOD WHERE meal_id=%s", (mid,))
        for item in foods:
            cur.execute(
                "INSERT INTO MEAL_FOOD (meal_id, food_id, quantity_servings) VALUES (%s,%s,%s)",
                (mid, item["food_id"], item["quantity_servings"])
            )
        conn.commit()
    except Exception as e:
        conn.rollback()
        cur.close(); conn.close()
        return jsonify({"error": str(e)}), 500
    cur.close(); conn.close()
    return jsonify({"success": True, "total_calories": round(total_cal, 1)})


@app.route("/api/meals/<int:mid>", methods=["DELETE"])
@login_required
def delete_meal(mid):
    if session.get("user_type") != "admin":
        meal = query("SELECT user_id FROM MEAL WHERE meal_id=%s", (mid,), fetchone=True)
        if not meal or meal["user_id"] != session["user_id"]:
            return jsonify({"error": "Forbidden"}), 403
    query("DELETE FROM MEAL WHERE meal_id=%s", (mid,), commit=True)
    return jsonify({"success": True})


# ── FOOD (admin write, all read) ──────────────────────────────────────────────
@app.route("/api/foods", methods=["GET"])
@login_required
def get_foods():
    return jsonify(query("SELECT * FROM FOOD ORDER BY food_name"))

@app.route("/api/foods", methods=["POST"])
@admin_required
def create_food():
    d = request.json
    last_id = query(
        "INSERT INTO FOOD (food_name, calories_per_serving, protein_g, carbs_g, fat_g, fiber_g) VALUES (%s,%s,%s,%s,%s,%s)",
        (d["food_name"], d.get("calories_per_serving"), d.get("protein_g"), d.get("carbs_g"), d.get("fat_g"), d.get("fiber_g")), commit=True
    )
    return jsonify({"food_id": last_id}), 201

@app.route("/api/foods/<int:fid>", methods=["PUT"])
@admin_required
def update_food(fid):
    d = request.json
    query("UPDATE FOOD SET food_name=%s, calories_per_serving=%s, protein_g=%s, carbs_g=%s, fat_g=%s, fiber_g=%s WHERE food_id=%s",
          (d["food_name"], d.get("calories_per_serving"), d.get("protein_g"), d.get("carbs_g"), d.get("fat_g"), d.get("fiber_g"), fid), commit=True)
    return jsonify({"success": True})

@app.route("/api/foods/<int:fid>", methods=["DELETE"])
@admin_required
def delete_food(fid):
    query("DELETE FROM FOOD WHERE food_id=%s", (fid,), commit=True)
    return jsonify({"success": True})


# ── WORKOUTS ──────────────────────────────────────────────────────────────────
@app.route("/api/workouts", methods=["GET"])
@login_required
def get_workouts():
    if session.get("user_type") == "admin":
        workouts = query(
            "SELECT w.*, u.email FROM WORKOUT w JOIN USER u ON w.user_id=u.user_id ORDER BY w.workout_datetime DESC"
        )
    else:
        user_id = request.args.get("user_id", session["user_id"])
        if str(user_id) != str(session["user_id"]):
            return jsonify({"error": "Forbidden"}), 403
        workouts = query(
            "SELECT w.*, u.email FROM WORKOUT w JOIN USER u ON w.user_id=u.user_id WHERE w.user_id=%s ORDER BY w.workout_datetime DESC",
            (user_id,)
        )
    for workout in workouts:
        workout["exercises"] = query(
            """SELECT we.exercise_id, we.`sets`, we.reps, we.duration_min,
                      e.exercise_name, e.muscle_group, e.calories_per_unit
               FROM WORKOUT_EXERCISE we JOIN EXERCISE e ON we.exercise_id=e.exercise_id
               WHERE we.workout_id=%s""",
            (workout["workout_id"],)
        )
    return jsonify(workouts)


@app.route("/api/workouts", methods=["POST"])
@login_required
def create_workout():
    d = request.json
    user_id = session["user_id"] if session.get("user_type") != "admin" else d.get("user_id", session["user_id"])
    exercises = d.get("exercises", [])
    if not d.get("workout_datetime") or not d.get("duration_min"):
        return jsonify({"error": "Datetime and duration required"}), 400
    if len(exercises) == 0:
        return jsonify({"error": "Add at least one exercise"}), 400
    if len(exercises) > 5:
        return jsonify({"error": "Maximum 5 exercises per workout"}), 400

    total_cal = 0
    for item in exercises:
        ex = query("SELECT calories_per_unit FROM EXERCISE WHERE exercise_id=%s", (item["exercise_id"],), fetchone=True)
        if ex and ex["calories_per_unit"]:
            multiplier = float(item.get("sets") or item.get("duration_min") or 1)
            total_cal += ex["calories_per_unit"] * multiplier

    conn = get_db()
    cur = conn.cursor(dictionary=True)
    try:
        cur.execute(
            "INSERT INTO WORKOUT (user_id, workout_datetime, duration_min, total_calories_burned) VALUES (%s,%s,%s,%s)",
            (user_id, d["workout_datetime"], d["duration_min"], round(total_cal, 1))
        )
        workout_id = cur.lastrowid
        for item in exercises:
            cur.execute(
                "INSERT INTO WORKOUT_EXERCISE (workout_id, exercise_id, `sets`, reps, duration_min) VALUES (%s,%s,%s,%s,%s)",
                (workout_id, item["exercise_id"], item.get("sets"), item.get("reps"), item.get("duration_min"))
            )
        conn.commit()
    except Exception as e:
        conn.rollback()
        cur.close(); conn.close()
        return jsonify({"error": str(e)}), 500
    cur.close(); conn.close()
    return jsonify({"workout_id": workout_id, "total_calories_burned": round(total_cal, 1)}), 201


@app.route("/api/workouts/<int:wid>", methods=["PUT"])
@login_required
def update_workout(wid):
    d = request.json
    if session.get("user_type") != "admin":
        w = query("SELECT user_id FROM WORKOUT WHERE workout_id=%s", (wid,), fetchone=True)
        if not w or w["user_id"] != session["user_id"]:
            return jsonify({"error": "Forbidden"}), 403
    exercises = d.get("exercises", [])
    if len(exercises) == 0:
        return jsonify({"error": "Add at least one exercise"}), 400
    if len(exercises) > 5:
        return jsonify({"error": "Maximum 5 exercises per workout"}), 400

    total_cal = 0
    for item in exercises:
        ex = query("SELECT calories_per_unit FROM EXERCISE WHERE exercise_id=%s", (item["exercise_id"],), fetchone=True)
        if ex and ex["calories_per_unit"]:
            multiplier = float(item.get("sets") or item.get("duration_min") or 1)
            total_cal += ex["calories_per_unit"] * multiplier

    conn = get_db()
    cur = conn.cursor(dictionary=True)
    try:
        cur.execute(
            "UPDATE WORKOUT SET workout_datetime=%s, duration_min=%s, total_calories_burned=%s WHERE workout_id=%s",
            (d["workout_datetime"], d["duration_min"], round(total_cal, 1), wid)
        )
        cur.execute("DELETE FROM WORKOUT_EXERCISE WHERE workout_id=%s", (wid,))
        for item in exercises:
            cur.execute(
                "INSERT INTO WORKOUT_EXERCISE (workout_id, exercise_id, `sets`, reps, duration_min) VALUES (%s,%s,%s,%s,%s)",
                (wid, item["exercise_id"], item.get("sets"), item.get("reps"), item.get("duration_min"))
            )
        conn.commit()
    except Exception as e:
        conn.rollback()
        cur.close(); conn.close()
        return jsonify({"error": str(e)}), 500
    cur.close(); conn.close()
    return jsonify({"success": True, "total_calories_burned": round(total_cal, 1)})


@app.route("/api/workouts/<int:wid>", methods=["DELETE"])
@login_required
def delete_workout(wid):
    if session.get("user_type") != "admin":
        w = query("SELECT user_id FROM WORKOUT WHERE workout_id=%s", (wid,), fetchone=True)
        if not w or w["user_id"] != session["user_id"]:
            return jsonify({"error": "Forbidden"}), 403
    query("DELETE FROM WORKOUT WHERE workout_id=%s", (wid,), commit=True)
    return jsonify({"success": True})


# ── PROGRESS ──────────────────────────────────────────────────────────────────
@app.route("/api/progress", methods=["GET"])
@login_required
def get_progress():
    if session.get("user_type") == "admin":
        return jsonify(query(
            "SELECT p.*, u.email FROM PROGRESS p JOIN USER u ON p.user_id=u.user_id ORDER BY p.progress_date DESC"
        ))
    user_id = request.args.get("user_id", session["user_id"])
    if str(user_id) != str(session["user_id"]):
        return jsonify({"error": "Forbidden"}), 403
    return jsonify(query(
        "SELECT p.*, u.email FROM PROGRESS p JOIN USER u ON p.user_id=u.user_id WHERE p.user_id=%s ORDER BY p.progress_date DESC",
        (user_id,)
    ))

@app.route("/api/progress", methods=["POST"])
@login_required
def create_progress():
    d = request.json
    user_id = session["user_id"] if session.get("user_type") != "admin" else d.get("user_id", session["user_id"])
    last_id = query(
        "INSERT INTO PROGRESS (user_id, progress_date, body_weight, body_fat_percent, notes) VALUES (%s,%s,%s,%s,%s)",
        (user_id, d["progress_date"], d.get("body_weight"), d.get("body_fat_percent"), d.get("notes")), commit=True
    )
    return jsonify({"progress_id": last_id}), 201

@app.route("/api/progress/<int:pid>", methods=["PUT"])
@login_required
def update_progress(pid):
    d = request.json
    if session.get("user_type") != "admin":
        p = query("SELECT user_id FROM PROGRESS WHERE progress_id=%s", (pid,), fetchone=True)
        if not p or p["user_id"] != session["user_id"]:
            return jsonify({"error": "Forbidden"}), 403
    query("UPDATE PROGRESS SET progress_date=%s, body_weight=%s, body_fat_percent=%s, notes=%s WHERE progress_id=%s",
          (d["progress_date"], d.get("body_weight"), d.get("body_fat_percent"), d.get("notes"), pid), commit=True)
    return jsonify({"success": True})

@app.route("/api/progress/<int:pid>", methods=["DELETE"])
@login_required
def delete_progress(pid):
    if session.get("user_type") != "admin":
        p = query("SELECT user_id FROM PROGRESS WHERE progress_id=%s", (pid,), fetchone=True)
        if not p or p["user_id"] != session["user_id"]:
            return jsonify({"error": "Forbidden"}), 403
    query("DELETE FROM PROGRESS WHERE progress_id=%s", (pid,), commit=True)
    return jsonify({"success": True})


if __name__ == "__main__":
    app.run(debug=True, port=5000)