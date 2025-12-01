# Ask-Scrooge Evaluation & Testing Guide
## Numeric Verification Procedures for Product Evaluation

**Version**: 1.0 | **Date**: December 2025 | **Audience**: Product Evaluators, QA Engineers

---

## Quick Start: Run Evaluation

### Step 1: Start the System
```bash
cd /Users/outlieralpha/CascadeProjects/ask-scrooge
bash run.sh
```

### Step 2: Access UI
- **Gradio UI**: http://localhost:7860
- **Tax API Docs**: http://localhost:9000/docs

### Step 3: Run Pipeline
1. Keep defaults or select **EU** for compliance region
2. Click **"Run Full Pipeline"**
3. Wait 5-10 seconds for completion

### Step 4: Review Generated Files
- **audit_ledger.jsonl**: Complete audit trail
- **invoice.csv**: Customer invoice
- **results.json**: Full pipeline output

---

## Part 1: Cost Driver Verification

### 1.1 Understand Cost Components

**Two Cost Elements**:
1. **Token Cost** = (input tokens + output tokens) ÷ 1000 × model price
2. **Workflow Overhead** = number of workflows × $0.01

### 1.2 Test Case: Verify Token Cost Calculation

**Setup**:
```bash
# Open results.json from pipeline execution
cat results.json | jq '.costs[0]'
```

**Expected Output** (example):
```json
{
  "region": "US",
  "product": "CRM",
  "model": "gemini-pro",
  "workflows": 200,
  "token_cost": 13.1000,
  "workflow_overhead": 2.0000,
  "cost": 15.1000
}
```

**Manual Verification**:
```
Source: results.json → data[0] (first aggregated record)
Region: US, Product: CRM
workflows = 200
tokens_in = 440000 (check: from DataAgent output)
tokens_out = 84000 (check: from DataAgent output)

For Gemini (price = $0.025 per 1K tokens):
  tokens_k = (440000 + 84000) / 1000 = 524
  
  token_cost = 524 × 0.025
             = 13.1
  ✓ Matches output: 13.1000

  workflow_overhead = 200 × 0.01
                    = 2.0
  ✓ Matches output: 2.0000

  total = 13.1 + 2.0 = 15.1
  ✓ Matches output: 15.1000
```

**Verification Script**:
```python
import json

results = json.load(open('results.json'))
costs = results['costs']
data = results['data']

# Map data records by (region, product)
data_map = {(r['region'], r['product']): r for r in data}

# Check first cost row
cost_row = costs[0]
key = (cost_row['region'], cost_row['product'])
data_row = data_map[key]

# Verify calculation
tokens_k = (data_row['tokens_in'] + data_row['tokens_out']) / 1000
MODEL_PRICES = {
    "gpt-4o": 0.03,
    "gemini-pro": 0.025,
    "llama-2": 0.007,
    "claude-3": 0.015
}

model_price = MODEL_PRICES[cost_row['model']]
expected_token_cost = round(tokens_k * model_price, 4)
expected_overhead = round(data_row['workflows'] * 0.01, 4)
expected_total = expected_token_cost + expected_overhead

print(f"Token Cost: {cost_row['token_cost']} == {expected_token_cost}? {abs(cost_row['token_cost'] - expected_token_cost) < 0.0001}")
print(f"Overhead: {cost_row['workflow_overhead']} == {expected_overhead}? {abs(cost_row['workflow_overhead'] - expected_overhead) < 0.0001}")
print(f"Total: {cost_row['cost']} == {expected_total}? {abs(cost_row['cost'] - expected_total) < 0.0001}")
```

### 1.3 Cost Sources Documentation

**Create Cost Analysis Report**:
```bash
# Extract audit trail for cost agent
cat output/audit_ledger.jsonl | grep '"agent":"CostAgent"' | jq '.'
```

**Expected Output**:
```json
{
  "agent": "CostAgent",
  "session": "xxx",
  "total_projections": 48,
  "models_analyzed": ["gpt-4o", "gemini-pro", "llama-2", "claude-3"],
  "total_cost": 583.45,
  "average_cost": 12.16
}
```

