struct func_600dce48_ctx {
    unsigned char pad0[4];
    unsigned short flags;
    unsigned char pad1[0x14 - 6];
    unsigned char field14;
};

extern "C" void func_600dce48(func_600dce48_ctx* ctx, unsigned char value) {
    if ((ctx->flags & 0x1f) == 0x14) {
        ctx->field14 = value;
    }
}