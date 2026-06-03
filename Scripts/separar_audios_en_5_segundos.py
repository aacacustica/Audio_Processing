import argparse
from pathlib import Path
import soundfile as sf
import tqdm


def arg_parser():
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "-f", "--folder",
        type=str,
        required=True,
        help="Carpeta donde están los .wav"
    )

    parser.add_argument(
        "-v", "--ventana",
        type=float,
        default=15,
        help="Duración de cada fragmento en minutos. Default: 15"
    )

    return parser.parse_args()


def format_time(seconds: float) -> str:
    """Convierte segundos a formato HHhMMmSSs."""
    seconds = int(seconds)
    h = seconds // 3600
    m = (seconds % 3600) // 60
    s = seconds % 60
    return f"{h:02d}h{m:02d}m{s:02d}s"


def split_audio(file_path: Path, output_folder: Path, ventana_minutos: float):
    with sf.SoundFile(file_path, mode="r") as audio:
        sr = audio.samplerate
        total_frames = len(audio)

        frames_por_fragmento = int(ventana_minutos * 60 * sr)

        fragment_idx = 0
        start_frame = 0

        while start_frame < total_frames:
            audio.seek(start_frame)

            data = audio.read(
                frames=frames_por_fragmento,
                dtype="float32",
                always_2d=False
            )

            if len(data) == 0:
                break

            end_frame = start_frame + len(data)

            start_seconds = start_frame / sr
            end_seconds = end_frame / sr

            start_label = format_time(start_seconds)
            end_label = format_time(end_seconds)

            output_name = (
                f"{file_path.stem}_"
                f"{start_label}-{end_label}"
                f"{file_path.suffix}"
            )

            output_path = output_folder / output_name

            sf.write(
                output_path,
                data,
                sr,
                subtype=audio.subtype
            )

            print(f"Guardado: {output_path.name}")

            fragment_idx += 1
            start_frame = end_frame


def main():
    args = arg_parser()

    audio_files_folder_path = Path(args.folder)
    ventana_separacion = args.ventana

    output_files_folder_path = audio_files_folder_path / "pistas_separadas"
    output_files_folder_path.mkdir(parents=True, exist_ok=True)

    for file_path in tqdm.tqdm(audio_files_folder_path.iterdir(),unit=file_path):
        if file_path.suffix.lower() == ".wav":
            print(f"\nProcesando: {file_path.name}")
            split_audio(
                file_path=file_path,
                output_folder=output_files_folder_path,
                ventana_minutos=ventana_separacion
            )


if __name__ == "__main__":
    main()