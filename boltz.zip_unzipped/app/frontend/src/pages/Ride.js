import { useEffect, useRef, useState } from 'react';
import mapboxgl from 'mapbox-gl';
import api from '@/lib/api';
import { MAPBOX_TOKEN } from '@/lib/api';
import { useAuth } from '@/context/AuthContext';
import { toast } from 'sonner';
import Speedometer from '@/components/Speedometer';
import { Play, Square, MapPin, Activity, Clock, Trophy, Leaf } from 'lucide-react';

mapboxgl.accessToken = MAPBOX_TOKEN;

function haversine(a, b) {
  const R = 6371000, toR = x => x * Math.PI / 180;
  const d1 = toR(b[1] - a[1]), d2 = toR(b[0] - a[0]);
  const h = Math.sin(d1/2)**2 + Math.cos(toR(a[1])) * Math.cos(toR(b[1])) * Math.sin(d2/2)**2;
  return 2 * R * Math.atan2(Math.sqrt(h), Math.sqrt(1-h));
}

export default function Ride() {
  const { user } = useAuth();
  const containerRef = useRef(null);
  const mapRef = useRef(null);
  const watchRef = useRef(null);
  const traceRef = useRef([]);
  const lastPosRef = useRef(null);
  const speedSmoothRef = useRef(0);
  const startTimeRef = useRef(null);

  const [ride, setRide] = useState(null);
  const [distance, setDistance] = useState(0);
  const [speed, setSpeed] = useState(0);
  const [duration, setDuration] = useState(0);
  const [maxSpeed, setMaxSpeed] = useState(0);
  const [center, setCenter] = useState([-79.38, 43.65]);
  const [result, setResult] = useState(null);

  // Init map
  useEffect(() => {
    if (!containerRef.current || mapRef.current) return;
    mapRef.current = new mapboxgl.Map({
      container: containerRef.current,
      style: 'mapbox://styles/mapbox/dark-v11',
      center, zoom: 14,
      attributionControl: false,
    });
    if (navigator.geolocation) {
      navigator.geolocation.getCurrentPosition((pos) => {
        const c = [pos.coords.longitude, pos.coords.latitude];
        setCenter(c);
        if (mapRef.current) mapRef.current.setCenter(c);
      }, () => {}, { enableHighAccuracy: true });
    }
    // load existing ongoing ride
    (async () => {
      try { const { data } = await api.get('/rides/current'); if (data) setRide(data); } catch { /* non-fatal */ }
    })();
    return () => { if (watchRef.current) navigator.geolocation.clearWatch(watchRef.current); mapRef.current?.remove(); mapRef.current = null; };
    // eslint-disable-next-line
  }, []);

  // Tick duration
  useEffect(() => {
    if (!ride || ride.status !== 'ongoing') return;
    startTimeRef.current = new Date(ride.start_time).getTime();
    const t = setInterval(() => setDuration(Math.floor((Date.now() - startTimeRef.current) / 1000)), 1000);
    return () => clearInterval(t);
  }, [ride]);

  const ensureLayer = () => {
    const map = mapRef.current; if (!map) return;
    if (map.getSource('route')) return;
    map.addSource('route', { type: 'geojson', data: { type: 'Feature', geometry: { type: 'LineString', coordinates: [] } } });
    map.addLayer({ id: 'route-glow', type: 'line', source: 'route', paint: { 'line-color': '#FF33CC', 'line-width': 9, 'line-opacity': 0.25, 'line-blur': 6 } });
    map.addLayer({ id: 'route', type: 'line', source: 'route', paint: { 'line-color': '#1E90FF', 'line-width': 4 } });
  };

  const updateRouteLayer = () => {
    const map = mapRef.current; if (!map) return;
    if (!map.getSource('route')) ensureLayer();
    const src = map.getSource('route');
    if (src) src.setData({ type: 'Feature', geometry: { type: 'LineString', coordinates: traceRef.current.map(p => [p.lng, p.lat]) } });
  };

  const start = async () => {
    try {
      const { data } = await api.post('/rides/start', { vehicle_type: user?.vehicle_type || 'ebike' });
      setRide(data); setResult(null); traceRef.current = []; lastPosRef.current = null;
      setDistance(0); setSpeed(0); setMaxSpeed(0); setDuration(0);
      toast.success('Ride started');

      if (mapRef.current) mapRef.current.once('load', ensureLayer);
      if (mapRef.current.loaded()) ensureLayer();

      if (!navigator.geolocation) return toast.error('Geolocation not available');
      watchRef.current = navigator.geolocation.watchPosition((pos) => {
        const cur = { lat: pos.coords.latitude, lng: pos.coords.longitude, ts: Date.now() };
        traceRef.current.push(cur);
        let delta = 0;
        if (lastPosRef.current) {
          delta = haversine([lastPosRef.current.lng, lastPosRef.current.lat], [cur.lng, cur.lat]);
          const newDist = (distance + delta / 1000);
          setDistance(newDist);
          const dt = (cur.ts - lastPosRef.current.ts) / 1000;
          if (dt > 0) {
            const inst = (delta / dt) * 3.6;
            speedSmoothRef.current = speedSmoothRef.current * 0.7 + inst * 0.3;
            const s = Math.round(speedSmoothRef.current);
            setSpeed(s);
            setMaxSpeed(prev => Math.max(prev, s));
          }
        }
        lastPosRef.current = cur;
        if (mapRef.current) mapRef.current.easeTo({ center: [cur.lng, cur.lat], duration: 800 });
        updateRouteLayer();
        // ping backend
        api.patch(`/rides/${data.ride_id}/update`, { current_lat: cur.lat, current_lng: cur.lng, distance_delta: delta / 1000 }).catch(() => {});
      }, (err) => { toast.error(`GPS error: ${err.message}`); }, { enableHighAccuracy: true, maximumAge: 1000, timeout: 15000 });
    } catch (e) { toast.error(e?.response?.data?.detail || 'Failed to start'); }
  };

  const stop = async () => {
    if (!ride) return;
    if (watchRef.current) navigator.geolocation.clearWatch(watchRef.current);
    try {
      const { data } = await api.post(`/rides/${ride.ride_id}/finish`, {
        total_distance: distance,
        gps_trace: traceRef.current.map(p => ({ lat: p.lat, lng: p.lng, timestamp: new Date(p.ts).toISOString() })),
      });
      setResult(data); setRide(null); setSpeed(0);
      toast.success(`Ride finished: +${data.rmrEarned} RMR`);
    } catch (e) { toast.error(e?.response?.data?.detail || 'Failed to finish'); }
  };

  const fmtTime = (s) => {
    const m = Math.floor(s / 60), ss = s % 60;
    return `${String(m).padStart(2,'0')}:${String(ss).padStart(2,'0')}`;
  };

  return (
    <div className="fade-in space-y-4">
      <div className="flex items-end justify-between">
        <div>
          <div className="text-[11px] tracking-[0.3em] text-white/50">// RIDE TRACKING</div>
          <h1 className="font-display font-bold text-3xl sm:text-4xl mt-1 gradient-text">Live Ride</h1>
        </div>
        {ride ? (
          <button onClick={stop} className="btn-neon btn-neon-pink" data-testid="ride-stop"><Square size={14} className="mr-1"/> Finish Ride</button>
        ) : (
          <button onClick={start} className="btn-neon btn-neon-green" data-testid="ride-start"><Play size={14} className="mr-1"/> Start Ride</button>
        )}
      </div>

      <div className="relative rounded-2xl overflow-hidden border border-white/10 h-[460px]">
        <div ref={containerRef} className="absolute inset-0" data-testid="ride-map"/>
        {/* Overlay stats */}
        <div className="absolute top-3 left-3 right-3 grid grid-cols-3 gap-2 pointer-events-none">
          <div className="glass-strong rounded-xl p-2 text-center">
            <div className="text-[9px] text-white/60 tracking-widest">DISTANCE</div>
            <div className="font-display font-bold text-lg text-neon-cyan">{distance.toFixed(2)} <span className="text-[10px] text-white/50">km</span></div>
          </div>
          <div className="glass-strong rounded-xl p-2 text-center">
            <div className="text-[9px] text-white/60 tracking-widest">DURATION</div>
            <div className="font-display font-bold text-lg text-neon-blue">{fmtTime(duration)}</div>
          </div>
          <div className="glass-strong rounded-xl p-2 text-center">
            <div className="text-[9px] text-white/60 tracking-widest">MAX SPEED</div>
            <div className="font-display font-bold text-lg text-neon-pink">{maxSpeed} <span className="text-[10px] text-white/50">km/h</span></div>
          </div>
        </div>
        {/* Speedometer */}
        <div className="absolute bottom-4 right-4 pointer-events-none">
          <Speedometer speed={speed} max={80} />
        </div>
        {/* Status badge */}
        <div className="absolute bottom-4 left-4 glass-strong rounded-full px-3 py-1.5 inline-flex items-center gap-2">
          <span className={`pulse-dot ${ride ? '' : 'opacity-30'}`}/>
          <span className="font-display tracking-widest text-xs">{ride ? 'TRACKING' : 'IDLE'}</span>
        </div>
      </div>

      {/* Result modal-like card */}
      {result && (
        <div className="bento neon-border-gold">
          <div className="flex items-center gap-2 mb-2 text-neon-gold">
            <Trophy size={20}/> <span className="font-display tracking-wider uppercase text-sm">Ride Complete</span>
          </div>
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
            <div><div className="text-[10px] text-white/55 tracking-widest">VOLTZ EARNED</div><div className="font-display font-bold text-2xl text-neon-gold">+{result.rmrEarned}</div></div>
            <div><div className="text-[10px] text-white/55 tracking-widest">DISTANCE</div><div className="font-display font-bold text-2xl text-neon-cyan">{result.validation?.computedDistance?.toFixed(2)} km</div></div>
            <div><div className="text-[10px] text-white/55 tracking-widest">AVG SPEED</div><div className="font-display font-bold text-2xl text-neon-blue">{result.validation?.averageSpeed?.toFixed(1)}</div></div>
            <div><div className="text-[10px] text-white/55 tracking-widest">VALIDATED</div><div className={`font-display font-bold text-2xl ${result.validation?.passed ? 'text-neon-green' : 'text-neon-pink'}`}>{result.validation?.passed ? 'YES' : 'FLAGGED'}</div></div>
          </div>
        </div>
      )}

      {/* Help */}
      <div className="text-xs text-white/45 flex flex-wrap gap-3 items-center">
        <Activity size={12} className="text-neon-green"/> GPS-validated rides earn VOLTZ.
        <Clock size={12} className="text-neon-blue"/> Min 60s duration.
        <MapPin size={12} className="text-neon-pink"/> Min 0.1 km distance.
        <Leaf size={12} className="text-neon-green"/> Every km saves CO₂ — see /carbon.
      </div>
    </div>
  );
}
