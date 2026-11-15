import os
from pipeline import DataPipeline

DATA_PATH = os.path.join(os.path.dirname(__file__), "data", "messy_employee_survey.csv")
OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "output")
os.makedirs(OUTPUT_DIR, exist_ok=True)


def main():
    print("=" * 60)
    print("Employee Survey Data Pipeline")
    print("=" * 60)

    pipeline = DataPipeline(DATA_PATH)
    results = pipeline.run()

    # Display the findings from the analysis
    print(f"  Top location by headcount: {results['headcount_by_location'].idxmax()}")
    print(f"  Department with the highest average salary: {results['avg_salary_by_dept'].idxmax()}")
    print(f"  Department with the highest satisfaction: {results['avg_satisfaction_by_dept'].idxmax()}")
    print(f"  Experience vs Salary correlation: {results['experience_salary_correlation']:.2f}")
    print(f"  Location with the highest average satisfaction: {results['avg_satisfaction_by_location'].idxmax()}")

    print("Pipeline not yet implemented — fill in pipeline.py to continue.")


if __name__ == "__main__":
    main()