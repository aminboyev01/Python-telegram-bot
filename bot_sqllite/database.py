import sqlite3

DB = "sample-database.db"


def get_countries():
    conn = sqlite3.connect(DB)
    cursor = conn.cursor()
    cursor.execute("SELECT country_id, country_name FROM countries")
    data = cursor.fetchall()
    conn.close()
    return data


def get_capital_by_country(country_id):
    conn = sqlite3.connect(DB)
    cursor = conn.cursor()
    cursor.execute(
        "SELECT city FROM city WHERE country = ? LIMIT 1", (country_id,)
    )
    result = cursor.fetchone()
    conn.close()
    return result[0] if result else "Poytaxt topilmadi"


def get_jobs():
    conn = sqlite3.connect(DB)
    cursor = conn.cursor()
    cursor.execute("SELECT job_id, job_title FROM jobs")
    data = cursor.fetchall()
    conn.close()
    return data


def get_salary(job_id):
    conn = sqlite3.connect(DB)
    cursor = conn.cursor()
    cursor.execute(
        "SELECT min_salary, max_salary FROM jobs WHERE job_id=?",
        (job_id,)
    )
    result = cursor.fetchone()
    conn.close()
    if result:
        return f"{result[0]} – {result[1]}"
    return "Ma'lumot topilmadi"
