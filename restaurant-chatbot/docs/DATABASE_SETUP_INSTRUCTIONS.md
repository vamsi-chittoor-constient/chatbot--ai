# Database Setup Instructions

## Prerequisites:
- PostgreSQL installed on your local machine
- The dump file: `A24_restaurant_dev_dump.sql`

---

## Method 1: Using Command Line (Quickest - Recommended)

### Step 1: Open Terminal/Command Prompt

### Step 2: Navigate to the folder with the SQL file
```bash
cd /path/to/folder/with/sql/file
```

### Step 3: Run this command to create and populate the database
```bash
psql -U postgres -f A24_restaurant_dev_dump.sql
```

**If you need to enter a password**, use:
```bash
PGPASSWORD='your_postgres_password' psql -U postgres -f A24_restaurant_dev_dump.sql
```

**That's it!** The database `A24_restaurant_dev` will be created with all tables and data.

---

## Method 2: Using pgAdmin GUI

### Step 1: Open pgAdmin

### Step 2: Connect to your PostgreSQL server
- Expand **Servers** in the left panel
- Connect to your local PostgreSQL server

### Step 3: Open Query Tool
- Right-click on **PostgreSQL** server
- Select **Query Tool**

### Step 4: Open the SQL file
- In Query Tool, click **File** → **Open File**
- Navigate to and select `A24_restaurant_dev_dump.sql`
- Click **Open**

### Step 5: Execute the SQL
- Click the **Execute/Refresh** button (▶️ icon) or press **F5**
- Wait for completion (you'll see "Query returned successfully" at the bottom)

### Step 6: Verify the database was created
- In the left panel, right-click on **Databases** → **Refresh**
- You should see `A24_restaurant_dev` database
- Expand it to see **Schemas** → **public** → **Tables**
- All tables should be populated with data

---

## Method 3: Alternative Command Line (If Method 1 doesn't work)

### If the dump doesn't include CREATE DATABASE:

```bash
createdb -U postgres A24_restaurant_dev
psql -U postgres -d A24_restaurant_dev -f A24_restaurant_dev_dump.sql
```

**With password:**
```bash
PGPASSWORD='your_postgres_password' createdb -U postgres A24_restaurant_dev
PGPASSWORD='your_postgres_password' psql -U postgres -d A24_restaurant_dev -f A24_restaurant_dev_dump.sql
```

---

## Verify Everything Worked:

### Check tables exist:
```bash
psql -U postgres -d A24_restaurant_dev -c "\dt"
```

### Check row counts:
```bash
psql -U postgres -d A24_restaurant_dev -c "SELECT COUNT(*) FROM users;"
psql -U postgres -d A24_restaurant_dev -c "SELECT COUNT(*) FROM menu_items;"
```

### Or using pgAdmin:
- Right-click on any table → **View/Edit Data** → **First 100 Rows**

---

## Troubleshooting:

**Error: "database already exists"**
- Drop the existing database first:
  ```bash
  dropdb -U postgres A24_restaurant_dev
  ```
  Then run the restore command again

**Error: "permission denied"**
- Make sure you're using a superuser account (usually `postgres`)
- Or use your admin username instead of `postgres`

**Error: "psql: command not found"**
- PostgreSQL is not in your PATH
- Use full path: `C:\Program Files\PostgreSQL\15\bin\psql` (Windows)
- Or: `/usr/local/bin/psql` (Mac/Linux)

---

## Database Connection Details:

After setup, use these credentials in your application:

```
Host: localhost
Port: 5432
Database: A24_restaurant_dev
Username: postgres (or your PostgreSQL username)
Password: (your PostgreSQL password)
```

---

**That's it! The database is ready to use with all schema and data.**
