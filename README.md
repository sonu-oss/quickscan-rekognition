# QuickScan Express

**Automated Visual Point-of-Sale & Object Scanner, powered by Amazon Rekognition.**

Upload a photo of a checkout tray, and QuickScan Express detects every item,
draws a bounding box around each one, and lists it in a table with a
confidence score — no barcode needed.

---

## 1. Problem it solves

- Traditional checkout requires scanning individual barcodes → queues and
  bottlenecks.
- Un-barcoded items (loose fruit, pastries, bulk goods) rely on manual
  visual inspection by staff, which is slow and error-prone.

## 2. How it works

```
User uploads          boto3 sends           Rekognition returns          Pillow draws          Streamlit shows
tray photo      ──►    image bytes    ──►    labels + bounding    ──►    boxes on the    ──►    annotated image +
(Streamlit)             (in-memory,           box coordinates            image                   summary table
                         no S3 needed)         (as % of image)
```

1. **Image ingestion** — user uploads an image through the Streamlit UI.
2. **AWS API integration** — the raw image bytes are sent straight to
   Amazon Rekognition's `detect_labels` API via `boto3` (no S3 upload step —
   Rekognition accepts inline bytes up to 5MB, which keeps this demo simple).
3. **Bounding box extraction** — Rekognition returns a JSON payload with
   label names, confidence scores, and (for physical objects) bounding box
   geometry as *ratios* of image width/height: `Left`, `Top`, `Width`, `Height`.
4. **Visual rendering** — the app converts those ratios into pixel
   coordinates for the specific uploaded image and draws boxes + captions
   with Pillow.
5. **Output display** — side-by-side original vs. annotated image, plus a
   Pandas-powered summary table (item, count, average confidence, whether
   it has a physical location) and a CSV export button.

## 3. Tech stack

| Layer | Technology |
|---|---|
| Frontend / UI | Streamlit |
| Computer vision | Amazon Rekognition (`detect_labels`) |
| AWS SDK | boto3 |
| Image annotation | Pillow (PIL) |
| Data / reporting | pandas |
| Config | python-dotenv |

## 4. Project structure

```
quickscan-express/
├── app.py                     # Streamlit UI + orchestration
├── src/
│   ├── rekognition_client.py  # boto3 wrapper: calls DetectLabels, parses response
│   ├── image_utils.py         # Draws bounding boxes with Pillow
│   └── report.py              # Builds pandas summary/detail tables
├── requirements.txt
├── .env.example                # Template for local AWS credentials
├── iam-policy.json             # Minimal IAM permissions needed
└── README.md
```

---

## 5. Setup

### Prerequisites

```bash
# Python 3.10+
python3 --version

# AWS CLI (used to configure credentials)
# macOS:
brew install awscli
# Windows/Linux: https://docs.aws.amazon.com/cli/latest/userguide/getting-started-install.html
```

You need an AWS account. Create an IAM user (or use an existing one) with
**only** the permission this app needs — see `iam-policy.json`:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "QuickScanRekognitionAccess",
      "Effect": "Allow",
      "Action": ["rekognition:DetectLabels"],
      "Resource": "*"
    }
  ]
}
```

In the AWS Console: **IAM → Users → your user → Add permissions → Attach
policies directly → Create policy → paste the JSON above.**

### Configure credentials (choose one)

**Option A — recommended: AWS CLI shared credentials**
```bash
aws configure
# Enter your Access Key ID, Secret Access Key, region (e.g. us-east-1), output format (json)
```
boto3 finds these automatically — no code or config file needed.

**Option B — quick local demo: `.env` file**
```bash
cp .env.example .env
# then edit .env and fill in:
#   AWS_ACCESS_KEY_ID=...
#   AWS_SECRET_ACCESS_KEY=...
#   AWS_DEFAULT_REGION=us-east-1
```
`.env` is already in `.gitignore` — never commit real credentials.

### Install and run

```bash
python3 -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate

pip install -r requirements.txt

streamlit run app.py
```

Streamlit will open `http://localhost:8501` in your browser.

---

## 6. Using the app

1. Upload a JPG/PNG of a tray or checkout surface (up to 5MB).
2. Optionally adjust the confidence threshold or max label count in the
   sidebar.
3. Click **Run Scan**.
4. Review the annotated image (bounding boxes + labels), the summary table,
   and the metrics (items located, distinct types, average confidence).
5. Export the summary as CSV, or expand the detailed audit view / raw JSON
   for a full inspection.

---

## 7. Pitch notes for evaluators

- **Key innovation:** real-time, multi-object detection with zero local
  GPU/ML infrastructure — all inference runs on AWS's managed Rekognition
  service, called through a simple `boto3` API request.
- **No barcode dependency:** works on loose/unbarcoded goods (produce,
  bakery items) where traditional POS scanning fails.
- **Auditability:** every detection includes a confidence score and, where
  available, exact spatial coordinates — useful for staff verification and
  building a defensible audit trail.
- **Scalability path:** the current build uses Rekognition's general
  `detect_labels` API (recognizes broad categories like "Apple" or
  "Fruit"). The natural next step is **Amazon Rekognition Custom
  Labels**, trained on your own product photos, to distinguish specific
  SKUs — e.g. a Gala Apple vs. a Fuji Apple, or your store's specific
  pastry line — which would let this evolve from an object scanner into a
  true visual point-of-sale system with per-item pricing lookups.

## 8. Cost notes

Amazon Rekognition's Free Tier includes 5,000 images/month for label
detection during your first 12 months; beyond that it's a small per-image
charge (check current pricing on the AWS Rekognition pricing page). This
app makes exactly one Rekognition call per scan, so cost scales linearly
and predictably with usage.

## 9. Troubleshooting

| Problem | Likely cause |
|---|---|
| "AWS credentials not found" | Run `aws configure`, or fill in `.env` and restart Streamlit. |
| "AWS rejected these credentials or permissions" | Your IAM user/role is missing the `rekognition:DetectLabels` permission — attach `iam-policy.json`. |
| Boxes look mis-positioned | Make sure you're viewing the **Annotated** tab, not the Original — boxes are only drawn on the annotated copy. |
| "Image too large" error | Rekognition's inline-bytes limit is 5MB; resize/compress the photo before uploading. |
