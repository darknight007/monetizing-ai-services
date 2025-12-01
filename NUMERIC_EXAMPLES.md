# Ask-Scrooge Numeric Transparency Examples
## Complete End-to-End Examples with Real Calculations

**Version**: 1.0 | **Date**: December 2025 | **Audience**: Business Leads, Evaluators

---

## Executive Summary

This document provides **complete worked examples** showing:
1. Every number from input to invoice
2. Step-by-step calculations
3. Exact traceability
4. All assumptions and constants

---

## Example Pipeline Run: Complete Walkthrough

### Scenario: Small SaaS Customer

**Period**: November 2025  
**Region**: US  
**Products**: CRM + Analytics  

---

## Stage 1: Input Data

### Source: `data/synthetic_usage.json`

**Raw Customer Records**:
```json
[
  {
    "customer_id": "cust_001",
    "region": "US",
    "product": "CRM",
    "workflows": 120,
    "avg_tokens_in": 2000,
    "avg_tokens_out": 400,
    "month": "2025-11"
  },
  {
    "customer_id": "cust_005",
    "region": "US",
    "product": "CRM",
    "workflows": 80,
    "avg_tokens_in": 2500,
    "avg_tokens_out": 450,
    "month": "2025-11"
  },
  {
    "customer_id": "cust_008",
    "region": "US",
    "product": "Analytics",
    "workflows": 150,
    "avg_tokens_in": 3000,
    "avg_tokens_out": 800,
    "month": "2025-11"
  },
  {
    "customer_id": "cust_015",
    "region": "US",
    "product": "Analytics",
    "workflows": 100,
    "avg_tokens_in": 4000,
    "avg_tokens_out": 1200,
    "month": "2025-11"
  }
]
```

---

## Stage 2: DataAgent Aggregation

### Operation: Group-by (region, product) and SUM

**Step 1: Identify Unique Pairs**
```
Pair 1: (US, CRM)        → records 1, 2
Pair 2: (US, Analytics)  → records 3, 4
```

**Step 2: Aggregate Metrics**

```
─────────────────────────────────────────────────────────────

PAIR 1: (US, CRM)

  Input Records:
    Record 1: workflows=120, avg_tokens_in=2000, avg_tokens_out=400
    Record 2: workflows=80,  avg_tokens_in=2500, avg_tokens_out=450

  Aggregation Formula:
    aggregated_workflows = SUM(workflows)
                         = 120 + 80
                         = 200
    
    aggregated_tokens_in = SUM(workflows × avg_tokens_in)
                         = (120 × 2000) + (80 × 2500)
                         = 240000 + 200000
                         = 440000
    
    aggregated_tokens_out = SUM(workflows × avg_tokens_out)
                          = (120 × 400) + (80 × 450)
                          = 48000 + 36000
                          = 84000

  OUTPUT ROW 1:
  {
    "region": "US",
    "product": "CRM",
    "workflows": 200,
    "tokens_in": 440000,
    "tokens_out": 84000
  }

─────────────────────────────────────────────────────────────

PAIR 2: (US, Analytics)

  Input Records:
    Record 3: workflows=150, avg_tokens_in=3000, avg_tokens_out=800
    Record 4: workflows=100, avg_tokens_in=4000, avg_tokens_out=1200

  Aggregation Formula:
    aggregated_workflows = 150 + 100 = 250
    
    aggregated_tokens_in = (150 × 3000) + (100 × 4000)
                         = 450000 + 400000
                         = 850000
    
    aggregated_tokens_out = (150 × 800) + (100 × 1200)
                          = 120000 + 120000
                          = 240000

  OUTPUT ROW 2:
  {
    "region": "US",
    "product": "Analytics",
    "workflows": 250,
    "tokens_in": 850000,
    "tokens_out": 240000
  }

─────────────────────────────────────────────────────────────
```

### DataAgent Output Summary

```
{
  "agent": "DataAgent",
  "records_processed": 4,
  "aggregated_rows": 2,
  "summary": [
    {"region": "US", "product": "CRM", "workflows": 200, "tokens_in": 440000, "tokens_out": 84000},
    {"region": "US", "product": "Analytics", "workflows": 250, "tokens_in": 850000, "tokens_out": 240000}
  ]
}
```

