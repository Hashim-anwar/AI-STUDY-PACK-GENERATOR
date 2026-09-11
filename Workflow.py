import json
import os
import re
import time
from typing import Any, Dict

import streamlit as st

try:

    from groq import Groq

except ImportError:

    Groq = None


from prompts import (
    PLANNING_PROMPT,
    CONTENT_PROMPT,
    ASSESSMENT_PROMPT,
    REVIEW_PROMPT,
    REFINEMENT_PROMPT,
)


# ============================================================
# CONFIGURATION
# ============================================================

DEFAULT_MODEL = os.getenv(
    "GROQ_MODEL",
    "openai/gpt-oss-120b",
)

MAX_RETRIES = 3

MAX_REFINEMENTS = 2


# ============================================================
# API KEY
# ============================================================

def get_api_key():

    # --------------------------------------------------------
    # Environment variable
    # --------------------------------------------------------

    api_key = os.getenv(
        "GROQ_API_KEY",
        "",
    ).strip()

    if api_key:
        return api_key


    # --------------------------------------------------------
    # Streamlit Secrets
    # --------------------------------------------------------

    try:

        api_key = st.secrets.get(
            "GROQ_API_KEY",
            "",
        )

        return str(api_key).strip()

    except Exception:

        return ""


# ============================================================
# GROQ CLIENT
# ============================================================

def get_client():

    if Groq is None:

        raise RuntimeError(
            "groq is not installed. "
            "Please check requirements.txt."
        )


    api_key = get_api_key()


    if not api_key:

        raise RuntimeError(
            "GROQ_API_KEY is missing. "
            "Add your Groq API key to Streamlit Secrets."
        )


    return Groq(
        api_key=api_key
    )


# ============================================================
# JSON PARSER
# ============================================================

def parse_json(text: str) -> Dict[str, Any]:

    if not text:

        raise ValueError(
            "AI returned an empty response."
        )


    text = text.strip()


    # --------------------------------------------------------
    # Remove Markdown code fences
    # --------------------------------------------------------

    text = re.sub(
        r"^```json\s*",
        "",
        text,
        flags=re.IGNORECASE,
    )

    text = re.sub(
        r"^```\s*",
        "",
        text,
    )

    text = re.sub(
        r"\s*```$",
        "",
        text,
    )


    # --------------------------------------------------------
    # Direct JSON
    # --------------------------------------------------------

    try:

        return json.loads(
            text
        )

    except json.JSONDecodeError:

        pass


    # --------------------------------------------------------
    # Find JSON object
    # --------------------------------------------------------

    start = text.find("{")

    end = text.rfind("}")


    if start >= 0 and end > start:

        json_text = text[
            start:end + 1
        ]

        try:

            return json.loads(
                json_text
            )

        except json.JSONDecodeError as error:

            raise ValueError(
                "AI returned invalid JSON."
            ) from error


    raise ValueError(
        "Could not find valid JSON in AI response."
    )


# ============================================================
# GENERIC AI CALL
# ============================================================

def call_ai(
    client,
    prompt,
    temperature=0.3,
):

    last_error = None


    for attempt in range(
        1,
        MAX_RETRIES + 1,
    ):

        try:

            response = client.chat.completions.create(

                model=DEFAULT_MODEL,

                messages=[
                    {
                        "role": "system",
                        "content": (
                            "You are an expert educational AI agent. "
                            "Follow the user's instructions exactly. "
                            "Return valid JSON only."
                        ),
                    },
                    {
                        "role": "user",
                        "content": prompt,
                    },
                ],

                temperature=temperature,

                response_format={
                    "type": "json_object"
                },

                # GPT-OSS supports configurable reasoning.
                # Medium provides a good balance for this workflow.
                reasoning_effort="medium",

            )


            text = (
                response.choices[0]
                .message
                .content
            )


            if not text:

                raise ValueError(
                    "AI returned an empty response."
                )


            return parse_json(
                text
            )


        except Exception as error:

            last_error = error


            if attempt < MAX_RETRIES:

                time.sleep(
                    attempt * 2
                )


    raise RuntimeError(

        f"AI generation failed after "
        f"{MAX_RETRIES} attempts: "
        f"{last_error}"

    )


# ============================================================
# STAGE 1 — PLANNING
# ============================================================

def planning_stage(

    client,

    subject,

    topic,

    level,

    language,

    difficulty,

    goals,

):

    prompt = PLANNING_PROMPT.format(

        subject=subject,

        topic=topic,

        level=level,

        language=language,

        difficulty=difficulty,

        goals=(
            goals
            if goals.strip()
            else "General understanding and exam preparation"
        ),

    )


    return call_ai(

        client,

        prompt,

        temperature=0.2,

    )


