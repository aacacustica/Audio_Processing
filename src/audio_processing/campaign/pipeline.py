from audio_processing.campaign.discovery import (
    discover_measurement_points,
)

class CampaignPipeline:
    def __init__(self, config, dry_run: bool = True):
        self.config = config
        self.dry_run = dry_run

    def run(self) -> None:
        points = discover_measurement_points(self.config)

        print()
        print("#----------PLAN DE EJECUCIÓN----------#")

        if not points:
            print("No se han encontrado puntos de medida.")
            return

        for point in points:
            self.run_point(point)

    def run_point(self, point) -> None:
        print()
        print(f"Punto:          {point.name}")
        print(f"Dispositivo:    {point.device_type}")
        print(f"Ruta entrada:   {point.raw_data_path}")
        print(f"Ruta salida:    {point.output_path}")
        print(f"")

        if self.config.execution.run_spl and point.needs_spl:
            print("#------------[SPL] Activo----------#")
            print(f"#----------Información SPL----------#")
            
            print(f"Archivo de calibración: {self.config.spl.calibration_file}")
            print(f"Filtro campaña: {self.config.spl.filter_campaign}")
            print(f"Filtro punto: {self.config.spl.filter_point}")
            print(f"Carpeta de salida: {self.config.spl.output_subfolder}")
            
        if self.config.execution.run_ai and point.needs_ai: 
            print("#------------[AI] Activo----------#")
            print(f"#----------Información IA----------#")
            
            print(f"Modelo: {self.config.ai.model}")
            print(f"Tamaño ventana: {self.config.ai.window_seconds}")
            print(f"Umbral: {self.config.ai.threshold}")
            print(f"Guardar embeddings: {self.config.ai.save_embeddings}")
            print(f"Guardar espectrograma: {self.config.ai.save_spectrograms}")
            print(f"Filtro punto: {self.config.ai.filter_point}")

        if ( self.config.execution.run_visualization and point.needs_visualization): 
            print("#------------[Visualization] Activo----------#")
            print(f"#----------Información Visualization----------#")
            
            print(f"Activo: {self.config.visualization.enabled}")
            print(f"Taxonomía: {self.config.visualization.taxonomy}")
            print(f"Segundos de agregación: {self.config.visualization.aggregation_seconds}")
            print(f"Percentiles: {self.config.visualization.percentiles}")
            print(f"OCA: {self.config.visualization.oca_type}")
            print(f"Número de segundos borrados al inicio del archivo: {self.config.visualization.remove_start_seconds}")
            print(f"Número de segundos borrados al final del archivo: {self.config.visualization.remove_end_seconds}")
            print(f"Zona horaria de tenerife: {self.config.visualization.tenerife_timezone}")

        if self.dry_run: return

        raise NotImplementedError("La ejecución real todavía no está migrada. Usa dry-run hasta implementar los servicios")    

        

