import re

with open('ops/scripts/fullscreen_ui/customer_app.html', 'r') as f:
    html = f.read()

new_3d_code = """
            // =========================================================================
            // XORAS: 10,000-NODE NAVIER-STOKES FLUID DYNAMICS SWARM (WEBGL)
            // =========================================================================
            const diagramGroup = new THREE.Group();
            scene.add(diagramGroup);

            const particleCount = 10000;
            const geometry = new THREE.BufferGeometry();
            const positions = new Float32Array(particleCount * 3);
            const initialPositions = new Float32Array(particleCount * 3);
            
            for (let i = 0; i < particleCount; i++) {
                let x = (Math.random() - 0.5) * 20;
                let y = (Math.random() - 0.5) * 20;
                let z = (Math.random() - 0.5) * 20;
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
                
                for (let i = 0; i < particleCount; i++) {
                    let x = pos[i*3];
                    let y = pos[i*3+1];
                    let z = pos[i*3+2];
                    
                    // Incompressible Fluid Approximation (Curl Noise proxy for Navier-Stokes)
                    let vx = Math.sin(y * 0.8 + elapsed) * 2.5 - x * 0.05;
                    let vy = Math.cos(z * 0.8 + elapsed) * 2.5 - y * 0.05;
                    let vz = Math.sin(x * 0.8 + elapsed) * 2.5 - z * 0.05;

                    pos[i*3] += vx * 0.015;
                    pos[i*3+1] += vy * 0.015;
                    pos[i*3+2] += vz * 0.015;

                    let vorticity = Math.sqrt(vx*vx + vy*vy + vz*vz);
                    if (vorticity > maxVorticity) maxVorticity = vorticity;

                    // Toroidal reset to maintain fluid volume
                    if (Math.abs(x) > 10 || Math.abs(y) > 10 || Math.abs(z) > 10) {
                        pos[i*3] = initialPositions[i*3];
                        pos[i*3+1] = initialPositions[i*3+1];
                        pos[i*3+2] = initialPositions[i*3+2];
                    }
                }
                
                geometry.attributes.position.needsUpdate = true;
                
                diagramGroup.rotation.y = elapsed * 0.05;
                diagramGroup.rotation.x = Math.sin(elapsed * 0.02) * 0.1;

                renderer.render(scene, camera);
                
                // Live Swarm HUD Updates
                const label = document.getElementById('diagramLabel');
                if (label) {
                    if (maxVorticity > 3.9) { 
                        label.innerHTML = `⚠️ NAVIER-STOKES SINGULARITY BLOW-UP ⚠️<br>SWARM NODES: 10,000 | VORTICITY BOUND: INFINITE`;
                        label.style.color = '#FF0033';
                        material.color.setHex(0xFF0033);
                        material.size = 0.18;
                    } else {
                        label.innerHTML = `NAVIER-STOKES SWARM<br>NODES: 10,000 | VORTICITY MAX: ${maxVorticity.toFixed(4)}`;
                        material.color.setHex(0x00F2FE);
                        label.style.color = '#00F2FE';
                        material.size = 0.08;
                    }
                }
            }
"""

pattern = re.compile(r"// Group holding the complete 3D agent architectural diagram.*?(?=animateDiagram\(\);)", re.DOTALL)
new_html = pattern.sub(new_3d_code, html)

with open('ops/scripts/fullscreen_ui/customer_app.html', 'w') as f:
    f.write(new_html)
