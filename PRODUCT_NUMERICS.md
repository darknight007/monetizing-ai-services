# Ask-Scrooge Product Numerics Documentation
## Complete Numeric Component Traceability & Verification Guide

**Version**: 1.0 | **Date**: December 2025 | **Audience**: Business Lead, Product Team, Evaluation

---

## Executive Summary

This document provides complete transparency on every numeric component in the Ask-Scrooge pricing engine, including:
- **Source of Truth** for each number
- **Calculation methodology** with step-by-step formulas
- **Verification procedures** for testing
- **Data flow diagram** showing dependencies
- **Invoice transparency** showing how pricing is derived

---

## Part 1: Data Flow & Numeric Sources

### Overall Pipeline Architecture

```
RAW USAGE DATA
    ↓
[DataAgent: Aggregation]
    ↓
AGGREGATED METRICS
    ├─→ [CostAgent: Cost Projection]
    │       ↓
    │   COST DATA
    │       ├─→ [PricingAgent: Price Calculation]
    │       │       ↓
    │       │   PRICING MODEL
    │       │       ↓
    │       │   [Customer Invoice]
    │       └─→ [Compliance Agent: Tax Validation]
    │
    └─→ [BundleAgent: Bundle Analysis]
            ↓
        BUNDLE RECOMMENDATION
```

---

## Part 2: Stage 1 - Data Aggregation (DataAgent)

### 2.1 Input Data Format

**Source**: `data/synthetic_usage.json` (Customer usage records)

**Required Fields per Record**:
| Field | Type | Example | Range | Purpose |
|-------|------|---------|-------|---------|
| `region` | String | "US" | US, EU, APAC, LATAM, MEA | Geographic segment |
| `product` | String | "CRM" | Any product name | Product line |
| `workflows` | Integer | 120 | > 0 | Execution count |
| `avg_tokens_in` | Integer | 2000 | > 0 | Input tokens per workflow |
| `avg_tokens_out` | Integer | 400 | > 0 | Output tokens per workflow |
| `month` | String | "2025-11" | YYYY-MM | Period identifier |

**Example Input Record**:
```json
{
  "customer_id": "cust_001",
  "region": "US",
  "product": "CRM",
  "workflows": 120,
  "avg_tokens_in": 2000,
  "avg_tokens_out": 400,
  "month": "2025-11"
}
```

### 2.2 Aggregation Logic

**Operation**: Group-by (Region, Product) and sum metrics

**Formula**:
```
For each unique (region, product) pair:
  
  aggregated_workflows = SUM(workflows) for all records with that pair
  
  aggregated_tokens_in = SUM(workflows × avg_tokens_in) for all records
  
  aggregated_tokens_out = SUM(workflows × avg_tokens_out) for all records
```

**Example Calculation**:
```
Input Records:
  Record 1: US, CRM, workflows=120, avg_tokens_in=2000, avg_tokens_out=400
  Record 2: US, CRM, workflows=80, avg_tokens_in=2500, avg_tokens_out=450
  Record 3: EU, Analytics, workflows=50, avg_tokens_in=5000, avg_tokens_out=1000

Output (Aggregated):
  {region: "US", product: "CRM",
    workflows: 200,
    tokens_in: 120×2000 + 80×2500 = 240000 + 200000 = 440000,
    tokens_out: 120×400 + 80×450 = 48000 + 36000 = 84000
  }
  
  {region: "EU", product: "Analytics",
    workflows: 50,
    tokens_in: 50×5000 = 250000,
    tokens_out: 50×1000 = 50000
  }
```

### 2.3 Verification for DataAgent

**Test Case 1: Basic Aggregation**
```bash
INPUT FILE: data/synthetic_usage.json
EXPECTED OUTPUT: Aggregated rows grouped by (region, product)

Verification Steps:
1. Count input records: 75 total
2. Identify unique (region, product) combinations
3. Manually sum workflows for each combination
4. Manually calculate total tokens using formulas above
5. Compare with DataAgent output in audit_ledger.jsonl

Expected audit entry:
{
  "agent": "DataAgent",
  "records_processed": 75,
  "aggregated_rows": <count of unique pairs>
}
```

**Test Case 2: Data Validation**
```bash
# Run individual test
python -c "
from agents.data_agent import run
from core.session_service import InMemorySessionService
sess = InMemorySessionService()
sid = sess.create_session()
data = run(sid, 'data/synthetic_usage.json')
print(f'Aggregated {len(data)} region-product combinations')
print('Sample:', data[0] if data else 'No data')
"
```

