from __future__ import annotations

import json
import re
from collections import Counter
from pathlib import Path
from typing import Any

import streamlit as st


APP_ROOT = Path(__file__).resolve().parent


def detect_project_root() -> Path:
    candidates = [
        APP_ROOT,
        APP_ROOT.parent,
    ]
    for candidate in candidates:
        if (candidate / "epistemic-rag").exists() or (candidate / "runs").exists():
            return candidate
    return APP_ROOT


ROOT = detect_project_root()
EPIC_ROOT = ROOT / "epistemic-rag"
DATA_ROOTS = {
    "EPIC v4": EPIC_ROOT / "data_v4",
    "EPIC v3": EPIC_ROOT / "data_v3",
}
if (ROOT / "runs").exists():
    DATA_ROOTS["Submission Bundle"] = ROOT / "runs"

REQUIRED_FILES = {
    "retrieved": "retrieved_docs.json",
    "structured": "structured_arguments.json",
    "clusters": "perspective_clusters.json",
    "summaries": "perspective_summaries.json",
    "final_output": "final_output.json",
    "main_viewpoints": "main_viewpoints.json",
    "evaluation": "evaluation.json",
}

SOURCE_TYPE_LABELS = {
    "brand": "Brand",
    "community": "Community",
    "credentialed": "Credentialed",
    "financial_media": "Financial media",
}

REASON_LABELS = {
    "interest_rate": "Loan rate vs expected return",
    "tax": "Tax treatment",
    "risk_tolerance": "Risk tolerance",
    "forgiveness": "Forgiveness rules",
    "psychology": "Peace of mind / debt stress",
    "liquidity": "Cash flow and flexibility",
    "retirement_match": "Employer match and compounding",
    "investment_return": "Long-run investment upside",
    "income_level": "Current and future income level",
    "time_horizon": "Time horizon",
    "withdrawal_rules": "Withdrawal restrictions",
    "retirement_rules": "Retirement account rules",
    "job_stability": "Job stability",
    "cash_flow": "Monthly cash flow",
    "housing_market": "Housing market conditions",
    "mobility": "Need for flexibility or mobility",
    "maintenance_cost": "Maintenance and ownership costs",
    "equity_building": "Equity building",
    "uncertainty": "Macro uncertainty",
}

POSTURE_COLORS = {
    "Confident": "#2d6a4f",
    "Conditional": "#c77d00",
    "Informational": "#577590",
}


def load_json(path: Path, default: Any = None) -> Any:
    if not path.exists():
        return default
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def list_runs() -> list[dict[str, Any]]:
    runs: list[dict[str, Any]] = []
    for label, data_root in DATA_ROOTS.items():
        if not data_root.exists():
            continue
        for child in sorted(data_root.iterdir()):
            if not child.is_dir():
                continue
            file_status = {name: (child / filename).exists() for name, filename in REQUIRED_FILES.items()}
            if not any(file_status.values()):
                continue
            runs.append(
                {
                    "display": f"{label} · {child.name}",
                    "version": label,
                    "path": child,
                    "files": file_status,
                    "complete": file_status["clusters"] and (file_status["main_viewpoints"] or file_status["final_output"]),
                }
            )
    runs.sort(key=lambda item: (not item["complete"], item["display"]))
    return runs


def humanize_reason(reason: str) -> str:
    return REASON_LABELS.get(reason, reason.replace("_", " ").strip().title())


def humanize_source_type(source_type: str) -> str:
    return SOURCE_TYPE_LABELS.get(source_type, source_type.replace("_", " ").title())


def extract_query(clusters: list[dict[str, Any]], structured: list[dict[str, Any]]) -> str:
    if clusters and clusters[0].get("passages"):
        return clusters[0]["passages"][0].get("query", "Unknown query")
    if structured:
        return structured[0].get("query", "Unknown query")
    return "Unknown query"


def extract_options(structured: list[dict[str, Any]]) -> tuple[str, str]:
    directions = Counter(item.get("coarse_direction") for item in structured)
    if not directions:
        return ("Option A", "Option B")
    # Query-relative option labels are not persisted yet, so we keep this generic for now.
    return ("Option A", "Option B")


