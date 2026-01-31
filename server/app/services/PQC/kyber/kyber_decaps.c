#include <stdio.h>
#include <stdint.h>
#include <oqs/oqs.h>

int main(void) {
    /* 1️⃣ Create Kyber KEM */
    OQS_KEM *kem = OQS_KEM_new("Kyber512");
    if (kem == NULL) {
        fprintf(stderr, "ERROR: Kyber512 not supported by liboqs\n");
        return 1;
    }

    /* 2️⃣ Load secret key */
    uint8_t sk[OQS_KEM_kyber_512_length_secret_key];
    uint8_t ct[OQS_KEM_kyber_512_length_ciphertext];

    FILE *fsk = fopen("pqc_keys/kyber_sk.bin", "rb");
    FILE *fct = fopen("pqc_keys/kyber_ct.bin", "rb");

    if (!fsk || !fct) {
        fprintf(stderr, "ERROR: Could not open Kyber input files\n");
        OQS_KEM_free(kem);
        return 1;
    }

    fread(sk, 1, sizeof(sk), fsk);
    fread(ct, 1, sizeof(ct), fct);

    fclose(fsk);
    fclose(fct);

    /* 3️⃣ Decapsulation */
    uint8_t ss[OQS_KEM_kyber_512_length_shared_secret];

    if (OQS_KEM_decaps(kem, ss, ct, sk) != OQS_SUCCESS) {
        fprintf(stderr, "ERROR: Kyber decapsulation failed\n");
        OQS_KEM_free(kem);
        return 1;
    }

    /* 4️⃣ Write shared secret */
    FILE *fss = fopen("pqc_keys/shared_secret_receiver.bin", "wb");
    if (!fss) {
        fprintf(stderr, "ERROR: Could not write shared secret\n");
        OQS_KEM_free(kem);
        return 1;
    }

    fwrite(ss, 1, sizeof(ss), fss);
    fclose(fss);

    OQS_KEM_free(kem);

    printf("Kyber decapsulation successful\n");
    return 0;
}