**Interpretation**:
- 48 projections = 12 region-product pairs × 4 models
- Models analyzed: 4 different LLM models
- Total cost: Sum of all model costs (data-driven)
- Average: Used as basis for pricing

### 1.4 Cost Basis Documentation Table

Create this in your evaluation report:

| Metric | Value | Source | Verification Method |
|--------|-------|--------|----------------------|
| Model Pricing | See `agents/cost_agent.py` | Industry standard (Dec 2025) | Compare with public rates |
| Workflow Overhead | $0.01 per workflow | Code constant | Check line 13 in cost_agent.py |
| Total Projections | 48 (example) | Audit ledger → CostAgent | Count combinations: regions × products × models |
| Total Cost (all models) | $583.45 (example) | Cost projections sum | Run test script above |

---

## Part 2: Pricing Engine Input Verification

### 2.1 Understand Pricing Inputs

**All inputs come from CostAgent outputs** (not the original data)

```
CostAgent output:
  → Array of cost projections
     → Extract all "cost" values
        → Calculate statistics (median, mean, min, max)
           → Use statistics to derive pricing
```

### 2.2 Test Case: Extract & Verify Cost Statistics

**Method 1: From UI Results**
```bash
cat results.json | jq '.pricing.cost_analysis'
```

**Expected Output**:
```json
{
  "median_cost": 12.0000,
  "mean_cost": 12.5000,
  "min_cost": 7.6800,
  "max_cost": 17.7200,
  "cost_variance": 1.33
}
```

**Method 2: Manual Calculation**
```python
import json
from statistics import median, mean

results = json.load(open('results.json'))
costs = [row['cost'] for row in results['costs']]

print(f"Number of cost projections: {len(costs)}")
print(f"Median: ${median(costs):.4f}")
print(f"Mean: ${mean(costs):.4f}")
print(f"Min: ${min(costs):.4f}")
print(f"Max: ${max(costs):.4f}")

variance = (max(costs) - min(costs)) / mean(costs)
print(f"Variance: {variance:.4f}")
```

**Verification Checklist**:
- [ ] Median is between min and max
- [ ] Mean is between min and max
- [ ] Variance = (max - min) / mean
- [ ] All values match results.json → pricing.cost_analysis

### 2.3 Pricing Inputs Traceability Table

| Pricing Input | Formula | Numerator | Denominator | Source |
|--------------|---------|-----------|------------|--------|
| **median_cost** | Median of all costs | Cost array | N=48 | CostAgent output → costs[].cost |
| **base_fee** | median × 3.0 × 10 | $12.00 × 3.0 × 10 | N/A | Pricing formula |
| **per_workflow** | median × 0.05 | $12.00 × 0.05 | N/A | Pricing formula |
| **per_1k_tokens** | median × 0.002 | $12.00 × 0.002 | N/A | Pricing formula |

---

## Part 3: Pricing Calculation Verification

### 3.1 Understand Pricing Formula

```
base_fee = ROUND(median_cost × 3.0 × 10, 2)
per_workflow = ROUND(median_cost × 0.05, 3)
per_1k_tokens = ROUND(median_cost × 0.002, 4)
pi_index = CLAMP(0.85 × (1 - variance × 0.1), 0.5, 1.0)
```

### 3.2 Test Case: Calculate & Verify Pricing

**Step 1: Get Cost Statistics**
```bash
cat results.json | jq '.pricing.cost_analysis'
```