def style_chip(text: str, bg: str = "#f3f4f6", fg: str = "#374151") -> str:
    return (
        f"<span style='display:inline-block;padding:4px 10px;border-radius:999px;"
        f"background:{bg};color:{fg};font-size:0.82rem;margin:2px 6px 2px 0;'>{text}</span>"
    )


def build_cluster_maps(clusters: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    return {cluster["cluster_id"]: cluster for cluster in clusters}


def get_display_viewpoints(run_dir: Path) -> list[dict[str, Any]]:
    main_viewpoints = load_json(run_dir / REQUIRED_FILES["main_viewpoints"], default=None)
    if main_viewpoints:
        return main_viewpoints
    final_output = load_json(run_dir / REQUIRED_FILES["final_output"], default=[])
    return final_output[:3]


def source_links_for_cluster(cluster: dict[str, Any]) -> list[tuple[str, str, str]]:
    links = []
    seen = set()
    for item in cluster.get("passages", []):
        url = item.get("url")
        name = item.get("source_name", "Unknown source")
        source_type = item.get("source_type", "unknown")
        key = (name, url, source_type)
        if not url or key in seen:
            continue
        seen.add(key)
        links.append(key)
    return links


def render_source_section(cluster: dict[str, Any], source_types: list[str]) -> None:
    st.markdown("**Source mix**")
    chips = "".join(style_chip(humanize_source_type(s)) for s in source_types)
    st.markdown(chips, unsafe_allow_html=True)
    links = source_links_for_cluster(cluster)
    if links:
        st.markdown("**Original documents**")
        for name, url, source_type in links[:6]:
            st.markdown(f"- [{name}]({url}) · {humanize_source_type(source_type)}")


def render_evidence_section(cluster: dict[str, Any]) -> None:
    passages = sorted(
        cluster.get("passages", []),
        key=lambda item: (float(item.get("confidence_score", 0.0)), float(item.get("bm25_score", 0.0))),
        reverse=True,
    )
    st.markdown("**Supporting evidence**")
    for item in passages[:3]:
        url = item.get("url")
        name = item.get("source_name", "Unknown source")
        source_type = humanize_source_type(item.get("source_type", "unknown"))
        posture = item.get("posture", "").title()
        header = f"{name} · {source_type}"
        if url:
            header = f"[{name}]({url}) · {source_type}"
        st.markdown(f"- {header}")
        st.caption(
            f"Claim: {item.get('main_claim', '')} "
            f"(posture: {posture}, retrieval rank: {item.get('retrieval_rank', 'n/a')})"
        )


def reason_match_score(reason: str, item: dict[str, Any]) -> int:
    reason_norm = str(reason).strip().lower()
    tags = [str(tag).strip().lower() for tag in item.get("reason_types", [])]
    claim = str(item.get("main_claim", "")).lower()
    support = str(item.get("supporting_text", "")).lower()

    score = 0
    if reason_norm in tags:
        score += 4
    humanized = humanize_reason(reason).lower()
    for token in re.split(r"[^a-z0-9]+", humanized):
        if len(token) < 4:
            continue
        if token in claim:
            score += 2
        if token in support:
            score += 1
    return score


def find_evidence_for_reason(cluster: dict[str, Any], reason: str) -> dict[str, Any] | None:
    passages = sorted(
        cluster.get("passages", []),
        key=lambda item: (
            reason_match_score(reason, item),
            float(item.get("confidence_score", 0.0)),
            float(item.get("bm25_score", 0.0)),
        ),
        reverse=True,
    )
    if not passages:
        return None
    top = passages[0]
    if reason_match_score(reason, top) <= 0:
        return None
    return top


def render_metrics_sidebar(evaluation: dict[str, Any]) -> None:
    if not evaluation:
        st.sidebar.info("No evaluation file found for this run yet.")
        return
    epic_key = "EPIC_v4" if "EPIC_v4" in evaluation else ("EPIC_v3" if "EPIC_v3" in evaluation else None)
    if not epic_key:
        st.sidebar.info("Evaluation file does not contain EPIC metrics.")
        return
    metrics = evaluation[epic_key]
    st.sidebar.markdown("### Evaluation snapshot")
    st.sidebar.metric("Purity", f"{metrics.get('purity_mean', 0.0):.2f}")
    st.sidebar.metric("Inter-cluster distance", f"{metrics.get('inter_cluster_distance', 0.0):.2f}")
    st.sidebar.metric("Balance-adjusted ECS", f"{metrics.get('balance_adjusted_ecs', 0.0):.2f}")
    st.sidebar.metric("Posture balance", f"{metrics.get('posture_balance', 0.0):.2f}")
    st.sidebar.metric("Direction balance", f"{metrics.get('direction_balance', 0.0):.2f}")


def render_viewpoint_card(
    viewpoint: dict[str, Any],
    cluster: dict[str, Any],
    column,
) -> None:
    label = viewpoint.get("label", viewpoint.get("cluster_id", "Perspective"))
    confidence = viewpoint.get("confidence", "Conditional")
    posture_color = POSTURE_COLORS.get(confidence, "#6b7280")
    source_types = viewpoint.get("source_types", cluster.get("source_types", []))
    source_count = viewpoint.get("source_count", len(cluster.get("source_names", [])))
    summary = viewpoint.get("summary", "")
    reasons = viewpoint.get("key_reasons", [])
    conditions = viewpoint.get("conditions", [])
    caveats = viewpoint.get("caveats", [])

    with column:
        st.markdown(
            f"""
            <div style="
                border:1px solid rgba(15,23,42,0.12);
                border-top:5px solid {posture_color};
                border-radius:18px;
                padding:18px 18px 8px 18px;
                min-height: 360px;
                background: linear-gradient(180deg, rgba(255,255,255,0.98), rgba(248,250,252,0.98));
                box-shadow: 0 12px 32px rgba(15,23,42,0.06);
            ">
                <div style="font-size:0.8rem;font-weight:700;letter-spacing:0.04em;text-transform:uppercase;color:{posture_color};">
                    {label}
                </div>
                <div style="margin-top:10px;font-size:1.04rem;line-height:1.55;color:#111827;">
                    {summary}
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        meta = (
            style_chip(f"Epistemic posture: {confidence}", bg="#fff7ed" if confidence == "Conditional" else "#ecfdf5", fg="#7c2d12" if confidence == "Conditional" else "#065f46")
            + style_chip(f"{source_count} grounded sources", bg="#eff6ff", fg="#1d4ed8")
        )
        st.markdown(meta, unsafe_allow_html=True)

        if reasons:
            st.markdown("**Why this view appears**")
            for reason in reasons[:3]:
                st.markdown(f"- {humanize_reason(reason)}")
                evidence = find_evidence_for_reason(cluster, reason)
                if evidence:
                    source_name = evidence.get("source_name", "Unknown source")
                    source_type = humanize_source_type(evidence.get("source_type", "unknown"))
                    url = evidence.get("url")
                    claim = evidence.get("main_claim", "").strip()
                    evidence_line = f"Supported by: “{claim}”"
                    if url:
                        evidence_line += f" — [{source_name}]({url}) · {source_type}"
                    else:
                        evidence_line += f" — {source_name} · {source_type}"
                    st.caption(evidence_line)

        if conditions:
            st.markdown("**Common conditions**")
            for condition in conditions[:3]:
                st.markdown(f"- {condition}")

        with st.expander("Caveats and exceptions", expanded=False):
            if caveats:
                for caveat in caveats[:5]:
                    st.markdown(f"- {caveat}")
            else:
                st.caption("No caveats were extracted for this perspective.")

        with st.expander("Grounding and evidence", expanded=False):
            render_source_section(cluster, source_types)
            st.divider()
            render_evidence_section(cluster)


def render_empty_state(run: dict[str, Any]) -> None:
    st.warning("This run has not produced all downstream artifacts yet.")
    st.markdown(
        "The interface becomes fully useful once the pipeline has produced clusters, summaries, and final output. "
        "For EPIC v4, run at least Steps 6 through 10."
    )
    statuses = run["files"]
    for label, exists in statuses.items():
        st.markdown(f"- `{label}`: {'available' if exists else 'missing'}")


def main() -> None:
    st.set_page_config(
        page_title="EPIC Interface",
        page_icon="🧭",
        layout="wide",
        initial_sidebar_state="expanded",
    )

    st.markdown(
        """
        <style>
        .block-container {padding-top: 2rem; padding-bottom: 3rem;}
        div[data-testid="stMetricValue"] {font-size: 1.15rem;}
        </style>
        """,
        unsafe_allow_html=True,
    )

    runs = list_runs()
    if not runs:
        st.error("No EPIC runs were found under `epistemic-rag/data_v3` or `epistemic-rag/data_v4`.")
        st.stop()

    st.sidebar.title("EPIC viewer")
    run_labels = [run["display"] for run in runs]
    default_index = next((i for i, run in enumerate(runs) if run["complete"]), 0)
    selected_label = st.sidebar.selectbox("Select a run", run_labels, index=default_index)
    run = next(item for item in runs if item["display"] == selected_label)
    run_dir = run["path"]

    clusters = load_json(run_dir / REQUIRED_FILES["clusters"], default=[])
    structured = load_json(run_dir / REQUIRED_FILES["structured"], default=[])
    summaries = load_json(run_dir / REQUIRED_FILES["summaries"], default=[])
    evaluation = load_json(run_dir / REQUIRED_FILES["evaluation"], default={})
    viewpoints = get_display_viewpoints(run_dir)

    st.sidebar.caption(f"Run directory: `{run_dir}`")
    st.sidebar.caption(f"Version: {run['version']}")
    render_metrics_sidebar(evaluation)

    if not run["complete"] or not clusters or not viewpoints:
        st.title("EPIC perspective interface")
        render_empty_state(run)
        st.stop()

    cluster_map = build_cluster_maps(clusters)
    query_text = extract_query(clusters, structured)
    source_type_counter = Counter(item.get("source_type") for item in structured)

    st.caption("YOUR QUESTION")
    st.title(query_text)
    st.markdown(
        """
        <div style="
            border:1px solid rgba(217,119,6,0.18);
            border-radius:14px;
            padding:14px 16px;
            background: linear-gradient(180deg, rgba(255,251,235,0.95), rgba(255,255,255,0.98));
            margin-bottom: 1rem;
        ">
            <div style="font-size:0.98rem;color:#7c2d12;">
                Experts and communities may frame this decision differently. The views below are grounded in retrieved documents,
                preserve caveats and conditions, and do not force a single final answer.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    overview_cols = st.columns([1.15, 1.15, 1.15, 0.9])
    overview_cols[0].metric("Primary viewpoints shown", len(viewpoints))
    overview_cols[1].metric("Discovered clusters", len(clusters))
    overview_cols[2].metric("Structured arguments", len(structured))
    overview_cols[3].markdown(
        "".join(
            style_chip(f"{humanize_source_type(k)} × {v}", bg="#f8fafc", fg="#334155")
            for k, v in sorted(source_type_counter.items())
        ),
        unsafe_allow_html=True,
    )

    st.divider()
    cols = st.columns(min(3, len(viewpoints)))
    for column, viewpoint in zip(cols, viewpoints[:3]):
        cluster = cluster_map.get(viewpoint.get("cluster_id"), {})
        render_viewpoint_card(viewpoint, cluster, column)

    st.divider()

    with st.expander("All discovered perspectives and run details", expanded=False):
        st.markdown("**Discovered clusters**")
        for cluster in sorted(clusters, key=lambda c: c.get("mean_confidence", 0.0), reverse=True):
            st.markdown(
                f"- `{cluster['cluster_id']}` · size={cluster.get('size', 0)} · "
                f"mean_confidence={cluster.get('mean_confidence', 0.0):.3f} · "
                f"directions={cluster.get('coarse_direction_distribution', {})}"
            )
        if summaries:
            st.divider()
            st.markdown("**Summary objects loaded**")
            st.json(summaries[:3])

    st.markdown(
        """
        <div style="
            margin-top: 1.3rem;
            border:1px dashed rgba(100,116,139,0.35);
            border-radius:14px;
            padding:14px 16px;
            background: rgba(248,250,252,0.8);
            color:#475569;
            font-size:0.95rem;
        ">
            This interface does not make a recommendation. It foregrounds the main perspectives in the retrieved evidence,
            while preserving conditions, caveats, and links back to original sources.
        </div>
        """,
        unsafe_allow_html=True,
    )


if __name__ == "__main__":
    main()
