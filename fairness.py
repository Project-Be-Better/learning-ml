from aif360.datasets import BinaryLabelDataset
from aif360.metrics import BinaryLabelDatasetMetric, ClassificationMetric
import pandas as pd
import sqlite3
import numpy as np

DB_NAME = "telemetry.db"

class FairnessAnalyzer:
    def __init__(self):
        self.conn = sqlite3.connect(DB_NAME)

    def get_fairness_data(self):
        """Joins trips with driver demographics."""
        query = """
            SELECT 
                d.age, 
                d.years_experience, 
                t.smoothness_score
            FROM trips t
            JOIN drivers d ON t.driver_id = d.driver_id
            WHERE t.smoothness_score IS NOT NULL
        """
        df = pd.read_sql_query(query, self.conn)
        
        # Define 'Favorable' outcome (e.g., score >= 80)
        df['favorable'] = (df['smoothness_score'] >= 80).astype(int)
        
        # Define protected attributes (Binary)
        # 1. Young vs Old (Threshold: 35)
        df['is_old'] = (df['age'] >= 35).astype(int)
        
        # 2. Novice vs Expert (Threshold: 10 years)
        df['is_expert'] = (df['years_experience'] >= 10).astype(int)
        
        return df

    def analyze_bias(self, attribute_name):
        """Analyzes bias for a given attribute using AIF360."""
        df = self.get_fairness_data()
        
        # Create AIF360 Dataset
        dataset = BinaryLabelDataset(
            df=df[[attribute_name, 'favorable']],
            label_names=['favorable'],
            protected_attribute_names=[attribute_name],
            favorable_label=1,
            unfavorable_label=0
        )
        
        # Privileged = 1, Unprivileged = 0
        privileged_groups = [{attribute_name: 1}]
        unprivileged_groups = [{attribute_name: 0}]
        
        metric = BinaryLabelDatasetMetric(
            dataset,
            unprivileged_groups=unprivileged_groups,
            privileged_groups=privileged_groups
        )
        
        results = {
            "disparate_impact": metric.disparate_impact(),
            "statistical_parity_difference": metric.statistical_parity_difference(),
            "privileged_favorable_rate": metric.num_positives(privileged=True) / metric.num_instances(privileged=True),
            "unprivileged_favorable_rate": metric.num_positives(privileged=False) / metric.num_instances(privileged=False)
        }
        
        return results

    def __del__(self):
        self.conn.close()

if __name__ == "__main__":
    analyzer = FairnessAnalyzer()
    
    print("⚖️ Fairness Analysis: Age (Old vs Young)")
    age_bias = analyzer.analyze_bias('is_old')
    for k, v in age_bias.items():
        print(f"  {k}: {v:.4f}")
        
    print("\n⚖️ Fairness Analysis: Experience (Expert vs Novice)")
    exp_bias = analyzer.analyze_bias('is_expert')
    for k, v in exp_bias.items():
        print(f"  {k}: {v:.4f}")

    print("\n💡 Interpretation Guidance:")
    print("  - Disparate Impact: Should be near 1.0 (0.8 to 1.25 is usually acceptable).")
    print("  - Statistical Parity: Should be near 0.0.")