---

## Stage 3: CostAgent Multi-Model Analysis

### Operation: Calculate costs for each row × each model

**Model Pricing Constants**:
```
gpt-4o:      $0.030 per 1K tokens
gemini-pro:  $0.025 per 1K tokens
llama-2:     $0.007 per 1K tokens
claude-3:    $0.015 per 1K tokens
WORKFLOW:    $0.010 per workflow
```

### Calculation for Row 1: (US, CRM)

**Input Data**:
```
region: US
product: CRM
workflows: 200
tokens_in: 440000
tokens_out: 84000
```

**FOR MODEL: gemini-pro ($0.025 per 1K)**

```
Step 1: Convert tokens to thousands
  tokens_in_k = 440000 / 1000 = 440
  tokens_out_k = 84000 / 1000 = 84
  total_tokens_k = 440 + 84 = 524

Step 2: Calculate token cost
  token_cost = (tokens_in_k + tokens_out_k) × model_price_per_1k
             = 524 × 0.025
             = 13.10

Step 3: Calculate workflow overhead
  workflow_overhead = workflows × WORKFLOW_COST
                    = 200 × 0.01
                    = 2.00

Step 4: Calculate total cost
  total_cost = token_cost + workflow_overhead
             = 13.10 + 2.00
             = 15.10

OUTPUT:
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

**FOR MODEL: gpt-4o ($0.030 per 1K)**

```
token_cost = 524 × 0.030 = 15.72
workflow_overhead = 200 × 0.01 = 2.00
total_cost = 15.72 + 2.00 = 17.72

OUTPUT:
{
  "region": "US",
  "product": "CRM",
  "model": "gpt-4o",
  "workflows": 200,
  "token_cost": 15.7200,
  "workflow_overhead": 2.0000,
  "cost": 17.7200
}
```

**FOR MODEL: llama-2 ($0.007 per 1K)**

```
token_cost = 524 × 0.007 = 3.668
workflow_overhead = 200 × 0.01 = 2.00
total_cost = 3.668 + 2.00 = 5.668

OUTPUT:
{
  "region": "US",
  "product": "CRM",
  "model": "llama-2",
  "workflows": 200,
  "token_cost": 3.6680,
  "workflow_overhead": 2.0000,
  "cost": 5.6680
}
```

**FOR MODEL: claude-3 ($0.015 per 1K)**

```
token_cost = 524 × 0.015 = 7.86
workflow_overhead = 200 × 0.01 = 2.00
total_cost = 7.86 + 2.00 = 9.86

OUTPUT:
{
  "region": "US",
  "product": "CRM",
  "model": "claude-3",
  "workflows": 200,
  "token_cost": 7.8600,
  "workflow_overhead": 2.0000,
  "cost": 9.8600
}
```

### Similar for Row 2: (US, Analytics)

**Input Data**:
```
workflows: 250
tokens_in: 850000
tokens_out: 240000
total_tokens_k = 1090000 / 1000 = 1090
```

**Cost Projections**:
```
gemini-pro: (1090 × $0.025) + (250 × $0.01) = 27.25 + 2.50 = $29.75
gpt-4o:     (1090 × $0.030) + (250 × $0.01) = 32.70 + 2.50 = $35.20
llama-2:    (1090 × $0.007) + (250 × $0.01) = 7.63 + 2.50 = $10.13
claude-3:   (1090 × $0.015) + (250 × $0.01) = 16.35 + 2.50 = $18.85
```

### CostAgent Output Summary

```
Total Cost Projections: 8 (2 rows × 4 models)

All costs: [15.10, 17.72, 5.668, 9.86, 29.75, 35.20, 10.13, 18.85]

Statistics:
  Total: $142.28
  Average: $17.79
  Min: $5.668
  Max: $35.20
  Median: $15.95 (average of 4th and 5th values when sorted)
```

---

## Stage 4: PricingAgent - Calculate Pricing

### Step 1: Extract Cost Statistics

```
All costs: [5.668, 9.86, 10.13, 15.10, 17.72, 18.85, 29.75, 35.20]

