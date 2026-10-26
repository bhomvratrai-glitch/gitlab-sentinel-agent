import os

# CWE-798: Hardcoded credential
api_key = "secret_production_gitlab_token_99999"

def ping_host(host: str) -> None:
    # CWE-78: Command Injection
    os.system(f"echo pinging {host}")

def get_user_query(user_id: int) -> str:
    # CWE-89: SQL Injection pattern
    query = f"SELECT * FROM users WHERE id = {user_id}"
    return query

def parse_config(raw_string: str):
    # CWE-94: Code Injection
    return eval(raw_string)

def calculate_checksum(val: int) -> int:
    return val * 42
