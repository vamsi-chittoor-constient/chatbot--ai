"""
Menu Sync Debug Test Script
============================
Automated test to verify debug logging for zero/null price items.

Usage:
    python test_menu_sync_debug.py
"""

import subprocess
import time
import re
from datetime import datetime

def run_command(cmd, shell=True):
    """Run shell command and return output"""
    try:
        result = subprocess.run(
            cmd,
            shell=shell,
            capture_output=True,
            text=True,
            timeout=30
        )
        return result.stdout + result.stderr
    except Exception as e:
        return f"Error: {str(e)}"

def print_section(title):
    """Print formatted section header"""
    print("\n" + "=" * 80)
    print(f"  {title}")
    print("=" * 80 + "\n")

def check_services():
    """Check if required services are running"""
    print_section("1. CHECKING SERVICES")

    output = run_command("docker compose -f docker-compose.root.yml ps")

    services = {
        'petpooja-app': 'healthy' in output or 'running' in output.lower(),
        'chatbot-app': 'healthy' in output or 'running' in output.lower(),
        'postgres': 'healthy' in output or 'running' in output.lower()
    }

    for service, status in services.items():
        icon = "✅" if status else "❌"
        print(f"{icon} {service}: {'Running' if status else 'Not Running'}")

    return all(services.values())

def get_zero_price_count():
    """Get count of items with zero price"""
    cmd = """docker exec a24-postgres psql -U admin -d restaurant_ai -c "SELECT COUNT(*) FROM menu_item WHERE is_deleted = FALSE AND menu_item_price = 0;" -t"""
    output = run_command(cmd)

    try:
        count = int(output.strip())
        return count
    except:
        return None

def get_zero_price_items():
    """Get list of zero-price items"""
    cmd = """docker exec a24-postgres psql -U admin -d restaurant_ai -c "SELECT menu_item_name, ext_petpooja_item_id FROM menu_item WHERE is_deleted = FALSE AND menu_item_price = 0 ORDER BY menu_item_name LIMIT 10;" """
    return run_command(cmd)

def restart_petpooja():
    """Restart PetPooja service"""
    print_section("3. RESTARTING PETPOOJA SERVICE")
    print("Triggering restart to force menu sync...")

    output = run_command("docker compose -f docker-compose.root.yml restart petpooja-app")
    print("Service restarted successfully")

def wait_for_sync(seconds=15):
    """Wait for sync to complete"""
    print(f"\nWaiting {seconds} seconds for sync to complete...")
    for i in range(seconds):
        time.sleep(1)
        print(f"  {i+1}/{seconds}", end='\r')
    print()

def check_logs_for_warnings():
    """Check logs for debug warnings"""
    print_section("4. CHECKING LOGS FOR DEBUG WARNINGS")

    # Get logs from last 60 seconds
    cmd = "docker compose -f docker-compose.root.yml logs petpooja-app --since 60s"
    output = run_command(cmd)

    # Find warning lines
    warning_pattern = r"WARNING.*empty/zero price.*"
    warnings = re.findall(warning_pattern, output, re.IGNORECASE)

    print(f"Found {len(warnings)} debug warnings:\n")

    if warnings:
        for warning in warnings[:10]:  # Show first 10
            # Extract item name and price value
            match = re.search(r"Item '([^']+)'.*price: (.+)", warning)
            if match:
                item_name = match.group(1)
                price_value = match.group(2).strip()
                print(f"  ⚠️  {item_name:40s} → Price: {price_value}")

        if len(warnings) > 10:
            print(f"\n  ... and {len(warnings) - 10} more warnings")
    else:
        print("  ❌ No debug warnings found")
        print("\n  Possible reasons:")
        print("     - Sync hasn't completed yet")
        print("     - All items have valid prices")
        print("     - Logs not enabled")

    return len(warnings)