Statistics:
  median_cost = (15.10 + 17.72) / 2 = 16.41  (middle two values)
  mean_cost = 142.28 / 8 = 17.79
  min_cost = 5.668
  max_cost = 35.20
  cost_variance = (35.20 - 5.668) / 17.79 = 1.66
```

### Step 2: Calculate Pricing Components

```
FORMULA: base_fee = ROUND(median_cost × 3.0 × 10, 2)
Calculation:
  base_fee = ROUND(16.41 × 3.0 × 10, 2)
           = ROUND(492.30, 2)
           = 492.30

FORMULA: per_workflow = ROUND(median_cost × 0.05, 3)
Calculation:
  per_workflow = ROUND(16.41 × 0.05, 3)
               = ROUND(0.8205, 3)
               = 0.821

FORMULA: per_1k_tokens = ROUND(median_cost × 0.002, 4)
Calculation:
  per_1k_tokens = ROUND(16.41 × 0.002, 4)
                = ROUND(0.03282, 4)
                = 0.0328
```

### Step 3: Calculate Pricing Index

```
FORMULA: pi_index = CLAMP(0.85 × (1 - cost_variance × 0.1), 0.5, 1.0)

Calculation:
  variance_impact = 1.66 × 0.1 = 0.166
  pi_index_raw = 0.85 × (1 - 0.166)
               = 0.85 × 0.834
               = 0.709
  pi_index_clamped = CLAMP(0.709, 0.5, 1.0)
                   = 0.709
  pi_index_final = ROUND(0.709, 2) = 0.71

Interpretation:
  Variance = 1.66 indicates moderate cost spread
  PI = 0.71 indicates medium-good confidence
```

### PricingAgent Output

```json
{
  "model": "HYBRID",
  "base_fee": 492.30,
  "per_workflow": 0.821,
  "per_1k_tokens": 0.0328,
  "pi_index": 0.71,
  "currency": "USD",
  "billing_period": "monthly",
  "margin_applied": 3.0,
  "cost_analysis": {
    "median_cost": 16.41,
    "mean_cost": 17.79,
    "min_cost": 5.668,
    "max_cost": 35.20,
    "cost_variance": 1.66
  }
}
```

---

## Stage 5: BundleAgent - Product Analysis

### Step 1: Aggregate Workflows by Product

```
From aggregated data:
  CRM:       200 workflows
  Analytics: 250 workflows
```

### Step 2: Identify Top 2 Products

```
Sorted by workflow count:
  1st: Analytics (250) ← highest
  2nd: CRM (200)       ← second highest
```

### Step 3: Calculate Bundle Metrics

```
FORMULA: balance_ratio = MIN(wf1, wf2) / MAX(wf1, wf2)

Calculation:
  balance_ratio = MIN(250, 200) / MAX(250, 200)
                = 200 / 250
                = 0.80

FORMULA: expected_uplift = 5 + INT(balance_ratio × 10)

Calculation:
  expected_uplift = 5 + INT(0.80 × 10)
                  = 5 + INT(8)
                  = 5 + 8
                  = 13%

LOGIC: confidence = "medium" if balance_ratio > 0.5 else "low"

Result:
  Since 0.80 > 0.5 → confidence = "medium"
```

### BundleAgent Output

```json
{
  "bundle_name": "Analytics+CRM",
  "products": ["Analytics", "CRM"],
  "workflows_product1": 250,
  "workflows_product2": 200,
  "expected_uplift_pct": 13,
  "balance_ratio": 0.80,
  "confidence": "medium",
  "reason": "Balanced usage across top 2 products, strong cross-sell potential"
}
```

---

## Stage 6: Customer Invoice Calculation

### Scenario: Customer Buys This Service

**Usage (Monthly)**:
```
Workflows executed: 100
Tokens input: 200000
Tokens output: 50000
```

### Invoice Calculation

```
INPUT (from PricingAgent):
  base_fee = $492.30
  per_workflow = $0.821
  per_1k_tokens = $0.0328

CUSTOMER USAGE:
  workflows = 100
  tokens_total = 200000 + 50000 = 250000
  tokens_k = 250000 / 1000 = 250

CALCULATION:

Step 1: Base fee
  base_fee_charge = $492.30 (fixed)