**Audit Trail**:
- Check `output/audit_ledger.jsonl` for DataAgent entry
- Verify `records_processed` matches input file size
- Verify `aggregated_rows` shows grouping worked

---

## Part 3: Stage 2 - Cost Projection (CostAgent)

### 3.1 Cost Model Overview

**Objective**: Project costs for each (region, product, model) combination

**Cost Formula**:
```
TOTAL_COST = TOKEN_COST + WORKFLOW_OVERHEAD

Where:
  TOKEN_COST = (tokens_in_k + tokens_out_k) × model_price_per_1k
  WORKFLOW_OVERHEAD = WORKFLOW_COST × workflows
  
  tokens_in_k = tokens_in / 1000  (convert to thousands)
  tokens_out_k = tokens_out / 1000
```

### 3.2 Model Pricing Table (Source of Truth)

**Last Updated**: December 2025 | **Basis**: Industry standard pricing per 1K tokens

| Model | Price per 1K Tokens | Usage Scenario |
|-------|-------------------|-----------------|
| gpt-4o | $0.030 | High accuracy, complex tasks |
| gemini-pro | $0.025 | Balanced cost-performance |
| llama-2 | $0.007 | Cost-optimized, lower accuracy |
| claude-3 | $0.015 | Generalist model |

**Workflow Overhead**: $0.01 per workflow (infrastructure, orchestration, queue management)

### 3.3 Cost Calculation Example

**Input** (from DataAgent):
```json
{
  "region": "US",
  "product": "CRM",
  "workflows": 200,
  "tokens_in": 440000,
  "tokens_out": 84000
}
```

**Step-by-Step Calculation** (using Gemini):
```
1. Convert tokens to thousands:
   tokens_in_k = 440000 / 1000 = 440
   tokens_out_k = 84000 / 1000 = 84
   total_tokens_k = 440 + 84 = 524

2. Get model pricing:
   model_price_per_1k = $0.025 (Gemini)

3. Calculate token cost:
   TOKEN_COST = 524 × $0.025 = $13.10

4. Calculate workflow overhead:
   WORKFLOW_OVERHEAD = $0.01 × 200 = $2.00

5. Calculate total cost:
   TOTAL_COST = $13.10 + $2.00 = $15.10
```

**Output** (for this region-product-model):
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

### 3.4 Multi-Model Analysis

CostAgent calculates costs for **all 4 models** for each region-product pair:

**Example Output** (3 region-product pairs × 4 models = 12 cost projections):
```
Scenario: 3 unique (region, product) combinations

For each combination:
  → gpt-4o cost
  → gemini-pro cost
  → llama-2 cost
  → claude-3 cost

Total projections generated: 3 × 4 = 12 rows
```

### 3.5 Verification for CostAgent

**Test Case 1: Cost Calculation Accuracy**
```bash
# Manual verification
INPUT: US/CRM with 200 workflows, 440K tokens_in, 84K tokens_out

FOR GEMINI (price=$0.025):
  tokens_k = (440000 + 84000) / 1000 = 524
  token_cost = 524 × 0.025 = $13.10
  workflow_overhead = 0.01 × 200 = $2.00
  total = $13.10 + $2.00 = $15.10

Compare with CostAgent output in results.json
Check: "cost": 15.1000
```

**Test Case 2: Audit Trail Verification**
```bash
Check output/audit_ledger.jsonl for CostAgent entry:
{
  "agent": "CostAgent",
  "summary": [...all cost projections...],
  "total_projections": <count>,
  "models_analyzed": ["gpt-4o", "gemini-pro", "llama-2", "claude-3"],
  "total_cost": <sum of all projections>,
  "average_cost": <mean of all projections>
}
```

**Test Case 3: Model Pricing Consistency**
```python
# Verify MODEL_PRICING dictionary
from agents.cost_agent import MODEL_PRICING, WORKFLOW_COST

print("Model Pricing (per 1K tokens):")
for model, price in MODEL_PRICING.items():
    print(f"  {model}: ${price}")

print(f"Workflow Overhead: ${WORKFLOW_COST}")

Expected:
  gpt-4o: $0.03
  gemini-pro: $0.025
  llama-2: $0.007
  claude-3: $0.015
  Workflow: $0.01
```

