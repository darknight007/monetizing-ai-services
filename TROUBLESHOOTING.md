# Ask-Scrooge Troubleshooting Guide

## Pipeline Execution Issues

### Data Requirements
The pipeline requires the following:
1. **Data File** (`data/synthetic_usage.json`) - Pre-populated with usage records
2. **LLM Configuration** - Falls back to deterministic defaults if not configured

### Current Data Format
Expected JSON structure in `data/synthetic_usage.json`:
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
  }
]
```

Required fields per record:
- `region`: One of US, EU, APAC, LATAM, MEA
- `product`: Service/product name
- `workflows`: Number of workflows (integer)
- `avg_tokens_in`: Average tokens input (integer)
- `avg_tokens_out`: Average tokens output (integer)

### Common Issues & Solutions

#### 1. **TypeError: write() argument must be str, not dict**
**Cause**: File writing was attempting to write non-string objects
**Solution**: ✅ Fixed in latest version - all data is now properly converted to strings before writing

#### 2. **Pipeline Completes but No Output Displayed**
**Possible Causes**:
- One of the agents is returning None or an empty object
- JSON serialization failure on non-standard types

**Solutions**:
- Check that `data/synthetic_usage.json` exists and has valid data
- Verify all required fields are present in the data file
- Check terminal logs for detailed error messages

#### 3. **LLM Configuration Missing**
**Expected Behavior**: If no LLM is configured (no `.env` with `GOOGLE_API_KEY`), agents use deterministic fallbacks
**Result**: Pipeline still completes successfully with default values
**Output Examples**:
- Cost Agent: Fixed cost multipliers
- Bundle Agent: "Premium Bundle" with 15% uplift
- Pricing Agent: Base fee $100, per-workflow $1, per-1K-tokens $0.01
- Compliance Agent: PASSED status

#### 4. **Audit Ledger Not Generating**
**Cause**: Audit ledger file operations failing
**Solution**: 
- Check file system permissions
- Ensure `output/` directory exists
- Review warning messages in pipeline status output

### Debugging Steps

1. **Check Data File**:
   ```bash
   python -c "import json; print(json.load(open('data/synthetic_usage.json')))"
   ```

2. **Test Individual Agent**:
   ```bash
   python -c "
   from core.session_service import InMemorySessionService
   from agents.data_agent import run as data_run
   sess = InMemorySessionService()
   sid = sess.create_session()
   data = data_run(sid)
   print(f'Data Agent returned {len(data)} records')
   "
   ```

3. **Check Logs**:
   - Gradio logs in terminal
   - Audit ledger: `output/audit_ledger.jsonl`
   - Tax API logs: `/tmp/tax_mock.log`

### File Outputs
When pipeline completes successfully:
- **audit_ledger.jsonl**: Complete audit trail in JSONL format
- **invoice.csv**: Simple invoice with bundle and base fee
- **results.json**: Full pipeline output including all agent results

### Environment Configuration
Optional for LLM features (falls back to deterministic defaults):
```bash
# Create .env file with:
GOOGLE_API_KEY=your_api_key_here
GCP_PROJECT_ID=your_project_id
```

## UI-Specific Notes

### Gradio (Current UI)
- **Port**: 7860 (configurable in `demo.launch()`)
- **Tab 1**: Pipeline execution and monitoring
- **Tab 2**: Bill calculator (standalone tool)
- **Tab 3**: Audit log viewer with filtering
- **Tab 4**: Results dashboard
- **File Downloads**: Available only after successful pipeline run

### Tips
- Region selection must match data records
- Multi-region validation checks all regions simultaneously
- JSON outputs are expandable in the UI
- Downloaded files are generated in current working directory

## Performance Considerations

### Expected Runtime
- Data Agent: <100ms (aggregation only)
- Cost Agent: 100-500ms (per record calculations)
- Bundle Agent: 500ms-2s (LLM call or fallback)
- Pricing Agent: 500ms-2s (LLM call or fallback)
- Compliance Agent: 200-1000ms (tax mock API call)
- **Total**: ~2-6 seconds for ~50 data records

### Large Datasets
For >1000 records, consider:
1. Sampling data before analysis
2. Running agents independently
3. Checking system resources

## Next Steps

If issues persist:
1. Review full error message in pipeline status output
2. Check terminal for detailed traceback
3. Verify data file integrity
4. Ensure all dependencies installed: `pip install -r requirements.txt`
