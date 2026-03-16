import sqlite3
import json
import os

# Placeholder for LLM integration (e.g., Gemini or OpenAI)
# In a real LangGraph setup, this would be a specialized node.

from src.core.config import DB_NAME

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
        
        # 1. Feature Analysis (XAI)
        xai = data['xai']
        fairness = data['fairness']
        
        # Filter out metadata like 'base_value' which isn't a driver behavior
        ignored_features = {"base_value"}
        feature_impacts = {
            k: v for k, v in xai.items() 
            if k not in ignored_features and isinstance(v, (int, float))
        }
        
        # Identify top positive impact feature
        top_feature = max(feature_impacts, key=feature_impacts.get) if feature_impacts else "consistency"
        
        # 2. Cohort Analysis (Fairness)
        diff = fairness.get('diff', 0)
        perf_status = "outperforming" if diff > 0 else "trailing"
        
        # 3. Generate Professional Narrative
        # This acts as the 'Coaching Note' for the dashboard
        narrative = (
            f"Hello {data['name']}! Based on your recent trips, you are {perf_status} your "
            f"age cohort by {abs(diff):.2f} points. This strong performance is primarily "
            f"driven by your excellent {top_feature.replace('_', ' ')}."
        )
        
        return narrative

if __name__ == "__main__":
    agent = BehaviorAgent()
    print("--- Behavior Agent Insights ---")
    print(agent.generate_narrative(1))