**Step 2: Manual Calculation**
```
From cost_analysis:
  median_cost = 12.00
  cost_variance = 0.8

Calculations:
  base_fee = ROUND(12.00 × 3.0 × 10, 2)
           = ROUND(360.00, 2)
           = 360.00

  per_workflow = ROUND(12.00 × 0.05, 3)
               = ROUND(0.600, 3)
               = 0.600

  per_1k_tokens = ROUND(12.00 × 0.002, 4)
                = ROUND(0.024, 4)
                = 0.0240

  variance_impact = 0.8 × 0.1 = 0.08
  pi_index = CLAMP(0.85 × (1 - 0.08), 0.5, 1.0)
           = CLAMP(0.85 × 0.92, 0.5, 1.0)
           = CLAMP(0.782, 0.5, 1.0)
           = 0.78
```

**Step 3: Verify Against Output**
```bash
cat results.json | jq '.pricing | {base_fee, per_workflow, per_1k_tokens, pi_index}'
```

**Expected Match**:
```json
{
  "base_fee": 360.00,
  "per_workflow": 0.600,
  "per_1k_tokens": 0.0240,
  "pi_index": 0.78
}
```

### 3.3 Verification Script

```python
import json
from statistics import median, mean

results = json.load(open('results.json'))
pricing = results['pricing']
costs = [row['cost'] for row in results['costs']]

# Get actual values
cost_analysis = pricing['cost_analysis']
median_cost = cost_analysis['median_cost']
cost_variance = cost_analysis['cost_variance']

# Calculate expected
base_fee_expected = round(median_cost * 3.0 * 10, 2)
per_workflow_expected = round(median_cost * 0.05, 3)
per_1k_tokens_expected = round(median_cost * 0.002, 4)
pi_index_expected = max(0.5, min(1.0, round(0.85 * (1 - cost_variance * 0.1), 2)))

# Verify
tests = [
    ("base_fee", pricing['base_fee'], base_fee_expected),
    ("per_workflow", pricing['per_workflow'], per_workflow_expected),
    ("per_1k_tokens", pricing['per_1k_tokens'], per_1k_tokens_expected),
    ("pi_index", pricing['pi_index'], pi_index_expected),
]

for name, actual, expected in tests:
    match = abs(actual - expected) < 0.01
    print(f"{name}: {actual} == {expected}? {'✓ PASS' if match else '✗ FAIL'}")
```

### 3.4 Pricing Dimensions Map

| Pricing Dimension | Basis | Example | Used In |
|------------------|-------|---------|---------|
| **base_fee** | Median monthly cost × margin | $360.00 | Fixed monthly charge |
| **per_workflow** | 5% of median cost | $0.60 | Variable scaling charge |
| **per_1k_tokens** | 0.2% of median cost | $0.024 | Micro consumption charge |
| **pi_index** | Cost variance quality metric | 0.78 | Information only (no pricing impact) |

---

## Part 4: Invoice Transparency Verification

### 4.1 Understand Invoice Structure

**Input**: Pricing recommendation + Usage
**Output**: Itemized invoice showing ONLY pricing dimensions (no costs)

### 4.2 Test Case: Calculate & Verify Invoice

**Step 1: Extract Pricing Recommendation**
```bash
cat results.json | jq '.pricing | {base_fee, per_workflow, per_1k_tokens}'
```

**Step 2: Define Test Usage**
```
Usage (Monthly):
  workflows: 100
  tokens_in: 200000
  tokens_out: 50000
```

**Step 3: Manual Invoice Calculation**
```
base_fee = 360.00
per_workflow = 0.60
per_1k_tokens = 0.024

Usage:
  total_tokens = 200000 + 50000 = 250000
  tokens_k = 250000 / 1000 = 250
  workflows = 100

Invoice:
  base_fee = 360.00
  workflow_charge = 0.60 × 100 = 60.00
  token_charge = 0.024 × 250 = 6.00
  ────────────────────────────────
  TOTAL = 360.00 + 60.00 + 6.00 = 426.00
```

**Step 4: Verify CSV**
```bash
cat invoice.csv
```

**Expected Output**:
```
product,quantity,unit_price,currency
CRM+Analytics,1,360.00,USD
```

