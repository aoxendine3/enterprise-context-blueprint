import json, os

B64_FILE = "/Users/ajoxendine68/Desktop/SSOT_Agentic_Brain/ops/scripts/fullscreen_ui/clara_b64.txt"
HTML_OUT = "/Users/ajoxendine68/Desktop/SSOT_Agentic_Brain/ops/scripts/fullscreen_ui/customer_app.html"

with open(B64_FILE, "r") as f:
    clara_data_uri = f.read().strip()

html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>XORAS Sovereign Stage</title>
    <style>
        * {{ margin:0; padding:0; box-sizing:border-box; }}
        body, html {{ width:100vw; height:100vh; overflow:hidden; background:#020408; font-family:-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; }}

        /* Canvas Viewport */
        #webglCanvas {{ position:absolute; top:0; left:0; width:100vw; height:100vh; z-index:1; }}

        /* Subtle Top Vignette */
        .vignette-overlay {{
            position:absolute; top:0; left:0; width:100vw; height:100vh; z-index:2;
            background: radial-gradient(circle at 50% 40%, rgba(0,0,0,0) 40%, rgba(2,4,8,0.7) 80%, rgba(2,4,8,0.95) 100%);
            pointer-events:none;
        }}

        /* Header Telemetry */
        .top-bar {{
            position:absolute; top:22px; left:32px; z-index:10;
            font-size:11px; font-weight:800; letter-spacing:3px; color:#A0B2C6;
            display:flex; align-items:center; text-shadow:0 2px 10px rgba(0,0,0,0.9);
        }}
        .live-dot {{ display:inline-block; width:8px; height:8px; border-radius:50%; background:#00F2FE; margin-right:9px; box-shadow:0 0 12px #00F2FE; animation:pulse 2s infinite; }}
        @keyframes pulse {{ 0% {{ opacity:0.3; }} 50% {{ opacity:1; }} 100% {{ opacity:0.3; }} }}

        /* Compact, Smaller Width Ticker Box across bottom */
        .compact-ticker-wrap {{
            position:absolute; bottom:28px; left:50%; transform:translateX(-50%);
            width:90%; max-width:640px; z-index:10;
            background: rgba(8, 12, 22, 0.78);
            backdrop-filter: blur(28px); -webkit-backdrop-filter: blur(28px);
            border: 1px solid rgba(0, 242, 254, 0.35);
            border-radius: 12px;
            padding: 12px 22px;
            box-shadow: 0 20px 45px rgba(0, 0, 0, 0.92), inset 0 1px 0 rgba(255,255,255,0.1);
            display: flex; flex-direction: column; align-items: center; text-align: center;
        }}
        .ticker-header {{
            display: flex; align-items: center; justify-content: space-between; width: 100%;
            margin-bottom: 4px; padding-bottom: 4px; border-bottom: 1px solid rgba(255,255,255,0.08);
        }}
        .ticker-tag {{ font-size: 10px; font-weight: 800; letter-spacing: 2px; color: #00F2FE; text-transform: uppercase; }}
        .ticker-vector-tag {{ font-size: 9px; font-weight: 700; letter-spacing: 1px; color: #64748B; }}

        .ticker-stream-box {{
            width: 100%; overflow: hidden; position: relative;
            height: 38px; display: flex; align-items: center; justify-content: center;
        }}
        .ticker-text {{
            font-size: 16px; font-weight: 500; font-style: italic; color: #F8FAFC; line-height: 1.35;
            letter-spacing: 0.3px; text-shadow: 0 1px 6px rgba(0,0,0,0.8);
            transition: opacity 0.2s ease;
        }}
    </style>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/three.js/r128/three.min.js"></script>
</head>
<body>
    <div class="vignette-overlay"></div>
    <canvas id="webglCanvas"></canvas>

    <div class="top-bar">
        <span class="live-dot"></span>XORAS SOVEREIGN STAGE
    </div>

    <div class="compact-ticker-wrap">
        <div class="ticker-header">
            <span class="ticker-tag" id="activeAgentRole">CLARA · THE SANCTUARY</span>
            <span class="ticker-vector-tag">768-DIMENSIONAL SPATIAL MESH</span>
        </div>
        <div class="ticker-stream-box">
            <div id="tickerContent" class="ticker-text">
                "Anthony, this is Clara. 768-point vector projection active in 3D motion."
            </div>
        </div>
    </div>

    <script>
        const scene = new THREE.Scene();
        const camera = new THREE.PerspectiveCamera(45, window.innerWidth / window.innerHeight, 0.1, 1000);
        camera.position.z = 10;

        const renderer = new THREE.WebGLRenderer({{ canvas: document.getElementById('webglCanvas'), antialias: true, alpha: true }});
        renderer.setSize(window.innerWidth, window.innerHeight);
        renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));

        // 1. Full-Screen 3D Textured Motion Plane (Never cut off head)
        const textureLoader = new THREE.TextureLoader();
        const claraTexture = textureLoader.load('{clara_data_uri}', () => {{
            renderer.render(scene, camera);
        }});

        // Create high-subdivision mesh for undulating spatial wave motion
        const planeGeo = new THREE.PlaneGeometry(12, 6.75, 48, 48);
        const planeMat = new THREE.MeshBasicMaterial({{
            map: claraTexture,
            side: THREE.DoubleSide,
            transparent: true,
            opacity: 0.95
        }});
        const portraitMesh = new THREE.Mesh(planeGeo, planeMat);
        portraitMesh.position.set(0, 0.2, 0); // Positioned so head/eyes stay centered
        scene.add(portraitMesh);

        // 2. Exact 768-Dimensional Vector Constellation (Dynamic Holographic Layer)
        const VECTOR_DIM = 768;
        const vectorPositions = new Float32Array(VECTOR_DIM * 3);
        const originalPositions = new Float32Array(VECTOR_DIM * 3);
        
        for (let i = 0; i < VECTOR_DIM * 3; i += 3) {{
            // Spherical Fibonacci / Vector embedding distribution
            const theta = Math.acos(1 - 2 * (i / 3) / VECTOR_DIM);
            const phi = Math.PI * (1 + Math.sqrt(5)) * (i / 3);
            const r = 5.2 + (Math.sin(i) * 0.4);
            
            const x = r * Math.sin(theta) * Math.cos(phi);
            const y = r * Math.sin(theta) * Math.sin(phi);
            const z = r * Math.cos(theta) * 0.7; // Compressed along z for stage depth
            
            vectorPositions[i] = x;
            vectorPositions[i+1] = y;
            vectorPositions[i+2] = z;
            
            originalPositions[i] = x;
            originalPositions[i+1] = y;
            originalPositions[i+2] = z;
        }}

        const vectorGeo = new THREE.BufferGeometry();
        vectorGeo.setAttribute('position', new THREE.BufferAttribute(vectorPositions, 3));
        const vectorMat = new THREE.PointsMaterial({{
            size: 0.065,
            color: 0x00F2FE,
            transparent: true,
            opacity: 0.85,
            blending: THREE.AdditiveBlending
        }});
        const vectorPoints = new THREE.Points(vectorGeo, vectorMat);
        scene.add(vectorPoints);

        // Connecting Vector Lines (768d Topological Graph)
        const lineMat = new THREE.LineBasicMaterial({{ color: 0x00A3FF, transparent: true, opacity: 0.15 }});
        const lineGeo = new THREE.BufferGeometry();
        const linePositions = [];
        for (let i = 0; i < VECTOR_DIM * 3; i += 18) {{
            linePositions.push(vectorPositions[i], vectorPositions[i+1], vectorPositions[i+2]);
            linePositions.push(vectorPositions[(i+9) % (VECTOR_DIM*3)], vectorPositions[(i+10) % (VECTOR_DIM*3)], vectorPositions[(i+11) % (VECTOR_DIM*3)]);
        }}
        lineGeo.setAttribute('position', new THREE.Float32BufferAttribute(linePositions, 3));
        const vectorLines = new THREE.LineSegments(lineGeo, lineMat);
        scene.add(vectorLines);

        // 3. Animation Loop with Breathing 3D Motion
        let clock = new THREE.Clock();
        function animate() {{
            requestAnimationFrame(animate);
            const elapsed = clock.getElapsedTime();

            // Organic subtle breathing wave motion on the 3D portrait plane
            const posAttr = planeGeo.attributes.position;
            for (let i = 0; i < posAttr.count; i++) {{
                const u = posAttr.getX(i);
                const v = posAttr.getY(i);
                // Gentle depth displacement wave
                const zWave = Math.sin(u * 0.8 + elapsed * 1.5) * Math.cos(v * 0.8 + elapsed * 1.2) * 0.12;
                posAttr.setZ(i, zWave);
            }}
            posAttr.needsUpdate = true;

            // Rotating 768-Point Vector Mesh
            vectorPoints.rotation.y = elapsed * 0.06;
            vectorPoints.rotation.x = Math.sin(elapsed * 0.04) * 0.15;
            vectorLines.rotation.y = elapsed * 0.06;
            vectorLines.rotation.x = Math.sin(elapsed * 0.04) * 0.15;

            // Micro camera parallax
            camera.position.x = Math.sin(elapsed * 0.3) * 0.12;
            camera.position.y = Math.cos(elapsed * 0.25) * 0.08;
            camera.lookAt(0, 0, 0);

            renderer.render(scene, camera);
        }}
        animate();

        window.addEventListener('resize', () => {{
            camera.aspect = window.innerWidth / window.innerHeight;
            camera.updateProjectionMatrix();
            renderer.setSize(window.innerWidth, window.innerHeight);
        }});

        // Real-time Text Polling Loop
        let lastText = '';
        setInterval(() => {{
            fetch('/current_transcript.txt?t=' + Date.now())
                .then(r => r.text())
                .then(t => {{
                    const clean = t.trim();
                    if(clean && !clean.toLowerCase().includes('not found') && !clean.toLowerCase().includes('404') && clean !== lastText) {{
                        lastText = clean;
                        const el = document.getElementById('tickerContent');
                        el.style.opacity = '0';
                        setTimeout(() => {{
                            el.innerText = '"' + clean + '"';
                            el.style.opacity = '1';
                        }}, 150);
                    }}
                }}).catch(()=>{{}});
        }}, 150);
    </script>
</body>
</html>
"""

with open(HTML_OUT, "w") as f:
    f.write(html_content)

print("3D_MOTION_STAGE_WITH_768_VECTOR_COMPILED")
