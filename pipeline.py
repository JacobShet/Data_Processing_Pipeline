import os
import pandas as pd
import matplotlib.pyplot as plt


class DataPipeline:
    """A reusable data processing pipeline"""

    def __init__(self, filepath):
        """Load the raw data from a CSV file."""
        try:
            self.df = pd.read_csv(filepath)
        except FileNotFoundError:
            print("File not found. Please check to make sure the file is correct.")
            raise

    def clean(self):
        """Run all cleaning steps. Returns self for chaining."""
        duplicate_count = self.df.duplicated(subset=["employee_id"]).sum()
        self.df = self.df.drop_duplicates(subset=["employee_id"], keep="first")
        self.df["name"] = self.df["name"].str.strip().str.title()
        self.df["office_location"] = self.df["office_location"].str.strip().str.lower()
        self.df["comments"] = self.df["comments"].str.strip().str.capitalize()
        self.df["department"] = self.df["department"].str.strip().str.lower()
        self.df["department"] = self.df["department"].str.replace(r'^h\.?r\.?$', "human resources", regex=True)

        # Map common abbreviations and variations to standardized names.
        department_map = {
            "eng": "engineering",
            "mktg": "marketing",
            "fin": "finance"
        }

        office_map = {
            "austin, tx": "austin",
            "atx": "austin",
            "sea": "seattle",
            "nyc": "new york",
            "chi": "chicago"
        }

        self.df["department"] = self.df["department"].replace(department_map).str.title()

        self.df["office_location"] = self.df["office_location"].replace(office_map).str.title()

        self.df["salary"] = self.df["salary"].astype("string")
        self.df["salary"] = self.df["salary"].str.replace("$", "", regex=False)
        self.df["salary"] = self.df["salary"].str.replace(",", "", regex=False)
        self.df["salary"] = pd.to_numeric(self.df["salary"], errors="coerce")
        self.df["years_experience"] = pd.to_numeric(self.df["years_experience"], errors="coerce")
        self.df["satisfaction_score"] = pd.to_numeric(self.df["satisfaction_score"], errors="coerce")

        # Convert multiple date formats into a consistent datetime format.
        original_dates = self.df["survey_date"].copy()
        converted_dates = pd.to_datetime(original_dates, format="%m/%d/%Y", errors="coerce")
        converted_dates = converted_dates.fillna(pd.to_datetime(original_dates, format="%Y-%m-%d", errors="coerce"))
        converted_dates = converted_dates.fillna(pd.to_datetime(original_dates, format="%d-%m-%Y", errors="coerce"))
        self.df["survey_date"] = converted_dates

        # No employee records were removed due to missing values.
        # Missing salary and years_experience values were preserved.
        # because replacing them with estimates could introduce inaccurate data.
        # Missing satisfaction scores were preserved because employees
        # may have chosen not to answer the survey questions.
        # Missing comments were replaced with "No comment left"
        # because comments are optional.

        self.df["comments"] = self.df["comments"].fillna("No comment left")

        # Identify and replace values outside the expected data ranges.
        invalid_salaries = (self.df["salary"] < 0).sum()
        self.df.loc[self.df["salary"] < 0, "salary"] = pd.NA

        invalid_experience = (self.df["years_experience"] > 50).sum()
        self.df.loc[self.df["years_experience"] > 50, "years_experience"] = pd.NA

        invalid_satisfaction = ((self.df["satisfaction_score"] < 1) | (self.df["satisfaction_score"] > 10)).sum()
        self.df.loc[(self.df["satisfaction_score"] < 1) | (self.df["satisfaction_score"] > 10), "satisfaction_score"] = pd.NA

        # Print the cleaning summary
        total_invalid_values = invalid_salaries + invalid_experience + invalid_satisfaction
        print(f"Removed {duplicate_count} duplicate records.")
        print("Standardized text columns and standardized department/location names.")
        print("Converted salary values to numeric.")
        print("Converted survey dates to datetime.")
        print(f"Handled {total_invalid_values} invalid values. ({invalid_salaries} salaries, {invalid_experience} experience, {invalid_satisfaction} satisfaction scores.)")
        print("Preserved missing employee records rather than deleting them")

        return self



    def analyze(self):
        """Perform analysis and return a summary dictionary."""
        self.dept_salary = self.df.groupby("department")["salary"].mean()

        self.dept_satisfaction = self.df.groupby("department")["satisfaction_score"].mean()

        self.headcount = self.df.groupby("office_location").size()

        self.exp_vs_salary = self.df["salary"].corr(self.df["years_experience"])

        self.salary_satisfaction = self.df["salary"].corr(self.df["satisfaction_score"])

        self.location_satisfaction = self.df.groupby("office_location")["satisfaction_score"].mean()

        summary = {
            "avg_salary_by_dept": self.dept_salary,
            "avg_satisfaction_by_dept": self.dept_satisfaction,
            "headcount_by_location" : self.headcount,
            "experience_salary_correlation": self.exp_vs_salary,
            "avg_satisfaction_by_location": self.location_satisfaction
        }

        print(summary)
        return summary



    def visualize(self, output_path="output/charts.png"):
        """Generate and save visualizations."""

        fig, axes = plt.subplots(1, 3, figsize=(15, 5))

        # Chart 1: Average Salary by Department, Bar Chart
        sorted_salary = self.dept_salary.sort_values(ascending=False)
        axes[0].bar(sorted_salary.index, sorted_salary.values, color="royalblue")
        axes[0].set_title("Avg Salary by Department")
        axes[0].set_xlabel("Department")
        axes[0].set_ylabel("Salary ($)")
        axes[0].tick_params(axis="x", rotation=45)

        # Chart 2: Salary Distribution, Histogram
        self.df["salary"].hist(ax=axes[1], bins=10, color="firebrick", edgecolor="black")
        axes[1].set_title("Salary Distribution")
        axes[1].set_xlabel("Salary ($)")
        axes[1].set_ylabel("Count")

        # Chart 3: Salary vs Satisfaction, Scatter Plot Chart
        axes[2].scatter(self.df["salary"], self.df["satisfaction_score"])
        axes[2].set_title("Salary vs Satisfaction")
        axes[2].set_xlabel("Salary ($)")
        axes[2].set_ylabel("Satisfaction")

        plt.tight_layout()
        try:
            plt.savefig(output_path, dpi=150)
        except OSError as e:
            print(f"Error saving the charts: {e}")
            raise
        plt.show()

    def export(self, output_path="output/clean_data.csv"):
        """Export the cleaned data to a new CSV file."""
        try:
            self.df.to_csv(output_path, index=False)
        except OSError as e:
            print(f"Error saving file: {e}")
            raise

    def run(self):
        """Execute the full pipeline: Clean -> analyze -> visualize -> export."""
        os.makedirs("output", exist_ok=True)
        self.clean()
        summary = self.analyze()
        self.visualize()
        self.export()

        return summary