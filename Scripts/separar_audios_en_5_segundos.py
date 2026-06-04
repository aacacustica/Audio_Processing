import argparse
from pathlib import Path
from datetime import datetime, timedelta
import soundfile as sf


def arg_parser():
    parser = argparse.ArgumentParser()

    parser.add_argument("-f", "--folder", type=str, required=True)
    parser.add_argument(
        "-v", "--ventana",
        type=float,
        default=15,
        help="Duración de cada fragmento en minutos"
    )

    return parser.parse_args()


def split_audio(file_path: Path, output_folder: Path, ventana_minutos: float):
    
    start_datetime = datetime.strptime(file_path.stem, "%Y%m%d_%H%M%S")

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

            # Tiempo final real del fragmento
            end_seconds = end_frame / sr
            fragment_datetime = start_datetime + timedelta(seconds=end_seconds)

            output_name = fragment_datetime.strftime("%Y%m%d_%H%M%S") + file_path.suffix
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

    for file_path in audio_files_folder_path.iterdir():
        if file_path.suffix.lower() == ".wav":
            print(f"Procesando: {file_path.name}")
            split_audio(
                file_path=file_path,
                output_folder=output_files_folder_path,
                ventana_minutos=ventana_separacion
            )


if __name__ == "__main__":
    main()