"""Pinned public trust for signed receipt-profile fixture attestations.

Private signing material is deliberately absent from the repository and wheel.
"""

TRUSTED_OBSERVERS = {
    "fixture-observer-attester": {
        "algorithm": "rsa-pkcs1v15-sha256",
        "exponent": 65537,
        "key_id": "fixture-receipt-observer-key-v1",
        "modulus_hex": "a1b25b7483e9a4d469ca65c4418a37a5c860681b8f36840a241a30855ae2dd3cb3ade21c4efa815c165b1d2fbc8eb49332fc0d1f8bcd79b0c576eaccdbde54df3150e2632d44504dac565fb6f28da732a240d4b7c86775f87b2e628113effdd5",
        "trust_epoch": 1
    }
}

TRUSTED_CLEANUP_ATTESTERS = {
    "fixture-cleanup-attester": {
        "algorithm": "rsa-pkcs1v15-sha256",
        "exponent": 65537,
        "key_id": "fixture-receipt-cleanup-key-v1",
        "modulus_hex": "6513c2bb128af3b9a8b30303d36909da2467293eb072aa3801408374aef705bdd015203d13ec3e9fc841d894d774286b21356b2b451a69a3da02d04d06aefba7694331b2b181936acdc94c81ad5350ebee3b5e1ca8c0b022f88659d9108e599d",
        "trust_epoch": 1
    }
}
