#include <stdint.h>
#include <arm_neon.h>

extern "C" void func_60c4a1e8(void *a, uint32_t *b, const uint64_t *c) {
    const uint64_t *cc = (const uint64_t *)__builtin_assume_aligned(c, 16);
    uint64x2_t tmp = vld1q_u64(cc);
    vst1q_u32(b, vreinterpretq_u32_u64(tmp));
}