Step 2: Workflow charge
  workflow_charge = per_workflow × workflows
                  = $0.821 × 100
                  = $82.10

Step 3: Token charge
  token_charge = per_1k_tokens × tokens_k
               = $0.0328 × 250
               = $8.20

Step 4: Total monthly bill
  TOTAL = base_fee_charge + workflow_charge + token_charge
        = $492.30 + $82.10 + $8.20
        = $582.60

SOURCES:
  ✓ Base $492.30 ← from pricing.base_fee
  ✓ Workflow $82.10 ← from pricing.per_workflow × 100
  ✓ Token $8.20 ← from pricing.per_1k_tokens × 250
  ✓ NO costs included (only pricing dimensions)
```

### Generated Invoice

**CSV Format** (`invoice.csv`):
```csv
product,quantity,unit_price,currency
Analytics+CRM,1,492.30,USD
```

**Extended Invoice** (for transparency):
```
═══════════════════════════════════════════════════════════

            MONTHLY INVOICE - Ask-Scrooge Pricing

Period: November 2025
Customer: Customer A (US)
Bundle: Analytics+CRM

───────────────────────────────────────────────────────────

PRICING DIMENSIONS:

  Base Fee (Fixed Monthly)
    Unit Price: $492.30
    Quantity: 1
    Amount: $492.30
    Source: Pricing model base fee

  Workflow Execution Charge
    Unit Price: $0.821 per workflow
    Quantity: 100 workflows
    Amount: $82.10
    Source: Pricing model per_workflow × actual usage

  Token Consumption Charge
    Unit Price: $0.0328 per 1K tokens
    Quantity: 250 (1K token units)
    Calculation: (200K + 50K) ÷ 1K = 250
    Amount: $8.20
    Source: Pricing model per_1k_tokens × actual usage

───────────────────────────────────────────────────────────

TOTAL DUE: $582.60 USD

───────────────────────────────────────────────────────────

BILLING DETAILS:
  Billing Period: Monthly
  Payment Terms: Net 30
  Currency: USD
  Bundle: Analytics+CRM (expected uplift: 13%)

Note: Pricing dimensions are sourced from AI-driven analysis
of operational costs. All rates are fixed for 12 months.

═══════════════════════════════════════════════════════════
```

---

## Complete Data Flow Diagram

```
RAW DATA (4 records)
│
├─ {cust_001: US, CRM, 120 wf, 2000/400 tok}
├─ {cust_005: US, CRM, 80 wf, 2500/450 tok}
├─ {cust_008: US, Analytics, 150 wf, 3000/800 tok}
└─ {cust_015: US, Analytics, 100 wf, 4000/1200 tok}
     │
     ▼ [DataAgent: Aggregate by (region, product)]
     │
     ├─ Output 1: US, CRM, 200 wf, 440K/84K tok
     └─ Output 2: US, Analytics, 250 wf, 850K/240K tok
          │
          ├─────────────────┬──────────────────┐
          │                 │                  │
          ▼                 ▼                  ▼
    [CostAgent:        [BundleAgent:     [Still needed
     Multi-model        Top 2 products]   for compliance]
     costing]
          │                 │
          │                 ├─ Analytics: 250 wf
          │                 ├─ CRM: 200 wf
     8 cost             │                 ├─ Balance: 0.80
     projections        │                 ├─ Uplift: 13%
          │                 │                  │
          │             ▼ [BundleAgent Output]
          │             │
          │        Bundle: Analytics+CRM
          │        Uplift: 13%
          │        Confidence: medium
          │
          ▼ [PricingAgent:
            Cost statistics → Pricing]
          │
    Cost median: $16.41
    Cost variance: 1.66
          │
          ├─ base_fee = $16.41 × 3.0 × 10 = $492.30
          ├─ per_workflow = $16.41 × 0.05 = $0.821
          ├─ per_1k_tokens = $16.41 × 0.002 = $0.0328
          └─ pi_index = 0.71
               │
               ▼ [Pricing Output]
               │
          Recommendation:
            base_fee: $492.30
            per_workflow: $0.821
            per_1k_tokens: $0.0328
            pi_index: 0.71
               │
               ▼ [Invoice Generation]
               │
          Customer Usage: 100 wf, 250K tok
               │
          Invoice:
            Base: $492.30
            Workflows: 100 × $0.821 = $82.10
            Tokens: 250 × $0.0328 = $8.20
            ────────────────────────
            TOTAL: $582.60 USD