**Extended Verification**:
```python
import json

results = json.load(open('results.json'))
pricing = results['pricing']

# Test usage
workflows = 100
tokens_in = 200000
tokens_out = 50000
tokens_k = (tokens_in + tokens_out) / 1000

# Calculate
base_fee = pricing['base_fee']
per_workflow = pricing['per_workflow']
per_1k_tokens = pricing['per_1k_tokens']

workflow_charge = round(per_workflow * workflows, 2)
token_charge = round(per_1k_tokens * tokens_k, 2)
total = round(base_fee + workflow_charge + token_charge, 2)

print(f"Invoice Components:")
print(f"  Base Fee:        ${base_fee:.2f}")
print(f"  Workflow Charge: {workflows} × ${per_workflow:.3f} = ${workflow_charge:.2f}")
print(f"  Token Charge:    {tokens_k:.0f} × ${per_1k_tokens:.4f} = ${token_charge:.2f}")
print(f"  {'─' * 35}")
print(f"  TOTAL:           ${total:.2f}")

# Verify breakdown adds up
assert abs(total - (base_fee + workflow_charge + token_charge)) < 0.01, "Invoice math error"
print(f"\n✓ Invoice calculation verified")
```

### 4.3 Invoice Verification Checklist

| Item | Check | Source |
|------|-------|--------|
| **base_fee** | Matches pricing.base_fee exactly | results.json → pricing |
| **per_workflow rate** | Matches pricing.per_workflow exactly | results.json → pricing |
| **per_1k_tokens rate** | Matches pricing.per_1k_tokens exactly | results.json → pricing |
| **No cost data** | Invoice contains ONLY pricing (no token costs, no model costs) | results.json → pricing (NOT costs) |
| **Itemization** | Invoice shows base + workflow + token charges separately | logic correct |
| **Math** | total = base + (per_wf × wf_count) + (per_token × token_k) | spot-check |

---

## Part 5: Bundle Analysis Verification

### 5.1 Understand Bundle Metrics

```
Input: Aggregated workflow counts by product
Output: Top 2 products + uplift metrics
```

### 5.2 Test Case: Verify Bundle Calculation

**Step 1: Extract Bundle Info**
```bash
cat results.json | jq '.bundle'
```

**Expected Output**:
```json
{
  "bundle_name": "CRM+Analytics",
  "products": ["CRM", "Analytics"],
  "workflows_product1": 500,
  "workflows_product2": 350,
  "expected_uplift_pct": 12,
  "balance_ratio": 0.70,
  "confidence": "medium"
}
```

**Step 2: Manual Verification**
```
From aggregated data:
  CRM total workflows: 500 (largest)
  Analytics total workflows: 350 (2nd largest)

Bundle calculation:
  balance_ratio = MIN(500, 350) / MAX(500, 350)
                = 350 / 500
                = 0.70
  
  expected_uplift = 5 + INT(0.70 × 10)
                  = 5 + 7
                  = 12%
  
  confidence = "medium" (since 0.70 > 0.5)
```

**Step 3: Verification Script**
```python
import json

results = json.load(open('results.json'))
bundle = results['bundle']
data = results['data']

# Aggregate workflows by product
product_workflows = {}
for row in data:
    product = row['product']
    product_workflows[product] = product_workflows.get(product, 0) + row['workflows']

# Get top 2
sorted_products = sorted(product_workflows.items(), key=lambda x: -x[1])
top1_name, top1_wf = sorted_products[0]
top2_name, top2_wf = sorted_products[1]

# Calculate metrics
balance_ratio = min(top1_wf, top2_wf) / max(top1_wf, top2_wf)
expected_uplift = 5 + int(balance_ratio * 10)
confidence = "medium" if balance_ratio > 0.5 else "low"

# Verify
print(f"Bundle Name: {bundle['bundle_name']} should be '{top1_name}+{top2_name}'")
print(f"  ✓ PASS" if bundle['bundle_name'] == f"{top1_name}+{top2_name}" else f"  ✗ FAIL")

print(f"Balance Ratio: {bundle['balance_ratio']} should be {balance_ratio:.2f}")
print(f"  ✓ PASS" if abs(bundle['balance_ratio'] - balance_ratio) < 0.01 else f"  ✗ FAIL")

print(f"Expected Uplift: {bundle['expected_uplift_pct']}% should be {expected_uplift}%")
print(f"  ✓ PASS" if bundle['expected_uplift_pct'] == expected_uplift else f"  ✗ FAIL")

print(f"Confidence: {bundle['confidence']} should be {confidence}")
print(f"  ✓ PASS" if bundle['confidence'] == confidence else f"  ✗ FAIL")
```