def verify_database_updates():
    """Check if database was updated recently"""
    print_section("5. VERIFYING DATABASE UPDATES")

    cmd = """docker exec a24-postgres psql -U admin -d restaurant_ai -c "SELECT menu_item_name, menu_item_price, TO_CHAR(updated_at, 'HH24:MI:SS') as update_time FROM menu_item WHERE is_deleted = FALSE AND menu_item_price = 0 AND updated_at > NOW() - INTERVAL '5 minutes' ORDER BY updated_at DESC LIMIT 5;" """

    output = run_command(cmd)

    if "rows)" in output:
        row_match = re.search(r'\((\d+) rows?\)', output)
        if row_match:
            count = int(row_match.group(1))
            print(f"✅ {count} zero-price items updated in last 5 minutes\n")
            print(output)
        else:
            print("❌ No items updated recently")
    else:
        print(output)

def analyze_price_values():
    """Analyze what price values are in database"""
    print_section("6. ANALYZING PRICE VALUES")

    cmd = """docker exec a24-postgres psql -U admin -d restaurant_ai -c "SELECT CASE WHEN menu_item_price = 0 THEN 'Zero' WHEN menu_item_price IS NULL THEN 'NULL' ELSE 'Valid' END as price_category, COUNT(*) FROM menu_item WHERE is_deleted = FALSE GROUP BY price_category;" """

    output = run_command(cmd)
    print(output)

def main():
    """Main test flow"""
    print("\n" + "=" * 80)
    print("  MENU SYNC DEBUG TEST")
    print("  Testing debug logging for zero/null price items")
    print("=" * 80)
    print(f"\n  Test Start: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")

    # Step 1: Check services
    if not check_services():
        print("\n❌ ERROR: Required services are not running!")
        print("   Please start services with:")
        print("   docker compose -f docker-compose.root.yml up -d")
        return

    # Step 2: Get baseline count
    print_section("2. BASELINE DATA")

    before_count = get_zero_price_count()
    if before_count is not None:
        print(f"Current zero-price items: {before_count}")

        if before_count > 0:
            print("\nSample zero-price items:")
            print(get_zero_price_items())
    else:
        print("❌ Could not get zero-price count")

    # Step 3: Restart service
    restart_petpooja()

    # Step 4: Wait for sync
    wait_for_sync(15)

    # Step 5: Check logs
    warning_count = check_logs_for_warnings()

    # Step 6: Verify updates
    verify_database_updates()

    # Step 7: Analyze
    analyze_price_values()

    # Summary
    print_section("TEST SUMMARY")

    print(f"Baseline zero-price items: {before_count}")
    print(f"Debug warnings found:      {warning_count}")

    if warning_count > 0 and before_count > 0:
        coverage = (warning_count / before_count) * 100
        print(f"Coverage:                  {coverage:.1f}%")

    print("\n" + "=" * 80)
    print("  RECOMMENDATIONS")
    print("=" * 80)

    if warning_count == 0:
        print("\n⚠️  No debug warnings detected")
        print("\n   Next steps:")
        print("   1. Check if sync completed: docker compose -f docker-compose.root.yml logs petpooja-app")
        print("   2. Verify logging is enabled")
        print("   3. Try manual sync if available")
    elif warning_count > 0:
        print("\n✅ Debug logging is working!")
        print("\n   Next steps:")
        print("   1. Review warning details in logs")
        print("   2. Identify which items need price updates")
        print("   3. Contact restaurant to update prices in PetPooja dashboard")
        print("   4. Or implement frontend 'Market Price' display")

    if before_count and before_count > 20:
        print(f"\n⚠️  High number of zero-price items ({before_count})")
        print("   Consider implementing frontend handling for these items")

    print("\n" + "=" * 80)
    print(f"  Test End: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 80 + "\n")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nTest interrupted by user")
    except Exception as e:
        print(f"\n\n❌ ERROR: {str(e)}")
        import traceback
        traceback.print_exc()
