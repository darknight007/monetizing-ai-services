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

        # Step 4: Pricing Agent (now uses real Vertex AI with async internally)
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

        # Prepare file data
        ledger_data = "\n".join([json.dumps(e) for e in read_ledger()])
        csv = "product,quantity,unit_price,currency\n"
        csv += f"{bundle.get('bundle_name', 'Premium Bundle')},1,{recommendation.get('base_fee', 0)},USD\n"
        full_results = json.dumps(results, indent=2, default=str)

        return (
            f"✅ Session ID: {sid[:8]}...\n✅ Pipeline complete!",
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
        import traceback
        error_msg = f"❌ Pipeline failed: {str(e)}\n\n{traceback.format_exc()}"
        return (error_msg, None, None, None, None, None, "", "", "")


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
            status_msg = result[0]
            
            # Prepare file data - safely handle None values
            try:
                if result[6]:  # ledger_data
                    with open("audit_ledger.jsonl", "w") as f:
                        f.write(str(result[6]))
                else:
                    with open("audit_ledger.jsonl", "w") as f:
                        f.write("")
                        
                if result[7]:  # csv
                    with open("invoice.csv", "w") as f:
                        f.write(str(result[7]))
                else:
                    with open("invoice.csv", "w") as f:
                        f.write("")
                        
                if result[8]:  # full_results
                    with open("results.json", "w") as f:
                        f.write(str(result[8]))
                else:
                    with open("results.json", "w") as f:
                        f.write("")
            except Exception as e:
                status_msg += f"\n⚠️ Warning: Could not save files: {str(e)}"
            
            return (
                status_msg, 
                result[1], 
                result[2], 
                result[3], 
                result[4],
                result[5],
                "audit_ledger.jsonl", 
                "invoice.csv", 
                "results.json"
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