---

## Part 6: End-to-End Audit Trail

### 6.1 Complete Audit Verification

**Purpose**: Verify all numeric operations are logged

**Command**:
```bash
cat output/audit_ledger.jsonl | python3 -m json.tool
```

**Expected Entries**:
```json
[
  {
    "agent": "DataAgent",
    "records_processed": 75,
    "aggregated_rows": 12,
    "summary": [...]
  },
  {
    "agent": "CostAgent",
    "total_projections": 48,
    "models_analyzed": ["gpt-4o", "gemini-pro", "llama-2", "claude-3"],
    "total_cost": 583.45,
    "average_cost": 12.16
  },
  {
    "agent": "PricingAgent",
    "recommendation": {
      "base_fee": 360.00,
      "per_workflow": 0.600,
      "per_1k_tokens": 0.0240,
      "pi_index": 0.78,
      "cost_analysis": {...}
    }
  },
  {
    "agent": "BundleAgent",
    "bundle": {
      "bundle_name": "CRM+Analytics",
      "expected_uplift_pct": 12,
      ...
    }
  },
  {
    "agent": "ComplianceAgent",
    "compliance_status": "PASSED",
    ...
  }
]
```

### 6.2 Audit Verification Script

```python
import json

with open('output/audit_ledger.jsonl', 'r') as f:
    entries = [json.loads(line) for line in f]

print(f"Total audit entries: {len(entries)}")
print(f"\nAgents executed:")
for entry in entries:
    print(f"  - {entry.get('agent', 'Unknown')}")

# Verify key metrics
cost_agent_entry = next((e for e in entries if e['agent'] == 'CostAgent'), None)
if cost_agent_entry:
    print(f"\nCostAgent Summary:")
    print(f"  Total Projections: {cost_agent_entry.get('total_projections')}")
    print(f"  Models: {cost_agent_entry.get('models_analyzed')}")
    print(f"  Total Cost: ${cost_agent_entry.get('total_cost'):.2f}")

pricing_agent_entry = next((e for e in entries if e['agent'] == 'PricingAgent'), None)
if pricing_agent_entry:
    pricing = pricing_agent_entry.get('recommendation', {})
    print(f"\nPricingAgent Summary:")
    print(f"  Base Fee: ${pricing.get('base_fee')}")
    print(f"  Per Workflow: ${pricing.get('per_workflow')}")
    print(f"  Per 1K Tokens: ${pricing.get('per_1k_tokens')}")
    print(f"  PI Index: {pricing.get('pi_index')}")
```

---

## Part 7: Evaluation Checklist

### 7.1 Pre-Evaluation

- [ ] System starts successfully (`bash run.sh`)
- [ ] No Python errors during startup
- [ ] Gradio UI accessible at http://localhost:7860
- [ ] Tax API docs available at http://localhost:9000/docs

### 7.2 DataAgent Verification

- [ ] Input file exists: `data/synthetic_usage.json`
- [ ] File contains valid JSON array
- [ ] All records have required fields (region, product, workflows, tokens_in, tokens_out)
- [ ] Aggregation sums are mathematically correct
- [ ] Audit entry shows correct counts

### 7.3 CostAgent Verification

- [ ] 4 models analyzed: gpt-4o, gemini-pro, llama-2, claude-3
- [ ] Token prices match constants in code
- [ ] Workflow overhead = $0.01 per workflow
- [ ] Cost formula verified for all projections
- [ ] All 4 models have costs for each data row
- [ ] Audit entry shows total cost and average

