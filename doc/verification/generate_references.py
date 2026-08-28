# verification/generate_references.py

import json
import datetime
from pathlib import Path
import os
from contextlib import contextmanager
from pytRIBS.classes import Results

# =============================================================================
# SCRIPT CONFIGURATION
# =============================================================================
TRIBS_VERSION = "6.0.0"
REFERENCE_FILE_OUTPUT = Path("doc/verification/reference_values.json")

# Define the root directories for each benchmark case
POINT_SCALE_ROOT = Path("point-scale-happy-jack")
WATERSHED_ROOT = Path("watershed-scale-big-spring")

# =============================================================================
# HELPER FUNCTION
# =============================================================================

@contextmanager
def working_directory(path):
    """A context manager that temporarily changes the working directory."""
    original_cwd = os.getcwd()
    try:
        os.chdir(path)
        yield
    finally:
        os.chdir(original_cwd)

# =============================================================================
# CORE LOGIC
# =============================================================================

def generate_mrf_water_balance(benchmark_root: Path, in_file_name: str) -> dict:
    """
    Loads model results using pytRIBS and extracts the entire water balance table.

    Args:
        benchmark_root: Path to the root of the benchmark directory.
        in_file_name: The name of the specific .in file to process.

    Returns:
        A dictionary representing the water balance values.
    """
    print(f"Processing: {in_file_name}...")
    relative_in_path = Path("src/in_files") / in_file_name

    with working_directory(benchmark_root):
        if not relative_in_path.exists():
            raise FileNotFoundError(f"Input file not found at: {benchmark_root / relative_in_path}")

        results = Results(str(relative_in_path))
        results.get_mrf_results()
        results.get_mrf_water_balance("full")
        
        water_balance_df = results.mrf['waterbalance']

        # CORRECTED LINE: Select the first row and convert it to a dictionary.
        water_balance_dict = water_balance_df.iloc[0].to_dict()

    print("...Done.")
    return water_balance_dict

def main():
    """Main driver for the script."""
    print("Starting reference value generation...")

    if not WATERSHED_ROOT.is_dir() or not POINT_SCALE_ROOT.is_dir():
        print("\nERROR: This script must be run from the root of the 'tRIBS-benchmarks' repository.")
        return

    reference_data = {
        "tRIBS_version": TRIBS_VERSION,
        "file_format_version": "1.1",
        "generated_on_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "benchmarks": {
            "point-scale-happy-jack": {
                "description": "Point-scale simulation at the Happy Jack site.",
                "values": generate_mrf_water_balance(POINT_SCALE_ROOT, "happy_jack.in")
            },
            "watershed-scale-serial": {
                "description": "Watershed-scale simulation for Big Spring basin in serial mode.",
                "values": generate_mrf_water_balance(WATERSHED_ROOT, "big_spring.in")
            },
            "watershed-scale-parallel": {
                "description": "Watershed-scale simulation for Big Spring basin in parallel mode.",
                "values": generate_mrf_water_balance(WATERSHED_ROOT, "big_spring_par.in")
            }
        }
    }

    print(f"\nWriting reference values to '{REFERENCE_FILE_OUTPUT}'...")
    with open(REFERENCE_FILE_OUTPUT, 'w') as f:
        json.dump(reference_data, f, indent=4)

    print("Successfully generated reference file.")

if __name__ == "__main__":
    main()