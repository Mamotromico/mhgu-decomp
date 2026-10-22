struct Context_605048e8 {
    unsigned char pad[0x344];
    int value;
};

extern "C" int func_605048e8(Context_605048e8 *ctx) {
    int result = 0;
    if (ctx->value == 2) {
        result = 1;
    }
    return result;
}