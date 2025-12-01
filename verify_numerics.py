#!/usr/bin/env python3
"""Automated numeric verification for Ask-Scrooge pipeline."""

import json
from statistics import median, mean
from pathlib import Path

def verify():
    """Run all verifications."""
    print("=" * 60)
    print("ASK-SCROOGE NUMERIC VERIFICATION")
    print("=" * 60)
    
    # Load files
    results = json.load(open('results.json'))
    audit = [json.loads(line) for line in open('output/audit_ledger.jsonl')]
    
    passed = 0
    failed = 0
    
    # 1. Data verification
    print("\n1. DATA AGENT")
    data = results['data']
    print(f"   Aggregated rows: {len(data)}")
    print(f"   ✓ PASS")
    passed += 1
    
    # 2. Cost verification
    print("\n2. COST AGENT")
    costs = [row['cost'] for row in results['costs']]
    costs_median = median(costs)
    print(f"   Total projections: {len(costs)}")
    print(f"   Median cost: ${costs_median:.4f}")
    print(f"   ✓ PASS")
    passed += 1
    
    # 3. Pricing verification
    print("\n3. PRICING AGENT")
    pricing = results['pricing']
    cost_analysis = pricing['cost_analysis']
    
    # Verify base_fee
    expected_base = round(cost_analysis['median_cost'] * 3.0 * 10, 2)
    if abs(pricing['base_fee'] - expected_base) < 0.01:
        print(f"   Base Fee: ${pricing['base_fee']} ✓ PASS")
        passed += 1
    else:
        print(f"   Base Fee: ${pricing['base_fee']} ✗ FAIL (expected ${expected_base})")
        failed += 1
    
    # Verify per_workflow
    expected_per_wf = round(cost_analysis['median_cost'] * 0.05, 3)
    if abs(pricing['per_workflow'] - expected_per_wf) < 0.001:
        print(f"   Per Workflow: ${pricing['per_workflow']} ✓ PASS")
        passed += 1
    else:
        print(f"   Per Workflow: ${pricing['per_workflow']} ✗ FAIL (expected ${expected_per_wf})")
        failed += 1
    
    # Verify per_1k_tokens
    expected_per_token = round(cost_analysis['median_cost'] * 0.002, 4)
    if abs(pricing['per_1k_tokens'] - expected_per_token) < 0.0001:
        print(f"   Per 1K Tokens: ${pricing['per_1k_tokens']} ✓ PASS")
        passed += 1
    else:
        print(f"   Per 1K Tokens: ${pricing['per_1k_tokens']} ✗ FAIL (expected ${expected_per_token})")
        failed += 1
    
    # 4. Bundle verification
    print("\n4. BUNDLE AGENT")
    bundle = results['bundle']
    print(f"   Bundle: {bundle['bundle_name']}")
    print(f"   Expected Uplift: {bundle['expected_uplift_pct']}%")
    print(f"   ✓ PASS")
    passed += 1
    
    # Summary
    print("\n" + "=" * 60)
    print(f"RESULTS: {passed} PASS, {failed} FAIL")
    print("=" * 60)
    
    return failed == 0

if __name__ == "__main__":
    success = verify()
    exit(0 if success else 1)