# ============================================================
# STAGE 2 — CONTENT GENERATION
# ============================================================

def content_stage(

    client,

    subject,

    topic,

    level,

    language,

    planning,

):

    planning_context = json.dumps(

        planning,

        ensure_ascii=False,

        indent=2,

    )


    prompt = CONTENT_PROMPT.format(

        subject=subject,

        topic=topic,

        level=level,

        language=language,

        planning=planning_context,

    )


    return call_ai(

        client,

        prompt,

        temperature=0.35,

    )


# ============================================================
# STAGE 3 — ASSESSMENT
# ============================================================

def assessment_stage(

    client,

    planning,

    content,

):

    planning_context = json.dumps(

        planning,

        ensure_ascii=False,

        indent=2,

    )


    content_context = json.dumps(

        content,

        ensure_ascii=False,

        indent=2,

    )


    prompt = ASSESSMENT_PROMPT.format(

        planning=planning_context,

        content=content_context,

    )


    return call_ai(

        client,

        prompt,

        temperature=0.3,

    )


# ============================================================
# STAGE 4 — REVIEW
# ============================================================

def review_stage(

    client,

    planning,

    content,

    assessment,

):

    prompt = REVIEW_PROMPT.format(

        planning=json.dumps(
            planning,
            ensure_ascii=False,
            indent=2,
        ),

        content=json.dumps(
            content,
            ensure_ascii=False,
            indent=2,
        ),

        assessment=json.dumps(
            assessment,
            ensure_ascii=False,
            indent=2,
        ),

    )


    return call_ai(

        client,

        prompt,

        temperature=0.15,

    )


# ============================================================
# STAGE 5 — REFINEMENT
# ============================================================

def refinement_stage(

    client,

    planning,

    content,

    assessment,

    review,

):

    prompt = REFINEMENT_PROMPT.format(

        planning=json.dumps(
            planning,
            ensure_ascii=False,
            indent=2,
        ),

        content=json.dumps(
            content,
            ensure_ascii=False,
            indent=2,
        ),

        assessment=json.dumps(
            assessment,
            ensure_ascii=False,
            indent=2,
        ),

        review=json.dumps(
            review,
            ensure_ascii=False,
            indent=2,
        ),

    )


    result = call_ai(

        client,

        prompt,

        temperature=0.2,

    )


    new_content = result.get(
        "content",
        content,
    )


    new_assessment = result.get(
        "assessment",
        assessment,
    )


    return (
        new_content,
        new_assessment,
    )


# ============================================================
# FINAL FORMATTER
# ============================================================

