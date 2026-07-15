import argparse

from audio_processing.campaign.config import load_config



def parse_arguments():
    parser = argparse.ArgumentParser(description='Make prediction with YAMNet model for audio files in a directory')
    parser.add_argument('-c', '--config', type=str, required=True, help='Directory with the campaign config')

    return parser.parse_args()

def main():
    args = parse_arguments()
    config = load_config(args.config)
    points = [point for point in config.points if point != "example"]

    print(f"#----------Información de campaña----------#")
    print(f"Campaña: {config.campaign.name}")
    print(f"Campaña-medidas: {config.campaign.input_root}")
    print(f"Campaña-resultados: {config.campaign.output_root}")

    print(f"#----------Información de ejecución----------#")
    print(f"SPL: {config.execution.run_spl}")
    print(f"AI: {config.execution.run_ai}")
    print(f"Visualizations: {config.execution.run_visualization}")
    print(f"Parada con error: {config.execution.stop_on_error}")

    print(f"#----------Información por dispositivo----------#")
    print(f"AUDIOMOTH activo: {config.devices.audiomoth.enabled}")
    print(f"SONOMETER activo: {config.devices.sonometer.enabled}")
    if config.devices.audiomoth.enabled:
        print(f"[AUDIOMOTH] Carpeta: {config.devices.audiomoth.folder_name}")
        print(f"[AUDIOMOTH] SPL: {config.devices.audiomoth.needs_spl}")
        print(f"[AUDIOMOTH] AI: {config.devices.audiomoth.needs_ai}")
        print(f"[AUDIOMOTH] Visualizations: {config.devices.audiomoth.visualizations}")
    if config.devices.sonometer.enabled:
        print(f"[SONOMETER] Carpeta: {config.devices.sonometer.folder_name}")
        print(f"[SONOMETER] SPL: {config.devices.sonometer.needs_spl}")
        print(f"[SONOMETER] AI: {config.devices.sonometer.needs_ai}")
        print(f"[SONOMETER] Visualizations: {config.devices.sonometer.visualize}")

    print(f"#----------Información SPL----------#")
    print(f"Activo: {config.spl.enabled}")
    print(f"Archivo de calibración: {config.spl.calibration_file}")
    print(f"Filtro campaña: {config.spl.filter_campaign}")
    print(f"Filtro punto: {config.spl.filter_point}")
    print(f"Carpeta de salida: {config.spl.output_subfolder}")

    print(f"#----------Información IA----------#")
    print(f"Activo {config.ai.enabled}")
    print(f"Modelo: {config.ai.model}")
    print(f"Tamaño ventana: {config.ai.window_seconds}")
    print(f"Umbral: {config.ai.threshold}")
    print(f"Guardar embeddings: {config.ai.save_embeddings}")
    print(f"Guardar espectrograma: {config.ai.save_spectrogram}")
    print(f"Filtro punto: {config.ai.filter_point}")

    print(f"#----------Información Visualization----------#")
    print(f"Activo: {config.visualization.enabled}")
    print(f"Taxonomía: {config.visualization.taxonomy}")
    print(f"Segundos de agregación: {config.visualization.aggregation_seconds}")
    print(f"Percentiles: {config.visualization.percentiles}")
    print(f"OCA: {config.visualizaiton.oca_type}")
    print(f"Número de segundos borrados al inicio del archivo: {config.visualization.remove_start_seconds}")
    print(f"Número de segundos borrados al final del archivo: {config.visualization.remove_end_seconds}")
    print(f"Zona horaria de tenerife: {config.visualizations.tenerife_timezone}")

    print(f"#----------Información de cada punto----------#")

    for point in points:
        print(f"Punto de medida: {point}")
        print(f"Corrección Decibelios: {point.correction_db}")
        print(f"Nueva fecha: {point.new_date}")
        print(f"Nuevo tiempo: {point.new_time}")
        print(f"Umbral fecha: {point.threshold_date}")
        print(f"Umbral tiempo: {point.threshold_time}")


    
