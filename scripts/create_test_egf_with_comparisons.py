#!/usr/bin/env python3
"""Create synthetic EGF files with comparisons for testing."""

import random
import sys
from datetime import datetime
from pathlib import Path

from egf import EGF
from edf import EDF


def create_egf_with_comparisons(
    edf_path: Path,
    output_path: Path,
    accuracy: float = 0.8,
    seed: int = 42,
    description: str = "Test grading with comparisons",
):
    """Create a synthetic EGF with comparisons at the specified accuracy."""
    # Load EDF to get submissions
    with EDF.open(edf_path) as edf:
        submissions = list(edf.submissions)
        print(f"Loaded {len(submissions)} submissions from EDF")

    # Create EGF referencing the EDF
    egf = EGF.reference_edf(str(edf_path), description)

    timestamp = int(datetime.now().timestamp() * 1000)
    random.seed(seed)

    # Add grades for all submissions
    for i, sub in enumerate(submissions):
        call_id = f"grade_call_{i:03d}"

        # Add LLM call for grading
        egf.add_llm_call(
            call_id=call_id,
            timestamp=timestamp + i * 1000,
            model="claude-sonnet-4-20250514",
            temperature=0.0,
            max_tokens=4096,
            messages=[
                {"role": "user", "content": f"Grade this submission: {sub.id}..."}
            ],
            output_content=f"Grade: {sub.grade}\n\nJustification: The submission demonstrates...",
            stop_reason="end_turn",
            input_tokens=2000,
            output_tokens=500,
            latency_ms=2500,
        )

        # Add grade result - use GT grade with some noise
        noise = random.randint(-1, 1)
        predicted_grade = max(0, min(10, sub.grade + noise))

        # Create a proper distribution that sums to 1.0
        dist = [0.0] * 11
        dist[predicted_grade] = 0.7
        if predicted_grade > 0:
            dist[predicted_grade - 1] = 0.15
        else:
            dist[predicted_grade] += 0.15
        if predicted_grade < 10:
            dist[predicted_grade + 1] = 0.15
        else:
            dist[predicted_grade] += 0.15

        egf.add_grade_result(
            submission_id=sub.id,
            grade=predicted_grade,
            grade_distribution=dist,
            call_ids=[call_id],
            graded_at=timestamp + i * 1000 + 500,
        )

    # Add comparisons between pairs of submissions
    comparison_count = 0
    for i in range(len(submissions)):
        for j in range(i + 1, min(i + 3, len(submissions))):  # Compare each with next 2
            sub_a = submissions[i]
            sub_b = submissions[j]

            comp_call_id = f"comp_call_{comparison_count:03d}"
            comp_id = f"comp_{comparison_count:03d}"

            # Determine winner based on GT grades
            gt_diff = sub_a.grade - sub_b.grade
            if gt_diff > 0:
                correct_winner = "a"
            elif gt_diff < 0:
                correct_winner = "b"
            else:
                correct_winner = random.choice(["a", "b"])

            # Use specified accuracy
            if random.random() < accuracy:
                winner = correct_winner
            else:
                winner = "b" if correct_winner == "a" else "a"

            # Add LLM call for comparison
            egf.add_llm_call(
                call_id=comp_call_id,
                timestamp=timestamp + 100000 + comparison_count * 1000,
                model="claude-sonnet-4-20250514",
                temperature=0.0,
                max_tokens=4096,
                messages=[
                    {
                        "role": "user",
                        "content": f"Compare submissions {sub_a.id} and {sub_b.id}...",
                    }
                ],
                output_content=f"Winner: {winner.upper()}\n\nSubmission {winner.upper()} demonstrates stronger understanding...",
                stop_reason="end_turn",
                input_tokens=4000,
                output_tokens=800,
                latency_ms=4000,
            )

            # Add comparison
            egf.add_comparison(
                comparison_id=comp_id,
                submission_a=sub_a.id,
                submission_b=sub_b.id,
                winner=winner,
                call_ids=[comp_call_id],
                compared_at=timestamp + 100000 + comparison_count * 1000 + 500,
                confidence=random.uniform(0.6, 0.95),
                justification=f"Submission {winner.upper()} shows better analysis and clearer argumentation.",
            )

            comparison_count += 1

    # Add a few external anchor comparisons (to test exclusion from accuracy)
    for i in range(3):
        sub = submissions[i]
        comp_call_id = f"ext_comp_call_{i:03d}"
        comp_id = f"ext_comp_{i:03d}"

        egf.add_llm_call(
            call_id=comp_call_id,
            timestamp=timestamp + 200000 + i * 1000,
            model="claude-sonnet-4-20250514",
            temperature=0.0,
            max_tokens=4096,
            messages=[
                {
                    "role": "user",
                    "content": f"Compare {sub.id} against exemplar anchor...",
                }
            ],
            output_content="Winner: A\n\nThe submission exceeds the anchor quality...",
            stop_reason="end_turn",
            input_tokens=4000,
            output_tokens=600,
            latency_ms=3500,
        )

        egf.add_comparison(
            comparison_id=comp_id,
            submission_a=sub.id,
            submission_b="external_anchor_exemplar",  # External - not in EDF
            winner="a",
            call_ids=[comp_call_id],
            compared_at=timestamp + 200000 + i * 1000 + 500,
            confidence=0.85,
            justification="Submission exceeds the anchor quality in argumentation.",
        )

    # Save EGF
    egf.save(str(output_path))
    print(f"Created EGF with {len(submissions)} grades and {comparison_count + 3} comparisons")
    print(f"  - {comparison_count} EDF-to-EDF comparisons")
    print(f"  - 3 external anchor comparisons")
    print(f"  - Target accuracy: {accuracy:.0%}")
    print(f"Saved to: {output_path}")


def main():
    edf_path = Path("d/nathan_low_quality_sec_a.edf")

    # Create first EGF with 80% comparison accuracy
    create_egf_with_comparisons(
        edf_path=edf_path,
        output_path=Path("d/comparisons_80pct.egf"),
        accuracy=0.8,
        seed=42,
        description="Grading with 80% comparison accuracy",
    )

    print()

    # Create second EGF with 65% comparison accuracy
    create_egf_with_comparisons(
        edf_path=edf_path,
        output_path=Path("d/comparisons_65pct.egf"),
        accuracy=0.65,
        seed=123,
        description="Grading with 65% comparison accuracy",
    )


if __name__ == "__main__":
    main()
