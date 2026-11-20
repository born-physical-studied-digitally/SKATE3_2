import json
import time
from pathlib import Path

from seismogram_pipeline.cli.get_all_metadata import analyze_image

# run.py always executes from /work at runtime — Felix confirmed input.json
# and input/ are staged as siblings of run.py, so this resolves correctly
# both in the container and in local testing.
WORK_DIR = Path(__file__).resolve().parent

def main():
    input_payload = json.loads((WORK_DIR / "input.json").read_text())

    image_filename = Path(input_payload["inputs"]["image"]["local_path"]).name
    image_path = WORK_DIR / "input" / image_filename

    params = input_payload.get("parameters", {})
    scale = params.get("scale", 0.25)

    out_dir = WORK_DIR / "output" / "artifacts"
    out_dir.mkdir(parents=True, exist_ok=True)

    start = time.time()
    try:
        analyze_image(str(image_path), str(out_dir), scale=scale)
        status = "success"
        error_message = ""
    except Exception as e:
        status = "failed"
        error_message = str(e)

    runtime_seconds = round(time.time() - start, 2)

    if status == "success":
        extracted_metadata = {}
        extracted_metadata = {}
        for key in ["roi", "meanlines", "intersections", "segments"]:
            path = out_dir / f"{key}.json"
            if path.exists():
                extracted_metadata[key] = json.loads(path.read_text())


        output = {
            "status": "success",
            "outputs": {
                "extracted_metadata": extracted_metadata,
                "cropped_regions": [
                    {"path": str(out_dir / "segment_regions.png")},
                    {"path": str(out_dir / "intersections_raster.png")},
                ],
            },
            "logs": "",
            "metrics": {"runtime_seconds": runtime_seconds},
        }
    else:
        output = {
            "status": "failed",
            "outputs": {},
            "logs": error_message,
            "metrics": {"runtime_seconds": runtime_seconds},
        }

    (out_dir.parent / "output.json").write_text(json.dumps(output, indent=2))

if __name__ == "__main__":
    main()