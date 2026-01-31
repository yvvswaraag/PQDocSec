#include <stdio.h>
#include <stdint.h>
#include <oqs/oqs.h>

int main(void) {
    OQS_KEM *kem = OQS_KEM_new("Kyber512");
    if (kem == NULL) {
        fprintf(stderr, "ERROR: Kyber512 not supported by liboqs\n");
        return 1;
    }

    uint8_t pk[OQS_KEM_kyber_512_length_public_key];
    uint8_t sk[OQS_KEM_kyber_512_length_secret_key];

    if (OQS_KEM_keypair(kem, pk, sk) != OQS_SUCCESS) {
        fprintf(stderr, "ERROR: Kyber key generation failed\n");
        OQS_KEM_free(kem);
        return 1;
    }

    FILE *fpk = fopen("server/pqc_keys/kyber_pk.bin", "wb");
    FILE *fsk = fopen("server/pqc_keys/kyber_sk.bin", "wb");

    if (!fpk || !fsk) {
        fprintf(stderr, "ERROR: Could not open key files for writing\n");
        OQS_KEM_free(kem);
        return 1;
    }

    fwrite(pk, 1, sizeof(pk), fpk);
    fwrite(sk, 1, sizeof(sk), fsk);

    fclose(fpk);
    fclose(fsk);

    OQS_KEM_free(kem);

    printf("Kyber keypair generated successfully\n");
    return 0;
}