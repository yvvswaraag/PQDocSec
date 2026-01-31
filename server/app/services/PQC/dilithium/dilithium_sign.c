#include <stdio.h>
#include <stdint.h>
#include <oqs/oqs.h>

int main(void) {
    /* 1️⃣ Create ML-DSA signer */
    OQS_SIG *sig = OQS_SIG_new("ML-DSA-44");
    if (sig == NULL) {
        fprintf(stderr, "ERROR: ML-DSA-44 not supported\n");
        return 1;
    }

    /* 2️⃣ Load secret key */
    uint8_t sk[sig->length_secret_key];

    FILE *fsk = fopen("pqc_keys/dilithium_sk.bin", "rb");
    if (!fsk) {
        fprintf(stderr, "ERROR: Could not open secret key file\n");
        OQS_SIG_free(sig);
        return 1;
    }

    fread(sk, 1, sizeof(sk), fsk);
    fclose(fsk);

    /* 3️⃣ Message to sign (example: SHA-512 hash output) */
    uint8_t message[64];  // replace with real hash input
    for (int i = 0; i < 64; i++) message[i] = (uint8_t)i;

    /* 4️⃣ Sign */
    uint8_t signature[sig->length_signature];
    size_t sig_len = 0;

    if (OQS_SIG_sign(sig,
                     signature, &sig_len,
                     message, sizeof(message),
                     sk) != OQS_SUCCESS) {
        fprintf(stderr, "ERROR: Signature generation failed\n");
        OQS_SIG_free(sig);
        return 1;
    }

    /* 5️⃣ Write signature */
    FILE *fs = fopen("pqc_keys/signature.bin", "wb");
    if (!fs) {
        fprintf(stderr, "ERROR: Could not write signature file\n");
        OQS_SIG_free(sig);
        return 1;
    }

    fwrite(signature, 1, sig_len, fs);
    fclose(fs);

    OQS_SIG_free(sig);

    printf("ML-DSA signature generated successfully\n");
    return 0;
}