def format_final_pack(

    planning,

    content,

    assessment,

    review,

):

    output = []


    # --------------------------------------------------------
    # TITLE
    # --------------------------------------------------------

    title = content.get(

        "title",

        planning.get(
            "study_title",
            "AI Study Pack",
        ),

    )


    output.append(
        f"# 🎓 {title}"
    )

    output.append("")


    # --------------------------------------------------------
    # LEARNING OBJECTIVES
    # --------------------------------------------------------

    objectives = planning.get(
        "learning_objectives",
        [],
    )


    if objectives:

        output.append(
            "## 🎯 Learning Objectives"
        )


        for objective in objectives:

            output.append(
                f"- {objective}"
            )


        output.append("")


    # --------------------------------------------------------
    # INTRODUCTION
    # --------------------------------------------------------

    introduction = content.get(
        "introduction",
        "",
    )


    if introduction:

        output.append(
            "## 📚 Introduction"
        )

        output.append(
            introduction
        )

        output.append("")


    # --------------------------------------------------------
    # CONTENT SECTIONS
    # --------------------------------------------------------

    sections = content.get(
        "sections",
        [],
    )


    for section in sections:

        heading = section.get(
            "heading",
            "Topic",
        )


        explanation = section.get(
            "explanation",
            "",
        )


        output.append(
            f"## {heading}"
        )


        output.append(
            explanation
        )


        examples = section.get(
            "examples",
            [],
        )


        if examples:

            output.append(
                "**Examples:**"
            )


            for example in examples:

                output.append(
                    f"- {example}"
                )


        key_points = section.get(
            "key_points",
            [],
        )


        if key_points:

            output.append(
                "**Key Points:**"
            )


            for point in key_points:

                output.append(
                    f"- {point}"
                )


        output.append("")


    # --------------------------------------------------------
    # EXTRA STUDY SECTIONS
    # --------------------------------------------------------

    study_groups = [

        (
            "⚡ Quick Notes",
            "quick_notes",
        ),

        (
            "🧠 Memory Tips",
            "memory_tips",
        ),

        (
            "⚠️ Common Mistakes",
            "common_mistakes",
        ),

        (
            "📌 Formula / Fact Box",
            "formula_or_fact_box",
        ),

    ]


    for heading, key in study_groups:

        values = content.get(
            key,
            [],
        )


        if values:

            output.append(
                f"## {heading}"
            )


            for value in values:

                output.append(
                    f"- {value}"
                )


            output.append("")


    # --------------------------------------------------------
    # REVISION SUMMARY
    # --------------------------------------------------------

    summary = content.get(
        "revision_summary",
        "",
    )


    if summary:

        output.append(
            "## ⏱️ Revision Summary"
        )

        output.append(
            summary
        )

        output.append("")


    # --------------------------------------------------------
    # ASSESSMENT
    # --------------------------------------------------------

    output.append(
        "## 📝 Practice Assessment"
    )


    questions = assessment.get(
        "questions",
        [],
    )


    for question in questions:

        number = question.get(
            "number",
            "",
        )


        question_text = question.get(
            "question",
            "",
        )


        question_type = question.get(
            "type",
            "",
        )


        question_difficulty = question.get(
            "difficulty",
            "",
        )


        output.append(

            f"### {number}. "
            f"{question_text}"

        )


        output.append(

            f"*{question_type} | "
            f"{question_difficulty}*"

        )


        options = question.get(
            "options",
            [],
        )


        if options:

            for option in options:

                output.append(
                    f"- {option}"
                )


        answer = question.get(
            "answer",
            "",
        )


        explanation = question.get(
            "explanation",
            "",
        )


        output.append(
            f"**Answer:** {answer}"
        )


        output.append(
            f"**Explanation:** {explanation}"
        )


        output.append("")


    # --------------------------------------------------------
    # REVIEW
    # --------------------------------------------------------

    output.append(
        "## 🔎 Quality Review"
    )


    score = review.get(
        "score",
        "N/A",
    )


    approved = review.get(
        "approved",
        False,
    )


    output.append(
        f"**Review Score:** {score}/100"
    )


    output.append(

        f"**Approved:** "
        f"{'Yes' if approved else 'No'}"

    )


    return "\n".join(
        output
    )


# ============================================================
# COMPLETE MULTI-STAGE WORKFLOW
# ============================================================

def run_study_workflow(

    subject: str,

    topic: str,

    level: str,

    language: str,

    difficulty: str,

    goals: str,

):

    client = get_client()


    trace = {

        "workflow": [

            "Started"

        ],

        "model": DEFAULT_MODEL,

        "provider": "Groq",

        "refinement_count": 0,

    }


    # ========================================================
    # STAGE 1
    # ========================================================

    planning = planning_stage(

        client,

        subject,

        topic,

        level,

        language,

        difficulty,

        goals,

    )


    trace["workflow"].append(
        "Stage 1: Planning completed"
    )


    # ========================================================
    # STAGE 2
    # ========================================================

    content = content_stage(

        client,

        subject,

        topic,

        level,

        language,

        planning,

    )


    trace["workflow"].append(
        "Stage 2: Content generation completed"
    )


    # ========================================================
    # STAGE 3
    # ========================================================

    assessment = assessment_stage(

        client,

        planning,

        content,

    )


    trace["workflow"].append(
        "Stage 3: Assessment completed"
    )


    # ========================================================
    # STAGE 4
    # ========================================================

    review = review_stage(

        client,

        planning,

        content,

        assessment,

    )


    trace["workflow"].append(
        "Stage 4: Review completed"
    )


    # ========================================================
    # STAGE 5 — REFINEMENT LOOP
    # ========================================================

    refinement_count = 0


    while (

        not review.get(
            "approved",
            False,
        )

        and

        refinement_count < MAX_REFINEMENTS

    ):

        refinement_count += 1


        content, assessment = refinement_stage(

            client,

            planning,

            content,

            assessment,

            review,

        )


        trace["workflow"].append(

            f"Stage 5: Refinement "
            f"{refinement_count} completed"

        )


        # ----------------------------------------------------
        # RE-REVIEW
        # ----------------------------------------------------

        review = review_stage(

            client,

            planning,

            content,

            assessment,

        )


        trace["workflow"].append(

            f"Final Review "
            f"{refinement_count} completed"

        )


    # ========================================================
    # FINAL STUDY PACK
    # ========================================================

    final_pack = format_final_pack(

        planning,

        content,

        assessment,

        review,

    )


    trace["refinement_count"] = (
        refinement_count
    )


    trace["final_review"] = review


    return {

        "final_pack": final_pack,

        "trace": trace,

    }