---

## Part 4: Stage 3 - Pricing Strategy (PricingAgent)

### 4.1 Pricing Model Selection

**Approach**: HYBRID (combines fixed base fee with usage-based charges)

**Rationale**: 
- Predictable baseline revenue (base fee)
- Scalable revenue (usage components)
- Suitable for SaaS/AI services

### 4.2 Price Component Calculation

**Input** (from CostAgent):
- Cost projections for all models and region-product combinations
- Cost statistics (median, mean, min, max)

**Step 1: Extract Cost Distribution**
```
costs = [15.10, 14.95, 16.20, ..., 8.50, ...]  # All costs from all projections

Compute statistics:
  median_cost = 50th percentile of costs
  mean_cost = average of all costs
  min_cost = lowest cost projection
  max_cost = highest cost projection
  cost_variance = (max_cost - min_cost) / mean_cost
```

**Step 2: Calculate Pricing Components**

```
DEFAULT_MARGIN = 3.0  # Standard 3x markup on median cost

BASE_FEE = ROUND(median_cost × margin × 10, 2)
  ├─ Why ×10? To amortize monthly cost over a year and apply margin
  └─ Example: median=$2.50 → $2.50 × 3.0 × 10 = $75.00/month

PER_WORKFLOW = ROUND(median_cost × 0.05, 3)
  ├─ Represents 5% of median cost per additional workflow
  └─ Example: median=$2.50 → $2.50 × 0.05 = $0.125 per workflow

PER_1K_TOKENS = ROUND(median_cost × 0.002, 4)
  ├─ Micro-pricing for token consumption (0.2% of cost)
  └─ Example: median=$2.50 → $2.50 × 0.002 = $0.005 per 1K tokens
```

### 4.3 Pricing Index Calculation

**Purpose**: Quality score for pricing recommendation (0.5-1.0)

**Formula**:
```
cost_variance = (max_cost - min_cost) / mean_cost
PI_INDEX = DEFAULT_PI_INDEX × (1 - cost_variance × 0.1)
PI_INDEX = CLAMP(PI_INDEX, 0.5, 1.0)

Where DEFAULT_PI_INDEX = 0.85

Interpretation:
  1.0 = Optimal pricing (low cost variance, predictable)
  0.85 = Good (moderate variance)
  0.5 = Risk (high variance, unpredictable)
```

**Example**:
```
Costs from all projections: [8.50, 9.20, 10.10, 15.10, 14.95, 16.20, ...]

Statistics:
  min = 8.50
  max = 16.20
  mean = 12.00
  
Calculation:
  cost_variance = (16.20 - 8.50) / 12.00 = 7.70 / 12.00 = 0.64
  PI_INDEX = 0.85 × (1 - 0.64 × 0.1)
           = 0.85 × (1 - 0.064)
           = 0.85 × 0.936
           = 0.796
           ≈ 0.80 (rounded to 2 decimals)
```

### 4.4 Complete Pricing Recommendation Output

**Key Numeric Components**:

| Component | Formula/Source | Example Value | Usage |
|-----------|---|---|---|
| **base_fee** | median_cost × 3.0 × 10 | $75.00 | Fixed monthly charge |
| **per_workflow** | median_cost × 0.05 | $0.125 | Variable per execution |
| **per_1k_tokens** | median_cost × 0.002 | $0.005 | Micro-charge per 1K tokens |
| **pi_index** | 0.85 × (1 - variance×0.1) | 0.80 | Quality/confidence metric |
| **margin_applied** | Constant | 3.0x | Cost markup ratio |
| **billing_period** | Constant | monthly | Fixed billing cycle |

### 4.5 Verification for PricingAgent

**Test Case 1: Cost Statistics Calculation**
```bash
# Extract costs from results.json
costs = [row["cost"] for row in results["costs"]]

# Calculate manually
median = sorted(costs)[len(costs)//2]
mean = sum(costs) / len(costs)
min_val = min(costs)
max_val = max(costs)

# Verify against recommendation
recommendation["cost_analysis"] should show:
{
  "median_cost": <your_median>,
  "mean_cost": <your_mean>,
  "min_cost": <your_min>,
  "max_cost": <your_max>,
  "cost_variance": <variance>
}
```

