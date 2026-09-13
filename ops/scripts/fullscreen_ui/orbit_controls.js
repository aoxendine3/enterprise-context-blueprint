/*
 * XORAS Real-Time 3D Interactive Orbit & Pan Controls Engine
 * Embedded Standalone Asset for Offline 3D Scene Interaction
 */
(function() {
    window.initInteractive3DControls = function(camera, domElement, onUpdate) {
        let isDragging = false;
        let previousMousePosition = { x: 0, y: 0 };
        let targetRotation = { x: 0, y: 0 };
        let currentRotation = { x: 0, y: 0 };
        let zoomDistance = camera.position.z || 10;

        domElement.style.cursor = 'grab';

        domElement.addEventListener('mousedown', (e) => {
            isDragging = true;
            previousMousePosition = { x: e.clientX, y: e.clientY };
            domElement.style.cursor = 'grabbing';
        });

        window.addEventListener('mousemove', (e) => {
            if (!isDragging) return;

            const deltaMove = {
                x: e.clientX - previousMousePosition.x,
                y: e.clientY - previousMousePosition.y
            };

            targetRotation.y += deltaMove.x * 0.005;
            targetRotation.x += deltaMove.y * 0.005;

            // Clamp vertical rotation
            targetRotation.x = Math.max(-Math.PI / 3, Math.min(Math.PI / 3, targetRotation.x));

            previousMousePosition = { x: e.clientX, y: e.clientY };
        });

        window.addEventListener('mouseup', () => {
            isDragging = false;
            domElement.style.cursor = 'grab';
        });

        domElement.addEventListener('wheel', (e) => {
            e.preventDefault();
            zoomDistance += e.deltaY * 0.005;
            zoomDistance = Math.max(4, Math.min(22, zoomDistance));
            camera.position.z = zoomDistance;
        }, { passive: false });

        return function updateControls() {
            currentRotation.x += (targetRotation.x - currentRotation.x) * 0.1;
            currentRotation.y += (targetRotation.y - currentRotation.y) * 0.1;

            if (onUpdate) {
                onUpdate(currentRotation.x, currentRotation.y, zoomDistance);
            }
        };
    };
})();
