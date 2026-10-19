struct Context6007109c {
    unsigned char pad[0x75f4];
    void *field;
};

extern "C" void *func_6007109c(Context6007109c *ctx) {
    void *p = ctx->field;
    return p ? (void *)((char *)p + 0x68) : 0;
}