#include <stdio.h>
#include <stdint.h>
#include <oqs/oqs.h>

int main(void) {
    OQS_SIG *sig = OQS_SIG_new("ML-DSA-44");
    if (sig == NULL) {
        fprintf(stderr, "ERROR: Dilithium2 not supported by liboqs\n");
        return 1;
    }

    uint8_t pk[sig->length_public_key];
    uint8_t sk[sig->length_secret_key];

    if (OQS_SIG_keypair(sig, pk, sk) != OQS_SUCCESS) {
        fprintf(stderr, "ERROR: Dilithium key generation failed\n");
        OQS_SIG_free(sig);
        return 1;
    }

    FILE *fpk = fopen("server/pqc_keys/dilithium_pk.bin", "wb");
    FILE *fsk = fopen("server/pqc_keys/dilithium_sk.bin", "wb");

    if (!fpk || !fsk) {
        fprintf(stderr, "ERROR: Could not open Dilithium key files\n");
        OQS_SIG_free(sig);
        return 1;
    }

    fwrite(pk, 1, sizeof(pk), fpk);
    fwrite(sk, 1, sizeof(sk), fsk);

    fclose(fpk);
    fclose(fsk);
    OQS_SIG_free(sig);

    printf("Dilithium keypair generated successfully\n");
    return 0;
}