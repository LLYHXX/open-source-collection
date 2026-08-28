#!/usr/bin/env python3
"""End-to-end MCP SSE test that exercises ALL tools via a real MCP client connection.

Run from host (not inside Docker):
    python mcp_server/tests/test_mcp_e2e.py

Requires: MCP SDK installed (pip install mcp)
Requires: Backend running on localhost:8001
"""

import asyncio
import json
import re
import sys
import traceback

# -------------------------------------------------------------------
# Configuration
# -------------------------------------------------------------------
MCP_URL = "http://localhost:8000/mcp/sse"
API_KEY = "test_api_key_ws3"
SECRET_KEY = "test_secret_key_ws3"


async def run_tests():
    from mcp import ClientSession
    from mcp.client.sse import sse_client

    headers = {"X-Api-Key": API_KEY, "X-Secret-Key": SECRET_KEY}
    results = {}
    created_dataset_id = None
    created_experiment_id = None
    created_label_id = None
    created_annotation_id = None
    created_eval_group_id = None

    async with sse_client(MCP_URL, headers=headers) as (read_stream, write_stream):
        async with ClientSession(read_stream, write_stream) as session:
            # Initialize
            init = await session.initialize()
            print(f"Connected: {init.serverInfo.name} v{init.serverInfo.version}")
            print(f"Protocol: {init.protocolVersion}")

            # List tools
            tools_result = await session.list_tools()
            tool_names = sorted([t.name for t in tools_result.tools])
            print(f"Tools ({len(tool_names)}): {tool_names}\n")

            # ============================================================
            # Test helper
            # ============================================================
            async def test_tool(name, params=None, expect_error=False):
                params = params or {}
                try:
                    result = await session.call_tool(name, params)
                    text = ""
                    is_err = result.isError if hasattr(result, "isError") else False
                    for c in result.content:
                        text += getattr(c, "text", str(c))

                    if is_err and not expect_error:
                        status = "FAIL (tool error)"
                        preview = text[:120]
                    elif is_err and expect_error:
                        status = "PASS (expected error)"
                        preview = text[:120]
                    else:
                        status = "PASS"
                        preview = text[:120]

                    results[name] = status
                    print(f"  [{status}] {name}: {preview}")
                    return text
                except Exception as e:
                    results[name] = f"EXCEPTION: {e}"
                    print(f"  [EXCEPTION] {name}: {e}")
                    traceback.print_exc()
                    return None

            FAKE_UUID = "00000000-0000-0000-0000-000000000000"

            # ============================================================
            # CONTEXT TOOLS (5)
            # ============================================================
            print("=" * 60)
            print("CONTEXT TOOLS")
            print("=" * 60)

            await test_tool("whoami")
            await test_tool("list_workspaces")
            await test_tool("read_schema", {"entity_type": "evaluations"})
            await test_tool("read_taxonomy", {"category": "eval_types"})
            await test_tool("search", {"query": "Demo", "limit": 5})

            # ============================================================
            # EVALUATION TOOLS (16)
            # ============================================================
            print("\n" + "=" * 60)
            print("EVALUATION TOOLS")
            print("=" * 60)

            await test_tool("list_evaluations", {"limit": 5})
            await test_tool(
                "get_evaluation", {"evaluation_id": FAKE_UUID}, expect_error=True
            )
            await test_tool(
                "compare_evaluations",
                {
                    "evaluation_ids": [
                        FAKE_UUID,
                        "00000000-0000-0000-0000-000000000001",
                    ],
                },
                expect_error=True,
            )
            await test_tool(
                "run_evaluation",
                {
                    "eval_template_id": FAKE_UUID,
                    "dataset_id": FAKE_UUID,
                },
                expect_error=True,
            )

            # Eval template tools
            et_text = await test_tool("list_eval_templates", {"limit": 5})
            await test_tool(
                "get_eval_template", {"eval_template_id": FAKE_UUID}, expect_error=True
            )

            # Try to find a real USER-owned eval template for deeper testing
            user_template_id = None
            if et_text:
                # Look for template IDs in the output
                et_ids = re.findall(r"`([0-9a-f-]{36})`", et_text)
                if et_ids:
                    user_template_id = et_ids[0]

            # update_eval_template (USER-owned only)
            await test_tool(
                "update_eval_template",
                {
                    "eval_template_id": FAKE_UUID,
                    "description": "Updated via MCP E2E test",
                },
                expect_error=True,
            )

            # delete_eval_template (with fake ID)
            await test_tool(
                "delete_eval_template",
                {
                    "eval_template_id": FAKE_UUID,
                },
                expect_error=True,
            )

            # duplicate_eval_template (with fake ID)
            await test_tool(
                "duplicate_eval_template",
                {
                    "eval_template_id": FAKE_UUID,
                    "name": "mcp-e2e-duplicate-test",
                },
                expect_error=True,
            )

            # test_eval_template (with fake ID)
            await test_tool(
                "test_eval_template",
                {
                    "eval_template_id": FAKE_UUID,
                    "mapping": {"response": "Test response", "query": "Test query"},
                },
                expect_error=True,
            )

            # Eval group tools
            eg_text = await test_tool("list_eval_groups", {"limit": 5})

            # Try to find a real eval group
            real_group_id = None
            if eg_text:
                eg_ids = re.findall(r"`([0-9a-f-]{36})`", eg_text)
                if eg_ids:
                    real_group_id = eg_ids[0]

            # get_eval_group
            if real_group_id:
                await test_tool("get_eval_group", {"eval_group_id": real_group_id})
            else:
                await test_tool(
                    "get_eval_group", {"eval_group_id": FAKE_UUID}, expect_error=True
                )

            # update_eval_group (with fake ID)
            await test_tool(
                "update_eval_group",
                {
                    "eval_group_id": FAKE_UUID,
                    "description": "Updated by MCP E2E",
                },
                expect_error=True,
            )

            # delete_eval_group (with fake ID)
            await test_tool(
                "delete_eval_group",
                {
                    "eval_group_id": FAKE_UUID,
                },
                expect_error=True,
            )

            # edit_eval_group_templates (with fake IDs)
            await test_tool(
                "edit_eval_group_templates",
                {
                    "eval_group_id": FAKE_UUID,
                    "added_template_ids": [FAKE_UUID],
                },
                expect_error=True,
            )

            # ============================================================
            # DATASET TOOLS (20)
            # ============================================================
            print("\n" + "=" * 60)
            print("DATASET TOOLS")
            print("=" * 60)

            ds_text = await test_tool("list_datasets", {"limit": 5})

            dataset_id = None
            if ds_text:
                ids = re.findall(r"datasets/([0-9a-f-]{36})", ds_text)
                if ids:
                    dataset_id = ids[0]

            if dataset_id:
                await test_tool(
                    "get_dataset",
                    {"dataset_id": dataset_id, "include_sample_rows": True},
                )
                await test_tool(
                    "get_dataset_rows", {"dataset_id": dataset_id, "limit": 5}
                )
            else:
                await test_tool(
                    "get_dataset", {"dataset_id": FAKE_UUID}, expect_error=True
                )
                await test_tool(
                    "get_dataset_rows", {"dataset_id": FAKE_UUID}, expect_error=True
                )

            # create_dataset
            ds_result = await test_tool(
                "create_dataset",
                {
                    "name": "MCP-E2E-Comprehensive-Test",
                    "columns": ["input", "expected_output", "context"],
                    "column_types": ["text", "text", "text"],
                },
            )
            if ds_result and "MCP-E2E-Comprehensive-Test" in ds_result:
                m = re.search(r"`([0-9a-f-]{36})`", ds_result)
                if m:
                    created_dataset_id = m.group(1)

            # add_dataset_rows
            if created_dataset_id:
                await test_tool(
                    "add_dataset_rows",
                    {
                        "dataset_id": created_dataset_id,
                        "rows": [
                            {
                                "input": "What is AI?",
                                "expected_output": "AI is artificial intelligence.",
                                "context": "tech",
                            },
                            {
                                "input": "What is ML?",
                                "expected_output": "ML is machine learning.",
                                "context": "tech",
                            },
                        ],
                    },
                )
            else:
                print("  [SKIP] add_dataset_rows — no dataset created")

            # update_dataset
            if created_dataset_id:
                await test_tool(
                    "update_dataset",
                    {
                        "dataset_id": created_dataset_id,
                        "name": "MCP-E2E-Comprehensive-Test-Updated",
                    },
                )
            else:
                await test_tool(
                    "update_dataset",
                    {
                        "dataset_id": FAKE_UUID,
                        "name": "test",
                    },
                    expect_error=True,
                )

            # add_columns
            if created_dataset_id:
                await test_tool(
                    "add_columns",
                    {
                        "dataset_id": created_dataset_id,
                        "columns": [{"name": "score", "data_type": "float"}],
                    },
                )
            else:
                await test_tool(
                    "add_columns",
                    {
                        "dataset_id": FAKE_UUID,
                        "columns": [{"name": "score", "data_type": "float"}],
                    },
                    expect_error=True,
                )

            # update_column (get column ID first)
            if created_dataset_id:
                # Get a column ID from get_dataset
                ds_detail = await test_tool(
                    "get_dataset", {"dataset_id": created_dataset_id}
                )
                col_id = None
                if ds_detail:
                    col_ids = re.findall(r"score.*?([0-9a-f-]{36})", ds_detail)
                    if not col_ids:
                        col_ids = re.findall(r"`([0-9a-f-]{36})`", ds_detail)
                    if col_ids and len(col_ids) > 1:
                        col_id = col_ids[
                            -1
                        ]  # last one is likely the new 'score' column

                if col_id:
                    await test_tool(
                        "update_column",
                        {
                            "dataset_id": created_dataset_id,
                            "column_id": col_id,
                            "new_name": "quality_score",
                        },
                    )
                else:
                    print("  [SKIP] update_column — no column ID found")
            else:
                await test_tool(
                    "update_column",
                    {
                        "dataset_id": FAKE_UUID,
                        "column_id": FAKE_UUID,
                        "new_name": "test",
                    },
                    expect_error=True,
                )

            # update_cell_value (with invalid cell to test error path)
            if created_dataset_id:
                await test_tool(
                    "update_cell_value",
                    {
                        "dataset_id": created_dataset_id,
                        "updates": {FAKE_UUID: "new value"},
                    },
                )
            else:
                await test_tool(
                    "update_cell_value",
                    {
                        "dataset_id": FAKE_UUID,
                        "updates": {FAKE_UUID: "new value"},
                    },
                    expect_error=True,
                )

            # delete_rows (with invalid row)
            await test_tool(
                "delete_rows",
                {
                    "dataset_id": created_dataset_id or FAKE_UUID,
                    "row_ids": [FAKE_UUID],
                },
                expect_error=True,
            )

            # delete_column (with invalid column)
            await test_tool(
                "delete_column",
                {
                    "dataset_id": created_dataset_id or FAKE_UUID,
                    "column_id": FAKE_UUID,
                },
                expect_error=True,
            )

            # clone_dataset
            if created_dataset_id:
                clone_result = await test_tool(
                    "clone_dataset",
                    {
                        "dataset_id": created_dataset_id,
                        "new_name": "MCP-E2E-Cloned-Dataset",
                    },
                )
                # Clean up cloned dataset
                if clone_result:
                    m = re.search(r"`([0-9a-f-]{36})`", clone_result)
                    if m:
                        cloned_id = m.group(1)
                        await test_tool("delete_dataset", {"dataset_ids": [cloned_id]})
            else:
                await test_tool(
                    "clone_dataset",
                    {
                        "dataset_id": FAKE_UUID,
                    },
                    expect_error=True,
                )
                await test_tool(
                    "delete_dataset", {"dataset_ids": [FAKE_UUID]}, expect_error=True
                )

            # Dataset eval tools
            if created_dataset_id:
                await test_tool(
                    "list_dataset_evals", {"dataset_id": created_dataset_id}
                )
                await test_tool(
                    "get_dataset_eval_stats", {"dataset_id": created_dataset_id}
                )
            else:
                await test_tool(
                    "list_dataset_evals", {"dataset_id": FAKE_UUID}, expect_error=True
                )
                await test_tool(
                    "get_dataset_eval_stats",
                    {"dataset_id": FAKE_UUID},
                    expect_error=True,
                )

            # add_dataset_eval (with invalid template)
            await test_tool(
                "add_dataset_eval",
                {
                    "dataset_id": created_dataset_id or FAKE_UUID,
                    "name": "Test-Eval",
                    "template_id": FAKE_UUID,
                    "mapping": {"output": FAKE_UUID},
                },
                expect_error=True,
            )

            # run_dataset_evals (with invalid eval)
            await test_tool(
                "run_dataset_evals",
                {
                    "dataset_id": created_dataset_id or FAKE_UUID,
                    "eval_ids": [FAKE_UUID],
                },
                expect_error=True,
            )

            # edit_dataset_eval (with invalid eval)
            await test_tool(
                "edit_dataset_eval",
                {
                    "dataset_id": created_dataset_id or FAKE_UUID,
                    "eval_id": FAKE_UUID,
                    "model": "gpt-4o",
                },
                expect_error=True,
            )

            # delete_dataset_eval (with invalid eval)
            await test_tool(
                "delete_dataset_eval",
                {
                    "dataset_id": created_dataset_id or FAKE_UUID,
                    "eval_id": FAKE_UUID,
                },
                expect_error=True,
            )

            # knowledge bases
            await test_tool("list_knowledge_bases", {"limit": 5})

            # ============================================================
            # ANNOTATION TOOLS (13)
            # ============================================================
            print("\n" + "=" * 60)
            print("ANNOTATION TOOLS")
            print("=" * 60)

            await test_tool("list_annotation_labels", {"limit": 5})
            await test_tool("list_annotations", {"limit": 5})
            await test_tool(
                "get_annotation", {"annotation_id": FAKE_UUID}, expect_error=True
            )

            # Create label + annotation
            label_result = await test_tool(
                "create_annotation_label",
                {
                    "name": "MCP-E2E-Quality-v2",
                    "label_type": "star",
                    "description": "Quality rating for E2E test",
                    "settings": {"no_of_stars": 5},
                },
            )
            if label_result:
                m = re.search(r"`([0-9a-f-]{36})`", label_result)
                if m:
                    created_label_id = m.group(1)

            # update_annotation_label
            if created_label_id:
                await test_tool(
                    "update_annotation_label",
                    {
                        "label_id": created_label_id,
                        "description": "Updated description",
                    },
                )
            else:
                await test_tool(
                    "update_annotation_label",
                    {
                        "label_id": FAKE_UUID,
                        "description": "test",
                    },
                    expect_error=True,
                )

            if created_label_id and created_dataset_id:
                ann_result = await test_tool(
                    "create_annotation",
                    {
                        "name": "MCP-E2E-Test-Annotation-v2",
                        "dataset_id": created_dataset_id,
                        "label_ids": [created_label_id],
                        "responses": 1,
                    },
                )
                if ann_result:
                    m = re.search(r"`([0-9a-f-]{36})`", ann_result)
                    if m:
                        created_annotation_id = m.group(1)
            else:
                print("  [SKIP] create_annotation — no label or dataset")

            # update_annotation
            if created_annotation_id:
                await test_tool(
                    "update_annotation",
                    {
                        "annotation_id": created_annotation_id,
                        "name": "MCP-E2E-Test-Annotation-Updated",
                    },
                )
            else:
                await test_tool(
                    "update_annotation",
                    {
                        "annotation_id": FAKE_UUID,
                        "name": "test",
                    },
                    expect_error=True,
                )

            # get_annotate_row
            if created_annotation_id:
                await test_tool(
                    "get_annotate_row",
                    {
                        "annotation_id": created_annotation_id,
                    },
                )
            else:
                await test_tool(
                    "get_annotate_row",
                    {
                        "annotation_id": FAKE_UUID,
                    },
                    expect_error=True,
                )

            # submit_annotation (with invalid — user not assigned)
            await test_tool(
                "submit_annotation",
                {
                    "annotation_id": created_annotation_id or FAKE_UUID,
                    "label_values": [
                        {
                            "row_id": FAKE_UUID,
                            "label_id": created_label_id or FAKE_UUID,
                            "column_id": FAKE_UUID,
                            "value": 5,
                        }
                    ],
                },
                expect_error=True,
            )

            # reset_annotations (with invalid)
            await test_tool(
                "reset_annotations",
                {
                    "annotation_id": created_annotation_id or FAKE_UUID,
                    "row_id": FAKE_UUID,
                },
                expect_error=True,
            )

            # annotation_summary
            if created_dataset_id:
                await test_tool(
                    "annotation_summary",
                    {
                        "dataset_id": created_dataset_id,
                    },
                )
            else:
                await test_tool(
                    "annotation_summary",
                    {
                        "dataset_id": FAKE_UUID,
                    },
                    expect_error=True,
                )

            # delete_annotation (clean up — test at end)
            if created_annotation_id:
                await test_tool(
                    "delete_annotation",
                    {
                        "annotation_ids": [created_annotation_id],
                    },
                )
            else:
                await test_tool(
                    "delete_annotation",
                    {
                        "annotation_ids": [FAKE_UUID],
                    },
                )

            # delete_annotation_label (clean up)
            if created_label_id:
                await test_tool(
                    "delete_annotation_label",
                    {
                        "label_id": created_label_id,
                    },
                )
            else:
                await test_tool(
                    "delete_annotation_label",
                    {
                        "label_id": FAKE_UUID,
                    },
                    expect_error=True,
                )

            # ============================================================
            # OPTIMIZATION TOOLS (10)
            # ============================================================
            print("\n" + "=" * 60)
            print("OPTIMIZATION TOOLS")
            print("=" * 60)

            opt_text = await test_tool("list_optimization_runs", {"limit": 5})
            await test_tool(
                "get_optimization_run",
                {"optimization_id": FAKE_UUID},
                expect_error=True,
            )
            await test_tool(
                "create_optimization_run",
                {
                    "name": "MCP-E2E-Opt-Test",
                    "column_id": FAKE_UUID,
                    "algorithm": "random_search",
                    "algorithm_config": {"num_variations": 3},
                },
                expect_error=True,
            )

            # Try to find a real optimization run for deeper testing
            opt_id = None
            if opt_text:
                opt_ids = re.findall(r"optimization[s]?/([0-9a-f-]{36})", opt_text)
                if not opt_ids:
                    opt_ids = re.findall(r"`([0-9a-f-]{36})`", opt_text)
                if opt_ids:
                    opt_id = opt_ids[0]

            # stop_optimization_run (with fake/real ID)
            await test_tool(
                "stop_optimization_run",
                {
                    "optimization_id": opt_id or FAKE_UUID,
                },
                expect_error=True,
            )

            # get_optimization_steps
            if opt_id:
                await test_tool("get_optimization_steps", {"optimization_id": opt_id})
            else:
                await test_tool(
                    "get_optimization_steps",
                    {"optimization_id": FAKE_UUID},
                    expect_error=True,
                )

            # get_optimization_graph
            if opt_id:
                await test_tool("get_optimization_graph", {"optimization_id": opt_id})
            else:
                await test_tool(
                    "get_optimization_graph",
                    {"optimization_id": FAKE_UUID},
                    expect_error=True,
                )

            # get_optimization_trial (with fake IDs)
            await test_tool(
                "get_optimization_trial",
                {
                    "optimization_id": FAKE_UUID,
                    "trial_id": FAKE_UUID,
                },
                expect_error=True,
            )

            # get_trial_prompt (with fake IDs)
            await test_tool(
                "get_trial_prompt",
                {
                    "optimization_id": FAKE_UUID,
                    "trial_id": FAKE_UUID,
                },
                expect_error=True,
            )

            # get_trial_scenarios (with fake IDs)
            await test_tool(
                "get_trial_scenarios",
                {
                    "optimization_id": FAKE_UUID,
                    "trial_id": FAKE_UUID,
                },
                expect_error=True,
            )

            # get_trial_evaluations (with fake IDs)
            await test_tool(
                "get_trial_evaluations",
                {
                    "optimization_id": FAKE_UUID,
                    "trial_id": FAKE_UUID,
                },
                expect_error=True,
            )

            # ============================================================
            # EXPERIMENT TOOLS (10)
            # ============================================================
            print("\n" + "=" * 60)
            print("EXPERIMENT TOOLS")
            print("=" * 60)

            await test_tool("list_experiments", {"limit": 5})
            await test_tool(
                "get_experiment_results",
                {"experiment_id": FAKE_UUID},
                expect_error=True,
            )
            await test_tool(
                "get_experiment_comparison",
                {"experiment_id": FAKE_UUID},
                expect_error=True,
            )
            await test_tool(
                "get_experiment_data", {"experiment_id": FAKE_UUID}, expect_error=True
            )
            await test_tool(
                "get_experiment_stats", {"experiment_id": FAKE_UUID}, expect_error=True
            )

            # create_experiment
            if created_dataset_id:
                exp_result = await test_tool(
                    "create_experiment",
                    {
                        "name": "MCP-E2E-Experiment-Comprehensive",
                        "dataset_id": created_dataset_id,
                        "variants": [
                            {"model": "gpt-4o", "temperature": 0.7},
                            {"model": "claude-3-5-sonnet", "temperature": 0.5},
                        ],
                    },
                )
                if exp_result:
                    m = re.search(r"`([0-9a-f-]{36})`", exp_result)
                    if m:
                        created_experiment_id = m.group(1)

                if created_experiment_id:
                    await test_tool(
                        "get_experiment_results",
                        {"experiment_id": created_experiment_id},
                    )
                    await test_tool(
                        "get_experiment_data",
                        {
                            "experiment_id": created_experiment_id,
                            "limit": 5,
                        },
                    )
                    await test_tool(
                        "get_experiment_stats", {"experiment_id": created_experiment_id}
                    )
            else:
                print("  [SKIP] create_experiment — no dataset available")

            # add_experiment_eval (with invalid template)
            await test_tool(
                "add_experiment_eval",
                {
                    "experiment_id": created_experiment_id or FAKE_UUID,
                    "name": "Test-Exp-Eval",
                    "template_id": FAKE_UUID,
                },
                expect_error=True,
            )

            # compare_experiments
            if created_experiment_id:
                await test_tool(
                    "compare_experiments",
                    {
                        "experiment_id": created_experiment_id,
                    },
                )
            else:
                await test_tool(
                    "compare_experiments",
                    {
                        "experiment_id": FAKE_UUID,
                    },
                    expect_error=True,
                )

            # rerun_experiment (with invalid)
            await test_tool(
                "rerun_experiment",
                {
                    "experiment_ids": [FAKE_UUID],
                },
                expect_error=True,
            )

            # delete_experiment
            if created_experiment_id:
                await test_tool(
                    "delete_experiment",
                    {
                        "experiment_ids": [created_experiment_id],
                    },
                )
            else:
                await test_tool(
                    "delete_experiment",
                    {
                        "experiment_ids": [FAKE_UUID],
                    },
                    expect_error=True,
                )

            # ============================================================
            # PROMPT WORKBENCH TOOLS (15)
            # ============================================================
            print("\n" + "=" * 60)
            print("PROMPT WORKBENCH TOOLS")
            print("=" * 60)

            # Prompt folders and labels
            await test_tool("list_prompt_folders", {"limit": 5})
            await test_tool("list_prompt_labels", {"limit": 5})

            # Prompt scenarios
            await test_tool("list_prompt_scenarios", {"limit": 5})

            # Prompt templates
            pt_text = await test_tool("list_prompt_templates", {"limit": 5})

            # Try to find a real prompt template for deeper testing
            pt_id = None
            if pt_text:
                pt_ids = re.findall(r"`([0-9a-f-]{36})`", pt_text)
                if pt_ids:
                    pt_id = pt_ids[0]

            if pt_id:
                await test_tool("get_prompt_template", {"template_id": pt_id})
                await test_tool(
                    "list_prompt_versions", {"template_id": pt_id, "limit": 5}
                )
                await test_tool("get_prompt_eval_configs", {"template_id": pt_id})
                await test_tool(
                    "list_prompt_simulations", {"template_id": pt_id, "limit": 5}
                )
            else:
                await test_tool(
                    "get_prompt_template", {"template_id": FAKE_UUID}, expect_error=True
                )
                await test_tool(
                    "list_prompt_versions",
                    {"template_id": FAKE_UUID},
                    expect_error=True,
                )
                await test_tool(
                    "get_prompt_eval_configs",
                    {"template_id": FAKE_UUID},
                    expect_error=True,
                )
                await test_tool(
                    "list_prompt_simulations",
                    {"template_id": FAKE_UUID},
                    expect_error=True,
                )

            # get_prompt_version with fake IDs
            await test_tool(
                "get_prompt_version",
                {
                    "template_id": FAKE_UUID,
                    "version_id": FAKE_UUID,
                },
                expect_error=True,
            )

            # commit_prompt_version with fake template
            await test_tool(
                "commit_prompt_version",
                {
                    "template_id": FAKE_UUID,
                    "version_name": "v1",
                },
                expect_error=True,
            )

            # compare_prompt_versions with fake IDs
            await test_tool(
                "compare_prompt_versions",
                {
                    "template_id": FAKE_UUID,
                    "version_id_a": FAKE_UUID,
                    "version_id_b": "00000000-0000-0000-0000-000000000001",
                },
                expect_error=True,
            )

            # Prompt simulation CRUD with fake IDs
            await test_tool(
                "get_prompt_simulation",
                {
                    "template_id": FAKE_UUID,
                    "simulation_id": FAKE_UUID,
                },
                expect_error=True,
            )

            await test_tool(
                "delete_prompt_simulation",
                {
                    "template_id": FAKE_UUID,
                    "simulation_id": FAKE_UUID,
                },
                expect_error=True,
            )

            # ============================================================
            # TRACING TOOLS (8)
            # ============================================================
            print("\n" + "=" * 60)
            print("TRACING TOOLS")
            print("=" * 60)

            await test_tool("list_projects", {"limit": 5})
            await test_tool("get_project", {"project_id": FAKE_UUID}, expect_error=True)

            trace_text = await test_tool("search_traces", {"limit": 3})

            trace_id = None
            if trace_text:
                ids = re.findall(r"traces/([0-9a-f-]{36})", trace_text)
                if ids:
                    trace_id = ids[0]

            if trace_id:
                await test_tool(
                    "get_trace", {"trace_id": trace_id, "include_spans": True}
                )
                await test_tool("get_trace_error_analysis", {"trace_id": trace_id})
            else:
                await test_tool("get_trace", {"trace_id": FAKE_UUID}, expect_error=True)
                await test_tool(
                    "get_trace_error_analysis",
                    {"trace_id": FAKE_UUID},
                    expect_error=True,
                )

            await test_tool("analyze_errors", {"days": 7, "limit": 20})
            await test_tool("list_alert_monitors", {"limit": 5})

            # create_trace_annotation with invalid trace
            await test_tool(
                "create_trace_annotation",
                {
                    "trace_id": FAKE_UUID,
                    "annotation_label_id": FAKE_UUID,
                    "value_float": 4.0,
                },
                expect_error=True,
            )

            # ============================================================
            # AGENT TOOLS (8)
            # ============================================================
            print("\n" + "=" * 60)
            print("AGENT TOOLS")
            print("=" * 60)

            await test_tool("list_agents", {"limit": 5})
            await test_tool("get_agent", {"agent_id": FAKE_UUID}, expect_error=True)
            await test_tool(
                "run_agent_test", {"run_test_id": FAKE_UUID}, expect_error=True
            )
            await test_tool("list_test_executions", {"run_test_id": FAKE_UUID})
            await test_tool(
                "get_test_execution", {"execution_id": FAKE_UUID}, expect_error=True
            )
            await test_tool(
                "get_call_execution",
                {"call_execution_id": FAKE_UUID},
                expect_error=True,
            )
            await test_tool(
                "list_agent_versions", {"agent_id": FAKE_UUID}, expect_error=True
            )
            await test_tool("list_scenarios", {"limit": 5})

            # ============================================================
            # SIMULATION TOOLS (32)
            # ============================================================
            print("\n" + "=" * 60)
            print("SIMULATION TOOLS")
            print("=" * 60)

            # Agent Definition CRUD
            await test_tool(
                "create_agent_definition",
                {"agent_name": "E2E-Test-Agent", "agent_type": "text"},
            )
            await test_tool(
                "update_agent_definition",
                {"agent_id": FAKE_UUID, "agent_name": "Updated"},
                expect_error=True,
            )
            await test_tool(
                "delete_agent_definition", {"agent_id": FAKE_UUID}, expect_error=True
            )
            await test_tool(
                "duplicate_agent_definition",
                {"agent_id": FAKE_UUID, "new_name": "Copy"},
                expect_error=True,
            )

            # Agent Version Management
            await test_tool(
                "create_agent_version", {"agent_id": FAKE_UUID}, expect_error=True
            )
            await test_tool(
                "activate_agent_version",
                {"agent_id": FAKE_UUID, "version_id": FAKE_UUID},
                expect_error=True,
            )
            await test_tool(
                "get_agent_version",
                {"agent_id": FAKE_UUID, "version_id": FAKE_UUID},
                expect_error=True,
            )
            await test_tool(
                "compare_agent_versions",
                {
                    "agent_id": FAKE_UUID,
                    "version_id_a": FAKE_UUID,
                    "version_id_b": FAKE_UUID,
                },
                expect_error=True,
            )

            # Scenario Management
            await test_tool(
                "create_scenario",
                {
                    "name": "E2E-Scenario",
                    "scenario_type": "script",
                    "agent_id": FAKE_UUID,
                },
                expect_error=True,
            )
            await test_tool(
                "get_scenario", {"scenario_id": FAKE_UUID}, expect_error=True
            )
            await test_tool(
                "update_scenario",
                {"scenario_id": FAKE_UUID, "name": "Updated"},
                expect_error=True,
            )
            await test_tool(
                "delete_scenario", {"scenario_id": FAKE_UUID}, expect_error=True
            )

            # Persona Management
            await test_tool("list_personas", {"limit": 5})
            await test_tool("get_persona", {"persona_id": FAKE_UUID}, expect_error=True)
            await test_tool(
                "create_persona", {"name": "E2E-Persona", "simulation_type": "text"}
            )
            await test_tool(
                "update_persona",
                {"persona_id": FAKE_UUID, "name": "Updated"},
                expect_error=True,
            )
            await test_tool(
                "delete_persona", {"persona_id": FAKE_UUID}, expect_error=True
            )
            await test_tool(
                "duplicate_persona",
                {"persona_id": FAKE_UUID, "new_name": "Copy"},
                expect_error=True,
            )

            # Simulator Agent
            await test_tool("list_simulator_agents", {"limit": 5})
            await test_tool(
                "create_simulator_agent",
                {"name": "E2E-SimAgent", "prompt": "You are a test user."},
            )
            await test_tool(
                "update_simulator_agent",
                {"simulator_agent_id": FAKE_UUID, "name": "Updated"},
                expect_error=True,
            )

            # Run Test
            await test_tool(
                "create_run_test",
                {
                    "name": "E2E-RunTest",
                    "agent_id": FAKE_UUID,
                    "scenario_ids": [FAKE_UUID],
                },
                expect_error=True,
            )
            await test_tool(
                "update_run_test",
                {"run_test_id": FAKE_UUID, "name": "Updated"},
                expect_error=True,
            )
            await test_tool(
                "delete_run_test", {"run_test_id": FAKE_UUID}, expect_error=True
            )
            await test_tool(
                "get_run_test_analytics", {"run_test_id": FAKE_UUID}, expect_error=True
            )

            # Test Execution Ops
            await test_tool(
                "cancel_test_execution",
                {"test_execution_id": FAKE_UUID},
                expect_error=True,
            )
            await test_tool(
                "rerun_test_execution",
                {"test_execution_id": FAKE_UUID},
                expect_error=True,
            )
            await test_tool(
                "get_test_execution_analytics",
                {"test_execution_id": FAKE_UUID},
                expect_error=True,
            )
            await test_tool(
                "delete_test_execution",
                {"test_execution_id": FAKE_UUID},
                expect_error=True,
            )

            # Call Execution Ops
            await test_tool(
                "get_call_transcript",
                {"call_execution_id": FAKE_UUID},
                expect_error=True,
            )
            await test_tool(
                "get_call_logs", {"call_execution_id": FAKE_UUID}, expect_error=True
            )
            await test_tool(
                "rerun_call_execution",
                {"call_execution_id": FAKE_UUID},
                expect_error=True,
            )

            # ============================================================
            # TRACING TOOLS - NEW (21)
            # ============================================================
            print("\n" + "=" * 60)
            print("TRACING TOOLS - NEW")
            print("=" * 60)

            # Span operations
            await test_tool("get_span", {"span_id": FAKE_UUID}, expect_error=True)
            await test_tool("list_spans", {"trace_id": FAKE_UUID}, expect_error=True)
            await test_tool("get_span_tree", {"trace_id": FAKE_UUID}, expect_error=True)

            # Session operations
            await test_tool("list_sessions", {"limit": 5})
            await test_tool("get_session", {"session_id": FAKE_UUID}, expect_error=True)
            await test_tool(
                "get_session_analytics", {"session_id": FAKE_UUID}, expect_error=True
            )

            # Score operations
            await test_tool(
                "list_trace_scores", {"trace_id": FAKE_UUID}, expect_error=True
            )
            await test_tool(
                "create_score",
                {"trace_id": FAKE_UUID, "annotation_label_id": FAKE_UUID},
                expect_error=True,
            )
            await test_tool(
                "update_trace_annotation",
                {"annotation_id": FAKE_UUID},
                expect_error=True,
            )
            await test_tool(
                "delete_trace_annotation",
                {"annotation_id": FAKE_UUID},
                expect_error=True,
            )

            # Alert monitors
            await test_tool(
                "create_alert_monitor",
                {
                    "name": "E2E-Monitor",
                    "metric_type": "trace_count",
                    "threshold_operator": "gt",
                    "critical_threshold_value": 100.0,
                },
            )
            await test_tool(
                "update_alert_monitor",
                {"monitor_id": FAKE_UUID, "name": "Updated"},
                expect_error=True,
            )
            await test_tool(
                "delete_alert_monitor", {"monitor_id": FAKE_UUID}, expect_error=True
            )

            # Project operations
            await test_tool("create_project", {"name": "E2E-Project"})
            await test_tool(
                "update_project",
                {"project_id": FAKE_UUID, "name": "Updated"},
                expect_error=True,
            )
            await test_tool(
                "delete_project", {"project_id": FAKE_UUID}, expect_error=True
            )

            # Tag operations
            await test_tool(
                "list_trace_tags", {"trace_id": FAKE_UUID}, expect_error=True
            )
            await test_tool(
                "add_trace_tags",
                {"trace_id": FAKE_UUID, "tags": ["test"]},
                expect_error=True,
            )
            await test_tool(
                "remove_trace_tags",
                {"trace_id": FAKE_UUID, "tags": ["test"]},
                expect_error=True,
            )

            # Analytics
            await test_tool("get_trace_analytics", {"time_range": "24h"})
            await test_tool("get_trace_timeline", {"time_range": "24h"})

            # ============================================================
            # EVAL TOOLS - NEW (8)
            # ============================================================
            print("\n" + "=" * 60)
            print("EVAL TOOLS - NEW")
            print("=" * 60)

            await test_tool("create_eval_template", {"name": "e2e-test-eval"})
            await test_tool("get_eval_logs", {"eval_template_id": FAKE_UUID})
            await test_tool(
                "get_eval_log_detail", {"log_id": FAKE_UUID}, expect_error=True
            )
            await test_tool(
                "get_eval_playground",
                {"eval_template_id": FAKE_UUID},
                expect_error=True,
            )
            await test_tool(
                "get_eval_code_snippet",
                {"eval_template_id": FAKE_UUID, "language": "python"},
                expect_error=True,
            )
            await test_tool(
                "submit_eval_feedback",
                {"eval_template_id": FAKE_UUID, "feedback_value": "passed"},
                expect_error=True,
            )
            await test_tool(
                "apply_eval_group_to_dataset",
                {"eval_group_id": FAKE_UUID, "dataset_id": FAKE_UUID},
                expect_error=True,
            )
            await test_tool("delete_eval_logs", {"log_ids": [FAKE_UUID]})

            # ============================================================
            # PROMPT TOOLS - NEW (7)
            # ============================================================
            print("\n" + "=" * 60)
            print("PROMPT TOOLS - NEW")
            print("=" * 60)

            await test_tool("create_prompt_template", {"name": "E2E-Prompt"})
            await test_tool(
                "update_prompt_template",
                {"template_id": FAKE_UUID, "name": "Updated"},
                expect_error=True,
            )
            await test_tool(
                "delete_prompt_template", {"template_id": FAKE_UUID}, expect_error=True
            )
            await test_tool(
                "create_prompt_version",
                {"template_id": FAKE_UUID, "prompt_config": {"messages": []}},
                expect_error=True,
            )
            await test_tool(
                "set_eval_config_for_prompt",
                {"template_id": FAKE_UUID, "eval_template_ids": [FAKE_UUID]},
                expect_error=True,
            )
            await test_tool(
                "get_prompt_execution_results",
                {"template_id": FAKE_UUID},
                expect_error=True,
            )
            await test_tool("run_prompt", {"template_id": FAKE_UUID}, expect_error=True)

            # ============================================================
            # USER & WORKSPACE TOOLS (17)
            # ============================================================
            print("\n" + "=" * 60)
            print("USER & WORKSPACE TOOLS")
            print("=" * 60)

            await test_tool("list_users", {"limit": 5})
            await test_tool("get_user", {"user_id": FAKE_UUID}, expect_error=True)
            await test_tool("get_user_permissions", {})
            await test_tool(
                "invite_users",
                {"emails": ["test-e2e@example.com"], "role": "workspace_member"},
            )
            await test_tool(
                "update_user_role",
                {"user_id": FAKE_UUID, "new_role": "MEMBER", "level": "org"},
                expect_error=True,
            )
            await test_tool(
                "deactivate_user", {"user_id": FAKE_UUID}, expect_error=True
            )
            await test_tool("remove_user", {"user_id": FAKE_UUID}, expect_error=True)
            await test_tool("list_workspace_members", {"limit": 5})
            await test_tool("create_workspace", {"name": "E2E-Test-WS"})
            await test_tool(
                "update_workspace",
                {"workspace_id": FAKE_UUID, "name": "Updated"},
                expect_error=True,
            )
            await test_tool(
                "add_workspace_member",
                {"workspace_id": FAKE_UUID, "user_id": FAKE_UUID},
                expect_error=True,
            )
            await test_tool("list_organizations")
            await test_tool("list_org_members", {"limit": 5})
            await test_tool("get_organization")
            await test_tool("list_api_keys", {"limit": 5})
            await test_tool("create_api_key", {"key_type": "user"})
            await test_tool("revoke_api_key", {"key_id": FAKE_UUID}, expect_error=True)

            # ============================================================
            # USAGE TOOLS (1)
            # ============================================================
            print("\n" + "=" * 60)
            print("USAGE TOOLS")
            print("=" * 60)

            await test_tool("get_cost_breakdown", {"days": 30})

            # ============================================================
            # EVAL GROUP CREATE (needs valid template IDs)
            # ============================================================
            print("\n" + "=" * 60)
            print("EVAL GROUP CREATE")
            print("=" * 60)

            await test_tool(
                "create_eval_group",
                {
                    "name": "MCP-E2E-Test-Group",
                    "eval_template_ids": [FAKE_UUID],
                },
                expect_error=True,
            )

            # ============================================================
            # CLEANUP: Delete test dataset
            # ============================================================
            if created_dataset_id:
                print("\n" + "=" * 60)
                print("CLEANUP")
                print("=" * 60)
                await test_tool("delete_dataset", {"dataset_ids": [created_dataset_id]})

            # ============================================================
            # SUMMARY
            # ============================================================
            print("\n" + "=" * 60)
            print("RESULTS SUMMARY")
            print("=" * 60)

            passed = sum(1 for v in results.values() if v.startswith("PASS"))
            failed = sum(1 for v in results.values() if v.startswith("FAIL"))
            errors = sum(1 for v in results.values() if v.startswith("EXCEPTION"))

            for name, status in results.items():
                marker = "OK" if status.startswith("PASS") else "XX"
                print(f"  [{marker}] {name}: {status}")

            print(
                f"\nTotal: {len(results)} | Passed: {passed} | Failed: {failed} | Exceptions: {errors}"
            )

            if failed + errors == 0:
                print("\n--- ALL TESTS PASSED ---")
            else:
                print("\n--- SOME TESTS FAILED ---")
                sys.exit(1)


if __name__ == "__main__":
    asyncio.run(run_tests())
