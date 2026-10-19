#include <arm_neon.h>

extern "C" float32x4_t func_60c4a1d8(void *unused, const float32x4_t *a, const float32x4_t *b)
{
    (void)unused;
    float32x4_t vb = *(const float32x4_t *)__builtin_assume_aligned(b, 16);
    float32x4_t va = *(const float32x4_t *)__builtin_assume_aligned(a, 16);
    return vmaxq_f32(va, vb);
}