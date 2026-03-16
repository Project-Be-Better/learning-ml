import sqlite3
import json
import os

# Placeholder for LLM integration (e.g., Gemini or OpenAI)
# In a real LangGraph setup, this would be a specialized node.

DB_NAME = "telemetry.db"

class BehaviorAgent:
    def __init__(self, model_name="gemini-1.5-pro"):
        self.model_name = model_name

    def fetch_driver_insights(self, driver_id):
        """Fetches raw XAI and Fairness data for a driver."""
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        cursor.execute("""
            SELECT name, explanation_json, fairness_metadata_json 
            FROM drivers WHERE driver_id = ?
        """, (driver_id,))
        row = cursor.fetchone()
        conn.close()
        
        if not row:
            return None
            
        return {
            "name": row[0],
            "xai": json.loads(row[1]) if row[1] else {},
            "fairness": json.loads(row[2]) if row[2] else {}
        }

    def generate_narrative(self, driver_id):
        """
        Translates raw data into a coaching narrative.
        In MVP, we use a template-based approach to show logic, 
        which would be replaced by an LLM call.
        """
        data = self.fetch_driver_insights(driver_id)
        if not data:
            return "Driver not found."

        # YOUR TURN: Implementation of the LLM prompt structure
        # prompt = f"""
        # You are the ExploreSG Behavior Agent.
        # Driver: {data['name']}
        # XAI Signature: {data['xai']}
        # Fairness Context: {data['fairness']}
        # 
        # Task: Generate a supportive, professional coaching sentence.
        # """
        
        # HEURISTIC MOCK (Representing what the LLM would output)
        xai = data['xai']
        fairness = data['fairness']
        
        top_feature = max(xai, key=lambda k: xai[k] if isinstance(xai[k], (int, float)) else 0) if xai else "consistency"
        perf_status = "outperforming" if fairness.get('diff', 0) > 0 else "trailing"
        
        narrative = (
            f"Hello {data['name']}! Based on your recent trips, you are {perf_status} "
            f"your cohort by {abs(fairness.get('diff', 0))} points. "
            f"Your high score is primarily driven by your excellent {top_feature.replace('_', ' ')}."
        )
        
        return narrative

if __name__ == "__main__":
    agent = BehaviorAgent()
    print("--- Behavior Agent Insights ---")
    print(agent.generate_narrative(1))
