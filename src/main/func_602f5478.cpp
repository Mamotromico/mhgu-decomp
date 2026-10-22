struct Context {
    unsigned char pad[0x28b8];
    int field;
};

extern "C" int func_602f5478(Context* ctx) {
    return ctx->field > 0;
}