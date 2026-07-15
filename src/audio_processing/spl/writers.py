from pathlib import Path
import pandas as pd


def write_leq_csv(
        rows: list[list],
        columns: list[str],
        output_path:str | Path) -> Path:
    
    output_path = Path(output_path)
    output_path.parent.mkdir(parents = True, exist_ok = True)

    df = pd.DataFrame(rows, columns=columns)

    if 'date' in df.columns: df = df.sort_values(by='date')
    df.to_csv(output_path,index=False)

    return output_path