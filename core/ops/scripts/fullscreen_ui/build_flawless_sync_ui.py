import json

# Generate base64 representations of clara and maxx
with open("/Users/ajoxendine68/Desktop/SSOT_Agentic_Brain/ops/scripts/fullscreen_ui/clara_b64.txt", "r") as f:
    clara_b64 = f.read().strip()

import base64
with open("/Users/ajoxendine68/Desktop/SSOT_Agentic_Brain/ops/scripts/fullscreen_ui/images/maxx.jpg", "rb") as f:
    maxx_b64 = "data:image/jpeg;base64," + base64.b64encode(f.read()).decode('utf-8')

HTML_FILE = "/Users/ajoxendine68/Desktop/SSOT_Agentic_Brain/ops/scripts/fullscreen_ui/customer_app.html"

html_code = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>XORAS Sovereign Stage</title>
    <style>
        * {{ margin:0; padding:0; box-sizing:border-box; }}
        body, html {{ width:100vw; height:100vh; overflow:hidden; background:#010204; font-family:-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; }}

        #webglCanvas {{ position:absolute; top:0; left:0; width:100vw; height:100vh; z-index:1; }}

        /* Top Left Header */
        .top-bar {{
            position:absolute; top:24px; left:36px; z-index:10;
            font-size:12px; font-weight:800; letter-spacing:3px; color:#A0B2C6;
            display:flex; align-items:center; text-shadow:0 2px 10px rgba(0,0,0,0.9);
        }}
        .live-dot {{ display:inline-block; width:9px; height:9px; border-radius:50%; background:#00F2FE; margin-right:10px; box-shadow:0 0 14px #00F2FE; animation:pulse 2s infinite; }}
        @keyframes pulse {{ 0% {{ opacity:0.3; }} 50% {{ opacity:1; }} 100% {{ opacity:0.3; }} }}

        /* Compact Ticker with Word-By-Word Glowing Subtitle Engine */
        .compact-ticker-wrap {{
            position:absolute; bottom:28px; left:50%; transform:translateX(-50%);
            width:88%; max-width:640px; z-index:10;
            background: rgba(8, 12, 22, 0.82);
            backdrop-filter: blur(30px); -webkit-backdrop-filter: blur(30px);
            border: 1px solid rgba(0, 242, 254, 0.4);
            border-radius: 12px;
            padding: 12px 24px;
            box-shadow: 0 20px 50px rgba(0, 0, 0, 0.95), inset 0 1px 0 rgba(255,255,255,0.1);
            display: flex; flex-direction: column; align-items: center; text-align: center;
        }}
        .ticker-header {{
            display: flex; align-items: center; justify-content: space-between; width: 100%;
            margin-bottom: 5px; padding-bottom: 5px; border-bottom: 1px solid rgba(255,255,255,0.08);
        }}
        .ticker-tag {{ font-size: 10px; font-weight: 800; letter-spacing: 2.5px; color: #00F2FE; text-transform: uppercase; }}
        .ticker-state {{ font-size: 9px; font-weight: 700; letter-spacing: 1.5px; color: #64748B; }}

        .ticker-stream-box {{
            width: 100%; overflow: hidden; position: relative;
            min-height: 40px; display: flex; align-items: center; justify-content: center;
            flex-wrap: wrap; gap: 6px; padding: 2px 0;
        }}

        /* Word styling */
        .speech-word {{
            font-size: 17px; font-weight: 500; font-style: italic; color: #64748B;
            transition: all 0.12s ease; display: inline-block;
        }}
        /* Real-time Highlight: Glow as spoken */
        .speech-word.active {{
            color: #00F2FE; font-weight: 800; transform: scale(1.15);
            text-shadow: 0 0 16px rgba(0, 242, 254, 0.95), 0 0 30px rgba(0, 242, 254, 0.6);
        }}
        .speech-word.spoken {{
            color: #F8FAFC;
        }}
    </style>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/three.js/r128/three.min.js"></script>
</head>
<body>
    <canvas id="webglCanvas"></canvas>

    <div class="top-bar">
        <span class="live-dot"></span>XORAS SOVEREIGN STAGE
    </div>

    <div class="compact-ticker-wrap">
        <div class="ticker-header">
            <span class="ticker-tag" id="activeAgentRole">CLARA · THE SANCTUARY</span>
            <span class="ticker-state" id="syncStatus">FLAWLESS SYNC ACTIVE</span>
        </div>
        <div class="ticker-stream-box" id="tickerContent">
            <span class="speech-word spoken">Flawless</span>
            <span class="speech-word active">word-by-word</span>
            <span class="speech-word">synchronization</span>
            <span class="speech-word">active.</span>
        </div>
    </div>

    <script>
        const CLARA_IMG = '{clara_b64}';
        const MAXX_IMG = '{maxx_b64}';

        const scene = new THREE.Scene();
        const camera = new THREE.PerspectiveCamera(45, window.innerWidth / window.innerHeight, 0.1, 1000);
        camera.position.z = 10;

        const renderer = new THREE.WebGLRenderer({{ canvas: document.getElementById('webglCanvas'), antialias: true, alpha: true }});
        renderer.setSize(window.innerWidth, window.innerHeight);
        renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));

        const textureLoader = new THREE.TextureLoader();
        let currentTexture = textureLoader.load(CLARA_IMG);

        // Subdivided 3D mesh plane for undulating depth wave
        const planeGeo = new THREE.PlaneGeometry(12, 6.75, 48, 48);
        const planeMat = new THREE.MeshBasicMaterial({{
            map: currentTexture,
            side: THREE.DoubleSide,
            transparent: true,
            opacity: 0.96
        }});
        const portraitMesh = new THREE.Mesh(planeGeo, planeMat);
        portraitMesh.position.set(0, 0.2, 0);
        scene.add(portraitMesh);

        // 768-Point Vector Constellation
        const VECTOR_DIM = 768;
        const vectorPositions = new Float32Array(VECTOR_DIM * 3);
        for (let i = 0; i < VECTOR_DIM * 3; i += 3) {{
            const theta = Math.acos(1 - 2 * (i / 3) / VECTOR_DIM);
            const phi = Math.PI * (1 + Math.sqrt(5)) * (i / 3);
            const r = 5.2 + (Math.sin(i) * 0.4);
            vectorPositions[i] = r * Math.sin(theta) * Math.cos(phi);
            vectorPositions[i+1] = r * Math.sin(theta) * Math.sin(phi);
            vectorPositions[i+2] = r * Math.cos(theta) * 0.7;
        }}
        const vectorGeo = new THREE.BufferGeometry();
        vectorGeo.setAttribute('position', new THREE.BufferAttribute(vectorPositions, 3));
        const vectorMat = new THREE.PointsMaterial({{ size: 0.065, color: 0x00F2FE, transparent: true, opacity: 0.85, blending: THREE.AdditiveBlending }});
        const vectorPoints = new THREE.Points(vectorGeo, vectorMat);
        scene.add(vectorPoints);

        let clock = new THREE.Clock();
        function animate() {{
            requestAnimationFrame(animate);
            const elapsed = clock.getElapsedTime();

            // Organic breathing wave on 3D portrait
            const posAttr = planeGeo.attributes.position;
            for (let i = 0; i < posAttr.count; i++) {{
                const u = posAttr.getX(i);
                const v = posAttr.getY(i);
                posAttr.setZ(i, Math.sin(u * 0.8 + elapsed * 1.5) * Math.cos(v * 0.8 + elapsed * 1.2) * 0.12);
            }}
            posAttr.needsUpdate = true;

            vectorPoints.rotation.y = elapsed * 0.06;
            vectorPoints.rotation.x = Math.sin(elapsed * 0.04) * 0.15;
            renderer.render(scene, camera);
        }}
        animate();

        window.addEventListener('resize', () => {{
            camera.aspect = window.innerWidth / window.innerHeight;
            camera.updateProjectionMatrix();
            renderer.setSize(window.innerWidth, window.innerHeight);
        }});

        // Real-time Word-By-Word Timing Synchronizer Loop
        let activeTiming = null;
        let lastTimingText = '';

        function renderWords(words) {{
            const container = document.getElementById('tickerContent');
            container.innerHTML = '';
            words.forEach((item, idx) => {{
                const span = document.createElement('span');
                span.className = 'speech-word';
                span.id = 'word-' + idx;
                span.innerText = item.word;
                container.appendChild(span);
            }});
        }}

        // Poll timing every 50ms for razor-sharp highlight
        setInterval(() => {{
            fetch('/current_timing.json?t=' + Date.now())
                .then(r => r.json())
                .then(data => {{
                    if (data && data.text && data.text !== lastTimingText) {{
                        lastTimingText = data.text;
                        activeTiming = data;
                        renderWords(data.words);
                        
                        // Switch agent image synchronously
                        if (data.agent === 'maxx') {{
                            planeMat.map = textureLoader.load(MAXX_IMG);
                            document.getElementById('activeAgentRole').innerText = 'MAXX · SOVEREIGN LEAD';
                        }} else {{
                            planeMat.map = textureLoader.load(CLARA_IMG);
                            document.getElementById('activeAgentRole').innerText = 'CLARA · THE SANCTUARY';
                        }}
                    }}

                    // Highlight words in real-time
                    if (activeTiming && activeTiming.words && !activeTiming.complete) {{
                        const elapsed = (Date.now() / 1000) - activeTiming.start_time;
                        activeTiming.words.forEach((w, idx) => {{
                            const el = document.getElementById('word-' + idx);
                            if (el) {{
                                if (elapsed >= w.start && elapsed <= w.end) {{
                                    el.className = 'speech-word active';
                                }} else if (elapsed > w.end) {{
                                    el.className = 'speech-word spoken';
                                }} else {{
                                    el.className = 'speech-word';
                                }}
                            }}
                        }});
                    }}
                }}).catch(()=>{{}});
        }}, 50);
    </script>
</body>
</html>
"""

with open(HTML_FILE, "w") as f:
    f.write(html_code)

print("FLAWLESS_SYNC_UI_DEPLOYED")
