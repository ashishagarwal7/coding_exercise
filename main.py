from fastapi import FastAPI, Query
from fastapi.responses import JSONResponse
from typing import Optional
import pandas as pd
from datetime import datetime
import numpy as np
import uvicorn

#loading the data from a CSV.
try:
    raw_df = pd.read_csv("example_data.csv", parse_dates=["timestamp"])
    raw_df.set_index("timestamp", inplace=True)
except Exception as e:
    # Not the best error handling, but it'll do for now
    print(f"Failed to load dataset: {e}")
    raw_df = pd.DataFrame()

app = FastAPI()

@app.get("/signals")
def list_signals():
    
    #Return all available signals that start with 'signal-'.
    signal_cols = [col for col in raw_df.columns if col.startswith("signal-")]
    return {"signals": signal_cols}


@app.get("/signals/{signal_name}")
def get_signal_data(
    signal_name: str,
    start: Optional[str] = None,
    end: Optional[str] = None,
    interval: Optional[str] = None
):
    
    #Get the values for a specific signal. Can filter by start/end and resample by interval.
    # Let's make sure we have the signal before doing anything else
    if signal_name not in raw_df.columns:
        return JSONResponse(
            status_code=400,
            content={"error": f"Signal '{signal_name}' not found."}
        )

    # Will work on a copy just in case we mess with it
    data = raw_df.copy()

    # Apply filters if provided - might want to validate datetime formats better
    if start:
        try:
            start_time = pd.to_datetime(start)
            data = data[data.index >= start_time]
        except:
            # Should really be more specific here
            return JSONResponse(status_code=400, content={"error": "Invalid start datetime format."})

    if end:
        try:
            end_time = pd.to_datetime(end)
            data = data[data.index <= end_time]
        except:
            return JSONResponse(status_code=400, content={"error": "Invalid end datetime format."})

    # Resample if interval is passed - this assumes a proper pandas frequency string
    if interval:
        try:
            data = data.resample(interval).mean()
        except Exception as e:
            return JSONResponse(status_code=400, content={"error": f"Resampling failed: {e}"})

    # Final structure: return a list of time-value dictionaries
    results = []
    for ts, val in zip(data.index, data[signal_name]):
        entry = {
            "timestamp": ts.strftime("%d-%m-%Y %H:%M"),
            "value": round(val, 8) if pd.notna(val) else None
        }
        results.append(entry)

    return results
