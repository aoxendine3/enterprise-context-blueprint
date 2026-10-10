const crypto = require('crypto');
const fs = require('fs');
const path = require('path');

/**
 * XORAS INSTITUTIONAL KEY GENERATOR
 * Simulates HSM provisioning for Trust Anchors.
 */

const anchors = [
    { id: 'AUTH-ADMIN-001', name: 'Global Governance Admin' },
    { id: 'AUTH-SEC-002', name: 'CISO' },
    { id: 'AUTH-ENG-003', name: 'Director of Engineering' }
];

const keyStore = {};
const registryUpdate = [];

anchors.forEach(a => {
    const { publicKey, privateKey } = crypto.generateKeyPairSync('ec', {
        namedCurve: 'secp256k1',
        publicKeyEncoding: { type: 'spki', format: 'pem' },
        privateKeyEncoding: { type: 'pkcs8', format: 'pem' }
    });

    keyStore[a.id] = privateKey;
    registryUpdate.push({
        id: a.id,
        publicKey: publicKey
    });
});

fs.writeFileSync('sandbox/hsm_private_keys.json', JSON.stringify(keyStore, null, 2));
fs.writeFileSync('sandbox/public_registry_patch.json', JSON.stringify(registryUpdate, null, 2));

console.log('INSTITUTIONAL KEYS GENERATED. Private keys stored in secure sandbox.');
