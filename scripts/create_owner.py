import argparse

# Placeholder: full owner creation will be wired to PostgreSQL auth tables.

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--email", required=True)
    parser.add_argument("--password", required=True)
    args = parser.parse_args()
    print(f"OWNER_BOOTSTRAP_REQUESTED email={args.email}")

if __name__ == "__main__":
    main()
