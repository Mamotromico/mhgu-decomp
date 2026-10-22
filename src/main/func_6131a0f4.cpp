struct func_6131a0f4_ctx {
    unsigned char pad_0[0xa15];
    volatile unsigned char field_a15;
    unsigned char pad_a16[0x2c2];
    volatile unsigned int field_cd8;
};

extern "C" void func_6131a0f4(func_6131a0f4_ctx *ctx, unsigned char value) {
    ctx->field_a15 = value;
    ctx->field_cd8 |= 0x8;
}