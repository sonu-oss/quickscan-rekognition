"""
src/report.py

Turns the flat list of detections into a clean pandas DataFrame for
display and CSV export - the "summary table" the pitch deck describes.
"""

import pandas as pd


def build_summary_table(detections: list[dict]) -> pd.DataFrame:
    """
    Groups detections by label and produces one row per distinct item,
    e.g.:

        Item        Count   Avg. Confidence   Has Location
        Apple       3       96.4%             Yes
        Banana      1       91.2%             Yes
        Fruit Stand 1       98.1%             No (scene label)

    "Has Location" tells the cashier/evaluator whether this label came with
    a bounding box (an actual physical item) or is a whole-scene description.
    """
    if not detections:
        return pd.DataFrame(columns=["Item", "Count", "Avg. Confidence (%)", "Has Location"])

    df = pd.DataFrame(detections)
    df["has_box"] = df["box"].notna()

    grouped = (
        df.groupby("label")
        .agg(
            count=("label", "size"),
            avg_confidence=("confidence", "mean"),
            has_box=("has_box", "any"),
        )
        .reset_index()
        .rename(columns={
            "label": "Item",
            "count": "Count",
            "avg_confidence": "Avg. Confidence (%)",
            "has_box": "Has Location",
        })
    )

    grouped["Avg. Confidence (%)"] = grouped["Avg. Confidence (%)"].round(1)
    grouped["Has Location"] = grouped["Has Location"].map({True: "Yes", False: "No (scene label)"})
    grouped = grouped.sort_values("Avg. Confidence (%)", ascending=False).reset_index(drop=True)

    return grouped


def build_instance_table(detections: list[dict]) -> pd.DataFrame:
    """
    A more granular table - one row per individually-boxed instance
    (e.g. 3 separate rows for 3 apples), useful for a detailed audit view.
    """
    rows = [
        {
            "Item": d["label"],
            "Confidence (%)": d["confidence"],
            "Category": ", ".join(d["parents"]) if d["parents"] else "—",
            "Located": "Yes" if d["box"] else "No",
        }
        for d in detections
    ]
    df = pd.DataFrame(rows)
    if not df.empty:
        df = df.sort_values("Confidence (%)", ascending=False).reset_index(drop=True)
    return df