**Test Case 2: Price Component Calculation**
```bash
median_cost = <from cost_analysis>
margin = 3.0

# Calculate base_fee
base_fee_calculated = round(median_cost × 3.0 × 10, 2)

# Verify against recommendation
recommendation["base_fee"] should equal base_fee_calculated

# Similar for per_workflow and per_1k_tokens
```

**Test Case 3: Pricing Index Validation**
```python
# Calculate PI Index
cost_variance = recommendation["cost_analysis"]["cost_variance"]
pi_index_calc = 0.85 * (1 - cost_variance * 0.1)
pi_index_clamped = max(0.5, min(1.0, pi_index_calc))

# Compare with recommendation["pi_index"]
assert abs(pi_index_clamped - recommendation["pi_index"]) < 0.01
```

---

## Part 5: Stage 4 - Bundle Analysis (BundleAgent)

### 5.1 Bundle Selection Criteria

**Input**: Aggregated usage data by product

**Logic**:
```
1. Sum workflows by product across all regions:
   product_workflows = {
     "CRM": 500,
     "Analytics": 300,
     "Support": 450,
     ...
   }

2. Sort by workflow count (descending)

3. Select top 2 products for bundling:
   Product1 (highest workflows)
   Product2 (second highest workflows)
```

### 5.2 Bundle Metrics Calculation

**Formula for Expected Uplift**:
```
balance_ratio = MIN(workflows_product1, workflows_product2) / 
                MAX(workflows_product1, workflows_product2)

expected_uplift_pct = 5 + INT(balance_ratio × 10)

Interpretation:
  balance_ratio = 1.0 (equal usage) → uplift = 5 + 10 = 15%
  balance_ratio = 0.5 (2:1 ratio) → uplift = 5 + 5 = 10%
  balance_ratio = 0.2 (5:1 ratio) → uplift = 5 + 2 = 7%
```

**Confidence Scoring**:
```
IF balance_ratio > 0.5:
  confidence = "medium"  (balanced usage across products)
ELSE:
  confidence = "low"     (imbalanced, lower cross-sell potential)
```

### 5.3 Example Bundle Calculation

**Input Data**:
```
Product Workflows (aggregated across all regions):
  CRM: 500 workflows
  Analytics: 350 workflows
  Support: 200 workflows
```

**Bundle Calculation**:
```
1. Top 2 products: CRM (500) + Analytics (350)

2. Bundle name: "CRM+Analytics"

3. Calculate metrics:
   balance_ratio = MIN(500, 350) / MAX(500, 350)
                 = 350 / 500
                 = 0.70
   
4. Expected uplift:
   expected_uplift = 5 + INT(0.70 × 10)
                   = 5 + 7
                   = 12%
   
5. Confidence:
   Since 0.70 > 0.5 → confidence = "medium"
```

**Output Bundle**:
```json
{
  "bundle_name": "CRM+Analytics",
  "products": ["CRM", "Analytics"],
  "expected_uplift_pct": 12,
  "confidence": "medium",
  "workflows_product1": 500,
  "workflows_product2": 350,
  "balance_ratio": 0.70
}
```

### 5.4 Verification for BundleAgent

**Test Case 1: Product Aggregation**
```bash
# Sum workflows by product manually
products = {}
for row in aggregated_data:
    products[row["product"]] += row["workflows"]

# Verify top 2 products match bundle selection
top_2 = sorted(products.items(), key=lambda x: -x[1])[:2]
assert bundle["products"] == [top_2[0][0], top_2[1][0]]
```

**Test Case 2: Uplift Calculation**
```python
# Calculate expected uplift
workflows1 = bundle["workflows_product1"]
workflows2 = bundle["workflows_product2"]
balance_ratio_calc = min(workflows1, workflows2) / max(workflows1, workflows2)
expected_uplift_calc = 5 + int(balance_ratio_calc * 10)

# Verify
assert bundle["expected_uplift_pct"] == expected_uplift_calc
assert abs(bundle["balance_ratio"] - balance_ratio_calc) < 0.01
```

---

## Part 6: Stage 5 - Invoice Generation

### 6.1 Invoice Transparent Calculation

**Purpose**: Show exactly how pricing dimensions map to customer charges

**Not** cost-based (no token costs), **entirely** pricing-based

### 6.2 Invoice Formula

**Input** (from Pricing Recommendation):
```json
{
  "base_fee": $75.00,
  "per_workflow": $0.125,
  "per_1k_tokens": $0.005,
  "billing_period": "monthly"
}
```

