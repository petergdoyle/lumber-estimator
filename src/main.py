import os

def main():
    print("Lumber Estimator Initialized")
    print(f"Working directory: {os.getcwd()}")
    
    # Placeholder for future logic
    input_dir = 'data'
    output_dir = 'output'
    
    if not os.path.exists(input_dir):
        print(f"Warning: {input_dir} directory not found.")
    else:
        files = os.listdir(input_dir)
        print(f"Input files found: {[f for f in files if not f.startswith('.') ]}")

if __name__ == "__main__":
    main()
