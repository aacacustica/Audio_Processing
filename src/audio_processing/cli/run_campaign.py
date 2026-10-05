import argparse

from audio_processing.campaign.config import load_config
from audio_processing.campaign.pipeline import CampaignPipeline


def parse_arguments():
    parser = argparse.ArgumentParser(description='Ejecuta o simula una campaña acústica desde un YAML')
    parser.add_argument('-c', '--config', type=str, required=True, help='Ruta al archivo YAML de campaña.')
    parser.add_argument('--run',action='store_true',help='Ejecuta procesos. Por defecto solo imprime el plan de ejecución.')
    parser.add_argument('--profile',type=str,default=None,help="Perfil de ejecución. Sobreescribe exection.profile del YAML")
    
    return parser.parse_args()

def main():
    args = parse_arguments()

    if args.config: config = args.config
    else: raise ValueError(f"El argumento de ruta al archivo YAML de campaña es obligatorio.")

    if args.profile: profile = args.profile
    else: raise ValueError(f"El argumento de perfil de ejecución es obligatorio.")

    config = load_config(config,profile)

    pipeline = CampaignPipeline(config = config, dry_run=not args.run)
    pipeline.run()

if __name__ == "__main__":
    main()