**Customer Usage**:
```json
{
  "workflows": 100,
  "tokens_in": 200000,
  "tokens_out": 50000
}
```

**Calculation**:
```
Step 1: Calculate token-based charge
  total_tokens = tokens_in + tokens_out
               = 200000 + 50000
               = 250000
  
  tokens_in_thousands = 250000 / 1000 = 250
  
  token_charge = per_1k_tokens × tokens_in_thousands
               = $0.005 × 250
               = $1.25

Step 2: Calculate workflow-based charge
  workflow_charge = per_workflow × workflows
                  = $0.125 × 100
                  = $12.50

Step 3: Calculate total monthly bill
  INVOICE_TOTAL = base_fee + workflow_charge + token_charge
                = $75.00 + $12.50 + $1.25
                = $88.75
```

### 6.3 Detailed Invoice Format

**Generated Invoice** (`invoice.csv`):
```
product,quantity,unit_price,currency
CRM+Analytics,1,75.00,USD

Detailed Breakdown:
Base Fee (monthly fixed): $75.00
Workflow Charge (100 × $0.125): $12.50
Token Charge (250K ÷ 1K × $0.005): $1.25
─────────────────────────────────
TOTAL: $88.75
```

**Extended Invoice with Pricing Dimensions** (JSON format):
```json
{
  "invoice": {
    "billing_period": "monthly",
    "pricing_dimensions": {
      "base_fee": {
        "amount": 75.00,
        "description": "Fixed monthly base fee",
        "source": "Pricing recommendation base_fee"
      },
      "workflow_charges": {
        "unit_price": 0.125,
        "quantity": 100,
        "amount": 12.50,
        "description": "Per-workflow execution charge",
        "source": "Pricing recommendation per_workflow × actual workflows"
      },
      "token_charges": {
        "unit_price": 0.005,
        "quantity": 250,
        "unit": "1K tokens",
        "amount": 1.25,
        "description": "Per-1K-token consumption charge",
        "calculation": "(200000 + 50000) / 1000 = 250 × $0.005",
        "source": "Pricing recommendation per_1k_tokens × actual tokens"
      }
    },
    "total": 88.75,
    "currency": "USD",
    "links_to_pricing": {
      "base_fee_from": "pricing_recommendation.base_fee",
      "per_workflow_from": "pricing_recommendation.per_workflow",
      "per_token_from": "pricing_recommendation.per_1k_tokens"
    }
  }
}
```

### 6.4 Verification for Invoice

**Test Case 1: Invoice Calculation Accuracy**
```bash
# From pricing recommendation
base_fee = 75.00
per_workflow = 0.125
per_1k_tokens = 0.005

# From customer usage
workflows = 100
tokens_total = 200000 + 50000 = 250000
tokens_k = 250000 / 1000 = 250

# Calculate
workflow_charge = 0.125 × 100 = 12.50
token_charge = 0.005 × 250 = 1.25
total = 75.00 + 12.50 + 1.25 = 88.75

# Verify matches invoice.csv
```

**Test Case 2: Pricing Dimension Traceability**
```bash
For each line item in invoice:
  ✓ base_fee → from recommendations.base_fee
  ✓ per_workflow × workflows → from recommendations.per_workflow
  ✓ per_1k_tokens × (tokens_in+tokens_out)/1000 → from recommendations.per_1k_tokens
  ✓ No cost data included (cost_agent outputs not in invoice)
  ✓ Total = sum of all charges
```

---

## Part 7: Complete Data Flow with Numerics

### 7.1 End-to-End Traceability Example

