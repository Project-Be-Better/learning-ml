import sqlite3
import json
from src.core.celery_app import celery_app
from src.agents.behavior.agent import BehaviorAgent
from src.core.config import DB_NAME

agent = BehaviorAgent()

@celery_app.task(name="generate_driver_narrative")
def generate_driver_narrative(driver_id: int):
    """
    Background task to generate a coaching narrative using the Behavior Agent.
    """
    try:
        # Generate the narrative
        narrative = agent.generate_narrative(driver_id)
        
        if not narrative or narrative == "Driver not found.":
            return {"status": "error", "driver_id": driver_id, "message": "Driver not found or error generating narrative"}
            
        # Optional: Save it back to the database if intended.
        # But wait, our GET /driver/{id} endpoint actually calls agent.generate_narrative(driver_id) live.
        # If we precompute, we must save it to the DB so the API doesn't have to call it.
        # Let's add 'coaching_narrative' column or use 'explanation_json' (but that's SHAP).
        # For ADR 003, we pre-compute and store it. We need a column for this.
        # Let's add it via try_add_column in simulator or just add it here with alter table.
        
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        
        # Ensure column exists (simple migration)
        try:
            cursor.execute("ALTER TABLE drivers ADD COLUMN coaching_narrative TEXT")
        except sqlite3.OperationalError:
            pass # Column already exists
            
        cursor.execute("""
            UPDATE drivers 
            SET coaching_narrative = ? 
            WHERE driver_id = ?
        """, (narrative, driver_id))
        
        conn.commit()
        conn.close()
        
        return {"status": "success", "driver_id": driver_id}
    except Exception as e:
        return {"status": "error", "message": str(e)}
