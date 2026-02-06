"""
Pre-Phase 5 Test Script
Verifies system stability before implementing Phase 5
"""

import sqlite3
import sys

print("=" * 60)
print("PRE-PHASE 5 STABILITY TEST")
print("=" * 60)
print()

results = {"passed": 0, "failed": 0}

def test_pass(name):
    results["passed"] += 1
    print(f"  ✅ PASS: {name}")

def test_fail(name, error=""):
    results["failed"] += 1
    print(f"  ❌ FAIL: {name} - {error}")

# Test 1: Database Connection
print("📦 Test 1: Database Connection")
try:
    conn = sqlite3.connect('integrated_users.db')
    cursor = conn.cursor()
    test_pass("Database connection")
except Exception as e:
    test_fail("Database connection", str(e))
    sys.exit(1)

# Test 2: Critical Tables Exist
print("\n📦 Test 2: Critical Tables")
critical_tables = [
    'users',
    'history_primary', 
    'history_secondary',
    'psychology_traits',
    'ai_usage_log'
]

cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
existing_tables = [r[0] for r in cursor.fetchall()]

for table in critical_tables:
    if table in existing_tables:
        test_pass(f"Table: {table}")
    else:
        test_fail(f"Table: {table}", "Not found")

# Test 3: Inferred Traits Table
print("\n📦 Test 3: Trait Inference Tables")
trait_tables = ['inferred_traits', 'inferred_personality']
found_trait_table = False
for t in trait_tables:
    if t in existing_tables:
        test_pass(f"Trait table: {t}")
        found_trait_table = True
        break

if not found_trait_table:
    test_fail("Trait inference table", "Neither inferred_traits nor inferred_personality found")

# Test 4: AI Budget Tables
print("\n📦 Test 4: AI Budget Tables")
budget_tables = ['ai_usage_log', 'ai_usage_patterns', 'ai_budget_notifications']
for table in budget_tables:
    if table in existing_tables:
        test_pass(f"Budget table: {table}")
    else:
        test_fail(f"Budget table: {table}", "Not found (may be created on first use)")

# Test 5: Import Core Modules
print("\n📦 Test 5: Core Module Imports")
try:
    from integrated_database import IntegratedDatabase
    test_pass("Import: IntegratedDatabase")
except Exception as e:
    test_fail("Import: IntegratedDatabase", str(e))

try:
    from smart_response.trait_inference import TraitInferenceEngine
    test_pass("Import: TraitInferenceEngine")
except Exception as e:
    test_fail("Import: TraitInferenceEngine", str(e))

try:
    from smart_response.ai_budget_manager import AIBudgetManager
    test_pass("Import: AIBudgetManager")
except Exception as e:
    test_fail("Import: AIBudgetManager", str(e))

try:
    from smart_response.dual_layer_history import DualLayerHistorySystem
    test_pass("Import: DualLayerHistorySystem")
except Exception as e:
    test_fail("Import: DualLayerHistorySystem", str(e))

# Test 6: Character Configs
print("\n📦 Test 6: Character Configurations")
try:
    from smart_response.characters.configs import DOMAIN_CHARACTER_CONFIGS, PHILOSOPHY_CHARACTER_CONFIGS
    domain_count = len(DOMAIN_CHARACTER_CONFIGS)
    philosophy_count = len(PHILOSOPHY_CHARACTER_CONFIGS)
    test_pass(f"Character configs loaded ({domain_count} domain, {philosophy_count} philosophy)")
except Exception as e:
    test_fail("Character configs", str(e))

# Summary
conn.close()
print()
print("=" * 60)
total = results["passed"] + results["failed"]
print(f"RESULTS: {results['passed']}/{total} tests passed")
print("=" * 60)

if results["failed"] == 0:
    print("\n✅ ALL TESTS PASSED - Ready for Phase 5!")
else:
    print(f"\n⚠️  {results['failed']} test(s) failed - Review before proceeding")
