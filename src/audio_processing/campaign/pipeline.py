from audio_processing.campaign.discovery import discover_measurement_points
from audio_processing.common.logging import setup_logging

from audio_processing.persistence.database import Database
from audio_processing.persistence.repositories import ContextRepository,FileRepository,MeasurementRepository
from audio_processing.spl.leq_processor import run_leq_for_file,run_leq_for_source
from audio_processing.spl.utils_acoustics import get_audiofiles,read_calibration_constants,timestamp_from_filename

from pathlib import Path
from zoneinfo import ZoneInfo

import soundfile as sf

class CampaignPipeline:

    
    def __init__(self, config, dry_run: bool = True):

        self.config = config
        self.dry_run = dry_run
        self.logger = None
        self.db: Database | None = None
    
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

        for source in sources: self.run_source(source)

    def _setup_runtime(self) -> None:

        self.logger = setup_logging( log_dir = Path(self.config.campaign.output_root)/self.config.outputs.subfolders.logs )
        if self.config.database.enabled: self.db = Database.from_config(self.config)
                       
    
    def run_source(self,source) -> None:

        if self.config.execution.run_spl and source.needs_spl: self.run_spl_database(source)
        if self.config.execution.run_ai and source.needs_ai: self.run_ai(source)
        if self.config.execution.run_visualization and source.needs_visualization: self.run_visualization(source)

    def run_spl(self,source) -> None:

        output_path = run_leq_for_source(
            source = source,
            config = self.config,
            logger = self.logger
        )

        if output_path is None: self.logger.warning(f"SPL no generó salida para {source.source_id}.")
        else: self.logger.info(f"SPL guardado en {output_path}.")

    def run_spl_database(self,source) -> None:

        if self.db is None: raise RuntimeError(f"La base de datos debe estar habilitada para persistir los resultados SPL.")

        audio_files =  get_audiofiles(Path(source.raw_data_path))

        if not audio_files: 
            self.logger.warning(f"No hay archivos WAV en {source.raw_data_path}")
            return

        with self.db.session() as session:

            context_repository = ContextRepository(session)

            context = context_repository.get_for_source(
                campaign_name       = self.config.campaign.name,
                point_name          = source.name,
                device_type         = source.device_type
            )

            context_id = context.id_contexto

            self.logger.info(f"Contexto {context_id} para {source.source_id}")

            calibration_file  = Path(self.config.spl.calibration_file)

            if not calibration_file.is_absolute(): calibration_file = Path(self.config._config_dir) / calibration_file

            calibration_constants = read_calibration_constants(calibration_file)

            for audio_file in audio_files:

                try:

                    info = sf.info(audio_file)
                    timestamp = timestamp_from_filename(audio_file)

                    if timestamp.tzinfo is None: timestamp = timestamp.replace(tzinfo=ZoneInfo(self.config.campaign.timezone))

                    duration_seconds = info.frames / info.samplerate

                    results =  run_leq_for_file(
                        audio_file              = audio_file,
                        calibration_constants   = calibration_constants,
                        config                  = self.config,
                        logger                  = self.logger
                    )

                    with self.db.session() as sessio:

                        file_repository = FileRepository(session)
                        measurement_repository = MeasurementRepository(session)
                        
                        source_file = file_repository.register(
                            context_id          = context_id,
                            filename            = audio_file.name,
                            datetime_inicio     = timestamp,
                            duracion_seconds    = duration_seconds,
                            sample_rate_hz      = info.samplerate
                        )

                        measurements = measurement_repository.replace_for_file(
                            context_id  = context_id,
                            file_id     = source_file.id_archivo,
                            results     = results
                        )

                        self.logger.info(
                                "SPL %s: archivo=%s, "
                                "id_archivo=%s, mediciones=%s",
                                source.source_id,
                                audio_file.name,
                                source_file.id_archivo,
                                len(measurements),
                            )

                except Exception as e:

                    self.logger.exception(f"Error procesando {audio_file}")
                    if self.config.execution.stop_on_error: raise




        
    def run_ai(self,source) -> None:
        from audio_processing.ai.processor import run_ai_for_source

        output_path = run_ai_for_source(
            source = source,
            config = self.config,
            logger = self.logger,
        )

        if output_path is None: self.logger.warning(f"AI no generó salida para {source.source_id}.")
        else: self.logger.info(f"AI guardado en {output_path}")

    def run_visualization(self,source) -> None:
        raise NotImplementedError(f"Visualization todavía no se ha migrado")
    
    
    def print_plan(self,point) -> None:
        
        self.print_source_plan(point)

        if self.config.execution.run_spl and point.needs_spl: self.print_spl_plan()
        if self.config.execution.run_ai and point.needs_ai: self.print_ai_plan()
        if self.config.execution.run_visualization and point.needs_visualization: self.print_visualization_plan()

        if self.dry_run: return

    def print_source_plan(self,point):

        print(f"#----------Información del punto----------#")
        print()
        print(f"Punto:          {point.name}")
        print(f"ID:             {point.source_id}")
        print(f"Dispositivo:    {point.device_type}")
        print(f"Ruta entrada:   {point.raw_data_path}")
        print(f"Ruta salida:    {point.output_path}")
        print(f"")

    def print_spl_plan(self):

        print()
        print("#------------[SPL] Funcionando----------#")
        print(f"#----------Información SPL----------#")
        
        print(f"Archivo de calibración:     {self.config.spl.calibration_file}")
        print(f"Filtro campaña:             {self.config.spl.filter_campaign}")
        print(f"Filtro punto:               {self.config.spl.filter_point}")
        print(f"Carpeta de salida:          {self.config.spl.output_subfolder}")
        print()

    def print_ai_plan(self):

        print() 
        print("#------------[AI] Funcionando----------#")
        print(f"#----------Información IA----------#")
        
        print(f"Modelo:                     {self.config.ai.model}")
        print(f"Tamaño ventana:             {self.config.ai.window_seconds}")
        print(f"Umbral:                     {self.config.ai.threshold}")
        print(f"Guardar embeddings:         {self.config.ai.save_embeddings}")
        print(f"Guardar espectrograma:      {self.config.ai.save_spectrograms}")
        print(f"Filtro punto:               {self.config.ai.filter_point}")
        print()

    def print_visualization_plan(self):    

        print() 
        print("#------------[Visualization] Funcionando----------#")
        print(f"#----------Información Visualization----------#")
        
        print(f"Activo:                                             {self.config.visualization.enabled}")
        print(f"Taxonomía:                                          {self.config.visualization.taxonomy}")
        print(f"Segundos de agregación:                             {self.config.visualization.aggregation_seconds}")
        print(f"Percentiles:                                        {self.config.visualization.percentiles}")
        print(f"OCA:                                                {self.config.visualization.oca_type}")
        print(f"Número de segundos borrados al inicio del archivo:  {self.config.visualization.remove_start_seconds}")
        print(f"Número de segundos borrados al final del archivo:   {self.config.visualization.remove_end_seconds}")
        print(f"Zona horaria de tenerife:                           {self.config.visualization.tenerife_timezone}")
        print()
