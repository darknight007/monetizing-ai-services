"""
Gradio UI for Ask-Scrooge Monetization Engine
Interactive dashboard for running and monitoring the pricing pipeline.
"""
import gradio as gr
import json
import time
from datetime import datetime
from core.session_service import InMemorySessionService
from core.memory_bank import MemoryBank
from core.audit_ledger import read_ledger, get_stats
from agents.data_agent import run as data_run
from agents.cost_agent import run as cost_run
from agents.bundle_agent import run as bundle_run
from agents.pricing_agent import run as pricing_run, calculate_bill
from agents.compliance_agent import run as compliance_run, validate_multiple_regions

# Initialize services (singleton pattern)
services = {
    "session_service": InMemorySessionService(),
    "memory_bank": MemoryBank()
}
sess_svc = services["session_service"]
mem = services["memory_bank"]


def run_pipeline(data_file, compliance_region, multi_region):
    sid = sess_svc.create_session()
    results = {}
    try:
        # Step 1: Data Agent
        rows = data_run(sid, path=data_file)
        results["data"] = rows

        # Step 2: Cost Agent
        cost_rows = cost_run(rows, session_id=sid)
        results["costs"] = cost_rows

        # Step 3: Bundle Agent
        bundle = bundle_run(rows, sid)
        results["bundle"] = bundle

        # Step 4: Pricing Agent
        recommendation = pricing_run(cost_rows, bundle, sid)
        results["pricing"] = recommendation

        # Step 5: Compliance Agent
        if multi_region:
            compliance = validate_multiple_regions(
                recommendation,
                ["US", "EU", "APAC", "LATAM", "MEA"],
                sid
            )
        else:
            compliance = compliance_run(recommendation, region=compliance_region, session_id=sid)
        results["compliance"] = compliance

        # Audit ledger
        ledger_data = "\n".join([json.dumps(e) for e in read_ledger()])
        # Invoice CSV
        csv = "product,quantity,unit_price,currency\n"
        csv += f"{bundle['bundle_name']},1,{recommendation['base_fee']},USD\n"
        # Full results JSON
        full_results = json.dumps(results, indent=2)

        return (
            f"Session ID: {sid[:8]}...\nPipeline complete!",
            rows,
            cost_rows,
            bundle,
            recommendation,
            compliance,
            ledger_data,
            csv,
            full_results
        )
    except Exception as e:
        return (f"❌ Pipeline failed: {str(e)}", None, None, None, None, None, None, None, None)


def bill_calculator(base_fee, per_workflow, per_1k_tokens, workflows, tokens_in, tokens_out):
    recommendation = {
        "base_fee": base_fee,
        "per_workflow": per_workflow,
        "per_1k_tokens": per_1k_tokens
    }
    bill = calculate_bill(recommendation, workflows, tokens_in, tokens_out)
    return bill


with gr.Blocks(title="Ask-Scrooge | Dynamic Monetization Engine") as demo:
    gr.Markdown("# 💰 Ask-Scrooge\n### Global Dynamic Monetization & Bundling Engine\n---")
    with gr.Tab("� Pipeline"):
        gr.Markdown("Run the complete monetization pipeline: Data → Cost → Bundle → Pricing → Compliance")
        data_file = gr.Textbox(value="data/synthetic_usage.json", label="Data File")
        compliance_region = gr.Dropdown(["US", "EU", "APAC", "LATAM", "MEA"], value="EU", label="Compliance Region")
        multi_region = gr.Checkbox(label="Multi-Region Validation", value=False)
        run_btn = gr.Button("Run Full Pipeline")
        status = gr.Markdown()
        data_out = gr.JSON(label="Aggregated Data")
        cost_out = gr.JSON(label="Cost Projections")
        bundle_out = gr.JSON(label="Bundle Recommendation")
        pricing_out = gr.JSON(label="Pricing Recommendation")
        compliance_out = gr.JSON(label="Compliance Check")
        ledger_download = gr.File(label="Audit Ledger (JSONL)", interactive=False)
        invoice_download = gr.File(label="Invoice (CSV)", interactive=False)
        results_download = gr.File(label="Full Results (JSON)", interactive=False)

        def pipeline_callback(data_file, compliance_region, multi_region):
            result = run_pipeline(data_file, compliance_region, multi_region)
            # Save files for download
            with open("audit_ledger.jsonl", "w") as f:
                f.write(result[5])
            with open("invoice.csv", "w") as f:
                f.write(result[6])
            with open("results.json", "w") as f:
                f.write(result[7])
            return (
                result[0], result[1], result[2], result[3], result[4],
                "audit_ledger.jsonl", "invoice.csv", "results.json"
            )

        run_btn.click(
            pipeline_callback,
            inputs=[data_file, compliance_region, multi_region],
            outputs=[status, data_out, cost_out, bundle_out, pricing_out, compliance_out, ledger_download, invoice_download, results_download]
        )

    with gr.Tab("💵 Bill Calculator"):
        gr.Markdown("Calculate a customer bill based on the current pricing recommendation")
        base_fee = gr.Number(label="Base Fee", value=100)
        per_workflow = gr.Number(label="Per Workflow", value=1)
        per_1k_tokens = gr.Number(label="Per 1K Tokens", value=0.01)
        workflows = gr.Number(label="Workflows", value=100)
        tokens_in = gr.Number(label="Tokens In", value=200000)
        tokens_out = gr.Number(label="Tokens Out", value=50000)
        calc_btn = gr.Button("Calculate Bill")
        bill_out = gr.JSON(label="Bill Breakdown")

        calc_btn.click(
            bill_calculator,
            inputs=[base_fee, per_workflow, per_1k_tokens, workflows, tokens_in, tokens_out],
            outputs=bill_out
        )

    with gr.Tab("📝 Audit Log"):
        gr.Markdown("### Audit Ledger")
        ledger = read_ledger()
        gr.JSON(ledger, label="Audit Entries")

    with gr.Tab("📈 Results Dashboard"):
        gr.Markdown("### Pipeline Results Dashboard")
        gr.Markdown("Run the pipeline to see results here.")

    gr.Markdown("---")
    gr.Markdown("**Ask-Scrooge v1.0.0** | Dynamic Monetization Engine\n\n⚠️ Demo uses deterministic fallbacks if LLM not configured")

