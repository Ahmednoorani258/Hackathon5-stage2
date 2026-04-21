import re

with open("production/agent/tools.py", "r") as f:
    content = f.read()

# Fix resolve_customer_id
old_resolve = """    # Otherwise, create a new customer
    cust_id = await conn.fetchval("INSERT INTO customers (email) VALUES ($1) RETURNING id", identifier)
    return str(cust_id)"""

new_resolve = """    # Otherwise, check if it's an email or phone and insert accordingly
    if "@" in identifier:
        cust_id = await conn.fetchval("INSERT INTO customers (email) VALUES ($1) RETURNING id", identifier)
    else:
        # Assume it's a phone number
        cust_id = await conn.fetchval("INSERT INTO customers (phone) VALUES ($1) RETURNING id", identifier)
        
    return str(cust_id)"""

if old_resolve in content:
    content = content.replace(old_resolve, new_resolve)
else:
    print("WARNING: Could not find old_resolve block in tools.py")

with open("production/agent/tools.py", "w") as f:
    f.write(content)
print("tools.py updated")
