#include <arm_neon.h>

extern "C" float32x4_t func_60c4a1f4(void *, const float32x4_t *p1, const float32x4_t *p2, const float32x4_t *p3)
{
    float32x4_t a = *p2;
    float32x4_t b = *p1;
    float32x4_t c = *p3;

    a = vmaxq_f32(b, a);
    return vminq_f32(a, c);
}