```
INPUT (Raw Usage Data):
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
US | CRM | workflows: 120 | tokens_in: 2000 | tokens_out: 400
US | CRM | workflows: 80  | tokens_in: 2500 | tokens_out: 450

↓ [DataAgent: Aggregation]

AGGREGATED (Region-Product Level):
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
US | CRM | workflows: 200
          tokens_in: 440000 (120×2000 + 80×2500)
          tokens_out: 84000 (120×400 + 80×450)

↓ [CostAgent: Multi-Model Costing] (×4 models)

COST PROJECTIONS:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
gemini-pro:
  tokens_k = (440000 + 84000) / 1000 = 524
  token_cost = 524 × $0.025 = $13.10
  workflow_overhead = $0.01 × 200 = $2.00
  total_cost = $15.10

gpt-4o:
  token_cost = 524 × $0.030 = $15.72
  workflow_overhead = $2.00
  total_cost = $17.72

[... llama-2: $7.68, claude-3: $10.86 ...]

↓ [PricingAgent: Cost Statistics & Pricing Strategy]

COST STATISTICS (across all models):
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
costs = [$15.10, $17.72, $7.68, $10.86, ...]
median_cost = $12.00 (example)
mean_cost = $12.50
min = $7.68
max = $17.72
variance = (17.72 - 7.68) / 12.50 = 0.80

↓ [Price Calculation]

PRICING COMPONENTS:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
base_fee = $12.00 × 3.0 × 10 = $360.00
per_workflow = $12.00 × 0.05 = $0.60
per_1k_tokens = $12.00 × 0.002 = $0.024
pi_index = 0.85 × (1 - 0.80 × 0.1) = 0.782

↓ [BundleAgent: Product Analysis]

BUNDLE METRICS:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Top products by workflows: CRM (500), Analytics (350)
balance_ratio = 350 / 500 = 0.70
expected_uplift = 5 + INT(0.70 × 10) = 12%

↓ [Customer Invoice]

MONTHLY INVOICE (for 100 workflows, 200K+50K tokens):
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Base Fee:                      $360.00
Workflow Charge (100 × $0.60):  $60.00
Token Charge (250 × $0.024):    $6.00
────────────────────────────────────
TOTAL:                         $426.00

Trace Back:
  $360.00 ← from pricing_agent.base_fee
   $60.00 ← from pricing_agent.per_workflow × 100 workflows
    $6.00 ← from pricing_agent.per_1k_tokens × 250 (tokens/1K)
```

---

## Part 8: Testing & Validation Checklist

### 8.1 Unit-Level Tests

**DataAgent**:
- [ ] Input file exists and is valid JSON
- [ ] All required fields present in records
- [ ] Aggregation sums are correct (spot-check 3 region-product pairs)
- [ ] Audit entry records correct counts

**CostAgent**:
- [ ] Model pricing constants match latest rates
- [ ] Workflow overhead is $0.01
- [ ] Token conversions to thousands are accurate
- [ ] Cost formula: (tokens_k × price) + (workflows × 0.01) is correct
- [ ] All 4 models have projections for each input row

**PricingAgent**:
- [ ] Median/mean/min/max correctly calculated from costs
- [ ] Base fee = median × 3.0 × 10 (correct rounding to 2 decimals)
- [ ] Per workflow = median × 0.05 (correct rounding to 3 decimals)
- [ ] Per 1K tokens = median × 0.002 (correct rounding to 4 decimals)
- [ ] PI index formula and clamping (0.5-1.0) are correct
- [ ] Example bill calculation matches formula

**BundleAgent**:
- [ ] Top 2 products correctly identified by workflow count
- [ ] Balance ratio calculated correctly
- [ ] Expected uplift formula: 5 + INT(ratio × 10)
- [ ] Confidence assignment based on balance_ratio threshold

**Invoice**:
- [ ] Base fee amount matches pricing recommendation
- [ ] Workflow charge = per_workflow × workflows
- [ ] Token charge = per_1k_tokens × (total_tokens / 1000)
- [ ] Total = base + workflow_charge + token_charge

### 8.2 Integration Tests

**End-to-End Pipeline**:
- [ ] Run with sample data, verify all 5 agents complete
- [ ] Cost stats in pricing output match actual costs from cost agent
- [ ] Pricing components correctly derived from cost stats
- [ ] Bundle from bundle agent referenced in pricing output
- [ ] Invoice numbers traceable to pricing recommendation
- [ ] Audit ledger contains entries from all agents

**Data Consistency**:
- [ ] Workflow counts from data agent match cost agent inputs
- [ ] Token counts from data agent match cost agent inputs
- [ ] Cost projections in cost agent match pricing agent inputs
- [ ] Pricing recommendation base numbers match invoice

### 8.3 Regression Tests

**Test Case File**: `tests/test_numerics.py`

```python
def test_data_aggregation():
    # Verify aggregation math with known inputs
    pass

def test_cost_calculation():
    # Verify cost formula with fixed inputs
    pass

def test_pricing_components():
    # Verify pricing calculations with fixed costs
    pass

def test_invoice_generation():
    # Verify invoice sums match pricing components
    pass

def test_full_pipeline_numerics():
    # End-to-end with assertions on numeric outputs
    pass
```

