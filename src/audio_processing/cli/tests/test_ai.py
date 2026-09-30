from pathlib import Path

from audio_processing.ai.ai_model import AudioClassifier
from audio_processing.ai.processor import run_ai_for_file
from audio_processing.campaign.config import load_config


def main():

    config = load_config()
    audio_file = Path("/home/martin/Campañas de test/ACLIMA/C1/3-Medidas/P3 - test/AUDIOMOTH/20251204_111321.wav")
    classifier = AudioClassifier()

    results = run_ai_for_file(
        audio_file=audio_file,
        classifier=classifier,
        config=config
    )

    print(f"Predicciones: {len(results)}")
    
    timestamps = sorted({result.timestamp for result in results})

    print(f"Ventanas con predicción: {len(timestamps)}")

    for result in results[:10]: print(result)


    
if __name__ == "__main__":
    main()