from audio_processing.campaign.discovery import discover_measurement_points
from audio_processing.common.logging import setup_logging
from audio_processing.common.filesystem import sha256_file

from audio_processing.persistence.database import Database
from audio_processing.persistence.repositories import ContextRepository,FileRepository,MeasurementRepository,ThirdOctaveRepository,PredictionRepository,PeakRepository,AlarmRepository
from audio_processing.spl.leq_processor import run_acoustic_for_file
from audio_processing.spl.utils_acoustics import get_audiofiles,read_calibration_constants,timestamp_from_filename
from audio_processing.ai.ai_model import AudioClassifier
from audio_processing.ai.processor import run_ai_for_file
from audio_processing.peaks.processor import detect_peaks
from audio_processing.alarms.aggregation import aggregate_measurements
from audio_processing.alarms.processor import detect_oca_alarms,detect_lmax_alarms,detect_lc_la_alarms,detect_l90_dynamic_alarms,detect_frequency_composition_alarms,detect_tonal_alarm

from audio_processing.visualization.time_plot import render_time_plot
from audio_processing.visualization.day_evolution import render_day_evolution,render_period_evolution
from audio_processing.visualization.heatmaps import render_acoustic_heatmaps
from audio_processing.visualization.night_evolution import render_night_evolution,render_night_evolution_15min
from audio_processing.visualization.indicators_heatmap import render_indicator_heatmap
from audio_processing.visualization.prediction_laeq_class import render_prediction_laeq_class
from audio_processing.visualization.prediction_stack_bar import render_prediciton_stack_bar
from audio_processing.visualization.prediciton_map import render_prediction_map
from audio_processing.visualization.prediction_laeq_period import render_prediction_laeq_period
from audio_processing.visualization.prediction_laeq_day import render_prediction_laeq_day
from audio_processing.visualization.prediction_laeq_week import render_prediction_laeq_week
from audio_processing.visualization.peak_distribution import render_peak_distribution,render_peak_distribution_week
from audio_processing.visualization.peak_frequency_heatmap import render_peak_frequency_heatmaps,render_peak_frequency_heatmaps_week
from audio_processing.visualization.peak_density import render_peak_density

from pathlib import Path
from zoneinfo import ZoneInfo
from collections import defaultdict

import soundfile as sf