---

## Part 9: Numeric Dependencies Map

### 9.1 What Feeds What

```
data/synthetic_usage.json
    ↓
    └→ DataAgent (aggregation)
        ↓
        → workflows: INTEGER
        → tokens_in: INTEGER (SUM of workflow × avg_tokens_in)
        → tokens_out: INTEGER (SUM of workflow × avg_tokens_out)
        ↓
        ├→ CostAgent (input: workflows, tokens_in, tokens_out)
        │   ↓
        │   → cost: FLOAT (token_cost + workflow_overhead)
        │   ↓
        │   └→ PricingAgent (input: costs array)
        │       ↓
        │       → median_cost: FLOAT
        │       → mean_cost: FLOAT
        │       → min_cost: FLOAT
        │       → max_cost: FLOAT
        │       → cost_variance: FLOAT
        │       ↓
        │       ├→ base_fee = median × 3.0 × 10
        │       ├→ per_workflow = median × 0.05
        │       ├→ per_1k_tokens = median × 0.002
        │       └→ pi_index = 0.85 × (1 - variance × 0.1)
        │           ↓
        │           └→ Invoice (input: pricing components + usage)
        │               ↓
        │               → total = base + (per_wf × wf_count) + (per_token × token_k)
        │
        └→ BundleAgent (input: workflows per product)
            ↓
            → bundle_name: STRING
            → products: ARRAY
            → expected_uplift_pct: INTEGER
            → confidence: STRING
            → balance_ratio: FLOAT
```

### 9.2 Critical Dependencies

| Component | Depends On | Impact If Wrong |
|-----------|-----------|-----------------|
| workflows | data_agent | Cost calculations, bundle analysis |
| tokens_in/out | data_agent | Token costs, pricing components |
| cost | cost_agent (uses tokens, MODEL_PRICING) | Price calculation, invoice |
| base_fee | cost_agent.median_cost | ~60% of customer bill |
| per_workflow | cost_agent.median_cost | Variable billing, revenue scaling |
| per_1k_tokens | cost_agent.median_cost | Micro-transaction pricing |
| pi_index | cost_agent.cost_variance | Quality metric (information only) |
| bundle_uplift | workflows per product | Revenue uplift forecast |

---

## Part 10: Sensitivity Analysis

### 10.1 How Changes Impact Pricing

**Scenario 1: Token Count Increases 10%**
```
Original:
  tokens_k = 524
  token_cost = 524 × $0.025 = $13.10

With +10% tokens:
  tokens_k = 576.4
  token_cost = 576.4 × $0.025 = $14.41
  Impact: +$1.31 per projection (+10%)

If this changes median_cost:
  base_fee increases proportionally
  per_workflow increases proportionally
  per_1k_tokens increases proportionally
```

**Scenario 2: Model Pricing Changes (e.g., Gemini $0.025 → $0.020)**
```
All gemini-pro projections decrease by $0.005 × tokens_k
If this changes median_cost significantly:
  All price components decrease
  Margin adjusted automatically (3.0x applied)
  PI index may improve (lower variance)
```

**Scenario 3: Margin Change (3.0x → 2.5x)**
```
base_fee = median_cost × 2.5 × 10 (instead of 3.0 × 10)
Result: -16.7% reduction in base_fee
  Example: $360 → $300

This would require code change in pricing_agent.py
Line: DEFAULT_MARGIN = 3.0 → 2.5
```

### 10.2 Verification After Changes

Always re-run:
1. Full pipeline with sample data
2. Invoice calculation test (manual math check)
3. Audit ledger inspection
4. Cost projections spot-check

---

## Part 11: Reference Data Files

### 11.1 Sample Input (data/synthetic_usage.json)

Located at: `/Users/outlieralpha/CascadeProjects/ask-scrooge/data/synthetic_usage.json`

Contains 75 records with fields: customer_id, region, product, workflows, avg_tokens_in, avg_tokens_out, month

### 11.2 Sample Output

**Audit Ledger Entry** (output/audit_ledger.jsonl):
```json
{"agent":"DataAgent","session":"...","summary":[...],"records_processed":75,"aggregated_rows":12}
{"agent":"CostAgent","session":"...","summary":[...],"total_projections":48,"models_analyzed":["gpt-4o","gemini-pro","llama-2","claude-3"],"total_cost":XXX,"average_cost":XXX}
{"agent":"PricingAgent","session":"...","recommendation":{...}}
{"agent":"BundleAgent","session":"...","bundle":{...}}
```

