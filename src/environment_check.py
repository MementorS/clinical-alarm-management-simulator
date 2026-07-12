import sys

import numpy as np
import pandas as pd
import matplotlib
import streamlit
import wfdb


def main():
    print("Clinical Alarm Management Simulator")
    print("-----------------------------------")

    print(f"Python executable: {sys.executable}")
    print(f"Python version: {sys.version}")

    print(f"NumPy version: {np.__version__}")
    print(f"Pandas version: {pd.__version__}")
    print(f"Matplotlib version: {matplotlib.__version__}")
    print(f"Streamlit version: {streamlit.__version__}")
    print(f"WFDB version: {wfdb.__version__}")

    print("-----------------------------------")
    print("Phase 1 environment test successful.")
    print("Target Roles: Clinical Application Specialist and Product Specialist")


if __name__ == "__main__":
    main()