class CampaignPipeline:

    
    def __init__(self, config, dry_run: bool = True):

        self.config = config
        self.dry_run = dry_run
        self.logger = None
        self.db: Database | None = None
        self.ai_classifier: AudioClassifier | None = None
    
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
        if self.config.runtime.run_ai: self.ai_classifier = AudioClassifier()
                       
    
    def run_source(self,source) -> None:

        runtime = self.config.runtime

        if runtime.run_spl and source.needs_spl: self.run_spl_database(source)
        if runtime.run_ai and source.needs_ai: self.run_ai(source)
        if runtime.run_peaks and self.config.peaks.enabled: self.run_peaks(source)
        if runtime.run_alarms and self.config.alarms.enabled: self.run_alarms(source)
        if(runtime.run_basic_visualization and self.config.visualization.enabled and source.needs_visualization): self.run_basic_visualization(source)
        if(runtime.run_advanced_visualization and self.config.visualization.enabled and source.needs_visualization): self.run_advanced_visualization(source)
        

    def run_spl_database(self,source) -> None:

        audio_files             = get_audiofiles(Path(source.raw_data_path))
        results_globales        = []
        results_tercios         = []
        campaign_name           = self.config.campaign.name
        point_name              = source.name
        device_type             = source.device_type
        calibration_file        = Path(self.config.spl.calibration_file)
        
        if not audio_files: 
            self.logger.warning(f"No hay archivos WAV en {source.raw_data_path}")
            return

        if self.db is None: 
            raise RuntimeError(f"La base de datos debe estar habilitada para persistir los resultados SPL.")

        if not calibration_file.is_absolute(): 
            calibration_file = Path(self.config._config_dir) / calibration_file
            
        calibration_constants   = read_calibration_constants(calibration_file)

        with self.db.session() as session:

            context_repository = ContextRepository(session)

            context = context_repository.get_for_source(
                campaign_name       = campaign_name,
                point_name          = point_name,
                device_type         = device_type
            )

            context_id = context.id_contexto

            self.logger.info(f"Contexto {context_id} para {source.source_id}")

        for audio_file in audio_files:
            try:

                content_hash = sha256_file(audio_file)

                if self._is_file_stage_complete(context_id=context_id,audio_file=audio_file,stage="spl",content_hash=content_hash):
                    self.logger.info(f"SPL {source.source_id}: archivo: {audio_file.name} omitido, hash sin cambios.")
                    continue


                info = sf.info(audio_file)
                timestamp = timestamp_from_filename(audio_file)

                if timestamp.tzinfo is None: timestamp = timestamp.replace(tzinfo=ZoneInfo(self.config.campaign.timezone))

                duration_seconds = info.frames / info.samplerate

                acoustic_result = run_acoustic_for_file(
                    audio_file              = audio_file,
                    calibration_constants   = calibration_constants,
                    config                  = self.config,
                    logger                  = self.logger
                )

                if sha256_file(audio_file) != content_hash: raise RuntimeError(f"El archivo {audio_file.name} cambió durante el cálculo SPL; se reintentará en la siguiente ejecución.")
                    

                with self.db.session() as session:

                    file_repository = FileRepository(session)
                    measurement_repository = MeasurementRepository(session)
                    third_octave_repository = ThirdOctaveRepository(session)

                    source_file = file_repository.register(
                        context_id          = context_id,
                        filename            = audio_file.name,
                        datetime_inicio     = timestamp,
                        duracion_seconds    = duration_seconds,
                        sample_rate_hz      = info.samplerate,
                        file_hash           = content_hash)
                    
                    results_globales = measurement_repository.sync_for_file(
                        context_id          = context_id,
                        file_id             = source_file.id_archivo,
                        results             = acoustic_result.levels)

                    if acoustic_result.third_octaves:

                        results_tercios = third_octave_repository.sync_for_measurements(
                            measurements        = results_globales,
                            results             = acoustic_result.third_octaves)

                    file_repository.mark_stage_complete(
                        file_id             = source_file.id_archivo,
                        stage               = "spl",
                        content_hash        = content_hash
                    )
                    
                    self.logger.info("SPL %s: archivo=%s, ""id_archivo=%s, ""mediciones=%s, ""tercios=%s",source.source_id,audio_file.name,source_file.id_archivo,len(results_globales),len(results_tercios), )
                    
            except Exception as e:

                self.logger.exception(f"Error procesando {audio_file}")
                if self.config.execution.stop_on_error: raise

    def _is_file_stage_complete(self,*,context_id: int,audio_file: Path,stage: str,content_hash: str) -> bool:

        if self.db is None: raise RuntimeError(f"La base de datos debe de estar habilitada")

        with self.db.session() as session:
            file_repository = FileRepository(session)
            source_file = file_repository.get_by_context_and_filename(context_id=context_id,filename=audio_file.name)
            return (source_file is not None and file_repository.is_stage_complete(file_id=source_file.id_archivo,stage=stage,content_hash=content_hash))

        
    def run_ai(self,source) -> None:

        audio_files = get_audiofiles(Path(source.raw_data_path))

        if self.db is None: raise RuntimeError("La base de datos debe de estar habilitada para persistir IA.")
        if self.ai_classifier is None: raise RuntimeError("AudioClassifier no está inicializado.")

        if not audio_files:
            self.logger.warning(f"No hay archivos WAV en {source.raw_data_path}")
            return

        with self.db.session() as session:

            context_repository = ContextRepository(session)
            context = context_repository.get_for_source(
                campaign_name   = self.config.campaign.name,
                point_name      = source.name,
                device_type     = source.device_type
            )

            context_id = context.id_contexto

        for audio_file in audio_files:

            try:

                content_hash = sha256_file(audio_file)

                if self._is_file_stage_complete(context_id=context_id,audio_file=audio_file,stage="ai",content_hash=content_hash):
                    self.logger.info(f"IA {source.source_id}: archivo= {audio_file.name} omitido, hash sin cambios")
                    continue

                info = sf.info(audio_file)
                timestamp = timestamp_from_filename(audio_file)

                if timestamp.tzinfo is None: timestamp = timestamp.replace(tzinfo=ZoneInfo(self.config.campaign.timezone))

                duration_seconds = info.frames / info.samplerate

                prediction_results = run_ai_for_file(
                    audio_file      = audio_file,
                    classifier      = self.ai_classifier,
                    config          = self.config,
                    logger          = self.logger
                )

                if sha256_file(audio_file) != content_hash: raise RuntimeError(f" El archivo {audio_file.name} cambió durante la inferencia IA; se reintentará en la siguiente ejecución.")

                with self.db.session() as session:

                    file_repository = FileRepository(session)

                    measurement_repository = MeasurementRepository(session)
                    prediction_repository = PredictionRepository(session)

                    source_file = file_repository.register(

                        context_id          = context_id,
                        filename            = audio_file.name,
                        datetime_inicio     = timestamp,
                        duracion_seconds    = duration_seconds,
                        sample_rate_hz      = info.samplerate,
                        file_hash           = content_hash
                    )

                    measurements = measurement_repository.list_by_file(source_file.id_archivo)

                    if not measurements: raise RuntimeError(f"No existen mediciones acústicas para enlazar IA del archivo: {audio_file.name}")

                    (predictions,links) = prediction_repository.sync_for_file(
                        file_id         = source_file.id_archivo,
                        measurements    = measurements,
                        results         = prediction_results,
                        model_name      = str(self.config.ai.model),
                        threshold       = float(self.config.ai.threshold)
                    )

                    file_repository.mark_stage_complete(
                        file_id         = source_file.id_archivo,
                        stage           = 'ai',
                        content_hash    = content_hash
                    )

                    file_id = source_file.id_archivo
                    prediction_count = len(predictions)
                    link_count = len(links)
            
                self.logger.info(f"IA {source.source_id}: archivo = {audio_file.name} ,id_archivo = {file_id} predicciones = {prediction_count}, enlaces_medicion = {link_count}")    

            except Exception as e:

                self.logger.exception(f"Error procesando IA de {audio_file}")

                if self.config.execution.stop_on_error: raise

        
    def run_peaks(self,source):

        if self.db is None: raise RuntimeError("La base de datos debe estar habilitada para persistir picos.")

        try:
            
            audio_files = get_audiofiles(Path(source.raw_data_path))
            
            if not audio_files: 
                self.logger.warning(f"No hay archivos WAV para calcular picos de {source.source_id}")
                return
            

            with self.db.session() as session:

                context_repository = ContextRepository(session)
                measurement_repository = MeasurementRepository(session)
                peak_repository = PeakRepository(session)
                file_repository = FileRepository(session)
                context = context_repository.get_for_source(
                    campaign_name       = self.config.campaign.name,
                    point_name          = source.name,
                    device_type         = source.device_type)

                context_id = context.id_contexto

                source_files = []

                for audio_file in audio_files:

                    source_file = (file_repository.get_by_context_and_filename(context_id=context_id,filename=audio_file.name))

                    if source_file is None: 
                        self.logger.warning(f"El archivo {audio_file.name} no está registrado en la base de datos")
                        continue

                    source_files.append(source_file)

                file_ids = [source_file.id_archivo for source_file in source_files]

                measurements = measurement_repository.list_by_files(file_ids)

                if not measurements: 
                    self.logger.warning(f"No existen mediciones acústicas para calcular picos de {source.source_id}")
                    return

                timezone = ZoneInfo(self.config.campaign.timezone)
                measurements_by_hour = defaultdict(list)

                for measurement in measurements:

                    local_datetime  = (measurement.datetime.astimezone(timezone))
                    hour_key        = local_datetime.replace(minute=0,second=0,microsecond=0)
                    measurements_by_hour[hour_key].append(measurement)

                peak_result = []
                for hour_key in sorted(measurements_by_hour):
                    hourly_measurement = (measurements_by_hour[hour_key])
                    hourly_results = detect_peaks(
                        measurements        = hourly_measurement,
                        window_size         = self.config.peaks.window_size,
                        adding_threshold    = self.config.peaks.adding_threshold,
                        width               = self.config.peaks.width,
                        prominence          = self.config.peaks.prominence
                        )

                    peak_result.extend(hourly_results)
                    self.logger.info(
                            "PEAKS %s: hora=%s, "
                            "mediciones=%s, picos=%s",
                            source.source_id,
                            hour_key,
                            len(hourly_measurement),
                            len(hourly_results),
                    )

                peaks, links = peak_repository.sync_for_context(
                    context_id      = context_id,
                    measurements    = measurements,
                    results         = peak_result,
                )

                self.logger.info(
                    "PEAKS %s: contexto=%s, "
                    "mediciones=%s, "
                    "picos=%s, "
                    "enlaces_medicion=%s",
                    source.source_id,
                    context_id,
                    len(measurements),
                    len(peaks),
                    len(links),
                )

        except Exception as e:
            self.logger.exception(f"Error procesando picos de {source.source_id}")
            if self.config.execution.stop_on_error: raise


    def run_alarms(self,source) -> None:

        if self.db is None: raise RuntimeError("La base de datos ha de estar habilitada para calcular alarmas.")

        try:

            with self.db.session() as session:

                context_repository          = ContextRepository(session)
                measurement_repository      = MeasurementRepository(session)
                third_octave_repository     = ThirdOctaveRepository(session)
                peak_repository             = PeakRepository(session)
                alarm_repository            = AlarmRepository(session)


                context = (context_repository.get_for_source(
                    campaign_name=self.config.campaign.name,
                    point_name = source.name,
                    device_type = source.device_type
                ))

                context_id = context.id_contexto

                audio_files                 = get_audiofiles(Path(source.raw_data_path))
                file_repository             = FileRepository(session)
                source_files                = []

                for audio_file in audio_files:
                    source_file = file_repository.get_by_context_and_filename(context_id=context_id,filename=audio_file.name)
                    if source_file is None: 
                        self.logger.warning(f"El archivo {audio_file.name} no está registrado en la base de datos")
                        continue
                    source_files.append(source_file)

                file_ids                    = [source_file.id_archivo for source_file in source_files]
                measurements                = (measurement_repository.list_by_files(file_ids))

                if not measurements: 
                    self.logger.warning(f"No existen mediciones para calcular alarmas de {source.source_id}")
                    return

                measurement_ids = [measurement.id_medicion for measurement in measurements]
                third_octaves   = (third_octave_repository.list_by_measurements(measurement_ids))
                peak_apex_ids   = (peak_repository.list_apex_measurement_ids(context_id=context_id,measurement_ids=measurement_ids))
                
                aggregations = (aggregate_measurements(
                    measurements                = measurements,
                    third_octaves               = third_octaves,
                    peak_apex_measurement_ids   = peak_apex_ids,
                    aggregation_seconds         = self.config.alarms.aggregation_seconds,
                    timezone                    = self.config.campaign.timezone
                ))

                if not aggregations: 
                    self.logger.warning(f"No se han generado agregados para alarmas de {source.source_id}")
                    return


            # -----------------------------------------
            # Separar por día LOCAL
            # -----------------------------------------
            # 
            aggregations_by_day = defaultdict(list)

            for aggregation in aggregations:

                local_day = aggregation.start_time.date()
                aggregations_by_day[local_day].append(aggregation)

            alarm_results = []

            for day in sorted(aggregations_by_day):

                daily_aggregations = aggregations_by_day[day]
                daily_results = []
                
                daily_results.extend(detect_oca_alarms(
                    aggregations=daily_aggregations,
                    oca_type=self.config.alarms.oca_limit
                ))

                daily_results.extend(detect_lmax_alarms(
                    aggregations=daily_aggregations,
                    threshold_db=self.config.alarms.lmax.threshold_db
                ))          
                
                daily_results.extend(detect_lc_la_alarms(
                    aggregations=daily_aggregations,
                    normative_threshold_db=self.config.alarms.lc_la.normative_threshold_db,
                    dynamic_threshold_db=self.config.alarms.lc_la.dynamic_threshold_db
                ))

                daily_results.extend(detect_l90_dynamic_alarms(
                    aggregations=daily_aggregations,
                    threshold_db=self.config.alarms.l90.threshold_db,
                    rolling_window=self.config.alarms.l90.rolling_window
                ))

                daily_results.extend(detect_frequency_composition_alarms(
                    aggregations=daily_aggregations,
                    jump_threshold_db=self.config.alarms.frequency_composition.jump_threshold_db
                ))

                if(self.config.alarms.tonal.enabled):
                    daily_results.extend(detect_tonal_alarm(
                        aggregations=daily_aggregations
                    ))

                alarm_results.extend(daily_results)

                self.logger.info(
                    "ALARMS %s: día=%s, agregados=%s, alarmas=%s",
                    source.source_id,
                    day,
                    len(daily_aggregations),
                    len(daily_results),
                )
                
            with self.db.session() as session:

                alarm_repository = AlarmRepository(session)

                alarm_rows,alarm_links = alarm_repository.sync_for_measurements(
                    context_id=context_id,
                    measurements=measurements,
                    results=alarm_results,
                    scope_measurement_ids=set(measurement_ids)
                )

                alarm_count = len(alarm_rows)
                link_count = len(alarm_links)

            self.logger.info(
                "ALARMS %s: contexto=%s, mediciones=%s, agregados=%s, "
                "alarmas=%s, enlaces=%s",
                source.source_id,
                context_id,
                len(measurements),
                len(aggregations),
                len(alarm_rows),
                len(alarm_links),
            )
                    

        except Exception as e:

            self.logger.exception(f"Error {e} procesando alarmas de {source.source_id}")

            if self.config.execution.stop_on_error: raise

    def run_basic_visualization(self,source) -> None:

        if self.db is None: raise RuntimeError("La base de datos debe estar habilitada para visualizar resultados.")

        try:
            with self.db.session() as session:

                context = ContextRepository(session).get_for_source(
                    campaign_name   = self.config.campaign.name,
                    point_name      = source.name,
                    device_type     = source.device_type
                )

                measurements = MeasurementRepository(session).list_by_context(
                    context_id      = context.id_contexto)

                prediction_measurements = PredictionRepository(session).list_with_measurements_for_context(
                    context_id      = context.id_contexto
                )

                if not measurements:
                    self.logger.warning(f"No hay mediciones para visualizar en: {source.source_id}")
                    return

                point_config            = getattr(self.config.points, source.name, None)
                correction_db           = getattr(point_config,"correction_db",0.0) if point_config is not None else 0.0
                timezone_name           = "Atlantic/Canary" if self.config.visualization.tenerife_timezone else self.config.campaign.timezone
                output_dir              = Path(source.output_path) / self.config.outputs.subfolders.spl.general_folder_name / self.config.outputs.subfolders.spl.visualization_folder_name
                class_map_path          = Path(self.config.visualization.class_map_csv)

                prediction_output_dir   = Path(source.output_path) / self.config.outputs.subfolders.ai.general_folder_name / self.config.outputs.subfolders.ai.visualization_folder_name

                if not class_map_path.is_absolute():
                    class_map_path = Path(self.config._config_dir) / class_map_path
                
                time_plot = render_time_plot(
                    measurements        = measurements,
                    output_dir          = output_dir,
                    plot_name           = source.name,
                    aggregation_seconds = int(self.config.visualization.aggregation_seconds),
                    percentiles         = list(self.config.visualization.percentiles),
                    oca_type            = self.config.visualization.oca_type,
                    correction_db       = float(correction_db),
                    timezone_name       = timezone_name
                )

                if time_plot:
                    time_png,time_csv = time_plot
                    self.logger.info(f"Visualización básica {source.source_id}: PNG = {time_png}, CSV = {time_csv}")

                day_result = render_day_evolution(
                    measurements        = measurements,
                    output_dir          = output_dir,
                    plot_name           = source.name,
                    timezone_name       = timezone_name
                )

                if day_result:
                    day_png,day_csv = day_result
                    self.logger.info(f"Evolución diaria: {source.source_id}: PNG = {day_png}, CSV = {day_csv}")

                period_outputs = render_period_evolution(
                    measurements        = measurements,
                    output_dir          = output_dir,
                    plot_name           = source.name,
                    timezone_name       = timezone_name
                )

                if period_outputs:
                    for period, (png_path,csv_path) in period_outputs.items():

                        self.logger.info(f"Evolución {period} {source.name}: PNG = {png_path}, CSV = {csv_path}")


                heatmapts_outputs = render_acoustic_heatmaps(
                    measurements        = measurements,
                    output_dir          = output_dir,
                    plot_name           = source.name,
                    timezone_name       = timezone_name
                )

                for kind, (png_path,csv_path) in heatmapts_outputs.items():
                    self.logger.info(f"Heatmap {kind} {source.name}: PNG: {png_path}, CSV = {csv_path}")

                night_result = render_night_evolution(
                    measurements        = measurements,
                    output_dir          = output_dir,
                    plot_name           = source.name,
                    timezone_name       = timezone_name
                )

                if night_result:
                    png_path = night_result[0]
                    csv_path = night_result[1]
                    self.logger.info(f"Night evolution {source.name}: PNG: {png_path}, CSV = {csv_path}")

                night_result = render_night_evolution_15min(
                    measurements        = measurements,
                    output_dir          = output_dir,
                    plot_name           = source.name,
                    timezone_name       = timezone_name
                )
                if night_result:
                    png_path = night_result[0]
                    csv_path = night_result[1]
                    self.logger.info(f"Night evolution 15min period {source.name}: PNG: {png_path}, CSV = {csv_path}")

                indicators_outputs = render_indicator_heatmap(
                    measurements        = measurements,
                    output_dir          = output_dir,
                    plot_name           = source.name,
                    timezone_name       = timezone_name,
                    correction_db       = float(correction_db)
                )

                if indicators_outputs:
                    indicator_png,indicator_csv,general_csv = indicators_outputs
                    self.logger.info(f"Mapa de indicadores {source.name}: PNG: {indicator_png}, CSV = {indicator_csv},resumen = {general_csv}")

                prediction_outputs = render_prediction_laeq_class(
                    prediction_measurements = prediction_measurements,
                    class_map_path          = class_map_path,
                    output_dir              = prediction_output_dir,
                    taxonomy                = self.config.visualization.taxonomy,
                    plot_name               = source.name,
                    correction_db           = float(correction_db)
                    
                )

                if prediction_outputs:
                    html_path,csv_path = prediction_outputs
                    self.logger.info(f"Treemap LAeq por clases {source.name}: HTML = {html_path}, CSV = {csv_path}")
                
                prediction_outputs = render_prediciton_stack_bar(
                    prediction_measurements = prediction_measurements,
                    class_map_path          = class_map_path,
                    output_dir              = prediction_output_dir,
                    taxonomy                = self.config.visualization.taxonomy,
                    plot_name               = source.name,
                    correction_db           = float(correction_db) 
                )

                if prediction_outputs:
                    html_path,csv_path = prediction_outputs
                    self.logger.info(f"Stack bar LAeq por clases {source.name}: HTML = {html_path}, CSV = {csv_path}")

                prediction_outputs = render_prediction_map(
                    prediction_measurements = prediction_measurements,
                    class_map_path          = class_map_path,
                    output_dir              = prediction_output_dir,
                    taxonomy                = self.config.visualization.taxonomy,
                    plot_name               = source.name,
                    aggregation_seconds     = int(self.config.visualization.aggregation_seconds),
                    timezone_name           = timezone_name 
                )

                if prediction_outputs:
                    png_path,csv_path = prediction_outputs
                    self.logger.info(f"Prediction map {source.name}: PNG = {png_path}, CSV = {csv_path}")


                prediction_outputs = render_prediction_laeq_period(
                    prediction_measurements = prediction_measurements,
                    class_map_path          = class_map_path,
                    taxonomy                = self.config.visualization.taxonomy,
                    output_dir              = prediction_output_dir,           
                    plot_name               = source.name,
                    correction_db           = float(correction_db),
                    timezone_name           = timezone_name
                )

                four_hour_output = render_prediction_laeq_period(
                    prediction_measurements = prediction_measurements,
                    class_map_path          = class_map_path,
                    taxonomy                = self.config.visualization.taxonomy,
                    output_dir              = prediction_output_dir,
                    plot_name               = source.name,
                    correction_db           = float(correction_db),
                    timezone_name           = timezone_name,
                    period_scheme           = 'four_hour'
                )

                if prediction_outputs:
                     for period, (html_path, csv_path) in prediction_outputs.items():
                        self.logger.info(f"Treemap LAeq por clase y periodo {source.name} , {period}: HTML = {html_path}, CSV = {csv_path}")
                            
                if four_hour_output:
                    for period, (html_path, csv_path) in four_hour_output.items():
                        self.logger.info(f"Treemap LAeq por clase y franja de 4 horas {source.name} , {period}: HTML = {html_path}, CSV = {csv_path}")
                            
                daily_outpus = render_prediction_laeq_day(
                    prediction_measurements = prediction_measurements,
                    class_map_path          = class_map_path,
                    taxonomy                = self.config.visualization.taxonomy,
                    output_dir              = prediction_output_dir,
                    plot_name               = source.name,
                    correction_db           = float(correction_db),
                    timezone_name           = timezone_name,
                )

                if daily_outpus:
                    for day, (html_path,csv_path) in daily_outpus.items():
                        self.logger.info(f"Treemap LAeq por clase y día {source.name}, {day}: HTML = {html_path}, CSV = {csv_path}")

                weekly_outputs = render_prediction_laeq_week(
                    prediction_measurements = prediction_measurements,
                    class_map_path          = class_map_path,
                    taxonomy                = self.config.visualization.taxonomy,
                    output_dir              = prediction_output_dir,
                    plot_name               = source.name,
                    correction_db           = float(correction_db),
                    timezone_name           = timezone_name
                )

                if weekly_outputs:
                    for week_start, (html_path,csv_path) in weekly_outputs.items():
                        self.logger.info(f"Treemap LAeq por clase y semana {source.name} , {week_start}: HTML = {html_path}, CSV = {csv_path}")
 
        except Exception as e:
            self.logger.exception("Error generando la visualización básica para: %s",source.source_id)
            if self.config.execution.stop_on_error: raise

    def run_advanced_visualization(self,source) -> None:
        if self.db is None: raise RuntimeError(f"La base de datos debe de estar habilitada para visualizar picos.")

        try:
            with self.db.session() as session:
                
                context = ContextRepository(session).get_for_source(
                    campaign_name   = self.config.campaign.name,
                    point_name      = source.name,
                    device_type     = source.device_type
                )

                peaks = PeakRepository(session).list_by_context(context.id_contexto)

                if not peaks: 
                    self.logger.info(f"No hay picos para visualizar en: {source.source_id}.")
                    return

                point_config = getattr(self.config.points, source.name, None)

                if point_config is not None:
                    correction_db = (getattr(point_config,"correction_db",0.0))
                else:
                    correction_db = 0.0

                output_dir = Path(source.output_path) / self.config.outputs.subfolders.spl.general_folder_name / self.config.outputs.subfolders.spl.visualization_folder_name

                result_peaks = render_peak_distribution(
                    peaks           = peaks,
                    output_dir      = output_dir,
                    plot_name       = source.name,
                    correction_db   = float(correction_db),
                    timezone_name   = self.config.campaign.timezone
                )

                if result_peaks:
                    png_path,night_png_path,csv_path = result_peaks

                    self.logger.info(f"Distribución de picos {source.name}: PNG = {png_path} , PNG nocturno = {night_png_path} , CSV = {csv_path}")

                result_peaks = render_peak_frequency_heatmaps(
                    peaks           = peaks,
                    output_dir      = output_dir,
                    plot_name       = source.name,
                    timezone_name   = self.config.campaign.timezone,
                )

                if result_peaks:
                    for period,(png_path,csv_path) in result_peaks.items():
                        self.logger.info(f"Mapa de frecuencia de picos {source.name}, {period}: PNG = {png_path} , CSV = {csv_path}")

                result_peaks = render_peak_frequency_heatmaps_week(
                    peaks           = peaks,
                    output_dir      = output_dir,
                    plot_name       = source.name,
                    timezone_name   = self.config.campaign.timezone
                )

                if result_peaks:
                    for week, outputs in result_peaks.items():
                        for period, (png_path, csv_path) in outputs.items():

                            self.logger.info(f"Mapa semanal de frecuencia de picos {source.name}, semana {week}, {period}: PNG = {png_path}, CSV = {csv_path}")

                result_peaks = render_peak_distribution_week(
                    peaks           = peaks,
                    output_dir      = output_dir,
                    plot_name       = source.name,
                    correction_db   = float(correction_db),
                    timezone_name   = self.config.campaign.timezone
                )

                if result_peaks:
                    for week, paths in result_peaks.items():
                        if paths:
                            standard_png, night_png, csv_path = paths
                            self.logger.info(f"Distribución de picos semanal {source.name}, {week}: PNG = {standard_png}, PNG nocturno = {night_png}, CSV = {csv_path}")

                
                result_peaks = render_peak_density(
                    peaks           = peaks,
                    output_dir      = output_dir,
                    plot_name       = source.name,
                    timezone_name   = self.config.campaign.timezone
                )

                if result_peaks:
                    for kind, (png_path, csv_path) in result_peaks.items():
                        self.logger.info(f"Distribución horaria de picos {source.name} ({kind}): PNG = {png_path}, CSV = {csv_path}" )
                            
                
                
        except Exception:
            self.logger.exception(f"Error generando la distribución de picos para {source.source_id}")

            if self.config.execution.stop_on_error: raise
    
    def print_plan(self,point) -> None:
        
        self.print_source_plan(point)

        if self.config.runtime.run_spl and point.needs_spl: self.print_spl_plan()
        if self.config.runtime.run_ai and point.needs_ai: self.print_ai_plan()
        if self.config.runtime.run_peaks and self.config.peaks.enabled: self.print_peaks_plan()
        if self.config.runtime.run_alarms and self.config.alarms.enabled: self.print_alarms_plan()

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
        print(f"#------------Información SPL----------#")
        
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

    def print_peaks_plan(self):

        print()
        print("#------------[PEAKS] Funcionando----------#")
        print("#-------------Información picos-----------#")
        print(f"Ventana mediana:             "f"{self.config.peaks.window_size}")
        print(f"Umbral añadido:              "f"{self.config.peaks.adding_threshold}")
        print(f"Anchura mínima:              "f"{self.config.peaks.width}")
        print(f"Prominencia:                 "f"{self.config.peaks.prominence}")


    def print_visualization_plan(self):    

        print() 
        print("#------------[Visualization] Funcionando----------#")
        print(f"#------------Información Visualization----------#")
        
        print(f"Activo:                                             {self.config.visualization.enabled}")
        print(f"Taxonomía:                                          {self.config.visualization.taxonomy}")
        print(f"Segundos de agregación:                             {self.config.visualization.aggregation_seconds}")
        print(f"Percentiles:                                        {self.config.visualization.percentiles}")
        print(f"OCA:                                                {self.config.visualization.oca_type}")
        print(f"Número de segundos borrados al inicio del archivo:  {self.config.visualization.remove_start_seconds}")
        print(f"Número de segundos borrados al final del archivo:   {self.config.visualization.remove_end_seconds}")
        print(f"Zona horaria de tenerife:                           {self.config.visualization.tenerife_timezone}")
        print()

    def print_alarms_plan(self):

        print()
        print("#------------[ALARMS] Funcionando----------#")
        print("#-------------Información alarmas-----------#")
        print("Agregación:             "f"{self.config.alarms.aggregation_seconds}s")
        print("OCA:                    "f"{self.config.alarms.oca_limit}")
        print("Lmax:                   "f"{self.config.alarms.lmax.threshold_db} dB")
        print("LC-LA normativo:        "f"{self.config.alarms.lc_la.normative_threshold_db} dB")
        print("LC-LA dinámico:         "f"{self.config.alarms.lc_la.dynamic_threshold_db} dB")
        print("L90 dinámico:           "f"{self.config.alarms.l90.threshold_db} dB")
        print("Salto frecuencial:      "f"{self.config.alarms.frequency_composition.jump_threshold_db} dB")
        print("Tonal:                  "f"{self.config.alarms.tonal.enabled}")