if __name__ == "__main__":
    demo.launch()


# Session management
if "sid" not in st.session_state:
    st.session_state["sid"] = sess_svc.create_session()
    st.session_state["pipeline_results"] = None

sid = st.session_state["sid"]


# Header
st.title("💰 Ask-Scrooge")
st.markdown("### Global Dynamic Monetization & Bundling Engine")
st.markdown("---")


# Sidebar controls
with st.sidebar:
    st.markdown("## 🎛️ Controls")
    
    # Pipeline execution
    if st.button("▶️ Run Full Pipeline", type="primary", use_container_width=True):
        st.session_state["run_pipeline"] = True
    
    st.markdown("---")
    
    # Configuration
    st.markdown("## ⚙️ Configuration")
    
    data_file = st.text_input(
        "Data File",
        value="data/synthetic_usage.json",
        help="Path to usage data JSON file"
    )
    
    compliance_region = st.selectbox(
        "Compliance Region",
        options=["US", "EU", "APAC", "LATAM", "MEA"],
        index=1,  # Default to EU
        help="Region for tax/compliance validation"
    )
    
    multi_region = st.checkbox(
        "Multi-Region Validation",
        value=False,
        help="Validate across all supported regions"
    )
    
    st.markdown("---")
    
    # Session info
    st.markdown("## 📊 Session Info")
    st.text(f"Session ID: {sid[:8]}...")
    st.text(f"Started: {datetime.now().strftime('%H:%M:%S')}")
    
    # Audit ledger stats
    ledger_stats = get_stats()
    if ledger_stats["exists"]:
        st.metric("Total Audit Entries", ledger_stats["total_entries"])


# Main content area
tab1, tab2, tab3, tab4 = st.tabs([
    "🚀 Pipeline", 
    "📈 Results", 
    "📝 Audit Log",
    "💵 Bill Calculator"
])


