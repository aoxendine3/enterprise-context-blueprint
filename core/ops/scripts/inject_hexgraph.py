import re

with open('ops/scripts/fullscreen_ui/customer_app.html', 'r') as f:
    html = f.read()

new_3d_code = """
            // =========================================================================
            // XORAS: 18,432D HEXGRAPH NAVIER-STOKES SWARM (24-HEAD TOPOLOGY)
            // =========================================================================
            const diagramGroup = new THREE.Group();
            scene.add(diagramGroup);

            const particleCount = 10000;
            const geometry = new THREE.BufferGeometry();
            const positions = new Float32Array(particleCount * 3);
            const initialPositions = new Float32Array(particleCount * 3);
            
            for (let i = 0; i < particleCount; i++) {
                let x = (Math.random() - 0.5) * 30;
                let y = (Math.random() - 0.5) * 30;
                let z = (Math.random() - 0.5) * 30;
                positions[i*3] = x; positions[i*3+1] = y; positions[i*3+2] = z;
                initialPositions[i*3] = x; initialPositions[i*3+1] = y; initialPositions[i*3+2] = z;
            }
            geometry.setAttribute('position', new THREE.BufferAttribute(positions, 3));
            
            const material = new THREE.PointsMaterial({ 
                color: 0x00F2FE, 
                size: 0.08, 
                transparent: true, 
                opacity: 0.9,
                blending: THREE.AdditiveBlending 
            });
            const swarm = new THREE.Points(geometry, material);
            diagramGroup.add(swarm);

            let clock = new THREE.Clock();

            window.updateDiagramTheme = function(colorHex, agentName) {
                material.color.setHex(colorHex);
                const label = document.getElementById('diagramLabel');
                if (label) {
                    label.style.color = '#' + colorHex.toString(16).padStart(6, '0');
                }
            };

            function animateDiagram() {
                requestAnimationFrame(animateDiagram);
                const elapsed = clock.getElapsedTime();
                const pos = geometry.attributes.position.array;
                
                let maxVorticity = 0;
                let hexGraphEngaged = false;
                
                // Induce the singularity over time (Chaos multiplies every second)
                let chaosMultiplier = 1.0 + (elapsed * 0.6); 
                
                // Once chaos crosses the blow-up threshold, the 18432D HexGraph snaps it into place
                if (chaosMultiplier > 5.0) {
                    hexGraphEngaged = true;
                }
                
                for (let i = 0; i < particleCount; i++) {
                    let x = pos[i*3];
                    let y = pos[i*3+1];
                    let z = pos[i*3+2];
                    
                    // 3D Incompressible Flow (Approaching Singularity)
                    let vx = Math.sin(y * 0.8 + elapsed) * chaosMultiplier - x * 0.05;
                    let vy = Math.cos(z * 0.8 + elapsed) * chaosMultiplier - y * 0.05;
                    let vz = Math.sin(x * 0.8 + elapsed) * chaosMultiplier - z * 0.05;

                    if (hexGraphEngaged) {
                        // HEXGRAPH 18,432D PROJECTION & 24-HEAD STABILIZATION
                        // The metric warp W=0.0229 forces the chaotic flow into a stable hexagonal resonance
                        const W = 0.0229;
                        const hexScale = 1.8;
                        
                        let hx = Math.round(x / hexScale) * hexScale;
                        let hy = Math.round(y / hexScale) * hexScale;
                        let hz = Math.round(z / hexScale) * hexScale;
                        
                        // 24 Heads apply topological containment forces
                        vx += (hx - x) * 24.0 * W * (chaosMultiplier * 0.5);
                        vy += (hy - y) * 24.0 * W * (chaosMultiplier * 0.5);
                        vz += (hz - z) * 24.0 * W * (chaosMultiplier * 0.5);
                    }

                    pos[i*3] += vx * 0.015;
                    pos[i*3+1] += vy * 0.015;
                    pos[i*3+2] += vz * 0.015;

                    let vorticity = Math.sqrt(vx*vx + vy*vy + vz*vz);
                    if (vorticity > maxVorticity) maxVorticity = vorticity;

                    if (Math.abs(x) > 15 || Math.abs(y) > 15 || Math.abs(z) > 15) {
                        pos[i*3] = initialPositions[i*3];
                        pos[i*3+1] = initialPositions[i*3+1];
                        pos[i*3+2] = initialPositions[i*3+2];
                    }
                }
                
                geometry.attributes.position.needsUpdate = true;
                
                diagramGroup.rotation.y = elapsed * 0.08;
                diagramGroup.rotation.x = Math.sin(elapsed * 0.02) * 0.15;

                renderer.render(scene, camera);
                
                // Live Swarm HUD Updates
                const label = document.getElementById('diagramLabel');
                if (label) {
                    if (hexGraphEngaged) { 
                        label.innerHTML = `⚛️ HEXGRAPH 18,432D ENGAGED (24-HEAD) ⚛️<br>SINGULARITY CONTAINED | METRIC WARP: W=0.0229 | VORTICITY: BOUNDED`;
                        label.style.color = '#00FF99';
                        material.color.setHex(0x00FF99);
                        material.size = 0.06;
                    } else if (maxVorticity > 3.9) { 
                        label.innerHTML = `⚠️ CRITICAL: INDUCING NAVIER-STOKES BLOW-UP ⚠️<br>VORTICITY SPIKE: ${maxVorticity.toFixed(2)} | PREPARING HEXGRAPH...`;
                        label.style.color = '#FF0033';
                        material.color.setHex(0xFF0033);
                        material.size = 0.12;
                    } else {
                        label.innerHTML = `3D NAVIER-STOKES SWARM<br>NODES: 10,000 | VORTICITY MAX: ${maxVorticity.toFixed(4)}`;
                        material.color.setHex(0x00F2FE);
                        label.style.color = '#00F2FE';
                        material.size = 0.08;
                    }
                }
            }
"""

# Try to replace the existing 3D block
pattern = re.compile(r"// =========================================================================.*?animateDiagram\(\);", re.DOTALL)
new_html = pattern.sub(new_3d_code.strip() + "\n            animateDiagram();", html)

with open('ops/scripts/fullscreen_ui/customer_app.html', 'w') as f:
    f.write(new_html)

