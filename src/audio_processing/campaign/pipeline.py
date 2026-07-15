
from audio_processing.campaign.discovery import *

class CampaignPipeline:
    def __init__(self,config):
        self.config = config
    
    def run(self) -> None:
        points = discover_measurement_points(self.config)
        for point in points: self.run_point(point)

    def run_point(self,point) -> None:
        
        if self.config.execution.run_spl and point.needs_spl: self.run_spl(point)
        
        if self.config.execution.run_ai and point.needs_ai: self.run_ai(point)

        if self.config.execution.run_visualization and point.needs_visualization: self.run_visualization(point)

    def run_spl(self,point) -> None:

        from audio_processing.spl.leq_processor import run_leq_for_point
        run_leq_for_point(point,self.config)
    
    def run_ai(self,point) -> None:

        from audio_processing.ai.inference import run_ai_for_point
        run_ai_for_point(point,self.config)

    def run_visualization(self,point) -> None:

        from audio_processing.visualization.pipeline import run_visualization_for_point
        run_visualization_for_point(point,self.config)

        

