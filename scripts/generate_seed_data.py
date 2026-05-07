"""
Seed data generator for BRD2 (Smart Offer Modeler).
Generates India-specific data with INR salaries.

Outputs to brd2/data/seed/:
  - market_benchmarks.csv   (80 rows: 10 roles × 8 metros)
  - salary_bands.csv        (80 rows: 10 roles × 8 metros)
  - internal_peers.csv      (1000 rows)

Run from the brd2/ directory:
    python scripts/generate_seed_data.py
"""
import csv
import random
import uuid
import pathlib

random.seed(42)

FIRST_NAMES = [
    "Arjun","Priya","Rahul","Ananya","Vikram","Deepa","Suresh","Kavitha","Arun","Meera",
    "Karthik","Pooja","Nikhil","Divya","Rohan","Sneha","Aditya","Nisha","Rajesh","Lakshmi",
    "Amit","Suhana","Vishal","Preeti","Sanjay","Swati","Mahesh","Asha","Ravi","Sunita",
    "Gaurav","Rekha","Varun","Geeta","Manish","Radha","Prakash","Usha","Naveen","Anjali",
    "Sachin","Vandana","Vivek","Padma","Ashish","Smita","Rajan","Jyoti","Harish","Kamala",
    "Girish","Savitha","Tushar","Bhavna","Dinesh","Hemant","Chandra","Venkat","Lalitha",
    "Sunil","Saritha","Mohan","Nandini","Krishnan","Revathi","Bala","Srikanth","Uma",
    "Ramesh","Shanthi","Gopal","Vijaya","Murali","Indira","Subramanian","Tejas","Kavya",
    "Pranav","Shruthi","Abhishek","Vidya","Siddharth","Aparna","Akash","Bhavana","Tarun",
    "Rashmi","Kunal","Archana","Jayesh","Madhuri","Parth","Rupal","Chirag","Hema","Mihir",
    "Pallavi","Yash","Shruti","Dhruv","Neha","Samir","Tanvi","Kartik","Isha","Rohit",
    "Ritika","Shubham","Payal","Ayush","Komal","Manan","Riya","Karan","Tanya","Harsh",
]

LAST_NAMES = [
    "Sharma","Patel","Kumar","Singh","Gupta","Mehta","Joshi","Nair","Reddy","Iyer",
    "Pillai","Menon","Krishnan","Rao","Agarwal","Bose","Das","Ghosh","Mukherjee","Shah",
    "Malhotra","Kapoor","Khanna","Verma","Mishra","Pandey","Tiwari","Dubey","Srivastava",
    "Naidu","Gowda","Hegde","Shetty","Kamath","Bhat","Pai","Kulkarni","Desai","Shukla",
    "Chandra","Banerjee","Roy","Sen","Dey","Mitra","Biswas","Chakraborty","Basu",
    "Narayanan","Subramanian","Sundaram","Venkatesh","Balakrishnan","Rangan","Murthy",
    "Saxena","Sinha","Tripathi","Awasthi","Dixit","Bajpai","Rastogi","Mathur","Tandon",
    "Choudhary","Yadav","Tiwary","Bhatt","Trivedi","Vyas","Raval","Thakkar","Modi",
]

METROS = [
    "Bengaluru","Mumbai","Hyderabad","Pune","Delhi NCR","Chennai","Noida","Gurugram",
]

METRO_MULTIPLIER = {
    "Bengaluru": 1.00, "Mumbai": 1.06, "Delhi NCR": 1.03, "Gurugram": 1.02,
    "Hyderabad": 0.93, "Pune": 0.91, "Chennai": 0.90, "Noida": 0.89,
}

ROLES = {
    "Software Engineer":        {"band_min": 900000,  "band_mid": 1500000,  "band_max": 2200000,  "grade": "L3",  "bonus": 0.10},
    "Senior Software Engineer": {"band_min": 2000000, "band_mid": 3500000,  "band_max": 5200000,  "grade": "L5",  "bonus": 0.15},
    "Staff Software Engineer":  {"band_min": 5000000, "band_mid": 7800000,  "band_max": 11500000, "grade": "L6",  "bonus": 0.20},
    "Principal Engineer":       {"band_min": 9500000, "band_mid": 15000000, "band_max": 22000000, "grade": "L7",  "bonus": 0.25},
    "Product Manager":          {"band_min": 1800000, "band_mid": 3000000,  "band_max": 4600000,  "grade": "M4",  "bonus": 0.15},
    "Senior Product Manager":   {"band_min": 4000000, "band_mid": 6500000,  "band_max": 9800000,  "grade": "M5",  "bonus": 0.20},
    "UX Designer":              {"band_min": 1200000, "band_mid": 2000000,  "band_max": 3100000,  "grade": "D4",  "bonus": 0.10},
    "Senior UX Designer":       {"band_min": 2600000, "band_mid": 4200000,  "band_max": 6200000,  "grade": "D5",  "bonus": 0.15},
    "Data Scientist":           {"band_min": 1600000, "band_mid": 2800000,  "band_max": 4300000,  "grade": "DS4", "bonus": 0.12},
    "Senior Data Scientist":    {"band_min": 4200000, "band_mid": 6800000,  "band_max": 10000000, "grade": "DS5", "bonus": 0.18},
}