```

---

## Verification Worksheet

**Use this to verify the example manually**:

```
STEP 1: Verify DataAgent Aggregation
  ☐ CRM workflows: 120 + 80 = 200 ✓
  ☐ CRM tokens_in: (120 × 2000) + (80 × 2500) = 440000 ✓
  ☐ CRM tokens_out: (120 × 400) + (80 × 450) = 84000 ✓
  ☐ Analytics workflows: 150 + 100 = 250 ✓
  ☐ Analytics tokens_in: (150 × 3000) + (100 × 4000) = 850000 ✓
  ☐ Analytics tokens_out: (150 × 800) + (100 × 1200) = 240000 ✓

STEP 2: Verify CostAgent Calculations
  ☐ CRM gemini token cost: (524 × $0.025) = $13.10 ✓
  ☐ CRM gemini workflow cost: 200 × $0.01 = $2.00 ✓
  ☐ CRM gemini total: $13.10 + $2.00 = $15.10 ✓
  ☐ Analytics gemini token cost: (1090 × $0.025) = $27.25 ✓
  ☐ Analytics gemini workflow cost: 250 × $0.01 = $2.50 ✓
  ☐ Analytics gemini total: $27.25 + $2.50 = $29.75 ✓

STEP 3: Verify PricingAgent Calculations
  ☐ Median cost: (15.10 + 17.72) / 2 = $16.41 ✓
  ☐ Base fee: $16.41 × 3.0 × 10 = $492.30 ✓
  ☐ Per workflow: $16.41 × 0.05 = $0.821 ✓
  ☐ Per 1K tokens: $16.41 × 0.002 = $0.0328 ✓

STEP 4: Verify BundleAgent Calculation
  ☐ Top products: Analytics (250), CRM (200) ✓
  ☐ Balance ratio: 200/250 = 0.80 ✓
  ☐ Expected uplift: 5 + INT(8) = 13% ✓

STEP 5: Verify Invoice
  ☐ Base: $492.30 ✓
  ☐ Workflow: $0.821 × 100 = $82.10 ✓
  ☐ Token: $0.0328 × 250 = $8.20 ✓
  ☐ Total: $492.30 + $82.10 + $8.20 = $582.60 ✓
```

---

## Summary of Key Numbers

| Component | Value | Source | Basis |
|-----------|-------|--------|-------|
| Input Workflows | 200 + 250 | Raw data | 4 customer records |
| Input Tokens | 524K + 1,090K | Raw data aggregation | Customer × avg usage |
| Cost Median | $16.41 | Cost projections | 8 models × 2 products |
| Base Fee | $492.30 | Pricing formula | median × 3.0 × 10 |
| Per Workflow | $0.821 | Pricing formula | median × 0.05 |
| Per 1K Tokens | $0.0328 | Pricing formula | median × 0.002 |
| PI Index | 0.71 | Pricing formula | Quality metric |
| Bundle Uplift | 13% | Bundle formula | 5 + INT(0.80 × 10) |
| Invoice Total | $582.60 | Invoice formula | base + wf + tokens |

---

## Real-World Validation

To validate this example with actual system output:

1. **Prepare test data**: Create JSON file with exactly these 4 records
2. **Run pipeline**: `bash run.sh` → click "Run Full Pipeline"
3. **Check results.json**: Verify all numeric outputs match this example
4. **Check invoice.csv**: Verify pricing components match
5. **Check audit_ledger.jsonl**: Verify all agent entries are logged

**Expected matches**:
- DataAgent: 2 aggregated rows
- CostAgent: 8 cost projections
- PricingAgent: base_fee=$492.30, per_workflow=$0.821, per_1k_tokens=$0.0328
- BundleAgent: 13% uplift
- Invoice: $582.60 for 100 workflows + 250K tokens

---

**Document Version**: 1.0  
**Last Updated**: December 2025  
**Use for**: Validation, evaluation, and transparency audit
