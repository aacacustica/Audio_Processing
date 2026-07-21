import os
import wave
from pathlib import Path
from dataclasses import dataclass

GROUPS = {
    "G1" : ["S2.1_dia" , "S2.2_dia" , "S2.3_dia"],
    "G2" : ["S2.4_dia" , "S2.5_dia" , "S2.6_dia"],
    "G3" : ["S3.1_dia" , "S3.2_dia" , "S3.3_dia"],
    "G4" : ["S3.4_dia" , "S3.5_dia" , "S3.6_dia"],
    "G5" : ["S4.1_noche" , "S4.2_noche" , "S4.3_noche"],
    "G6" : ["S4.4_noche" , "S4.5_noche" , "S4.6_noche"]
    }

GROUPS_FOLDERS = {
    "S2.1_dia": "G1",
    "S2.2_dia": "G1",
    "S2.3_dia": "G1",
    "S2.4_dia": "G2",
    "S2.5_dia": "G2",
    "S2.6_dia": "G2",
    "S3.1_dia": "G3",
    "S3.2_dia": "G3",
    "S3.3_dia": "G3",
    "S3.4_dia": "G4",
    "S3.5_dia": "G4",
    "S3.6_dia": "G4",
    "S4.1_noche": "G5",
    "S4.2_noche": "G5",
    "S4.3_noche": "G5",
    "S4.4_noche": "G6",
    "S4.5_noche": "G6",
    "S4.6_noche": "G6"
}


MEDIDAS_CORTAS_MEDIDAS_PATH = r"\\192.168.205.115\aac_server\OCIO\26013_ETS_Salburua\02-07_Medidas_cortas\3-Medidas"
CARPETA_DE_SALIDA = r"\\192.168.205.115\aac_server\OCIO\26013_ETS_Salburua\Medidas juntadas"

@dataclass(frozen=True)
class WavInfo:
    path: Path
    channels: int
    sample_width: int
    frame_rate: int
    compression_type: str
    frames: int

    @property
    def duration_seconds(self) -> float:
        return self.frames / self.frame_rate

def read_wav_info(path: Path) -> WavInfo:
    try:
        with wave.open(str(path), "rb") as wav_file:
            return WavInfo(
                path=path,
                channels=wav_file.getnchannels(),
                sample_width=wav_file.getsampwidth(),
                frame_rate=wav_file.getframerate(),
                compression_type=wav_file.getcomptype(),
                frames=wav_file.getnframes(),
            )
    except (wave.Error, EOFError, OSError) as exc:
        raise RuntimeError(f"No se pudo leer {path}: {exc}") from exc
    
def concatenar_wavs(input_paths,output_path,overwrite,chunk_frames = 1_048_576):

    infos = [read_wav_info(path) for path in input_paths]
    print(f"infos:{infos}")
    print(f"input_paths:{input_paths}")
    output_path = Path(output_path)
    reference = infos[0]
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with wave.open(str(output_path),"wb") as output_wav:

        output_wav.setnchannels(reference.channels)
        output_wav.setsampwidth(reference.sample_width)
        output_wav.setframerate(reference.frame_rate)
        output_wav.setcomptype("NONE","not compressed")

        for input_path in input_paths:
            with wave.open(str(input_path),"rb") as input_wav:
                while True:
                    frames = input_wav.readframes(chunk_frames)
                    if not frames: break
                    output_wav.writeframesraw(frames)

    duracion_total = sum( info.duration_seconds for info in infos)
        
    
    print( f"Archivo creado correctamente: {output_path}\n" f"Duración aproximada: {duracion_total:.2f} segundos")
        
        
    
    
    

def main():

    medidas_folder_files = sorted(os.listdir(MEDIDAS_CORTAS_MEDIDAS_PATH))

    results = {
        "G1": [],
        "G2": [],
        "G3": [],
        "G4": [],
        "G5": [],
        "G6": []
    }

    for file in medidas_folder_files:
        for key in GROUPS_FOLDERS.keys():
            if os.path.basename(file) == key:
                full_filename = os.path.join(MEDIDAS_CORTAS_MEDIDAS_PATH,file,'AUDIOMOTH')
                print(f"full_filename:{full_filename}")
                for wavfilename in os.listdir(full_filename):
                    if wavfilename.endswith('.WAV'):
                        print(f"wavfilename:{wavfilename}")
                        wavfullpath = os.path.join(full_filename,wavfilename)
                        print(f"wavfullpath:{wavfullpath}")
                        results[GROUPS_FOLDERS[key]].append(wavfullpath)
    
    
    for key,wavs_paths in results.items():

        wavs_paths = sorted(wavs_paths)
        output_folder = (Path(CARPETA_DE_SALIDA) / key / "AUDIOMOTH")
        output_path = output_folder / f"{key}_unido.WAV"
        concatenar_wavs(wavs_paths,output_path,False)

    
if __name__ == "__main__":
    main()
        