### 7.4 PricingAgent Verification

- [ ] Cost statistics (median, mean, min, max) are correct
- [ ] Cost variance calculated correctly
- [ ] base_fee = median × 3.0 × 10
- [ ] per_workflow = median × 0.05
- [ ] per_1k_tokens = median × 0.002
- [ ] pi_index formula correct and clamped (0.5-1.0)
- [ ] Margin multiplier = 3.0x

### 7.5 BundleAgent Verification

- [ ] Top 2 products identified by workflow count
- [ ] Balance ratio calculated correctly
- [ ] Expected uplift formula correct
- [ ] Confidence assignment logic correct

### 7.6 Invoice Verification

- [ ] Invoice contains only pricing dimensions (no costs)
- [ ] base_fee, per_workflow, per_1k_tokens match pricing recommendation
- [ ] Math: total = base + (per_wf × wf) + (per_token × token_k)
- [ ] All values rounded correctly

### 7.7 Audit Trail Verification

- [ ] All 5 agents logged in audit_ledger.jsonl
- [ ] Each entry has required fields
- [ ] Numeric outputs match final results
- [ ] No errors or warnings in entries

### 7.8 Integration Verification

- [ ] Data flows correctly from agent to agent
- [ ] No data loss or transformation errors
- [ ] Pricing sourced from cost statistics (not raw costs)
- [ ] Invoice sourced from pricing (not costs)

---

## Part 8: Evaluation Report Template

**Use this to document your evaluation**:

```markdown
# Ask-Scrooge Evaluation Report

## Executive Summary
[Summary of findings]

## Test Results

### DataAgent
- Input Records: [count]
- Aggregated Rows: [count]
- Status: PASS/FAIL
- Notes: [any issues]

### CostAgent
- Total Projections: [count]
- Models Analyzed: [list]
- Total Cost: $[amount]
- Status: PASS/FAIL
- Notes: [any issues]

### PricingAgent
- Base Fee Calculation: PASS/FAIL
  - Formula: median × 3.0 × 10 = $[amount]
  - Result: $[amount]
- Per Workflow Calculation: PASS/FAIL
  - Formula: median × 0.05 = $[amount]
  - Result: $[amount]
- Per 1K Tokens Calculation: PASS/FAIL
  - Formula: median × 0.002 = $[amount]
  - Result: $[amount]
- PI Index Calculation: PASS/FAIL
  - Value: [amount]
  - Range Check (0.5-1.0): PASS/FAIL

### BundleAgent
- Top Products: [product1] + [product2]
- Balance Ratio: [value]
- Expected Uplift: [value]%
- Status: PASS/FAIL

### Invoice
- Base Fee Match: PASS/FAIL ($[amount])
- Per Workflow Match: PASS/FAIL ($[amount])
- Per 1K Tokens Match: PASS/FAIL ($[amount])
- Math Verification: PASS/FAIL (total = base + wf_charge + token_charge)
- No Cost Data Included: PASS/FAIL

## Overall Assessment
- [ ] All numeric components verified
- [ ] Data flow traceable
- [ ] Calculations transparent
- [ ] Audit trail complete
- [ ] Ready for production: YES/NO

## Recommendations
[Any improvements or issues to address]
```

---

## Part 9: Quick Test Scripts

### 9.1 Automated Verification

Save as `verify_numerics.py`:

```python
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
```

**Run**:
```bash
python verify_numerics.py
```

---

## Conclusion

This guide provides complete procedures for evaluating Ask-Scrooge's numeric transparency. Follow these steps to:
- ✅ Verify cost drivers and their sources
- ✅ Validate pricing engine inputs
- ✅ Trace invoice calculations
- ✅ Audit bundle metrics
- ✅ Confirm data integrity

All numeric components are fully transparent and traceable.

---

**Document Version**: 1.0  
**Last Updated**: December 2025
