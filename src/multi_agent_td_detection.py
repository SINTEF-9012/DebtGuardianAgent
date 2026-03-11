#!/usr/bin/env python3
"""
Run multi-agent technical debt detection experiment.
This script runs a user proxy, a generator (detector) agent, a critic agent, and a refiner agent 
to assign, validate, and refine classification labels. 
"""
import os
import time
import argparse
from datetime import datetime
import config
from settings import DATA_DIR, RESULT_DIR
from debt_utils import get_code_snippets, get_td_ground_truth, save_td_labels, normalize_td_label
from ollama_utils import start_ollama_server, stop_ollama_server
from agent_utils import create_agent
from evaluation import evaluate_and_save_td


# --- Inference with Multi Agents for TD Detection ---
def run_multi_agent_inference_td_detection(code_snippets, llm_config, sys_prompt_detector, sys_prompt_critic, sys_prompt_refiner, task_prompt, exp_name, result_dir):
    gen_td_results = []
    critic_td_results = []
    refiner_td_results = []
    try:
        user_proxy = create_agent(
            agent_type="conversable",
            name="user_proxy_agent",
            llm_config=llm_config,
            sys_prompt="A human admin.",
            description="A proxy for human input."
        )

        td_detector_gen = create_agent(
            agent_type="assistant",
            name="td_detection_generator_agent",
            llm_config=llm_config,
            sys_prompt=sys_prompt_detector,
            description="Analyze the code snippet in order to determine whether it contains a code smell.",
        )
        critic = create_agent(
            agent_type="assistant",
            name="td_detection_critic_agent",
            llm_config=llm_config,
            sys_prompt=sys_prompt_critic,
        )
        refiner = create_agent(
            agent_type="assistant",
            name="td_detection_refiner_agent",
            llm_config=llm_config,
            sys_prompt=sys_prompt_refiner,
        )

        for i, code_snippet in enumerate(code_snippets):
            #print(f"\n--- Processing code snippet {i+1}/{len(code_snippets)} ---")
            generator_response = user_proxy.initiate_chat(
                recipient=td_detector_gen,
                message=task_prompt + code_snippet,
                max_turns=1,
                summary_method="last_msg"
            ).summary.strip()
            #print(f"[Debug] Raw generator response for code snippet {i+1}: {generator_response}")

            if generator_response is not None:
                gen_td_result = normalize_td_label(generator_response)
                #print(f"[Info] Detector agent processed code snippet {i+1}: {gen_td_result}")
                gen_td_results.append(gen_td_result)
            else:
                gen_td_results.append("NONE")
                print(f"[Warning] Skipped code snippet {i+1} — no response or invalid format.")

            content_critic = f"""
                Check whether the GENERATOR_LABEL correctly identifies the code smell in the given Java code snippet. 
                If correct, return the same digit. If incorrect, return the corrected digit only. 
                Do not include explanations or extra text.

                CODE_SNIPPET: {code_snippet}
                GENERATOR_LABEL: {gen_td_result}
                """
            
            res_critic = critic.generate_reply(messages=[{"content": content_critic, "role": "user"}])
            if res_critic is not None and "content" in res_critic:
                critic_td_result = normalize_td_label(res_critic["content"].strip())
                #print(f"[Info] Critic agent processed code snippet {i+1}: {critic_td_result}")
                critic_td_results.append(critic_td_result)
            else:
                critic_td_results.append("NONE")
                print(f"[Warning] Critic skipped code snippet {i+1} — no response or invalid format.")

            content_refiner = f"""
                Review the code snippet and both labels. 
                Decide the final best label (0-4) based on your own analysis, preferring the CRITIC_LABEL if both are reasonable. 
                Return only the final digit, no explanations or extra text.

                CODE_SNIPPET: {code_snippet}
                GENERATOR_LABEL: {gen_td_result}
                CRITIC_LABEL: {critic_td_result}
                """
            res_refiner = refiner.generate_reply(messages=[{"content": content_refiner, "role": "user"}])
            if res_refiner is not None and "content" in res_refiner:
                refiner_td_result = normalize_td_label(res_refiner["content"].strip())
                #print(f"[Info] Refiner agent processed code snippet {i+1}: {refiner_td_result}")
                refiner_td_results.append(refiner_td_result)
            else:
                refiner_td_results.append("NONE")
                print(f"[Warning] Refiner skipped code snippet {i+1} — no response or invalid format.")

    except Exception as e:
        print("Error during multi-agent TD detection inference:", str(e))
    return refiner_td_results


def main():
    parser = argparse.ArgumentParser(description="Multi-agent technical debt detection runner")
    parser.add_argument("--input", default=config.IN_FILE, help="Input log file name (in config.DATA_DIR)")
    parser.add_argument("--gt", default=config.GT_FILE, help="Ground-truth file name (in config.DATA_DIR)")
    parser.add_argument("--result-dir", default=RESULT_DIR, help="Directory to store results")
    parser.add_argument("--design", default=None, help="Experiment design name (prefixes allowed: NA-, SA-, DA-, MA-). If omitted, DA-{shot} will be used.")
    parser.add_argument("--shot", default="few", choices=["zero", "few"], help="zero or few shot prompt selection")
    args = parser.parse_args()

    TASK = "td-detection"  
    shot = args.shot.lower()
    if shot not in ("zero", "few"):
        raise SystemExit("--shot must be 'zero' or 'few'")

    # Select prompts based on shot
    if shot == "zero":
        sys_prompt_generator = config.SYS_MSG_TD_DETECTION_GENERATOR_ZERO_SHOT
        sys_prompt_critic = config.SYS_MSG_TD_DETECTION_CRITIC_ZERO_SHOT
        sys_prompt_refiner = config.SYS_MSG_TD_DETECTION_REFINER_ZERO_SHOT
    else:
        sys_prompt_generator = config.SYS_MSG_TD_DETECTION_GENERATOR_FEW_SHOT
        sys_prompt_critic = config.SYS_MSG_TD_DETECTION_CRITIC_FEW_SHOT
        sys_prompt_refiner = config.SYS_MSG_TD_DETECTION_REFINER_FEW_SHOT

    llm_config = config.LLM_CONFIG
    os.makedirs(RESULT_DIR, exist_ok=True)

    # Determine DESIGN with MA- prefix by default 
    design = args.design
    if design is None:
        DESIGN = f"MA-{shot}"
    else:
        if any(design.startswith(p) for p in ("NA-", "SA-", "DA-", "MA-")):
            DESIGN = design
        else:
            DESIGN = design

    project_name = f"{TASK}_{DESIGN}"
    model = llm_config["config_list"][0]["model"].replace(":", "-")
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    exp_name = f"{project_name}_{model}_{timestamp}"

    input_file_path = os.path.join(DATA_DIR, args.input)
    ground_truth_file_path = os.path.join(DATA_DIR, args.gt)

    task_prompt = config.TASK_PROMPT_TD_DETECTION

    code_snippets = get_code_snippets(input_file_path)

    #proc = start_ollama_server()
    #time.sleep(5)
    #try:
    td_results = run_multi_agent_inference_td_detection(code_snippets, llm_config, sys_prompt_generator, sys_prompt_critic, sys_prompt_refiner, task_prompt, exp_name, RESULT_DIR)
    save_td_labels(td_results, llm_config, DESIGN, RESULT_DIR)
    #finally:
    #    stop_ollama_server(proc)

    # Load ground truth and evaluate
    gt = get_td_ground_truth(ground_truth_file_path)
    results = evaluate_and_save_td(normalize_td_label, gt, td_results, exp_name)
    #print("Evaluation results:", results)


if __name__ == "__main__":
    main()
