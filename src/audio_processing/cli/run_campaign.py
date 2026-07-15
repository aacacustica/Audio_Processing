import argparse

from audio_processing.campaign.config import load_config
from audio_processing.campaign.pipeline import CampaignPipeline


def parse_arguments():
    parser = argparse.ArgumentParser(description='Make prediction with YAMNet model for audio files in a directory')
    parser.add_argument('-c', '--config', type=str, required=True, help='Ruta al archivo YAML de campaña.')
    parser.add_argument('--run',action='store_true',help='Ejecuta procesos reales. Por defecto solo hace dry-run.')
    return parser.parse_args()

def main():
    args = parse_arguments()
    config = load_config(args.config)

    pipeline = CampaignPipeline(config = config, dry_run=not args.run)
    pipeline.run()

if __name__ == "__main__":
    main()