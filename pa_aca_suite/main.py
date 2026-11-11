import subprocess
import sys

def run(cmd):
    print(f"Executing: {cmd}")
    subprocess.run(cmd, shell=True, check=True)

def main():
    print("🦆 Welcome to the PA-ACA Analysis Suite! Quack!")
    print("1. Extract Data & Generate Docs")
    print("2. Run Audit Tool (Visuals/Calculators)")
    print("3. Exit")
    
    choice = input("\nSelect an option: ")
    
    if choice == "1":
        run("python3 extractor.py")
        run("python3 docs.py")
    elif choice == "2":
        prem = input("Enter current monthly premium (or press Enter to skip): ")
        min_r = input("Enter minimum rate filter (or press Enter to skip): ")
        
        cmd = "python3 audit.py"
        if prem: cmd += f" --premium {prem}"
        if min_r: cmd += f" --min {min_r}"
        run(cmd)
    else:
        print("Waddling away... Goodbye!")

if __name__ == "__main__":
    main()
