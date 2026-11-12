/* Impulse response of Conduit's adjustable Bloom (ref/bloom.c) at 48 kHz, for comparing with Amble's.
   usage: bloom_ir type seconds size damping decay_seconds > out.f32 (stereo float) */
#include "bloom.h"
#include <math.h>
#include <stdio.h>
#include <stdlib.h>
int main(int argc, char **argv) {
    int type = atoi(argv[1]); double secs = atof(argv[2]); float size = atof(argv[3]), damp = atof(argv[4]), T = atof(argv[5]);
    Bloom b; bloom_init(&b, 1.024); bloom_set(&b, size, 0.5f, damp);
    float decay = expf(-4.2f * size / T) / 0.75f;
    int n = (int)(secs * 48000); float buf[2 * 256];
    for (int i = 0; i < n; i += 256) {
        for (int j = 0; j < 256; j++) buf[2*j] = buf[2*j+1] = (i == 0 && j == 0) ? 1.f : 0.f;
        bloom_process(&b, type, decay, buf, buf, 256);
        fwrite(buf, sizeof(float), 512, stdout);
    }
    return 0;
}