# Tab 1: Pipeline Execution
with tab1:
    st.markdown("### Pipeline Execution")
    st.markdown("Run the complete monetization pipeline: Data → Cost → Bundle → Pricing → Compliance")
    
    if st.session_state.get("run_pipeline"):
        try:
            # Progress tracking
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            results = {}
            
            # Step 1: Data Agent
            status_text.text("📊 Running Data Agent...")
            progress_bar.progress(20)
            time.sleep(0.3)  # Visual feedback
            
            rows = data_run(sid, path=data_file)
            results["data"] = rows
            st.success(f"✅ Data Agent: Aggregated {len(rows)} product/region combinations")
            
            with st.expander("View Aggregated Data"):
                st.json(rows)
            
            # Step 2: Cost Agent
            status_text.text("💰 Running Cost Agent...")
            progress_bar.progress(40)
            time.sleep(0.3)
            
            cost_rows = cost_run(rows, session_id=sid)
            results["costs"] = cost_rows
            st.success(f"✅ Cost Agent: Calculated {len(cost_rows)} cost projections")
            
            with st.expander("View Cost Projections (sample)"):
                st.json(cost_rows[:6])
            
            # Step 3: Bundle Agent
            status_text.text("📦 Running Bundle Agent...")
            progress_bar.progress(60)
            time.sleep(0.3)
            
            bundle = bundle_run(rows, sid)
            results["bundle"] = bundle
            st.success(f"✅ Bundle Agent: Proposed bundle '{bundle['bundle_name']}'")
            
            with st.expander("View Bundle Recommendation"):
                st.json(bundle)
            
            # Step 4: Pricing Agent
            status_text.text("💵 Running Pricing Agent...")
            progress_bar.progress(80)
            time.sleep(0.3)
            
            recommendation = pricing_run(cost_rows, bundle, sid)
            results["pricing"] = recommendation
            st.success(f"✅ Pricing Agent: Recommended ${recommendation['base_fee']}/month base fee")
            
            with st.expander("View Pricing Recommendation"):
                st.json(recommendation)
            
            # Step 5: Compliance Agent
            status_text.text("🛡️ Running Compliance Agent...")
            progress_bar.progress(90)
            time.sleep(0.3)
            
            if multi_region:
                compliance = validate_multiple_regions(
                    recommendation,
                    ["US", "EU", "APAC", "LATAM", "MEA"],
                    sid
                )
            else:
                compliance = compliance_run(recommendation, region=compliance_region, session_id=sid)
            
            results["compliance"] = compliance
            
            if isinstance(compliance, dict) and compliance.get("compliance_status") == "PASSED":
                st.success(f"✅ Compliance Agent: Validation passed for {compliance_region}")
            elif isinstance(compliance, dict):
                st.warning(f"⚠️ Compliance Agent: Validation issues detected")
            else:
                passed = sum(1 for r in compliance.values() if r.get("compliance_status") == "PASSED")
                st.success(f"✅ Compliance Agent: {passed}/{len(compliance)} regions validated")
            
            with st.expander("View Compliance Check"):
                st.json(compliance)
            
            # Complete
            progress_bar.progress(100)
            status_text.text("✅ Pipeline complete!")
            st.balloons()
            
            # Store results
            st.session_state["pipeline_results"] = results
            st.session_state["run_pipeline"] = False
            
            # Download buttons
            st.markdown("---")
            st.markdown("### 📥 Downloads")
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                # Audit ledger
                ledger_data = "\n".join([json.dumps(e) for e in read_ledger()])
                st.download_button(
                    label="📝 Audit Ledger (JSONL)",
                    data=ledger_data,
                    file_name=f"audit_ledger_{sid[:8]}.jsonl",
                    mime="application/x-ndjson"
                )
            
            with col2:
                # Invoice CSV
                csv = "product,quantity,unit_price,currency\n"
                csv += f"{bundle['bundle_name']},1,{recommendation['base_fee']},USD\n"
                st.download_button(
                    label="💵 Invoice (CSV)",
                    data=csv,
                    file_name=f"invoice_{sid[:8]}.csv",
                    mime="text/csv"
                )
            
            with col3:
                # Full results JSON
                st.download_button(
                    label="📊 Full Results (JSON)",
                    data=json.dumps(results, indent=2),
                    file_name=f"results_{sid[:8]}.json",
                    mime="application/json"
                )
        
        except Exception as e:
            st.error(f"❌ Pipeline failed: {str(e)}")
            st.exception(e)
            st.session_state["run_pipeline"] = False


# Tab 2: Results Dashboard
with tab2:
    st.markdown("### Pipeline Results Dashboard")
    
    if st.session_state.get("pipeline_results"):
        results = st.session_state["pipeline_results"]
        
        # Key metrics
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            data_count = len(results.get("data", []))
            st.metric("Data Rows", data_count)
        
        with col2:
            cost_count = len(results.get("costs", []))
            st.metric("Cost Projections", cost_count)
        
        with col3:
            bundle_name = results.get("bundle", {}).get("bundle_name", "N/A")
            st.metric("Bundle", bundle_name)
        
        with col4:
            base_fee = results.get("pricing", {}).get("base_fee", 0)
            st.metric("Base Fee", f"${base_fee}")
        
        st.markdown("---")
        
        # Pricing breakdown
        st.markdown("### 💵 Pricing Model")
        pricing = results.get("pricing", {})
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("**Rate Card**")
            st.write(f"- **Base Fee**: ${pricing.get('base_fee', 0)}/month")
            st.write(f"- **Per Workflow**: ${pricing.get('per_workflow', 0)}")
            st.write(f"- **Per 1K Tokens**: ${pricing.get('per_1k_tokens', 0)}")
            st.write(f"- **PI Index**: {pricing.get('pi_index', 0)}")
        
        with col2:
            st.markdown("**Example Bill**")
            example = pricing.get("example_calculation", {})
            if example:
                st.write(f"- Base: ${example.get('base_fee', 0)}")
                st.write(f"- Workflows: ${example.get('workflow_charge', 0)}")
                st.write(f"- Tokens: ${example.get('token_charge', 0)}")
                st.write(f"**Total: ${example.get('total_monthly', 0)}**")
        
        # Justification
        st.markdown("**AI Justification**")
        st.info(pricing.get("justification", "No justification available"))
        
        st.markdown("---")
        
        # Bundle details
        st.markdown("### 📦 Bundle Recommendation")
        bundle = results.get("bundle", {})
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.write(f"**Bundle Name**: {bundle.get('bundle_name')}")
            st.write(f"**Expected Uplift**: {bundle.get('expected_uplift_pct')}%")
            st.write(f"**Confidence**: {bundle.get('confidence', 'N/A')}")
        
        with col2:
            st.markdown("**Reasoning**")
            st.write(bundle.get("llm_justification", "No reasoning available"))
    
    else:
        st.info("👈 Run the pipeline to see results here")


