struct elem_600e0d7c { char data[12]; };
struct ctx_600e0d7c { char pad[0x18c]; struct elem_600e0d7c *field; };

extern "C" struct elem_600e0d7c *func_600e0d7c(struct ctx_600e0d7c *ctx, int index) {
    struct elem_600e0d7c *p = ctx->field;
    return p ? p + index : 0;
}