**Results JSON** (results.json):
```json
{
  "data": [...aggregated rows...],
  "costs": [...cost projections...],
  "bundle": {...bundle recommendation...},
  "pricing": {...pricing recommendation...},
  "compliance": {...compliance check...}
}
```

**Invoice CSV** (invoice.csv):
```
product,quantity,unit_price,currency
CRM+Analytics,1,<base_fee>,USD
```

---

## Part 12: Quick Reference - Numeric Formulas

| Component | Formula | Source | Verification |
|-----------|---------|--------|---|
| **aggregated_workflows** | SUM(workflows) by (region, product) | Input data | Count records for each pair |
| **aggregated_tokens_in** | SUM(workflows × avg_tokens_in) | Input data | Manual sum calculation |
| **aggregated_tokens_out** | SUM(workflows × avg_tokens_out) | Input data | Manual sum calculation |
| **token_cost** | (tokens_in_k + tokens_out_k) × model_price | MODEL_PRICING | Price × token count |
| **workflow_overhead** | WORKFLOW_COST × workflows | Constant ($0.01) | Count × $0.01 |
| **total_cost** | token_cost + workflow_overhead | Cost agent | Sum of components |
| **median_cost** | 50th percentile of costs | Cost array | Sort and find middle |
| **base_fee** | median_cost × 3.0 × 10 | Pricing formula | Multiply and round |
| **per_workflow** | median_cost × 0.05 | Pricing formula | Multiply and round |
| **per_1k_tokens** | median_cost × 0.002 | Pricing formula | Multiply and round |
| **pi_index** | CLAMP(0.85 × (1 - variance × 0.1), 0.5, 1.0) | Pricing formula | Calculate variance |
| **balance_ratio** | MIN(wf1, wf2) / MAX(wf1, wf2) | Bundle metrics | Ratio calculation |
| **expected_uplift** | 5 + INT(balance_ratio × 10) | Bundle metrics | Integer math |
| **invoice_total** | base_fee + (per_wf × workflows) + (per_token × tokens_k) | Pricing dimensions | Sum components |

---

## Part 13: FAQ - Numeric Questions

**Q: Why multiply base_fee by 10?**
A: To annualize monthly costs and apply a monthly margin. If median cost is $2.50/month over a year, customer amortizes $25, then applies 3x margin = $75/month.

**Q: Why is workflow overhead $0.01 fixed?**
A: Represents minimum infrastructure cost per workflow (queue, orchestration, logging). Independent of token volume.

**Q: Why 0.05 and 0.002 for per-workflow and per-token?**
A: Calibrated to create sensible micro-charges. 0.05 = 5% of cost impact per workflow, 0.002 = 0.2% per 1K tokens.

**Q: How is PI index used?**
A: Information metric only. High PI (0.9-1.0) = predictable costs. Low PI (0.5-0.7) = volatile costs. Doesn't affect pricing, just quality signal.

**Q: Can we change MODEL_PRICING?**
A: Yes, edit `agents/cost_agent.py` line 8-12. Changes apply to all future cost calculations. Re-run pipeline to see impact.

**Q: Can we change the margin (3.0x)?**
A: Yes, edit `agents/pricing_agent.py` line 12. DEFAULT_MARGIN = 3.0 → any value. Proportionally scales all pricing components.

**Q: What if cost_variance is 0 (all costs identical)?**
A: PI = 0.85 × (1 - 0 × 0.1) = 0.85 (optimal scenario, high confidence).

**Q: What if tokens are 0?**
A: Token cost = 0, but workflow_overhead still applies. Total cost = workflows × $0.01.

---

## Conclusion

Every numeric component in Ask-Scrooge is traceable, auditable, and transparent. This documentation enables:
- ✅ Business leads to understand pricing logic
- ✅ Evaluators to verify calculations
- ✅ Engineers to implement tests
- ✅ Customers to see exactly how their bill is calculated

**Audit Trail**: All numeric operations logged in `output/audit_ledger.jsonl` for compliance and verification.

---

**Document Version**: 1.0  
**Last Updated**: December 2025  
**Maintained By**: Ask-Scrooge Product Team