PERF_WEIGHTS = [("Exceeds", 0.25), ("Meets", 0.60), ("Below", 0.15)]
COMPA_BY_RATING = {
    "Exceeds": (0.98, 1.15),
    "Meets":   (0.88, 1.05),
    "Below":   (0.80, 0.92),
}


def random_name():
    return f"{random.choice(FIRST_NAMES)} {random.choice(LAST_NAMES)}"


def weighted_choice(options):
    items, weights = zip(*options)
    return random.choices(items, weights=weights, k=1)[0]


def generate_market_benchmarks():
    rows = []
    for role, cfg in ROLES.items():
        for metro in METROS:
            mult = METRO_MULTIPLIER[metro]
            mid = cfg["band_mid"] * mult
            bonus = cfg["bonus"]
            rows.append({
                "benchmark_id": str(uuid.uuid4())[:8].upper(),
                "role_title": role,
                "location_metro": metro,
                "p25_base": round(mid * 0.82),
                "p50_base": round(mid * 0.98),
                "p75_base": round(mid * 1.20),
                "p90_base": round(mid * 1.45),
                "p50_total_cash": round(mid * 0.98 * (1 + bonus)),
                "p75_total_cash": round(mid * 1.20 * (1 + bonus)),
                "source": "Mercer_India_2026",
                "effective_date": "2026-01-01",
            })
    return rows


def generate_salary_bands():
    rows = []
    for role, cfg in ROLES.items():
        for metro in METROS:
            mult = METRO_MULTIPLIER[metro]
            rows.append({
                "band_id": str(uuid.uuid4())[:8].upper(),
                "role_title": role,
                "location_metro": metro,
                "band_min": round(cfg["band_min"] * mult),
                "band_midpoint": round(cfg["band_mid"] * mult),
                "band_max": round(cfg["band_max"] * mult),
                "grade_level": cfg["grade"],
                "effective_year": 2026,
            })
    return rows


def generate_internal_peers(n=1000):
    rows = []
    roles = list(ROLES.keys())
    for i in range(n):
        role = random.choice(roles)
        metro = random.choice(METROS)
        cfg = ROLES[role]
        mult = METRO_MULTIPLIER[metro]
        mid = cfg["band_mid"] * mult
        perf = weighted_choice(PERF_WEIGHTS)
        lo, hi = COMPA_BY_RATING[perf]
        compa = random.uniform(lo, hi)
        base = round(mid * compa / 10000) * 10000
        yoe = random.randint(2, 18)
        yoc = random.randint(1, min(yoe, 8))
        rows.append({
            "employee_id": f"EMP-{2000 + i:04d}",
            "peer_name": random_name(),
            "role_title": role,
            "location_metro": metro,
            "years_experience": yoe,
            "years_at_company": yoc,
            "base_salary": base,
            "annual_bonus_target_pct": cfg["bonus"],
            "performance_rating": perf,
            "hired_date": f"{random.randint(2017, 2024)}-{random.randint(1,12):02d}-{random.randint(1,28):02d}",
        })
    return rows


def write_csv(rows, path):
    path = pathlib.Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=rows[0].keys())
        writer.writeheader()
        writer.writerows(rows)
    print(f"  Wrote {len(rows):,} rows → {path}")


if __name__ == "__main__":
    BASE = pathlib.Path(__file__).parent.parent  # brd2/
    print("Generating BRD2 seed data...")
    write_csv(generate_market_benchmarks(),  BASE / "data/seed/market_benchmarks.csv")
    write_csv(generate_salary_bands(),       BASE / "data/seed/salary_bands.csv")
    write_csv(generate_internal_peers(1000), BASE / "data/seed/internal_peers.csv")
    print("Done. Run 'python scripts/seed_bigquery.py' to load into BigQuery.")
