import argparse

from audio_processing.campaign.config import load_config
from audio_processing.campaign.pipeline import CampaignPipeline


def parse_arguments():
    parser = argparse.ArgumentParser(description='Ejecuta o simula una campaña acústica desde un YAML')
    parser.add_argument('-c', '--config', type=str, required=True, help='Ruta al archivo YAML de campaña.')
    parser.add_argument('--run',action='store_true',help='Ejecuta procesos. Por defecto solo imprime el plan de ejecución.')
    
    return parser.parse_args()

def main():
    args = parse_arguments()
    config = load_config(args.config)

    pipeline = CampaignPipeline(config = config, dry_run=not args.run)
    pipeline.run()

if __name__ == "__main__":
    main()