"""ROS-independent spatial association and observation confirmation."""
from dataclasses import dataclass
import math

@dataclass
class Track:
    id: int
    x: float
    y: float
    confidence: float
    count: int=1

class RegistryStore:
    def __init__(self,radius=.45,min_observations=3):
        if radius<=0 or min_observations<1:raise ValueError('Invalid registry parameters')
        self.radius=radius;self.min_observations=min_observations;self.tracks=[];self.source_ids={}

    def add(self,x,y,confidence=1.,source_id=0):
        if not all(math.isfinite(v) for v in (x,y,confidence)) or not 0<=confidence<=1:
            raise ValueError('Non-finite position or invalid confidence')
        track=self.source_ids.get(source_id) if source_id>0 else None
        if track is None:
            candidates=[t for t in self.tracks if math.hypot(t.x-x,t.y-y)<=self.radius]
            track=min(candidates,key=lambda t:math.hypot(t.x-x,t.y-y),default=None)
        if track is None:
            track=Track(len(self.tracks)+1,x,y,confidence);self.tracks.append(track)
        else:
            n=track.count;track.x=(track.x*n+x)/(n+1);track.y=(track.y*n+y)/(n+1)
            track.confidence=(track.confidence*n+confidence)/(n+1);track.count+=1
        if source_id>0:self.source_ids[source_id]=track
        return track

    def confirmed(self):return [t for t in self.tracks if t.count>=self.min_observations]