# Tab 3: Audit Log
with tab3:
    st.markdown("### Audit Ledger")
    
    # Filters
    col1, col2 = st.columns(2)
    
    with col1:
        filter_agent = st.selectbox(
            "Filter by Agent",
            options=["All"] + ["DataAgent", "CostAgent", "BundleAgent", "PricingAgent", "ComplianceAgent"]
        )
    
    with col2:
        filter_session = st.checkbox("Current Session Only", value=True)
    
    # Load and filter ledger
    ledger = read_ledger()
    
    if filter_session:
        ledger = [e for e in ledger if e.get("session") == sid]
    
    if filter_agent != "All":
        ledger = [e for e in ledger if e.get("agent") == filter_agent]
    
    # Display
    st.write(f"**{len(ledger)} entries found**")
    
    if ledger:
        # Show most recent first
        ledger_reversed = list(reversed(ledger))
        
        for entry in ledger_reversed[:50]:  # Show max 50
            agent = entry.get("agent", "Unknown")
            timestamp = datetime.fromtimestamp(entry.get("ts", 0)).strftime("%H:%M:%S")
            
            with st.expander(f"[{timestamp}] {agent}"):
                st.json(entry)
    else:
        st.info("No audit entries found")


# Tab 4: Bill Calculator
with tab4:
    st.markdown("### 💵 Bill Calculator")
    st.markdown("Calculate a customer bill based on the current pricing recommendation")
    
    if st.session_state.get("pipeline_results"):
        recommendation = st.session_state["pipeline_results"].get("pricing", {})
        
        # Display rate card
        st.markdown("**Current Rate Card**")
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("Base Fee", f"${recommendation.get('base_fee', 0)}/mo")
        with col2:
            st.metric("Per Workflow", f"${recommendation.get('per_workflow', 0)}")
        with col3:
            st.metric("Per 1K Tokens", f"${recommendation.get('per_1k_tokens', 0)}")
        
        st.markdown("---")
        
        # Input form
        st.markdown("**Enter Usage**")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            workflows = st.number_input("Workflows", min_value=0, value=100, step=10)
        with col2:
            tokens_in = st.number_input("Tokens In", min_value=0, value=200000, step=10000)
        with col3:
            tokens_out = st.number_input("Tokens Out", min_value=0, value=50000, step=10000)
        
        if st.button("Calculate Bill", type="primary"):
            bill = calculate_bill(recommendation, workflows, tokens_in, tokens_out)
            
            st.markdown("---")
            st.markdown("### 💰 Bill Breakdown")
            
            # Breakdown
            col1, col2 = st.columns(2)
            
            with col1:
                st.write(f"**Base Fee**: ${bill['base_fee']}")
                st.write(f"**Workflow Charge**: ${bill['workflow_charge']}")
                st.write(f"**Token Charge**: ${bill['token_charge']}")
            
            with col2:
                st.markdown(f"### **Total: ${bill['subtotal']}**")
            
            # Usage summary
            st.markdown("---")
            st.markdown("**Usage Summary**")
            st.write(f"- Workflows: {workflows:,}")
            st.write(f"- Tokens (In): {tokens_in:,}")
            st.write(f"- Tokens (Out): {tokens_out:,}")
            st.write(f"- Total Tokens: {tokens_in + tokens_out:,}")
    
    else:
        st.info("👈 Run the pipeline first to load pricing recommendation")


# Footer
st.markdown("---")
st.markdown(
    """
    <div style='text-align: center; color: #666; font-size: 0.9em;'>
        <p>Ask-Scrooge v1.0.0 | Dynamic Monetization Engine</p>
        <p>⚠️ Demo uses deterministic fallbacks if LLM not configured</p>
    </div>
    """,
    unsafe_allow_html=True
)
