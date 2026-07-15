from audio_processing.campaign.discovery import discover_measurement_points
from audio_processing.common.logging import setup_logging

from pathlib import Path


class CampaignPipeline:

    
    def __init__(self, config, dry_run: bool = True):

        self.config = config
        self.dry_run = dry_run
        self.logger = None
    
    def run(self) -> None:

        sources = discover_measurement_points(self.config)
        
        print()
        print("#----------PLAN DE EJECUCIÓN----------#")
        print()

        if not sources: 
            print("No se han encontrado fuentes de medida")
            return

        for source in sources: self.print_plan(source)

        if self.dry_run: return

        self._setup_runtime()

        for source in sources: self.run_source(sources)

    def _setup_runtime(self) -> None:

        self.logger = setup_logging( 
            log_dir = Path(self.config.campaign.output_root)/self.config.outputs.subfolders.logs
            )
    
    def run_source(self,source) -> None:

        if self.config.execution.run_spl and source.needs_spl: self.run_spl(source)
        if self.config.execution.run_ai and source.needs_ai: self.run_ai(source)
        if self.config.execution.run_visualization and source.needs_visualization: self.run_visualization(source)

    def run_spl(self,source) -> None:
        from audio_processing.spl.leq_processor import run_leq_for_source

        output_path = run_leq_for_source(
            source = source,
            config = self.config,
            logger = self.logger
        )

        if output_path is None: self.logger.warning(f"SPL no generó salida para {source.source_id}")
        else: self.logger.info(f"SPL guardado en {output_path}")

    def run_ai(self,source) -> None:
        raise NotImplementedError(f"AI todavía no se ha migrado")
    def run_visualization(self,source) -> None:
        raise NotImplementedError(f"Visualization todavía no se ha migrado")
    
    
    def print_plan(self,point) -> None:
        
        self.print_source_plan(point)

        if self.config.execution.run_spl and point.needs_spl: self.print_spl_plan()
        if self.config.execution.run_ai and point.needs_ai: self.print_ai_plan()
        if self.config.execution.run_visualization and point.needs_visualization: self.print_visualization_plan

        if self.dry_run: return

        raise NotImplementedError("La ejecución real todavía no está migrada. Usa dry-run hasta implementar los servicios")    

    def print_source_plan(self,point):

        print(f"#----------Información del punto----------#")
        print()
        print(f"Punto:          {point.name}")
        print(f"Dispositivo:    {point.device_type}")
        print(f"Ruta entrada:   {point.raw_data_path}")
        print(f"Ruta salida:    {point.output_path}")
        print(f"")

    def print_spl_plan(self):

        print()
        print("#------------[SPL] Activo----------#")
        print(f"#----------Información SPL----------#")
        
        print(f"Archivo de calibración: {self.config.spl.calibration_file}")
        print(f"Filtro campaña: {self.config.spl.filter_campaign}")
        print(f"Filtro punto: {self.config.spl.filter_point}")
        print(f"Carpeta de salida: {self.config.spl.output_subfolder}")
        print()

    def print_ai_plan(self):

        print() 
        print("#------------[AI] Activo----------#")
        print(f"#----------Información IA----------#")
        
        print(f"Modelo: {self.config.ai.model}")
        print(f"Tamaño ventana: {self.config.ai.window_seconds}")
        print(f"Umbral: {self.config.ai.threshold}")
        print(f"Guardar embeddings: {self.config.ai.save_embeddings}")
        print(f"Guardar espectrograma: {self.config.ai.save_spectrograms}")
        print(f"Filtro punto: {self.config.ai.filter_point}")
        print()

    def print_visualization_plan(self):    

        print() 
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
        print()
