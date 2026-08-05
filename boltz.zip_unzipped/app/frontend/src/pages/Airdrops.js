import { useEffect, useRef, useState } from 'react';
import mapboxgl from 'mapbox-gl';
import api, { MAPBOX_TOKEN } from '@/lib/api';
import { toast } from 'sonner';
import { Gift, Navigation, Sparkles } from 'lucide-react';

mapboxgl.accessToken = MAPBOX_TOKEN;

export default function Airdrops() {
  const containerRef = useRef(null);
  const mapRef = useRef(null);
  const [airdrops, setAirdrops] = useState([]);
  const [me, setMe] = useState(null);
  const [busy, setBusy] = useState(null);

  useEffect(() => {
    const onPos = (pos) => {
      const c = [pos.coords.longitude, pos.coords.latitude];
      setMe({ lat: pos.coords.latitude, lng: pos.coords.longitude });
      if (!mapRef.current && containerRef.current) {
        mapRef.current = new mapboxgl.Map({
          container: containerRef.current,
          style: 'mapbox://styles/mapbox/dark-v11',
          center: c, zoom: 14, attributionControl: false,
        });
      } else if (mapRef.current) {
        mapRef.current.easeTo({ center: c, duration: 600 });
      }
      // load airdrops
      api.get(`/airdrops/nearby?lat=${pos.coords.latitude}&lng=${pos.coords.longitude}`).then(({ data }) => setAirdrops(data));
    };
    const onErr = () => {
      const c = [-79.38, 43.65];
      if (!mapRef.current && containerRef.current) {
        mapRef.current = new mapboxgl.Map({
          container: containerRef.current,
          style: 'mapbox://styles/mapbox/dark-v11',
          center: c, zoom: 13, attributionControl: false,
        });
      }
      api.get(`/airdrops/nearby?lat=43.65&lng=-79.38`).then(({ data }) => setAirdrops(data));
    };
    if (navigator.geolocation) navigator.geolocation.getCurrentPosition(onPos, onErr, { enableHighAccuracy: true });
    else onErr();
    return () => { mapRef.current?.remove(); mapRef.current = null; };
  }, []);

  // Draw markers
  useEffect(() => {
    const map = mapRef.current; if (!map) return;
    const addMarkers = () => {
      airdrops.forEach((a) => {
        const el = document.createElement('div');
        el.style.cssText = 'width:36px;height:36px;border-radius:50%;background:radial-gradient(circle,#FFD700,#FF33CC);box-shadow:0 0 18px #FFD700;display:flex;align-items:center;justify-content:center;color:#000;font-weight:900;font-family:Orbitron;cursor:pointer';
        el.textContent = a.value;
        new mapboxgl.Marker(el).setLngLat([a.longitude, a.latitude]).addTo(map);
      });
      if (me) {
        const m = document.createElement('div');
        m.style.cssText = 'width:18px;height:18px;border-radius:50%;background:#1E90FF;box-shadow:0 0 16px #1E90FF;border:2px solid #fff';
        new mapboxgl.Marker(m).setLngLat([me.lng, me.lat]).addTo(map);
      }
    };
    if (map.loaded()) addMarkers(); else map.once('load', addMarkers);
  }, [airdrops, me]);

  const claim = async (a) => {
    if (!me) return toast.error('Enable location to claim');
    setBusy(a.airdrop_id);
    try {
      const { data } = await api.post(`/airdrops/${a.airdrop_id}/claim`, { lat: me.lat, lng: me.lng });
      toast.success(data.message);
      setAirdrops(prev => prev.filter(x => x.airdrop_id !== a.airdrop_id));
    } catch (e) { toast.error(e?.response?.data?.detail || 'Too far?'); }
    finally { setBusy(null); }
  };

  return (
    <div className="fade-in space-y-4">
      <div>
        <div className="text-[11px] tracking-[0.3em] text-white/50">// AIRDROPS</div>
        <h1 className="font-display font-bold text-3xl sm:text-4xl mt-1 gradient-text">Geo Airdrop Hunt</h1>
        <p className="text-white/55 mt-1">Drops glow gold on the map. Get within their radius to claim VOLTZ.</p>
      </div>

      <div ref={containerRef} className="h-[400px] rounded-2xl overflow-hidden border border-white/10" data-testid="airdrop-map"/>

      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
        {airdrops.map(a => (
          <div key={a.airdrop_id} className="bento neon-border-gold" data-testid={`airdrop-${a.airdrop_id}`}>
            <div className="flex items-start justify-between">
              <div>
                <div className="flex items-center gap-2"><Gift className="text-neon-gold" size={20}/><span className="font-display tracking-wide font-bold">{a.description}</span></div>
                <div className="text-[11px] text-white/55 mt-1">Radius {a.radius}m • {a.latitude.toFixed(4)}, {a.longitude.toFixed(4)}</div>
              </div>
              <div className="text-right">
                <div className="font-display font-black text-2xl text-neon-gold">+{a.value}</div>
                <div className="text-[10px] tracking-widest text-white/50">VOLTZ</div>
              </div>
            </div>
            <button onClick={() => claim(a)} disabled={busy === a.airdrop_id} className="btn-neon btn-neon-gold w-full justify-center text-xs mt-3" data-testid={`claim-${a.airdrop_id}`}>
              <Navigation size={12} className="mr-1"/> Claim
            </button>
          </div>
        ))}
        {airdrops.length === 0 && (
          <div className="bento col-span-full text-center py-8 text-white/50"><Sparkles className="mx-auto mb-2"/> No active airdrops nearby</div>
        )}
      </div>
    </div>
  );
}
