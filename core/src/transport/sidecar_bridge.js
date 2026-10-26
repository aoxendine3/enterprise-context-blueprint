/**
 * ============================================================================
 * XORAS::OS — HIGH-ASSURANCE SECURE SIDECAR INTEGRATION BRIDGE
 * Path: /core/src/transport/sidecar_bridge.js
 * Standards Compliance: NIST SP 800-218, NASA-STD-8719.13C (Fail-Closed)
 * ============================================================================
 */

(function () {
    'use strict';

    // 1. Immutable State Machine Definitions
    const State = Object.freeze({
        UNINITIALIZED: 'UNINITIALIZED',
        VERIFYING: 'VERIFYING',
        ACTIVE: 'ACTIVE',
        FAIL_CLOSED: 'FAIL_CLOSED'
    });

    let currentSystemState = State.UNINITIALIZED;

    // 2. Strict Host Configuration & Allowed Origins (Anchored to Host Trust Base)
    const TRUSTED_ORIGINS_ALLOWLIST = Object.freeze([
        'http://127.0.0.1:8080',
        'http://localhost:8080',
        'https://sovereign.xoras.local'
    ]);

    const APPROVED_ROUTES = Object.freeze([
        '/api/v1/sidecar/conversation',
        '/api/v1/sidecar/metadata',
        '/api/v1/sidecar/workspace'
    ]);

    const ALLOWED_CSS_PROPERTIES = Object.freeze([
        'background-color',
        'color',
        'font-family',
        'font-size',
        'theme-color'
    ]);

    // 3. Security Credentials & Context Containers (Privately Scoped)
    let secureSessionToken = null;
    let activeProjectIdentity = '';
    let parentWindowSource = null;
    let expectedParentOrigin = null;

    /**
     * Terminate all operations and lock the UI into a non-bypassable fail-closed state.
     * Replaces innerHTML string interpolation with safe, transactional textContent DOM updates.
     */
    function triggerFailClosedLockdown(reason) {
        currentSystemState = State.FAIL_CLOSED;
        secureSessionToken = null;
        activeProjectIdentity = '';
        
        console.error(`[CRITICAL SECURITY ABORT] State transition to FAIL_CLOSED: ${reason}`);

        const enforceLockdownDOM = () => {
            document.body.style.backgroundColor = '#0B0E11';
            document.body.style.color = '#FF9100';
            document.body.style.fontFamily = 'monospace';
            
            while (document.body.firstChild) {
                document.body.removeChild(document.body.firstChild);
            }

            const alertContainer = document.createElement('div');
            alertContainer.style.padding = '40px';
            alertContainer.style.border = '2px solid #FF9100';
            alertContainer.style.margin = '50px auto';
            alertContainer.style.maxWidth = '600px';
            alertContainer.style.boxShadow = '0 0 20px rgba(255, 145, 0, 0.3)';

            const header = document.createElement('h1');
            header.textContent = '🔒 SYSTEM FAIL-CLOSED ACTIVE';
            alertContainer.appendChild(header);

            const detail = document.createElement('p');
            detail.textContent = `Security Policy Violation Detected. Active session terminated. Reference: ${reason}`;
            alertContainer.appendChild(detail);

            const timestamp = document.createElement('div');
            timestamp.style.fontSize = '12px';
            timestamp.style.color = '#2C3843';
            timestamp.textContent = `System Epoch: ${Date.now()} ms`;
            alertContainer.appendChild(timestamp);

            document.body.appendChild(alertContainer);
        };

        if (document.body) {
            enforceLockdownDOM();
        } else {
            window.addEventListener('DOMContentLoaded', enforceLockdownDOM);
        }
    }

    /**
     * Safely load and validate credentials from sessionStorage.
     * Absolutely purges URL-based token exposures.
     */
    function resolveSecurityCredentials() {
        const urlParams = new URLSearchParams(window.location.search);
        if (urlParams.has('token') || urlParams.has('auth_token')) {
            triggerFailClosedLockdown('Token exposure detected in URL query parameters.');
            return false;
        }

        const storedToken = sessionStorage.getItem('X-SOVRA-DEEP-LOCK-TOKEN');
        if (!storedToken) {
            triggerFailClosedLockdown('Active session credentials missing from secure storage.');
            return false;
        }

        if (storedToken.length < 32) {
            triggerFailClosedLockdown('Insecure session token length detected.');
            return false;
        }

        secureSessionToken = storedToken;
        return true;
    }

    /**
     * Strictly validates incoming message payloads from the parent frame.
     */
    function handleIncomingHostMessage(event) {
        if (currentSystemState === State.FAIL_CLOSED) return;

        if (!TRUSTED_ORIGINS_ALLOWLIST.includes(event.origin)) {
            triggerFailClosedLockdown(`Unauthorized message origin: ${event.origin}`);
            return;
        }

        if (event.source !== window.parent) {
            triggerFailClosedLockdown('Message source mismatch: Originating window is not direct parent.');
            return;
        }

        const data = event.data;
        if (!data || typeof data !== 'object') {
            triggerFailClosedLockdown('Malformed postMessage payload received.');
            return;
        }

        if (!data.type) {
            triggerFailClosedLockdown('Missing schema type parameter in message envelope.');
            return;
        }

        switch (data.type) {
            case 'INITIALIZE_WORKSPACE':
                if (currentSystemState !== State.VERIFYING) {
                    triggerFailClosedLockdown('Illegal initialization attempt out of state sequence.');
                    return;
                }
                if (!data.projectId || typeof data.projectId !== 'string' || data.projectId.trim() === '') {
                    triggerFailClosedLockdown('Invalid or empty project identity schema.');
                    return;
                }
                activeProjectIdentity = data.projectId;
                currentSystemState = State.ACTIVE;
                console.info('[SYSTEM BRIDGE] Workspace initialized. State transitioned to ACTIVE.');
                break;

            case 'APPLY_THEME_MUTATION':
                if (currentSystemState !== State.ACTIVE) return;
                applySecureThemeStyle(data.styles);
                break;

            default:
                triggerFailClosedLockdown(`Unknown action event schema type: ${data.type}`);
        }
    }

    /**
     * Safely applies user/parent configurations under strict CSS property allowlists.
     */
    function applySecureThemeStyle(styles) {
        if (!styles || typeof styles !== 'object') {
            triggerFailClosedLockdown('Theme styling payload is malformed.');
            return;
        }

        for (const [property, value] of Object.entries(styles)) {
            if (!ALLOWED_CSS_PROPERTIES.includes(property)) {
                triggerFailClosedLockdown(`Security violation: CSS property '${property}' is not on the system allowlist.`);
                return;
            }

            const cleanValue = String(value).replace(/[<>;()]/g, '');
            document.documentElement.style.setProperty(`--theme-${property}`, cleanValue);
        }
    }

    /**
     * Wrapper for safe, restricted, same-origin fetch calls.
     */
    async function secureFetch(route, options = {}) {
        if (currentSystemState !== State.ACTIVE) {
            throw new Error('Blocked secure fetch call: system state must be ACTIVE.');
        }

        if (!APPROVED_ROUTES.includes(route)) {
            triggerFailClosedLockdown(`Attempted illegal egress route: ${route}`);
            throw new Error(`Egress route blocked: ${route}`);
        }

        const headers = new Headers(options.headers || {});
        headers.set('Authorization', `Bearer ${secureSessionToken}`);
        headers.set('X-SOVRA-PROJECT-ID', activeProjectIdentity);

        const secureOptions = {
            ...options,
            headers: headers,
            credentials: 'same-origin'
        };

        try {
            const response = await fetch(route, secureOptions);
            if (response.status === 401 || response.status === 403) {
                triggerFailClosedLockdown(`Authorization fault returned from server: ${response.status}`);
                throw new Error('Critical access termination.');
            }
            return response;
        } catch (error) {
            triggerFailClosedLockdown(`Network connection aborted: ${error.message}`);
            throw error;
        }
    }

    // 4. Initialization Gating
    function initializeBridge() {
        currentSystemState = State.VERIFYING;

        if (!resolveSecurityCredentials()) return;

        window.addEventListener('message', handleIncomingHostMessage);

        setTimeout(() => {
            if (currentSystemState === State.VERIFYING) {
                triggerFailClosedLockdown('Workspace initialization timeout exceeded. Parent frame failed to sync.');
            }
        }, 5000);
    }

    window.sidecar = Object.freeze({
        fetch: secureFetch,
        getStatus: () => currentSystemState,
        getProjectIdentity: () => activeProjectIdentity
    });

    initializeBridge();
})();
