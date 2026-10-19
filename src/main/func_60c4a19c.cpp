#include <arm_neon.h>
#include <stdint.h>

extern "C" uint32x4_t func_60c4a19c(uint32_t, const uint32_t *p)
{
    return vld1q_u32(p);
}