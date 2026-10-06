
import json
from app.db.session import SessionLocal
from app.evaluation import run_evaluation, seed_cases

db=SessionLocal()
try:
    seed_cases(db); run_id=run_evaluation(db); print(json.dumps({"run_id":run_id,"status":"completed"}))
finally: db.close()
