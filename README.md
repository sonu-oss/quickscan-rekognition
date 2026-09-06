# QuickScan Express

Automated visual point-of-sale and object scanner powered by Amazon Rekognition.

Upload a photo of a checkout tray. QuickScan detects visible objects, draws their bounding boxes, and presents confidence-scored inventory tables—without barcodes.

## Features

- Sends images directly to Amazon Rekognition `DetectLabels`; no S3 bucket is required.
- Annotates detected objects with bounding boxes and labels.
- Shows item summary and detailed audit tables.
- Exports the scan summary to CSV.
- Keeps AWS credentials local through environment variables, an AWS profile, or an ignored `.env` file.

## Stack

- [Streamlit](https://streamlit.io/)
- Amazon Rekognition via `boto3`
- Pillow, pandas, and python-dotenv

## Prerequisites

- Python 3.10+
- An AWS account with credentials permitted to call `rekognition:DetectLabels`

Attach the minimal policy in [`iam-policy.json`](iam-policy.json) to the IAM user or role used by the app.

## Setup

```bash
git clone https://github.com/sonu-oss/quickscan-rekognition.git
cd quickscan-rekognition

python -m venv .venv
# Windows PowerShell
.\.venv\Scripts\Activate.ps1
# macOS/Linux: source .venv/bin/activate

pip install -r requirements.txt
```

### Configure AWS credentials

Preferred: configure a local AWS CLI profile:

```bash
aws configure
```

Or use a local `.env` file:

```bash
cp .env.example .env
```

Fill the credential values in `.env`. It is ignored by Git; never commit real credentials.

## Run

```bash
streamlit run app.py
```

Open the local URL printed by Streamlit, upload a JPG or PNG up to 5 MB, then select **Run Scan**.

## Project layout

```text
app.py                       Streamlit UI and orchestration
src/rekognition_client.py    Rekognition client and response parsing
src/image_utils.py           Bounding-box rendering
src/report.py                Summary and detail tables
iam-policy.json              Minimal IAM policy
.env.example                 Safe configuration template
```

## Security

The app does not store credentials. `.env`, Streamlit secrets, virtual environments, and common credential file formats are excluded through `.gitignore`.

## License

No license has been selected yet. Add one before distributing or accepting external contributions.
