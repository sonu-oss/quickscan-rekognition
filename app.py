"""QuickScan Express Streamlit application using Amazon Rekognition labels."""

import io
import os
import time

import streamlit as st
from dotenv import load_dotenv
from PIL import Image, UnidentifiedImageError

from src.image_utils import draw_bounding_boxes
from src.rekognition_client import RekognitionError, detect_labels, flatten_instances
from src.report import build_instance_table, build_summary_table

load_dotenv()

st.set_page_config(page_title="QuickScan Express", page_icon="cart", layout="wide")

st.markdown(
    """
    <style>
        .block-container { max-width: 1440px; padding-top: 2rem; padding-bottom: 3rem; }
        [data-testid="stMetricValue"] { font-size: 1.6rem; }
        .stDataFrame { border-radius: 8px; overflow: hidden; }
    </style>
    """,
    unsafe_allow_html=True,
)

with st.sidebar:
    st.header("Scan settings")
    region = st.text_input(
        "AWS region",
        value=os.getenv("AWS_DEFAULT_REGION", "ap-south-1"),
        help="The AWS region in which Rekognition will process this scan.",
    )
    st.info("General-label detection is enabled at 20% confidence or higher.")
    st.divider()
    st.caption(
        "**Credentials:** loaded from environment variables, `.env`, or your "
        "local AWS profile. They are never stored in this application."
    )

st.title("QuickScan Express")
st.caption("Automated Visual Point-of-Sale and Object Scanner - powered by Amazon Rekognition")
st.markdown(
    "Upload a checkout image and QuickScan identifies visible objects, draws their "
    "locations, and reports confidence scores."
)
st.divider()

uploaded_file = st.file_uploader(
    "Upload a tray / checkout image",
    type=["jpg", "jpeg", "png"],
    help="JPG or PNG, up to 5 MB (Rekognition inline image limit).",
)

if uploaded_file is None:
    st.info("Upload an image to run a scan.")
    st.stop()

MAX_BYTES = 5 * 1024 * 1024
file_bytes = uploaded_file.getvalue()
if len(file_bytes) > MAX_BYTES:
    st.error(
        f"This image is {len(file_bytes) / (1024 * 1024):.1f} MB, above the "
        "5 MB limit for a scan. Please upload a smaller image."
    )
    st.stop()

try:
    original_image = Image.open(io.BytesIO(file_bytes)).convert("RGB")
except (UnidentifiedImageError, OSError):
    st.error("This file could not be read as a valid JPG or PNG image.")
    st.stop()

if not st.button("Run Scan", type="primary"):
    st.image(original_image, caption="Ready to scan", use_container_width=True)
    st.stop()

with st.spinner("Sending image to Amazon Rekognition..."):
    start = time.perf_counter()
    try:
        response = detect_labels(
            image_bytes=file_bytes,
            region_name=region.strip(),
            max_labels=1000,
            min_confidence=20.0,
        )
    except RekognitionError as err:
        st.error(str(err))
        st.stop()
    elapsed = time.perf_counter() - start

detections = flatten_instances(response)
annotated_image = draw_bounding_boxes(original_image, detections)
located_count = sum(detection["box"] is not None for detection in detections)
distinct_items = len({detection["label"] for detection in detections if detection["box"] is not None})

st.success(
    f"Scan complete in {elapsed:.2f}s - {located_count} item(s) located across "
    f"{distinct_items} distinct item type(s)."
)

image_column, table_column = st.columns([3, 2], gap="large")
with image_column:
    annotated_tab, original_tab = st.tabs(["Annotated", "Original"])
    with annotated_tab:
        st.image(annotated_image, use_container_width=True)
    with original_tab:
        st.image(original_image, use_container_width=True)

with table_column:
    st.subheader("Detected inventory")
    summary_df = build_summary_table(detections)
    st.dataframe(summary_df, use_container_width=True, hide_index=True)

    metric_1, metric_2, metric_3 = st.columns(3)
    metric_1.metric("Items located", located_count)
    metric_2.metric("Distinct types", distinct_items)
    average_confidence = summary_df["Avg. Confidence (%)"].mean() if not summary_df.empty else 0
    metric_3.metric("Avg. confidence", f"{average_confidence:.0f}%")

    st.download_button(
        "Export summary (CSV)",
        data=summary_df.to_csv(index=False).encode("utf-8"),
        file_name="quickscan_summary.csv",
        mime="text/csv",
    )

st.divider()
with st.expander("Detailed audit view (every detection instance)"):
    st.dataframe(build_instance_table(detections), use_container_width=True, hide_index=True)
with st.expander("Raw Rekognition JSON response"):
    st.json(response)
